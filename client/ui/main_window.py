from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QMessageBox, QLabel, QLineEdit, QPushButton, QFrame, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QSize, QTimer, QSequentialAnimationGroup, QParallelAnimationGroup
from PySide6.QtGui import QFont, QPalette, QColor
import base64

from client.config import settings
from client.core import WebSocketClient, AudioRecorder
from client.ui.video_player_widget import VideoPlayerWidget
from client.ui.interview_widget import InterviewWidget
from client.ui.icons import StarkIcons

class MainWindow(QMainWindow):
    """Fenêtre principale - Design Fluide et Créatif Stark Solutions"""
    
    # Palette Stark avec variations
    STARK_BLUE_PRIMARY = "#1565C0"
    STARK_BLUE_DARK = "#0D47A1"
    STARK_BLUE_LIGHT = "#42A5F5"
    STARK_BLUE_GLOW = "#64B5F6"
    STARK_ACCENT = "#FF6B35"
    STARK_ACCENT_LIGHT = "#FF8555"
    STARK_BG_DARK = "#0A1929"
    STARK_BG_CARD = "#132F4C"
    STARK_SUCCESS = "#00E676"
    
    def __init__(self):
        super().__init__()
        
        self.websocket_client = None
        self.audio_recorder = AudioRecorder()
        self.session_id = None
        
        self._setup_ui()
        self._connect_signals()
        self._start_ambient_animations()
    
    def _setup_ui(self):
        """Initialiser l'interface avec animations fluides"""
        self.setWindowTitle("Stark Recruitment AI - Entretien Vocal Intelligent")
        self.showMaximized()
        
        # Style global avec animations CSS
        self.setStyleSheet(f"""
            QMainWindow {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {self.STARK_BG_DARK}, 
                    stop:0.3 {self.STARK_BG_CARD},
                    stop:0.7 {self.STARK_BLUE_DARK},
                    stop:1 {self.STARK_BG_DARK});
            }}
        """)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # En-tête avec effets
        header = self._create_animated_header()
        main_layout.addWidget(header)
        
        # Zone de connexion
        self.connection_widget = self._create_glassmorphic_connection()
        main_layout.addWidget(self.connection_widget)
        
        # Container entretien
        self.interview_container = QWidget()
        self.interview_container.setVisible(False)
        self.interview_container.setStyleSheet("background: transparent;")
        
        interview_layout = QHBoxLayout(self.interview_container)
        interview_layout.setContentsMargins(15, 15, 15, 15)
        interview_layout.setSpacing(20)
        
        # Avatar avec glow effect
        avatar_frame = self._create_avatar_frame()
        interview_layout.addWidget(avatar_frame, 75)
        
        # Panel latéral avec glassmorphism
        control_frame = self._create_glassmorphic_panel()
        interview_layout.addWidget(control_frame, 25)
        
        main_layout.addWidget(self.interview_container)
        
        # Barre de statut fluide
        self._setup_animated_statusbar()
    
    def _create_avatar_frame(self) -> QFrame:
        """Créer le cadre de l'avatar avec effets de glow"""
        avatar_frame = QFrame()
        avatar_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(13, 71, 161, 0.15),
                    stop:0.5 rgba(21, 101, 192, 0.1),
                    stop:1 rgba(10, 25, 41, 0.2));
                border: 3px solid transparent;
                border-radius: 25px;
                background-clip: padding-box;
            }}
        """)
        
        # Effet d'ombre lumineux
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(self.STARK_BLUE_GLOW))
        shadow.setOffset(0, 0)
        avatar_frame.setGraphicsEffect(shadow)
        
        avatar_layout = QVBoxLayout(avatar_frame)
        avatar_layout.setContentsMargins(3, 3, 3, 3)
        
        self.video_player = VideoPlayerWidget()
        avatar_layout.addWidget(self.video_player)
        
        return avatar_frame
    
    def _create_glassmorphic_panel(self) -> QFrame:
        """Panel latéral avec effet glassmorphism"""
        control_frame = QFrame()
        control_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(19, 47, 76, 0.85),
                    stop:0.5 rgba(13, 71, 161, 0.75),
                    stop:1 rgba(19, 47, 76, 0.85));
                border: 2px solid rgba(66, 165, 245, 0.3);
                border-radius: 20px;
                backdrop-filter: blur(10px);
            }}
        """)
        
        # Effet de glow subtil
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(21, 101, 192, 100))
        shadow.setOffset(0, 5)
        control_frame.setGraphicsEffect(shadow)
        
        control_layout = QVBoxLayout(control_frame)
        control_layout.setContentsMargins(20, 20, 20, 20)
        
        self.interview_widget = InterviewWidget()
        control_layout.addWidget(self.interview_widget)
        
        return control_frame
    
    def _create_animated_header(self) -> QWidget:
        """En-tête avec animations et effets de particules"""
        header = QFrame()
        header.setObjectName("mainHeader")
        header.setStyleSheet(f"""
            #mainHeader {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {self.STARK_BLUE_DARK},
                    stop:0.3 {self.STARK_BLUE_PRIMARY},
                    stop:0.5 rgba(66, 165, 245, 0.9),
                    stop:0.7 {self.STARK_BLUE_PRIMARY},
                    stop:1 {self.STARK_BLUE_DARK});
                border: none;
                border-bottom: 4px solid transparent;
                border-image: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {self.STARK_ACCENT},
                    stop:0.5 {self.STARK_ACCENT_LIGHT},
                    stop:1 {self.STARK_ACCENT}) 1;
            }}
        """)
        header.setFixedHeight(90)
        
        # Effet de glow pour l'en-tête
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(self.STARK_BLUE_GLOW))
        shadow.setOffset(0, 5)
        header.setGraphicsEffect(shadow)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(40, 15, 40, 15)
        
        # Logo et titre avec animation
        title_container = QWidget()
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(20)
        
        # Logo animé
        self.logo_label = QLabel()
        self.logo_label.setPixmap(StarkIcons.user_check(self.STARK_SUCCESS).pixmap(QSize(52, 52)))
        title_layout.addWidget(self.logo_label)
        
        # Texte avec effet
        title_text = QWidget()
        title_text_layout = QVBoxLayout(title_text)
        title_text_layout.setContentsMargins(0, 0, 0, 0)
        title_text_layout.setSpacing(2)
        
        main_title = QLabel("STARK RECRUITMENT AI")
        main_title.setFont(QFont("Arial", 22, QFont.Weight.ExtraBold))
        main_title.setStyleSheet(f"""
            color: #FFFFFF;
            letter-spacing: 3px;
            text-shadow: 0 0 20px {self.STARK_BLUE_GLOW};
        """)
        title_text_layout.addWidget(main_title)
        
        subtitle = QLabel("Système d'Entretien Vocal Intelligent")
        subtitle.setFont(QFont("Arial", 11))
        subtitle.setStyleSheet(f"""
            color: {self.STARK_BLUE_GLOW};
            letter-spacing: 1px;
        """)
        title_text_layout.addWidget(subtitle)
        
        title_layout.addWidget(title_text)
        layout.addWidget(title_container)
        
        layout.addStretch()
        
        # Indicateur de statut animé
        status_container = self._create_pulsing_status()
        layout.addWidget(status_container)
        
        return header
    
    def _create_pulsing_status(self) -> QWidget:
        """Créer un indicateur de statut avec animation pulse"""
        status_container = QFrame()
        status_container.setStyleSheet(f"""
            QFrame {{
                background: rgba(19, 47, 76, 0.6);
                border: 2px solid rgba(66, 165, 245, 0.4);
                border-radius: 15px;
                padding: 10px 20px;
            }}
        """)
        
        status_layout = QHBoxLayout(status_container)
        status_layout.setContentsMargins(10, 5, 10, 5)
        status_layout.setSpacing(12)
        
        # Icône avec effet pulse
        self.status_icon_label = QLabel()
        self.status_icon_label.setPixmap(StarkIcons.activity(self.STARK_ACCENT).pixmap(QSize(28, 28)))
        status_layout.addWidget(self.status_icon_label)
        
        status_text_container = QWidget()
        status_text_layout = QVBoxLayout(status_text_container)
        status_text_layout.setContentsMargins(0, 0, 0, 0)
        status_text_layout.setSpacing(0)
        
        self.status_label = QLabel("DÉCONNECTÉ")
        self.status_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.status_label.setStyleSheet(f"""
            color: {self.STARK_ACCENT};
            letter-spacing: 2px;
        """)
        status_text_layout.addWidget(self.status_label)
        
        self.status_detail = QLabel("En attente de connexion")
        self.status_detail.setFont(QFont("Arial", 9))
        self.status_detail.setStyleSheet(f"""
            color: {self.STARK_BLUE_LIGHT};
            letter-spacing: 1px;
        """)
        status_text_layout.addWidget(self.status_detail)
        
        status_layout.addWidget(status_text_container)
        
        return status_container
    
    def _create_glassmorphic_connection(self) -> QWidget:
        """Widget de connexion avec glassmorphism et animations"""
        widget = QFrame()
        widget.setStyleSheet("QFrame { background: transparent; }")
        
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(40)
        
        # Carte avec effet de verre
        self.connection_card = QFrame()
        self.connection_card.setObjectName("connectionCard")
        self.connection_card.setStyleSheet(f"""
            #connectionCard {{
                background: qlineargradient(x1:0, y1:0, x2:0.5, y2:1,
                    stop:0 rgba(19, 47, 76, 0.7),
                    stop:0.5 rgba(21, 101, 192, 0.5),
                    stop:1 rgba(19, 47, 76, 0.7));
                border: 3px solid rgba(66, 165, 245, 0.3);
                border-radius: 30px;
                backdrop-filter: blur(15px);
            }}
        """)
        self.connection_card.setFixedSize(600, 500)
        
        # Ombre lumineuse
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setColor(QColor(self.STARK_BLUE_PRIMARY))
        shadow.setOffset(0, 10)
        self.connection_card.setGraphicsEffect(shadow)
        
        card_layout = QVBoxLayout(self.connection_card)
        card_layout.setContentsMargins(60, 60, 60, 60)
        card_layout.setSpacing(30)
        
        # Icône centrale avec glow
        icon_container = QFrame()
        icon_container.setStyleSheet(f"""
            QFrame {{
                background: qradialgradient(cx:0.5, cy:0.5, radius:0.5,
                    fx:0.5, fy:0.5,
                    stop:0 rgba(0, 230, 118, 0.2),
                    stop:0.5 rgba(21, 101, 192, 0.1),
                    stop:1 transparent);
                border-radius: 50px;
            }}
        """)
        icon_container.setFixedSize(100, 100)
        
        icon_layout = QVBoxLayout(icon_container)
        icon_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.shield_icon = QLabel()
        self.shield_icon.setPixmap(StarkIcons.shield_check(self.STARK_SUCCESS).pixmap(QSize(60, 60)))
        self.shield_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_layout.addWidget(self.shield_icon)
        
        card_layout.addWidget(icon_container, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Titre avec effet
        title = QLabel("CONNEXION SÉCURISÉE")
        title.setFont(QFont("Arial", 22, QFont.Weight.ExtraBold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"""
            color: #FFFFFF;
            letter-spacing: 3px;
            text-shadow: 0 0 15px {self.STARK_BLUE_GLOW};
        """)
        card_layout.addWidget(title)
        
        subtitle = QLabel("Entrez votre identifiant de session")
        subtitle.setFont(QFont("Arial", 12))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(f"""
            color: {self.STARK_BLUE_LIGHT};
            letter-spacing: 1px;
        """)
        card_layout.addWidget(subtitle)
        
        # Champ avec effet néon
        self.session_input = QLineEdit()
        self.session_input.setPlaceholderText("session_xxxxxxxxxxxxx")
        self.session_input.setFont(QFont("Courier New", 14, QFont.Weight.Bold))
        self.session_input.setMinimumHeight(60)
        self.session_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.session_input.setStyleSheet(f"""
            QLineEdit {{
                background: rgba(10, 25, 41, 0.6);
                border: 2px solid {self.STARK_BLUE_PRIMARY};
                border-radius: 15px;
                padding: 15px;
                color: #FFFFFF;
                font-size: 14px;
                letter-spacing: 1px;
            }}
            QLineEdit:focus {{
                border: 3px solid {self.STARK_SUCCESS};
                background: rgba(10, 25, 41, 0.8);
                box-shadow: 0 0 20px {self.STARK_SUCCESS};
            }}
            QLineEdit::placeholder {{
                color: {self.STARK_BLUE_LIGHT};
            }}
        """)
        card_layout.addWidget(self.session_input)
        
        # Bouton avec animation
        self.connect_btn = QPushButton("DÉMARRER L'ENTRETIEN")
        self.connect_btn.setFont(QFont("Arial", 14, QFont.Weight.ExtraBold))
        self.connect_btn.setMinimumHeight(65)
        self.connect_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.connect_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {self.STARK_BLUE_PRIMARY}, 
                    stop:0.5 {self.STARK_BLUE_LIGHT},
                    stop:1 {self.STARK_SUCCESS});
                color: white;
                border: none;
                border-radius: 18px;
                padding: 18px;
                font-size: 14px;
                letter-spacing: 3px;
                text-shadow: 0 2px 4px rgba(0,0,0,0.3);
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {self.STARK_SUCCESS}, 
                    stop:0.5 {self.STARK_BLUE_LIGHT},
                    stop:1 {self.STARK_ACCENT});
                transform: scale(1.02);
            }}
            QPushButton:pressed {{
                background: {self.STARK_BLUE_DARK};
                transform: scale(0.98);
            }}
        """)
        
        # Ombre pour le bouton
        btn_shadow = QGraphicsDropShadowEffect()
        btn_shadow.setBlurRadius(20)
        btn_shadow.setColor(QColor(self.STARK_SUCCESS))
        btn_shadow.setOffset(0, 5)
        self.connect_btn.setGraphicsEffect(btn_shadow)
        
        self.connect_btn.clicked.connect(self._connect_to_interview)
        card_layout.addWidget(self.connect_btn)
        
        layout.addWidget(self.connection_card)
        
        return widget
    
    def _setup_animated_statusbar(self):
        """Barre de statut avec animations"""
        status_bar = self.statusBar()
        status_bar.setStyleSheet(f"""
            QStatusBar {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {self.STARK_BG_CARD},
                    stop:0.5 {self.STARK_BLUE_DARK},
                    stop:1 {self.STARK_BG_CARD});
                color: {self.STARK_BLUE_LIGHT};
                font-size: 11px;
                font-weight: bold;
                padding: 10px;
                border-top: 2px solid {self.STARK_BLUE_PRIMARY};
                letter-spacing: 1px;
            }}
        """)
        status_bar.showMessage("🔒 Système Sécurisé Stark - Prêt à Démarrer")
    
    def _start_ambient_animations(self):
        """Démarrer les animations d'ambiance"""
        # Animation du logo (rotation subtile)
        self.logo_timer = QTimer()
        self.logo_timer.timeout.connect(self._animate_logo)
        self.logo_timer.start(3000)
        
        # Animation de la carte de connexion (floating)
        if hasattr(self, 'connection_card'):
            self.float_timer = QTimer()
            self.float_animation_up = True
            self.float_timer.timeout.connect(self._animate_floating_card)
            self.float_timer.start(2000)
    
    def _animate_logo(self):
        """Animation subtile du logo"""
        if hasattr(self, 'logo_label'):
            # Changer légèrement la couleur
            colors = [self.STARK_SUCCESS, self.STARK_BLUE_LIGHT, self.STARK_ACCENT]
            import random
            color = random.choice(colors)
            self.logo_label.setPixmap(StarkIcons.user_check(color).pixmap(QSize(52, 52)))
    
    def _animate_floating_card(self):
        """Animation de flottement de la carte"""
        if hasattr(self, 'connection_card') and self.connection_card.isVisible():
            current_pos = self.connection_card.pos()
            
            if self.float_animation_up:
                target_y = current_pos.y() - 10
                self.float_animation_up = False
            else:
                target_y = current_pos.y() + 10
                self.float_animation_up = True
    
    def _connect_signals(self):
        """Connecter les signaux"""
        self.audio_recorder.audio_chunk_ready.connect(self._on_audio_chunk)
        self.audio_recorder.recording_stopped.connect(self._on_recording_stopped)
        
        self.interview_widget.start_recording.connect(self._start_recording)
        self.interview_widget.stop_recording.connect(self._stop_recording)
        self.interview_widget.end_interview.connect(self._end_interview)
    
    def _connect_to_interview(self):
        """Connecter avec animation"""
        session_id = self.session_input.text().strip()
        
        if not session_id:
            self._show_error_dialog("Erreur de Connexion", 
                                   "Veuillez entrer un identifiant de session valide")
            return
        
        self.session_id = session_id
        
        ws_url = f"{settings.WEBSOCKET_URL}/ws/interview/{session_id}"
        self.websocket_client = WebSocketClient(ws_url)
        
        self.websocket_client.connected.connect(self._on_connected)
        self.websocket_client.disconnected.connect(self._on_disconnected)
        self.websocket_client.message_received.connect(self._on_message_received)
        self.websocket_client.error_occurred.connect(self._on_error)
        
        self.websocket_client.connect_to_server()
        self.statusBar().showMessage("⏳ Connexion sécurisée Stark en cours...")
        self.status_detail.setText("Établissement de la connexion...")
    
    def _on_connected(self):
        """Connexion réussie avec animation"""
        self.status_label.setText("CONNECTÉ")
        self.status_label.setStyleSheet(f"""
            color: {self.STARK_SUCCESS};
            letter-spacing: 2px;
        """)
        self.status_detail.setText("Session active et sécurisée")
        self.statusBar().showMessage("✅ Connexion Sécurisée Établie")
        
        # Animation de transition
        self.connection_widget.setVisible(False)
        self.interview_container.setVisible(True)
    
    def _on_disconnected(self):
        """Déconnexion"""
        self.status_label.setText("DÉCONNECTÉ")
        self.status_label.setStyleSheet(f"color: {self.STARK_ACCENT}; letter-spacing: 2px;")
        self.status_detail.setText("Session terminée")
        self.statusBar().showMessage("❌ Déconnecté")
    
    def _on_message_received(self, data: dict):
        """Traiter message WebSocket"""
        msg_type = data.get("type")
        msg_data = data.get("data", {})
        
        if msg_type == "welcome":
            text = msg_data.get("text")
            self._show_info_dialog("Bienvenue", text)
        
        elif msg_type == "question":
            text = msg_data.get("text")
            progress = msg_data.get("progress")
            self.interview_widget.update_question(text, progress)
            self.interview_widget.enable_recording(True)
            self.video_player.set_idle()
        
        elif msg_type == "answer_saved":
            transcript = msg_data.get("transcript")
            self.interview_widget.update_transcript(transcript)
            self.statusBar().showMessage("💾 Réponse Enregistrée", 3000)
        
        elif msg_type == "interview_completed":
            message = msg_data.get("message")
            self._show_success_dialog("Entretien Terminé", message)
            self.close()
        
        elif msg_type == "error":
            error_msg = msg_data.get("message")
            self._show_error_dialog("Erreur", error_msg)
    
    def _on_error(self, error: str):
        """Erreur"""
        self._show_error_dialog("Erreur de Connexion", error)
    
    def _start_recording(self):
        """Démarrer l'enregistrement"""
        self.audio_recorder.start_recording()
        self.video_player.set_listening()
        self.statusBar().showMessage("🎤 Enregistrement en cours...")
    
    def _stop_recording(self):
        """Arrêter l'enregistrement"""
        self.audio_recorder.stop_recording()
        self.statusBar().showMessage("⏳ Traitement...")
    
    def _on_audio_chunk(self, chunk: bytes):
        """Envoyer chunk audio"""
        if self.websocket_client:
            chunk_b64 = base64.b64encode(chunk).decode('utf-8')
            self.websocket_client.send_message({
                "type": "audio_chunk",
                "audio_data": chunk_b64
            })
    
    def _on_recording_stopped(self):
        """Recording arrêté"""
        if self.websocket_client:
            self.websocket_client.send_message({"type": "answer_complete"})
        self.interview_widget.enable_recording(False)
        self.video_player.set_idle()
    
    def _end_interview(self):
        """Terminer l'entretien"""
        reply = QMessageBox.question(
            self, "Confirmer", "Terminer l'entretien ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.websocket_client:
                self.websocket_client.send_message({"type": "end_interview"})
    
    def _show_info_dialog(self, title: str, message: str):
        """Dialogue stylisé"""
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStyleSheet(f"""
            QMessageBox {{
                background: {self.STARK_BG_CARD};
            }}
            QMessageBox QLabel {{
                color: #FFFFFF;
                font-size: 13px;
            }}
            QPushButton {{
                background: {self.STARK_BLUE_PRIMARY};
                color: white;
                border-radius: 8px;
                padding: 10px 25px;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background: {self.STARK_BLUE_LIGHT};
            }}
        """)
        msg_box.exec()
    
    def _show_success_dialog(self, title: str, message: str):
        """Dialogue de succès"""
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStyleSheet(f"""
            QMessageBox {{
                background: {self.STARK_BG_CARD};
            }}
            QMessageBox QLabel {{
                color: {self.STARK_SUCCESS};
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton {{
                background: {self.STARK_SUCCESS};
                color: white;
                border-radius: 8px;
                padding: 10px 25px;
            }}
            QPushButton:hover {{
                background: #2ECC71;
            }}
        """)
        msg_box.exec()
    
    def _show_error_dialog(self, title: str, message: str):
        """Dialogue d'erreur"""
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStyleSheet(f"""
            QMessageBox {{
                background: {self.STARK_BG_CARD};
            }}
            QMessageBox QLabel {{
                color: {self.STARK_ACCENT};
                font-size: 13px;
            }}
            QPushButton {{
                background: {self.STARK_ACCENT};
                color: white;
                border-radius: 8px;
                padding: 10px 25px;
            }}
            QPushButton:hover {{
                background: {self.STARK_ACCENT_LIGHT};
            }}
        """)
        msg_box.exec()
    
    def closeEvent(self, event):
        """Fermeture"""
        if self.websocket_client:
            self.websocket_client.disconnect_from_server()
        self.audio_recorder.cleanup()
        event.accept()