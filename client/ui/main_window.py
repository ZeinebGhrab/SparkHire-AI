"""
Fenêtre Principale - FIX AUDIO COMPLET
Problème résolu: QAudioSink configuré dynamiquement selon le vrai sample rate
du TTS (Coqui génère du 22050Hz ou 24000Hz, pas du 16000Hz fixe).

FIX VOIX COUPÉE: le timer de surveillance IdleState ne démarre qu'après
la durée théorique de l'audio, évitant les faux positifs au démarrage.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QMessageBox, QLabel, QLineEdit, QPushButton, QFrame,
    QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QSize, QByteArray, QBuffer, QIODevice, QTimer
from PySide6.QtGui import QFont, QColor
from PySide6.QtMultimedia import QAudioFormat, QAudioSink, QAudio, QMediaDevices
import sys
import base64
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from client.ui.stark_theme import StarkTheme
from client.ui.icons import StarkIcons
from client.ui.video_player_widget import VideoPlayerWidget
from client.ui.interview_widget import InterviewWidget
from client.core.websocket_client import WebSocketClient
from client.core.audio_recorder import AudioRecorder
from client.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.websocket_client = None
        self.audio_recorder = None
        self.session_id = None
        self.is_connecting = False

        # ── Audio (sera reconfiguré dynamiquement selon le sample rate reçu) ──
        self.audio_sink = None
        self.audio_buffer = None
        self.audio_io_buffer = None
        self.audio_check_timer = None
        self._audio_delay_timer = None  # FIX: timer de délai avant check IdleState

        # ── État chunks ──
        self._pending_msg_type: str = ""
        self._pending_msg_data: dict = {}
        self._audio_chunks: list = []
        self._audio_total_chunks: int = 0
        self._audio_sample_rate: int = 22050   # sera mis à jour depuis les métadonnées
        self._audio_channels: int = 1
        self._audio_bits: int = 16

        # Créer le sink audio par défaut
        self._create_audio_sink(22050, 1, 16)

        self._setup_ui()

    # ================================================================
    # GESTION AUDIO SINK DYNAMIQUE
    # ================================================================

    def _create_audio_sink(self, sample_rate: int, channels: int, bits: int):
        """
        Crée un QAudioSink avec le bon format.
        Appelé au démarrage et à chaque nouveau format reçu.
        """
        if self.audio_sink:
            self.audio_sink.stop()
            self.audio_sink = None

        fmt = QAudioFormat()
        fmt.setSampleRate(sample_rate)
        fmt.setChannelCount(channels)

        if bits == 16:
            fmt.setSampleFormat(QAudioFormat.SampleFormat.Int16)
        elif bits == 32:
            fmt.setSampleFormat(QAudioFormat.SampleFormat.Float)
        else:
            fmt.setSampleFormat(QAudioFormat.SampleFormat.Int16)

        # Vérifier que le device supporte ce format
        output_device = QMediaDevices.defaultAudioOutput()
        if output_device and not output_device.isFormatSupported(fmt):
            logger.warning(
                f"Format {sample_rate}Hz {bits}bit non supporté nativement, "
                f"Qt va resampler"
            )

        self.audio_sink = QAudioSink(fmt)
        self.audio_sink.setVolume(1.0)
        logger.info(f"🔊 AudioSink créé: {sample_rate}Hz, {channels}ch, {bits}bit")

    def _ensure_audio_format(self, sample_rate: int, channels: int, bits: int):
        """Reconfigure le sink si le format a changé."""
        if (sample_rate != self._audio_sample_rate
                or channels != self._audio_channels
                or bits != self._audio_bits):
            logger.info(
                f"Format audio changé: {self._audio_sample_rate}Hz → {sample_rate}Hz"
            )
            self._audio_sample_rate = sample_rate
            self._audio_channels = channels
            self._audio_bits = bits
            self._create_audio_sink(sample_rate, channels, bits)

    # ================================================================
    # UI
    # ================================================================

    def _setup_ui(self):
        self.setWindowTitle("Stark Recruitment AI - Entretien Vocal")
        self.showMaximized()
        self.setStyleSheet(f"QMainWindow {{ background: {StarkTheme.GRADIENT_BACKGROUND}; }}")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        main_layout.addWidget(self._create_header())

        self.connection_widget = self._create_connection_widget()
        main_layout.addWidget(self.connection_widget)

        self.interview_container = self._create_interview_container()
        self.interview_container.setVisible(False)
        main_layout.addWidget(self.interview_container)

        self._setup_statusbar()

    def _create_header(self) -> QWidget:
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background: {StarkTheme.GRADIENT_HEADER};
                border-bottom: 3px solid {StarkTheme.ORANGE_ACCENT};
            }}
        """)
        header.setFixedHeight(80)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(StarkTheme.BLUE_DARK))
        shadow.setOffset(0, 3)
        header.setGraphicsEffect(shadow)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(40, 15, 40, 15)

        title_container = QWidget()
        tl = QHBoxLayout(title_container)
        tl.setContentsMargins(0, 0, 0, 0)
        tl.setSpacing(15)

        logo = QLabel()
        logo.setPixmap(StarkIcons.logo_stark().pixmap(QSize(50, 50)))
        tl.addWidget(logo)

        tw = QWidget()
        twl = QVBoxLayout(tw)
        twl.setContentsMargins(0, 0, 0, 0)
        twl.setSpacing(2)

        main_title = QLabel("STARK RECRUITMENT AI")
        main_title.setFont(QFont(StarkTheme.FONT_FAMILY_PRIMARY, 20, QFont.Weight.ExtraBold))
        main_title.setStyleSheet(f"color: {StarkTheme.WHITE}; letter-spacing: 2px;")
        twl.addWidget(main_title)

        subtitle = QLabel("Entretien Vocal Intelligent - Mode Vocal Pur")
        subtitle.setFont(QFont(StarkTheme.FONT_FAMILY_PRIMARY, 10))
        subtitle.setStyleSheet(f"color: {StarkTheme.BLUE_EXTRA_LIGHT};")
        twl.addWidget(subtitle)

        tl.addWidget(tw)
        layout.addWidget(title_container)
        layout.addStretch()
        self.status_container = self._create_status_indicator()
        layout.addWidget(self.status_container)
        return header

    def _create_status_indicator(self) -> QWidget:
        container = QFrame()
        container.setStyleSheet(f"""
            QFrame {{
                background: rgba(255,255,255,0.1);
                border: 1px solid rgba(255,255,255,0.2);
                border-radius: {StarkTheme.RADIUS_MEDIUM};
                padding: 8px 15px;
            }}
        """)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(10)

        self.status_icon_label = QLabel()
        self.status_icon_label.setPixmap(StarkIcons.activity().pixmap(QSize(24, 24)))
        layout.addWidget(self.status_icon_label)

        stc = QWidget()
        stl = QVBoxLayout(stc)
        stl.setContentsMargins(0, 0, 0, 0)
        stl.setSpacing(0)

        self.status_label = QLabel("DÉCONNECTÉ")
        self.status_label.setFont(QFont(StarkTheme.FONT_FAMILY_PRIMARY, 11, QFont.Weight.Bold))
        self.status_label.setStyleSheet(f"color: {StarkTheme.WHITE}; letter-spacing: 1px;")
        stl.addWidget(self.status_label)

        self.status_detail = QLabel("En attente de connexion")
        self.status_detail.setFont(QFont(StarkTheme.FONT_FAMILY_PRIMARY, 8))
        self.status_detail.setStyleSheet(f"color: {StarkTheme.BLUE_EXTRA_LIGHT};")
        stl.addWidget(self.status_detail)

        layout.addWidget(stc)
        return container

    def _create_connection_widget(self) -> QWidget:
        widget = QFrame()
        widget.setStyleSheet("QFrame { background: transparent; }")
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {StarkTheme.WHITE};
                border: 2px solid {StarkTheme.BLUE_EXTRA_LIGHT};
                border-radius: {StarkTheme.RADIUS_XLARGE};
            }}
        """)
        card.setFixedSize(550, 420)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(StarkTheme.BLUE_PRIMARY))
        shadow.setOffset(0, 8)
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(50, 40, 50, 40)
        card_layout.setSpacing(20)

        icon_container = QFrame()
        icon_container.setStyleSheet(
            f"QFrame {{ background: {StarkTheme.BLUE_EXTRA_LIGHT}; border-radius: 40px; }}"
        )
        icon_container.setFixedSize(80, 80)
        il = QVBoxLayout(icon_container)
        il.setAlignment(Qt.AlignmentFlag.AlignCenter)
        shield_icon = QLabel()
        shield_icon.setPixmap(StarkIcons.headphones(StarkTheme.ORANGE_ACCENT).pixmap(QSize(50, 50)))
        il.addWidget(shield_icon)
        card_layout.addWidget(icon_container, alignment=Qt.AlignmentFlag.AlignCenter)

        title = QLabel("MODE VOCAL PUR")
        title.setFont(QFont(StarkTheme.FONT_FAMILY_PRIMARY, 20, QFont.Weight.ExtraBold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"color: {StarkTheme.ORANGE_ACCENT}; letter-spacing: 2px;")
        card_layout.addWidget(title)

        subtitle = QLabel("Entrez votre identifiant de session")
        subtitle.setFont(QFont(StarkTheme.FONT_FAMILY_PRIMARY, 11))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(f"color: {StarkTheme.GRAY_MEDIUM};")
        card_layout.addWidget(subtitle)

        self.session_input = QLineEdit()
        self.session_input.setPlaceholderText("session_xxxxxxxxxxxxx")
        self.session_input.setFont(QFont(StarkTheme.FONT_FAMILY_MONO, 12, QFont.Weight.Bold))
        self.session_input.setMinimumHeight(50)
        self.session_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.session_input.setStyleSheet(f"""
            QLineEdit {{
                background: {StarkTheme.GRAY_EXTRA_LIGHT};
                border: 2px solid {StarkTheme.GRAY_LIGHT};
                border-radius: {StarkTheme.RADIUS_MEDIUM};
                padding: {StarkTheme.SPACING_MD};
                color: {StarkTheme.GRAY_DARK};
            }}
            QLineEdit:focus {{
                border: 2px solid {StarkTheme.ORANGE_ACCENT};
                background: {StarkTheme.WHITE};
            }}
        """)
        card_layout.addWidget(self.session_input)

        self.connect_btn = QPushButton("DÉMARRER L'ENTRETIEN")
        self.connect_btn.setFont(QFont(StarkTheme.FONT_FAMILY_PRIMARY, 13, QFont.Weight.Bold))
        self.connect_btn.setMinimumHeight(55)
        self.connect_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.connect_btn.setStyleSheet(StarkTheme.get_button_style("accent"))
        self.connect_btn.clicked.connect(self._connect_to_interview)
        card_layout.addWidget(self.connect_btn)

        layout.addWidget(card)
        return widget

    def _create_interview_container(self) -> QWidget:
        container = QWidget()
        container.setStyleSheet("QWidget { background: transparent; }")
        layout = QHBoxLayout(container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        self.video_player = VideoPlayerWidget()
        layout.addWidget(self.video_player, stretch=2)

        self.interview_widget = InterviewWidget()
        self.interview_widget.setMaximumWidth(450)
        self.interview_widget.start_recording.connect(self._on_start_recording)
        self.interview_widget.stop_recording.connect(self._on_stop_recording)
        self.interview_widget.end_interview.connect(self._on_end_interview)
        layout.addWidget(self.interview_widget, stretch=1)

        return container

    def _setup_statusbar(self):
        self.statusBar().setStyleSheet(f"""
            QStatusBar {{
                background: {StarkTheme.WHITE};
                color: {StarkTheme.GRAY_DARK};
                font-size: 11px; font-weight: bold;
                padding: 8px;
                border-top: 1px solid {StarkTheme.GRAY_LIGHT};
            }}
        """)
        self.statusBar().showMessage("🎧 Mode Vocal Pur Activé")

    # ================================================================
    # CONNEXION
    # ================================================================

    def _connect_to_interview(self):
        if self.is_connecting:
            return
        session_id = self.session_input.text().strip()
        if not session_id or not session_id.startswith("session_"):
            self._show_error_dialog("❌ Erreur", "Format attendu: session_xxxxxxxxxxxxx")
            return

        self.session_id = session_id
        self.is_connecting = True
        self.connect_btn.setEnabled(False)
        self.connect_btn.setText("CONNEXION EN COURS...")
        self.session_input.setEnabled(False)

        ws_url = f"{settings.WEBSOCKET_URL}/ws/interview/{session_id}"
        self.websocket_client = WebSocketClient(ws_url)
        self.websocket_client.disconnected.connect(self._on_websocket_disconnected)
        self.websocket_client.connected.connect(self._on_websocket_connected)
        self.websocket_client.message_received.connect(self._on_websocket_message)
        self.websocket_client.error_occurred.connect(self._on_websocket_error)
        self.websocket_client.connect_to_server()
        self.statusBar().showMessage("🔍 Connexion...")

    def _on_websocket_connected(self):
        logger.info("✅ WebSocket connecté")
        self.status_label.setText("VALIDATION")
        self.status_label.setStyleSheet(
            f"color: {StarkTheme.WARNING}; letter-spacing: 1px; font-weight: bold;"
        )

    def _on_websocket_disconnected(self, code: int, reason: str):
        if self.is_connecting:
            self._handle_connection_failure(reason or f"Code {code}")
            return
        self.status_label.setText("DÉCONNECTÉ")
        self.status_label.setStyleSheet(f"color: {StarkTheme.ERROR}; letter-spacing: 1px;")

    def _on_websocket_error(self, error: str):
        self.statusBar().showMessage(f"❌ {error}")

    # ================================================================
    # RÉCEPTION MESSAGES + CHUNKS
    # ================================================================

    def _on_websocket_message(self, data: dict):
        msg_type = data.get("type")
        msg_data = data.get("data", {})

        logger.info(f"📨 {msg_type}")

        if msg_type == "error":
            err = msg_data.get("message", "Erreur")
            if msg_data.get("error_type") == "SESSION_INVALID":
                self._handle_connection_failure(err)
            else:
                self._show_error_dialog("Erreur", err)
            return

        if msg_type == "question_loading":
            self.interview_widget.update_question(msg_data.get("progress", {}))
            self.statusBar().showMessage("⏳ Génération audio...")
            self.video_player.set_speaking()
            return

        if msg_type in ("welcome", "question", "interview_completed"):
            if msg_data.get("audio_mode") == "chunked":
                # ── Stocker les métadonnées de FORMAT ──
                self._pending_msg_type = msg_type
                self._pending_msg_data = msg_data
                self._audio_chunks = []
                self._audio_total_chunks = msg_data.get("total_chunks", 0)

                # Récupérer le vrai sample rate envoyé par le serveur
                sr   = msg_data.get("sample_rate", 22050)
                ch   = msg_data.get("channels", 1)
                bits = msg_data.get("bits_per_sample", 16)

                # Reconfigurer le sink si nécessaire
                self._ensure_audio_format(sr, ch, bits)

                logger.info(
                    f"Chunked: {self._audio_total_chunks} chunks "
                    f"@ {sr}Hz {ch}ch {bits}bit pour '{msg_type}'"
                )
                return

            # Fallback inline
            audio_b64 = msg_data.get("audio_data")
            if audio_b64:
                self._play_bytes_direct(base64.b64decode(audio_b64))
            self._finalize_message(msg_type, msg_data)
            return

        if msg_type == "audio_chunk_data":
            self._audio_chunks.append(msg_data.get("data", ""))
            idx   = msg_data.get("chunk_index", 0)
            total = msg_data.get("total", 1)
            self.statusBar().showMessage(f"📦 Audio {idx + 1}/{total}...")
            return

        if msg_type == "audio_chunk_end":
            if self._audio_chunks:
                try:
                    # Assembler tous les chunks
                    pcm_bytes = b"".join(
                        base64.b64decode(c) for c in self._audio_chunks
                    )
                    logger.info(
                        f"✅ PCM assemblé: {len(self._audio_chunks)} chunks "
                        f"→ {len(pcm_bytes):,} bytes "
                        f"@ {self._audio_sample_rate}Hz"
                    )
                    # Jouer directement (PCM pur, format déjà configuré)
                    self._play_pcm(pcm_bytes)
                except Exception as e:
                    logger.error(f"❌ Assemblage: {e}")
                    self.interview_widget.enable_recording(True)
            else:
                self.interview_widget.enable_recording(True)

            # FIX: _finalize_message est appelé ici mais enable_recording
            # sera géré par _check_audio_finished une fois l'audio terminé.
            # On appelle _finalize_message uniquement pour la mise à jour UI
            # (progression, statuts), PAS pour enable_recording.
            self._finalize_message(self._pending_msg_type, self._pending_msg_data)
            self._audio_chunks = []
            self._pending_msg_type = ""
            self._pending_msg_data = {}
            return

        if msg_type == "answer_saved":
            logger.info("✅ Réponse sauvegardée")
            self.statusBar().showMessage("✅ Réponse enregistrée")
            self.video_player.set_idle()

    def _finalize_message(self, msg_type: str, msg_data: dict):
        if msg_type == "welcome":
            self.is_connecting = False
            self.status_label.setText("CONNECTÉ")
            self.status_label.setStyleSheet(
                f"color: {StarkTheme.SUCCESS}; letter-spacing: 1px; font-weight: bold;"
            )
            self.status_detail.setText("Mode vocal actif")
            self.connection_widget.setVisible(False)
            self.interview_container.setVisible(True)
            if not self.audio_recorder:
                self.audio_recorder = AudioRecorder()
                self.audio_recorder.audio_chunk_ready.connect(self._on_audio_chunk)
            self.video_player.set_speaking()
            self.statusBar().showMessage("🎧 Bienvenue — écoutez le message d'accueil")

        elif msg_type == "question":
            self.interview_widget.update_question(msg_data.get("progress", {}))
            self.interview_widget.set_audio_playing()
            self.video_player.set_speaking()
            self.statusBar().showMessage("🔊 Question en lecture...")

        elif msg_type == "interview_completed":
            self._show_info_dialog("Entretien Terminé", "شكراً لك! انتهت المقابلة.")
            self.statusBar().showMessage("🎉 Terminé!")

    # ================================================================
    # LECTURE PCM BRUT  ← FIX PRINCIPAL : voix coupée
    # ================================================================

    def _play_pcm(self, pcm_bytes: bytes):
        """
        Joue du PCM brut (s16le) via QAudioSink.

        FIX voix coupée :
        - On calcule la durée théorique de l'audio depuis la taille des données.
        - On attend (durée - 300 ms) avant de commencer à surveiller IdleState.
        - Cela évite le faux positif IdleState qui se produit au tout début
          de la lecture (QAudioSink passe brièvement en IdleState avant que
          le premier sample ne soit consommé).
        """
        try:
            # Stopper toute lecture en cours + annuler les timers
            if self.audio_sink:
                self.audio_sink.stop()
            if self.audio_check_timer:
                self.audio_check_timer.stop()
                self.audio_check_timer = None
            if self._audio_delay_timer:
                self._audio_delay_timer.stop()
                self._audio_delay_timer = None

            # Monter le buffer PCM
            self.audio_buffer    = QByteArray(pcm_bytes)
            self.audio_io_buffer = QBuffer(self.audio_buffer)
            self.audio_io_buffer.open(QIODevice.OpenModeFlag.ReadOnly)
            self.audio_sink.start(self.audio_io_buffer)

            # ── Calcul durée théorique ──
            bytes_per_sample = self._audio_bits // 8
            if bytes_per_sample > 0 and self._audio_sample_rate > 0 and self._audio_channels > 0:
                total_samples = len(pcm_bytes) / (bytes_per_sample * self._audio_channels)
                expected_ms   = int((total_samples / self._audio_sample_rate) * 1000)
            else:
                expected_ms = 3000  # fallback 3 s

            # Démarrer le check IdleState 300 ms avant la fin théorique,
            # mais jamais avant 500 ms (pour ne pas attraper le démarrage)
            delay_ms = max(expected_ms - 300, 500)

            logger.info(
                f"▶️ Lecture PCM: {len(pcm_bytes):,} bytes "
                f"@ {self._audio_sample_rate}Hz {self._audio_channels}ch {self._audio_bits}bit "
                f"| durée estimée: {expected_ms} ms | check IdleState dans: {delay_ms} ms"
            )

            # Lancer le timer de délai (one-shot)
            self._audio_delay_timer = QTimer()
            self._audio_delay_timer.setSingleShot(True)
            self._audio_delay_timer.timeout.connect(self._start_idle_check)
            self._audio_delay_timer.start(delay_ms)

        except Exception as e:
            logger.error(f"❌ _play_pcm: {e}")
            self.interview_widget.enable_recording(True)

    def _start_idle_check(self):
        """Démarre la surveillance de l'IdleState après le délai calculé."""
        self._audio_delay_timer = None
        self.audio_check_timer = QTimer()
        self.audio_check_timer.timeout.connect(self._check_audio_finished)
        self.audio_check_timer.start(100)

    def _play_bytes_direct(self, audio_bytes: bytes):
        """Fallback: joue des bytes WAV inline (extraire PCM d'abord)."""
        if audio_bytes[:4] == b'RIFF':
            import struct
            idx = audio_bytes.find(b'data', 12)
            if idx != -1:
                # Lire sample rate depuis le WAV header
                fmt_idx = audio_bytes.find(b'fmt ', 12)
                if fmt_idx != -1:
                    sr = struct.unpack_from('<I', audio_bytes, fmt_idx + 12)[0]
                    ch = struct.unpack_from('<H', audio_bytes, fmt_idx + 10)[0]
                    bps = struct.unpack_from('<H', audio_bytes, fmt_idx + 22)[0]
                    self._ensure_audio_format(sr, ch, bps)
                self._play_pcm(audio_bytes[idx + 8:])
                return
        self._play_pcm(audio_bytes)

    def _check_audio_finished(self):
        """Vérifie si QAudioSink a terminé la lecture (IdleState)."""
        if self.audio_sink and self.audio_sink.state() == QAudio.State.IdleState:
            logger.info("✅ Lecture terminée → envoi audio_finished")
            if self.audio_check_timer:
                self.audio_check_timer.stop()
                self.audio_check_timer = None
            self.video_player.set_idle()
            # Signaler au serveur que la lecture est terminée
            if self.websocket_client:
                self.websocket_client.send_message({"type": "audio_finished"})
            self.interview_widget.enable_recording(True)
            self.statusBar().showMessage("✅ Vous pouvez répondre")

    # ================================================================
    # ENREGISTREMENT
    # ================================================================

    def _on_start_recording(self):
        if self.audio_recorder:
            self.audio_recorder.start_recording()
            self.video_player.set_listening()
            self.statusBar().showMessage("🎤 Enregistrement...")

    def _on_stop_recording(self):
        if self.audio_recorder:
            self.audio_recorder.stop_recording()
            if self.websocket_client:
                self.websocket_client.send_message({"type": "answer_complete"})
            self.video_player.set_idle()
            self.interview_widget.enable_recording(False)

    def _on_audio_chunk(self, audio_data: bytes):
        if self.websocket_client:
            self.websocket_client.send_message({
                "type":       "audio_chunk",
                "audio_data": base64.b64encode(audio_data).decode("utf-8"),
            })

    def _on_end_interview(self):
        reply = QMessageBox.question(
            self, "Terminer", "Confirmer la fin de l'entretien?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes and self.websocket_client:
            self.websocket_client.send_message({"type": "end_interview"})

    # ================================================================
    # UTILITAIRES
    # ================================================================

    def _handle_connection_failure(self, msg: str):
        self.is_connecting = False
        self.connect_btn.setEnabled(True)
        self.connect_btn.setText("DÉMARRER L'ENTRETIEN")
        self.session_input.setEnabled(True)
        if self.websocket_client:
            try:
                self.websocket_client.disconnect_from_server()
            except Exception:
                pass
            self.websocket_client = None
        self._show_error_dialog("Connexion impossible", msg)

    def _show_error_dialog(self, title: str, msg: str):
        b = QMessageBox(self)
        b.setIcon(QMessageBox.Icon.Critical)
        b.setWindowTitle(title)
        b.setText(msg)
        b.exec()

    def _show_info_dialog(self, title: str, msg: str):
        b = QMessageBox(self)
        b.setIcon(QMessageBox.Icon.Information)
        b.setWindowTitle(title)
        b.setText(msg)
        b.exec()

    def closeEvent(self, event):
        if self.websocket_client:
            self.websocket_client.disconnect_from_server()
        if self.audio_recorder:
            self.audio_recorder.cleanup()
        if self.audio_sink:
            self.audio_sink.stop()
        if self.audio_check_timer:
            self.audio_check_timer.stop()
        if self._audio_delay_timer:
            self._audio_delay_timer.stop()
        super().closeEvent(event)