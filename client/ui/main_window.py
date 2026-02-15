"""
Fenêtre Principale - MODE VOCAL PUR
Les questions sont posées uniquement en audio, sans affichage de texte

MODIFICATIONS CLÉS:
- Pas d'affichage du texte des questions
- Lecture automatique de l'audio des questions
- Interface simplifiée centrée sur l'écoute
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QMessageBox, QLabel, QLineEdit, QPushButton, QFrame, 
    QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QSize, QUrl
from PySide6.QtGui import QFont, QColor
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from client.ui.stark_theme import StarkTheme
from client.ui.icons import StarkIcons
from client.ui.video_player_widget import VideoPlayerWidget
from client.ui.interview_widget import InterviewWidget  # Version vocal
from client.core.websocket_client import WebSocketClient
from client.core.audio_recorder import AudioRecorder
from client.config import settings
import base64


"""
Fenêtre Principale - MODE VOCAL PUR
Audio streamé directement en base64 (pas d'URLs)
VERSION COMPLÈTE
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QMessageBox, QLabel, QLineEdit, QPushButton, QFrame, 
    QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QSize, QByteArray, QBuffer, QIODevice, QTimer
from PySide6.QtGui import QFont, QColor
from PySide6.QtMultimedia import QAudioFormat, QAudioSink
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from client.ui.stark_theme import StarkTheme
from client.ui.icons import StarkIcons
from client.ui.video_player_widget import VideoPlayerWidget
from client.ui.interview_widget import InterviewWidget
from client.core.websocket_client import WebSocketClient
from client.core.audio_recorder import AudioRecorder
from client.config import settings
import base64
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    Fenêtre Principale - MODE VOCAL PUR
    Audio direct via WebSocket (pas d'URLs)
    """
    
    def __init__(self):
        super().__init__()
        
        self.websocket_client = None
        self.audio_recorder = None
        self.session_id = None
        self.is_connecting = False
        
        # ✅ Configuration audio pour lecture directe
        self.audio_format = QAudioFormat()
        self.audio_format.setSampleRate(16000)
        self.audio_format.setChannelCount(1)
        self.audio_format.setSampleFormat(QAudioFormat.SampleFormat.Int16)
        
        self.audio_sink = QAudioSink(self.audio_format)
        self.audio_buffer = None
        self.audio_io_buffer = None
        self.audio_check_timer = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Initialiser l'interface"""
        self.setWindowTitle("Stark Recruitment AI - Entretien Vocal Intelligent (Mode Vocal Pur)")
        self.showMaximized()
        
        self.setStyleSheet(f"""
            QMainWindow {{
                background: {StarkTheme.GRADIENT_BACKGROUND};
            }}
        """)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # EN-TÊTE
        header = self._create_header()
        main_layout.addWidget(header)
        
        # ZONE DE CONNEXION
        self.connection_widget = self._create_connection_widget()
        main_layout.addWidget(self.connection_widget)
        
        # ZONE D'ENTRETIEN
        self.interview_container = self._create_interview_container()
        self.interview_container.setVisible(False)
        main_layout.addWidget(self.interview_container)
        
        # BARRE DE STATUT
        self._setup_statusbar()
    
    def _create_header(self) -> QWidget:
        """Créer l'en-tête"""
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
        
        # Logo + Titre
        title_container = QWidget()
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(15)
        
        logo_label = QLabel()
        logo_label.setPixmap(StarkIcons.logo_stark().pixmap(QSize(50, 50)))
        title_layout.addWidget(logo_label)
        
        text_widget = QWidget()
        text_layout = QVBoxLayout(text_widget)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)
        
        main_title = QLabel("STARK RECRUITMENT AI")
        main_title.setFont(QFont(StarkTheme.FONT_FAMILY_PRIMARY, 20, QFont.Weight.ExtraBold))
        main_title.setStyleSheet(f"color: {StarkTheme.WHITE}; letter-spacing: 2px;")
        text_layout.addWidget(main_title)
        
        subtitle = QLabel("Entretien Vocal Intelligent - Mode Vocal Pur")
        subtitle.setFont(QFont(StarkTheme.FONT_FAMILY_PRIMARY, 10))
        subtitle.setStyleSheet(f"color: {StarkTheme.BLUE_EXTRA_LIGHT};")
        text_layout.addWidget(subtitle)
        
        title_layout.addWidget(text_widget)
        layout.addWidget(title_container)
        layout.addStretch()
        
        # Indicateur de statut
        self.status_container = self._create_status_indicator()
        layout.addWidget(self.status_container)
        
        return header
    
    def _create_status_indicator(self) -> QWidget:
        """Créer l'indicateur de statut"""
        container = QFrame()
        container.setStyleSheet(f"""
            QFrame {{
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
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
        
        status_text_container = QWidget()
        status_text_layout = QVBoxLayout(status_text_container)
        status_text_layout.setContentsMargins(0, 0, 0, 0)
        status_text_layout.setSpacing(0)
        
        self.status_label = QLabel("DÉCONNECTÉ")
        self.status_label.setFont(QFont(StarkTheme.FONT_FAMILY_PRIMARY, 11, QFont.Weight.Bold))
        self.status_label.setStyleSheet(f"color: {StarkTheme.WHITE}; letter-spacing: 1px;")
        status_text_layout.addWidget(self.status_label)
        
        self.status_detail = QLabel("En attente de connexion")
        self.status_detail.setFont(QFont(StarkTheme.FONT_FAMILY_PRIMARY, 8))
        self.status_detail.setStyleSheet(f"color: {StarkTheme.BLUE_EXTRA_LIGHT};")
        status_text_layout.addWidget(self.status_detail)
        
        layout.addWidget(status_text_container)
        
        return container
    
    def _create_connection_widget(self) -> QWidget:
        """Créer le widget de connexion"""
        widget = QFrame()
        widget.setStyleSheet("QFrame { background: transparent; }")
        
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(30)
        
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {StarkTheme.WHITE};
                border: 2px solid {StarkTheme.BLUE_EXTRA_LIGHT};
                border-radius: {StarkTheme.RADIUS_XLARGE};
            }}
        """)
        card.setFixedSize(550, 450)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(StarkTheme.BLUE_PRIMARY))
        shadow.setOffset(0, 8)
        card.setGraphicsEffect(shadow)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(50, 50, 50, 50)
        card_layout.setSpacing(25)
        
        icon_container = QFrame()
        icon_container.setStyleSheet(f"""
            QFrame {{
                background: {StarkTheme.BLUE_EXTRA_LIGHT};
                border-radius: 40px;
            }}
        """)
        icon_container.setFixedSize(80, 80)
        
        icon_layout = QVBoxLayout(icon_container)
        icon_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        shield_icon = QLabel()
        shield_icon.setPixmap(StarkIcons.headphones(StarkTheme.ORANGE_ACCENT).pixmap(QSize(50, 50)))
        icon_layout.addWidget(shield_icon)
        
        card_layout.addWidget(icon_container, alignment=Qt.AlignmentFlag.AlignCenter)
        
        title = QLabel("MODE VOCAL PUR")
        title.setFont(QFont(StarkTheme.FONT_FAMILY_PRIMARY, 20, QFont.Weight.ExtraBold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"color: {StarkTheme.ORANGE_ACCENT}; letter-spacing: 2px;")
        card_layout.addWidget(title)
        
        subtitle = QLabel("L'avatar parle naturellement - Audio direct")
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
        
        btn_shadow = QGraphicsDropShadowEffect()
        btn_shadow.setBlurRadius(15)
        btn_shadow.setColor(QColor(StarkTheme.ORANGE_ACCENT))
        btn_shadow.setOffset(0, 4)
        self.connect_btn.setGraphicsEffect(btn_shadow)
        
        card_layout.addWidget(self.connect_btn)
        
        layout.addWidget(card)
        
        return widget
    
    def _create_interview_container(self) -> QWidget:
        """Créer le conteneur d'entretien"""
        container = QWidget()
        container.setStyleSheet("QWidget { background: transparent; }")
        
        layout = QHBoxLayout(container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # AVATAR
        self.video_player = VideoPlayerWidget()
        layout.addWidget(self.video_player, stretch=2)
        
        # CONTRÔLES (version vocal)
        self.interview_widget = InterviewWidget()
        self.interview_widget.setMaximumWidth(450)
        
        self.interview_widget.start_recording.connect(self._on_start_recording)
        self.interview_widget.stop_recording.connect(self._on_stop_recording)
        self.interview_widget.end_interview.connect(self._on_end_interview)
        
        layout.addWidget(self.interview_widget, stretch=1)
        
        return container
    
    def _setup_statusbar(self):
        """Configurer la barre de statut"""
        status_bar = self.statusBar()
        status_bar.setStyleSheet(f"""
            QStatusBar {{
                background: {StarkTheme.WHITE};
                color: {StarkTheme.GRAY_DARK};
                font-size: 11px;
                font-weight: bold;
                padding: 8px;
                border-top: 1px solid {StarkTheme.GRAY_LIGHT};
            }}
        """)
        status_bar.showMessage("🎧 Mode Vocal Pur Activé - L'avatar parle naturellement")
    
    def _connect_to_interview(self):
        """Connecter à l'entretien"""
        if self.is_connecting:
            return
    
        session_id = self.session_input.text().strip()
    
        if not session_id or not session_id.startswith("session_"):
            self._show_error_dialog(
                "❌ Erreur", 
                "Veuillez entrer un identifiant de session valide.\n\nFormat: session_xxxxxxxxxxxxx"
            )
            return
    
        self.session_id = session_id
        self.is_connecting = True
    
        self.connect_btn.setEnabled(False)
        self.connect_btn.setText("CONNEXION EN COURS...")
        self.session_input.setEnabled(False)
    
        ws_url = f"{settings.WEBSOCKET_URL}/ws/interview/{session_id}"
        logger.info(f"🔌 Connexion WebSocket: {ws_url}")
        
        self.websocket_client = WebSocketClient(ws_url)
    
        self.websocket_client.disconnected.connect(self._on_websocket_disconnected)
        self.websocket_client.connected.connect(self._on_websocket_connected)
        self.websocket_client.message_received.connect(self._on_websocket_message)
        self.websocket_client.error_occurred.connect(self._on_websocket_error)
    
        try:
            self.websocket_client.connect_to_server()
            self.statusBar().showMessage("🔍 Validation de session en cours...")
        except Exception as e:
            self._handle_connection_failure(f"Impossible de se connecter: {e}")
    
    def _on_websocket_connected(self):
        """WebSocket connecté"""
        logger.info("✅ WebSocket connecté")
        self.status_label.setText("VALIDATION")
        self.status_label.setStyleSheet(f"color: {StarkTheme.WARNING}; letter-spacing: 1px; font-weight: bold;")
        self.status_detail.setText("Vérification de session...")
        self.statusBar().showMessage("🔍 Validation de session en cours...")
    
    def _on_websocket_disconnected(self, code: int, reason: str):
        """WebSocket déconnecté"""
        logger.info(f"🔌 WebSocket déconnecté: code={code}, reason={reason}")
        
        if self.is_connecting:
            if code == 4003:
                error_msg = reason if reason else "Session invalide ou expirée"
                self._handle_connection_failure(error_msg)
            else:
                self._handle_connection_failure(f"Erreur de connexion (code {code}): {reason}")
            return
    
        self.status_label.setText("DÉCONNECTÉ")
        self.status_label.setStyleSheet(f"color: {StarkTheme.ERROR}; letter-spacing: 1px;")
        self.status_detail.setText("Connexion perdue")
        self.statusBar().showMessage("❌ Déconnecté du serveur")
    
    def _on_websocket_message(self, data: dict):
        """Message WebSocket reçu"""
        msg_type = data.get("type")
        msg_data = data.get("data", {})
        
        logger.info(f"📨 Message reçu: type={msg_type}")
        
        if msg_type == "error":
            error_msg = msg_data.get("message", "Erreur inconnue")
            error_type = msg_data.get("error_type", "GENERAL_ERROR")
        
            if error_type == "SESSION_INVALID":
                self._handle_connection_failure(error_msg)
                return
        
            self._show_error_dialog("Erreur", error_msg)
            self.statusBar().showMessage(f"❌ {error_msg}")
            return
        
        if msg_type == "welcome":
            self.is_connecting = False
            
            self.status_label.setText("CONNECTÉ")
            self.status_label.setStyleSheet(f"color: {StarkTheme.SUCCESS}; letter-spacing: 1px; font-weight: bold;")
            self.status_detail.setText("Mode vocal actif")
            
            self.statusBar().showMessage(f"🎧 Mode vocal activé - L'avatar va parler")
            
            self.connection_widget.setVisible(False)
            self.interview_container.setVisible(True)
            
            if not self.audio_recorder:
                self.audio_recorder = AudioRecorder()
                self.audio_recorder.audio_chunk_ready.connect(self._on_audio_chunk)
            
            # ✅ Jouer l'audio directement
            audio_data = msg_data.get("audio_data")
            if audio_data:
                logger.info("🔊 Lecture audio de bienvenue...")
                self._play_audio_direct(audio_data)
            else:
                logger.warning("⚠️ Pas d'audio dans le message de bienvenue")
            
            self.video_player.set_speaking()
            
        elif msg_type == "question":
            progress = msg_data.get("progress", {})
            audio_data = msg_data.get("audio_data")
            
            logger.info(f"📝 Question reçue: {progress.get('current')}/{progress.get('total')}")
            
            self.interview_widget.update_question(progress)
            
            # ✅ Jouer l'audio automatiquement
            if audio_data:
                logger.info("🔊 Lecture audio de la question...")
                self._play_audio_direct(audio_data)
                self.interview_widget.set_audio_playing()
            else:
                logger.warning("⚠️ Pas d'audio dans la question")
                self.statusBar().showMessage("⚠️ Audio de question non disponible")
                self.interview_widget.enable_recording(True)
            
            self.video_player.set_speaking()
            
        elif msg_type == "answer_saved":
            logger.info("✅ Réponse sauvegardée")
            self.statusBar().showMessage("✅ Réponse enregistrée")
            self.video_player.set_idle()
            
        elif msg_type == "interview_completed":
            logger.info("🎉 Entretien terminé")
            audio_data = msg_data.get("audio_data")
            
            if audio_data:
                self._play_audio_direct(audio_data)
            
            message = "شكراً لك! انتهت المقابلة." if msg_data.get("language") == "ar" else "Thank you! The interview is complete."
            self._show_info_dialog("Entretien Terminé", message)
            self.statusBar().showMessage("🎉 Entretien complété avec succès!")
    
    def _play_audio_direct(self, audio_data_b64: str):
        """
        ✅ NOUVEAU: Jouer l'audio directement depuis base64
        L'avatar parle naturellement sans URLs
        """
        try:
            logger.info("🎵 Décodage audio base64...")
            
            # Décoder le base64
            audio_bytes = base64.b64decode(audio_data_b64)
            logger.info(f"   Taille: {len(audio_bytes)} bytes")
            
            # Arrêter la lecture en cours
            if self.audio_sink:
                self.audio_sink.stop()
            
            # Arrêter le timer précédent
            if self.audio_check_timer:
                self.audio_check_timer.stop()
            
            # Créer un buffer Qt
            self.audio_buffer = QByteArray(audio_bytes)
            self.audio_io_buffer = QBuffer(self.audio_buffer)
            self.audio_io_buffer.open(QIODevice.OpenModeFlag.ReadOnly)
            
            # Jouer via QAudioSink
            self.audio_sink.start(self.audio_io_buffer)
            
            logger.info("✅ Lecture audio démarrée")
            
            # Mettre à jour l'UI
            self.video_player.set_speaking()
            self.statusBar().showMessage("🔊 L'avatar parle...")
            
            # ✅ Timer pour détecter la fin de lecture
            self.audio_check_timer = QTimer()
            self.audio_check_timer.timeout.connect(self._check_audio_finished)
            self.audio_check_timer.start(100)  # Vérifier toutes les 100ms
            
        except Exception as e:
            logger.error(f"❌ Erreur lecture audio: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self.statusBar().showMessage(f"⚠️ Erreur: {e}")
            self.interview_widget.enable_recording(True)
    
    def _check_audio_finished(self):
        """Vérifier si la lecture audio est terminée"""
        if self.audio_sink.state() == QAudioSink.State.IdleState:
            logger.info("✅ Audio terminé")
            
            self.video_player.set_idle()
            self.interview_widget.enable_recording(True)
            self.statusBar().showMessage("✅ Vous pouvez répondre")
            
            if self.audio_check_timer:
                self.audio_check_timer.stop()
    
    def _on_websocket_error(self, error: str):
        """Erreur WebSocket"""
        logger.error(f"❌ Erreur WebSocket: {error}")
        self._show_error_dialog("Erreur WebSocket", error)
        self.statusBar().showMessage(f"❌ Erreur: {error}")
    
    def _on_start_recording(self):
        """Démarrer l'enregistrement"""
        logger.info("🎤 Démarrage enregistrement")
        if self.audio_recorder:
            self.audio_recorder.start_recording()
            self.video_player.set_listening()
            self.statusBar().showMessage("🎤 Enregistrement en cours...")
    
    def _on_stop_recording(self):
        """Arrêter l'enregistrement"""
        logger.info("⏹️ Arrêt enregistrement")
        if self.audio_recorder:
            self.audio_recorder.stop_recording()
            
            if self.websocket_client:
                self.websocket_client.send_message({
                    "type": "answer_complete"
                })
            
            self.video_player.set_idle()
            self.statusBar().showMessage("⏹️ Enregistrement arrêté, traitement...")
            self.interview_widget.enable_recording(False)
    
    def _on_audio_chunk(self, audio_data: bytes):
        """Chunk audio reçu"""
        if self.websocket_client:
            audio_b64 = base64.b64encode(audio_data).decode('utf-8')
            self.websocket_client.send_message({
                "type": "audio_chunk",
                "audio_data": audio_b64
            })
    
    def _on_end_interview(self):
        """Terminer l'entretien"""
        reply = QMessageBox.question(
            self,
            "Terminer l'Entretien",
            "Êtes-vous sûr de vouloir terminer l'entretien maintenant?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.websocket_client:
                self.websocket_client.send_message({"type": "end_interview"})
            self.statusBar().showMessage("🔚 Entretien terminé")
    
    def _handle_connection_failure(self, error_message: str):
        """Gérer échec de connexion"""
        logger.error(f"❌ Échec connexion: {error_message}")
        
        self.is_connecting = False
        self.connect_btn.setEnabled(True)
        self.connect_btn.setText("DÉMARRER L'ENTRETIEN")
        self.session_input.setEnabled(True)
    
        if self.websocket_client:
            try:
                self.websocket_client.disconnect_from_server()
            except:
                pass
            self.websocket_client = None
    
        self._show_error_dialog("Connexion Impossible", error_message)
        self.statusBar().showMessage("❌ Connexion échouée")
    
    def _show_error_dialog(self, title: str, message: str):
        """Dialogue d'erreur"""
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.exec()
    
    def _show_info_dialog(self, title: str, message: str):
        """Dialogue d'information"""
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.exec()
    
    def closeEvent(self, event):
        """Nettoyage à la fermeture"""
        logger.info("🔚 Fermeture de l'application")
        
        if self.websocket_client:
            self.websocket_client.disconnect_from_server()
        
        if self.audio_recorder:
            self.audio_recorder.cleanup()
        
        if self.audio_sink:
            self.audio_sink.stop()
        
        if self.audio_check_timer:
            self.audio_check_timer.stop()
        
        super().closeEvent(event)