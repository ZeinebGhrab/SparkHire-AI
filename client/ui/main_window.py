from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QMessageBox, QLabel, QLineEdit, QPushButton, QFrame
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QSize
from PySide6.QtGui import QFont, QPalette, QColor
import base64

from client.config import settings
from client.core import WebSocketClient, AudioRecorder
from client.ui.video_player_widget import VideoPlayerWidget
from client.ui.interview_widget import InterviewWidget
from client.ui.icons import StarkIcons

class MainWindow(QMainWindow):
    """Fenêtre principale - Design Stark Solutions Professionnel"""
    
    # Palette de couleurs Stark Solutions
    STARK_BLUE_PRIMARY = "#1565C0"      # Bleu principal
    STARK_BLUE_DARK = "#0D47A1"         # Bleu foncé
    STARK_BLUE_LIGHT = "#42A5F5"        # Bleu clair
    STARK_ACCENT = "#FF6B35"            # Accent orange
    STARK_BG_DARK = "#0A1929"           # Background sombre
    STARK_BG_CARD = "#132F4C"           # Background carte
    
    def __init__(self):
        super().__init__()
        
        self.websocket_client = None
        self.audio_recorder = AudioRecorder()
        self.session_id = None
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """Initialiser l'interface avec le thème Stark"""
        self.setWindowTitle("Stark Recruitment AI - Entretien Vocal Intelligent")
        
        # Plein écran par défaut
        self.showMaximized()
        
        # Style global avec palette Stark
        self.setStyleSheet(f"""
            QMainWindow {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {self.STARK_BG_DARK}, 
                    stop:0.5 {self.STARK_BG_CARD}, 
                    stop:1 {self.STARK_BLUE_DARK});
            }}
        """)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # En-tête Stark
        header = self._create_stark_header()
        main_layout.addWidget(header)
        
        # Zone de connexion
        self.connection_widget = self._create_connection_widget()
        main_layout.addWidget(self.connection_widget)
        
        # Container entretien (caché au départ)
        self.interview_container = QWidget()
        self.interview_container.setVisible(False)
        
        interview_layout = QHBoxLayout(self.interview_container)
        interview_layout.setContentsMargins(10, 10, 10, 10)
        interview_layout.setSpacing(15)
        
        # Avatar (78% de l'écran)
        avatar_frame = QFrame()
        avatar_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(13, 71, 161, 0.3),
                    stop:1 rgba(10, 25, 41, 0.5));
                border: 3px solid {self.STARK_BLUE_PRIMARY};
                border-radius: 20px;
            }}
        """)
        avatar_layout = QVBoxLayout(avatar_frame)
        avatar_layout.setContentsMargins(0, 0, 0, 0)
        
        self.video_player = VideoPlayerWidget()
        avatar_layout.addWidget(self.video_player)
        
        interview_layout.addWidget(avatar_frame, 78)
        
        # Panel latéral (22%)
        control_frame = QFrame()
        control_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {self.STARK_BLUE_DARK},
                    stop:1 {self.STARK_BG_CARD});
                border: 2px solid {self.STARK_BLUE_PRIMARY};
                border-radius: 15px;
            }}
        """)
        control_layout = QVBoxLayout(control_frame)
        control_layout.setContentsMargins(15, 15, 15, 15)
        
        self.interview_widget = InterviewWidget()
        control_layout.addWidget(self.interview_widget)
        
        interview_layout.addWidget(control_frame, 22)
        
        main_layout.addWidget(self.interview_container)
        
        # Barre de statut Stark
        status_bar = self.statusBar()
        status_bar.setStyleSheet(f"""
            QStatusBar {{
                background: {self.STARK_BG_CARD};
                color: {self.STARK_BLUE_LIGHT};
                font-size: 11px;
                font-weight: bold;
                padding: 8px;
                border-top: 2px solid {self.STARK_BLUE_PRIMARY};
            }}
        """)
        status_bar.showMessage("🔒 Système Sécurisé Stark - Prêt à Démarrer")
    
    def _create_stark_header(self) -> QWidget:
        """Créer l'en-tête avec branding Stark"""
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {self.STARK_BLUE_DARK},
                    stop:0.5 {self.STARK_BLUE_PRIMARY},
                    stop:1 {self.STARK_BLUE_DARK});
                border-bottom: 3px solid {self.STARK_ACCENT};
            }}
        """)
        header.setFixedHeight(80)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(30, 15, 30, 15)
        
        # Logo et titre Stark
        title_container = QWidget()
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(15)
        
        # Logo Stark (icône user-check)
        logo_label = QLabel()
        logo_label.setPixmap(StarkIcons.user_check(self.STARK_BLUE_LIGHT).pixmap(QSize(48, 48)))
        title_layout.addWidget(logo_label)
        
        # Texte
        title_text = QWidget()
        title_text_layout = QVBoxLayout(title_text)
        title_text_layout.setContentsMargins(0, 0, 0, 0)
        title_text_layout.setSpacing(0)
        
        main_title = QLabel("STARK RECRUITMENT AI")
        main_title.setFont(QFont("Arial", 20, QFont.Weight.ExtraBold))
        main_title.setStyleSheet(f"color: #FFFFFF;")
        title_text_layout.addWidget(main_title)
        
        subtitle = QLabel("Système d'Entretien Vocal Intelligent")
        subtitle.setFont(QFont("Arial", 10))
        subtitle.setStyleSheet(f"color: {self.STARK_BLUE_LIGHT};")
        title_text_layout.addWidget(subtitle)
        
        title_layout.addWidget(title_text)
        layout.addWidget(title_container)
        
        layout.addStretch()
        
        # Indicateur de statut avec icône
        status_container = QWidget()
        status_layout = QHBoxLayout(status_container)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(10)
        
        # Icône d'activité
        status_icon = QLabel()
        status_icon.setPixmap(StarkIcons.activity(self.STARK_ACCENT).pixmap(QSize(32, 32)))
        status_layout.addWidget(status_icon)
        
        status_text_container = QWidget()
        status_text_layout = QVBoxLayout(status_text_container)
        status_text_layout.setContentsMargins(0, 0, 0, 0)
        status_text_layout.setSpacing(0)
        
        self.status_label = QLabel("DÉCONNECTÉ")
        self.status_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.status_label.setStyleSheet(f"color: {self.STARK_ACCENT};")
        status_text_layout.addWidget(self.status_label)
        
        self.status_detail = QLabel("En attente de connexion")
        self.status_detail.setFont(QFont("Arial", 8))
        self.status_detail.setStyleSheet(f"color: {self.STARK_BLUE_LIGHT};")
        status_text_layout.addWidget(self.status_detail)
        
        status_layout.addWidget(status_text_container)
        layout.addWidget(status_container)
        
        return header
    
    def _create_connection_widget(self) -> QWidget:
        """Widget de connexion avec design Stark"""
        widget = QFrame()
        widget.setStyleSheet("QFrame { background: transparent; }")
        
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(30)
        
        # Carte de connexion Stark
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {self.STARK_BG_CARD},
                    stop:1 {self.STARK_BG_DARK});
                border: 3px solid {self.STARK_BLUE_PRIMARY};
                border-radius: 25px;
            }}
        """)
        card.setFixedSize(550, 450)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(50, 50, 50, 50)
        card_layout.setSpacing(25)
        
        # Icône centrale (Shield Check pour sécurité)
        icon_label = QLabel()
        icon_label.setPixmap(StarkIcons.shield_check(self.STARK_BLUE_LIGHT).pixmap(QSize(80, 80)))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(icon_label)
        
        # Titre
        title = QLabel("CONNEXION SÉCURISÉE")
        title.setFont(QFont("Arial", 20, QFont.Weight.ExtraBold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("#FFFFFF")
        card_layout.addWidget(title)
        
        subtitle = QLabel("Entrez votre identifiant de session")
        subtitle.setFont(QFont("Arial", 11))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(f"color: {self.STARK_BLUE_LIGHT};")
        card_layout.addWidget(subtitle)
        
        # Champ session ID
        self.session_input = QLineEdit()
        self.session_input.setPlaceholderText("session_xxxxxxxxxxxxx")
        self.session_input.setFont(QFont("Courier New", 13, QFont.Weight.Bold))
        self.session_input.setMinimumHeight(55)
        self.session_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.session_input.setStyleSheet(f"""
            QLineEdit {{
                background: rgba(255, 255, 255, 0.1);
                border: 2px solid {self.STARK_BLUE_PRIMARY};
                border-radius: 12px;
                padding: 15px;
                color: #FFFFFF;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border: 2px solid {self.STARK_ACCENT};
                background: rgba(255, 255, 255, 0.15);
            }}
            QLineEdit::placeholder {{
                color: {self.STARK_BLUE_LIGHT};
            }}
        """)
        card_layout.addWidget(self.session_input)
        
        # Bouton connexion Stark
        connect_btn = QPushButton("DÉMARRER L'ENTRETIEN")
        connect_btn.setFont(QFont("Arial", 13, QFont.Weight.ExtraBold))
        connect_btn.setMinimumHeight(60)
        connect_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        connect_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {self.STARK_BLUE_PRIMARY}, 
                    stop:1 {self.STARK_BLUE_LIGHT});
                color: white;
                border: none;
                border-radius: 15px;
                padding: 15px;
                font-size: 13px;
                letter-spacing: 2px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {self.STARK_BLUE_LIGHT}, 
                    stop:1 {self.STARK_ACCENT});
            }}
            QPushButton:pressed {{
                background: {self.STARK_BLUE_DARK};
            }}
        """)
        connect_btn.clicked.connect(self._connect_to_interview)
        card_layout.addWidget(connect_btn)
        
        layout.addWidget(card)
        
        return widget
    
    def _connect_signals(self):
        """Connecter les signaux"""
        self.audio_recorder.audio_chunk_ready.connect(self._on_audio_chunk)
        self.audio_recorder.recording_stopped.connect(self._on_recording_stopped)
        
        self.interview_widget.start_recording.connect(self._start_recording)
        self.interview_widget.stop_recording.connect(self._stop_recording)
        self.interview_widget.end_interview.connect(self._end_interview)
    
    def _connect_to_interview(self):
        """Connecter à une session"""
        session_id = self.session_input.text().strip()
        
        if not session_id:
            self._show_error_dialog("Erreur de Connexion", 
                                   "Veuillez entrer un identifiant de session valide")
            return
        
        self.session_id = session_id
        
        # Créer WebSocket
        ws_url = f"{settings.WEBSOCKET_URL}/ws/interview/{session_id}"
        self.websocket_client = WebSocketClient(ws_url)
        
        # Connecter signaux
        self.websocket_client.connected.connect(self._on_connected)
        self.websocket_client.disconnected.connect(self._on_disconnected)
        self.websocket_client.message_received.connect(self._on_message_received)
        self.websocket_client.error_occurred.connect(self._on_error)
        
        # Se connecter
        self.websocket_client.connect_to_server()
        self.statusBar().showMessage("⏳ Connexion sécurisée Stark en cours...")
        self.status_detail.setText("Établissement de la connexion...")
    
    def _on_connected(self):
        """Connexion réussie"""
        self.status_label.setText("CONNECTÉ")
        self.status_label.setStyleSheet(f"color: #00FF88;")
        self.status_detail.setText("Session active et sécurisée")
        self.statusBar().showMessage("✅ Connexion Sécurisée Établie - Session Active")
        
        self.connection_widget.setVisible(False)
        self.interview_container.setVisible(True)
    
    def _on_disconnected(self):
        """Déconnexion"""
        self.status_label.setText("DÉCONNECTÉ")
        self.status_label.setStyleSheet(f"color: {self.STARK_ACCENT};")
        self.status_detail.setText("Session terminée")
        self.statusBar().showMessage("❌ Déconnecté du Serveur")
    
    def _on_message_received(self, data: dict):
        """Traiter message WebSocket"""
        msg_type = data.get("type")
        msg_data = data.get("data", {})
        
        if msg_type == "welcome":
            text = msg_data.get("text")
            audio_url = msg_data.get("audio_url")
            
            self._show_info_dialog("Bienvenue", text)
            
            if audio_url:
                full_url = f"{settings.BACKEND_URL}{audio_url}"
                # TODO: Télécharger et jouer l'audio
        
        elif msg_type == "question":
            text = msg_data.get("text")
            progress = msg_data.get("progress")
            audio_url = msg_data.get("audio_url")
            
            self.interview_widget.update_question(text, progress)
            
            if audio_url:
                # TODO: Jouer l'audio
                pass
            
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
            self._show_error_dialog("Erreur Système", error_msg)
    
    def _on_error(self, error: str):
        """Erreur"""
        self._show_error_dialog("Erreur de Connexion", error)
        self.statusBar().showMessage(f"❌ Erreur: {error}")
    
    def _start_recording(self):
        """Démarrer l'enregistrement"""
        self.audio_recorder.start_recording()
        self.video_player.set_listening()
        self.statusBar().showMessage("🎤 Enregistrement en cours...")
    
    def _stop_recording(self):
        """Arrêter l'enregistrement"""
        self.audio_recorder.stop_recording()
        self.statusBar().showMessage("⏳ Traitement de votre réponse...")
    
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
            self.websocket_client.send_message({
                "type": "answer_complete"
            })
        
        self.interview_widget.enable_recording(False)
        self.video_player.set_idle()
    
    def _end_interview(self):
        """Terminer l'entretien"""
        reply = QMessageBox.question(
            self,
            "Confirmer l'Action",
            "Êtes-vous sûr de vouloir terminer l'entretien ?\n\n"
            "Cette action est irréversible.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.websocket_client:
                self.websocket_client.send_message({
                    "type": "end_interview"
                })
    
    def _show_info_dialog(self, title: str, message: str):
        """Dialogue d'information Stark"""
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStyleSheet(f"""
            QMessageBox {{
                background-color: {self.STARK_BG_CARD};
            }}
            QMessageBox QLabel {{
                color: #FFFFFF;
                font-size: 13px;
            }}
            QPushButton {{
                background-color: {self.STARK_BLUE_PRIMARY};
                color: white;
                border-radius: 5px;
                padding: 8px 20px;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {self.STARK_BLUE_LIGHT};
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
                background-color: {self.STARK_BG_CARD};
            }}
            QMessageBox QLabel {{
                color: #00FF88;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton {{
                background-color: #27ae60;
                color: white;
                border-radius: 5px;
                padding: 8px 20px;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: #2ecc71;
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
                background-color: {self.STARK_BG_CARD};
            }}
            QMessageBox QLabel {{
                color: {self.STARK_ACCENT};
                font-size: 13px;
            }}
            QPushButton {{
                background-color: {self.STARK_ACCENT};
                color: white;
                border-radius: 5px;
                padding: 8px 20px;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: #FF8555;
            }}
        """)
        msg_box.exec()
    
    def closeEvent(self, event):
        """Gérer fermeture"""
        if self.websocket_client:
            self.websocket_client.disconnect_from_server()
        
        self.audio_recorder.cleanup()
        event.accept()