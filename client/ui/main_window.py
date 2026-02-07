from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QMessageBox, QLabel, QLineEdit, QPushButton, QSplitter
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import base64

from client.config import settings
from client.core import WebSocketClient, AudioRecorder
from client.ui.video_player_widget import VideoPlayerWidget
from client.ui.interview_widget import InterviewWidget

class MainWindow(QMainWindow):
    """Fenêtre principale de l'application client"""
    
    def __init__(self):
        super().__init__()
        
        self.websocket_client = None
        self.audio_recorder = AudioRecorder()
        self.session_id = None
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """Initialiser l'interface"""
        self.setWindowTitle("Stark Recruitment - Entretien Vocal")
        self.setGeometry(100, 100, settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # En-tête
        header = self._create_header()
        main_layout.addWidget(header)
        
        # Zone de connexion (si pas encore connecté)
        self.connection_widget = self._create_connection_widget()
        main_layout.addWidget(self.connection_widget)
        
        # Splitter principal (caché au départ)
        self.interview_container = QSplitter(Qt.Orientation.Horizontal)
        self.interview_container.setVisible(False)
        
        # Avatar (gauche)
        self.video_player = VideoPlayerWidget()
        self.interview_container.addWidget(self.video_player)
        
        # Interface entretien (droite)
        self.interview_widget = InterviewWidget()
        self.interview_container.addWidget(self.interview_widget)
        
        # Ratio 40/60
        self.interview_container.setSizes([480, 720])
        
        main_layout.addWidget(self.interview_container)
        
        # Barre de statut
        self.statusBar().showMessage("Prêt")
    
    def _create_header(self) -> QWidget:
        """Créer l'en-tête"""
        header = QWidget()
        header.setStyleSheet("""
            QWidget {
                background-color: #2C3E50;
                color: white;
            }
        """)
        header.setFixedHeight(70)
        
        layout = QHBoxLayout(header)
        
        title = QLabel("🎤 Stark Recruitment - Entretien Vocal")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: white;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        self.status_indicator = QLabel("●")
        self.status_indicator.setFont(QFont("Arial", 20))
        self.status_indicator.setStyleSheet("color: #E74C3C;")
        layout.addWidget(self.status_indicator)
        
        status_label = QLabel("Déconnecté")
        status_label.setStyleSheet("color: white;")
        self.status_label = status_label
        layout.addWidget(status_label)
        
        return header
    
    def _create_connection_widget(self) -> QWidget:
        """Créer widget de connexion"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Titre
        title = QLabel("Entrer l'ID de session")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Champ session ID
        self.session_input = QLineEdit()
        self.session_input.setPlaceholderText("Ex: session_abc123def456")
        self.session_input.setFont(QFont("Arial", 12))
        self.session_input.setMaximumWidth(400)
        self.session_input.setMinimumHeight(40)
        self.session_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.session_input, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Bouton connexion
        connect_btn = QPushButton("Se connecter")
        connect_btn.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        connect_btn.setMinimumHeight(50)
        connect_btn.setMaximumWidth(200)
        connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498DB;
                color: white;
                border-radius: 10px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #2980B9;
            }
        """)
        connect_btn.clicked.connect(self._connect_to_interview)
        layout.addWidget(connect_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        return widget
    
    def _connect_signals(self):
        """Connecter les signaux"""
        # Audio recorder
        self.audio_recorder.audio_chunk_ready.connect(self._on_audio_chunk)
        self.audio_recorder.recording_stopped.connect(self._on_recording_stopped)
        
        # Interview widget
        self.interview_widget.start_recording.connect(self._start_recording)
        self.interview_widget.stop_recording.connect(self._stop_recording)
        self.interview_widget.end_interview.connect(self._end_interview)
    
    def _connect_to_interview(self):
        """Connecter à une session d'entretien"""
        session_id = self.session_input.text().strip()
        
        if not session_id:
            QMessageBox.warning(self, "Erreur", "Veuillez entrer un ID de session")
            return
        
        self.session_id = session_id
        
        # Créer WebSocket client
        ws_url = f"{settings.WEBSOCKET_URL}/ws/interview/{session_id}"
        self.websocket_client = WebSocketClient(ws_url)
        
        # Connecter signaux WebSocket
        self.websocket_client.connected.connect(self._on_connected)
        self.websocket_client.disconnected.connect(self._on_disconnected)
        self.websocket_client.message_received.connect(self._on_message_received)
        self.websocket_client.error_occurred.connect(self._on_error)
        
        # Se connecter
        self.websocket_client.connect_to_server()
        self.statusBar().showMessage("Connexion en cours...")
    
    def _on_connected(self):
        """Callback connexion réussie"""
        self.status_indicator.setStyleSheet("color: #27AE60;")
        self.status_label.setText("Connecté")
        self.statusBar().showMessage("Connecté avec succès")
        
        # Masquer zone de connexion, afficher entretien
        self.connection_widget.setVisible(False)
        self.interview_container.setVisible(True)
    
    def _on_disconnected(self):
        """Callback déconnexion"""
        self.status_indicator.setStyleSheet("color: #E74C3C;")
        self.status_label.setText("Déconnecté")
        self.statusBar().showMessage("Déconnecté")
    
    def _on_message_received(self, data: dict):
        """Traiter message WebSocket"""
        msg_type = data.get("type")
        msg_data = data.get("data", {})
        
        if msg_type == "welcome":
            # Message de bienvenue
            text = msg_data.get("text")
            audio_url = msg_data.get("audio_url")
            
            QMessageBox.information(self, "Bienvenue", text)
            
            if audio_url:
                # Construire chemin complet
                full_url = f"{settings.BACKEND_URL}{audio_url}"
                # TODO: Télécharger et jouer l'audio
        
        elif msg_type == "question":
            # Nouvelle question
            text = msg_data.get("text")
            progress = msg_data.get("progress")
            audio_url = msg_data.get("audio_url")
            
            self.interview_widget.update_question(text, progress)
            
            if audio_url:
                # TODO: Jouer l'audio de la question
                pass
            
            # Activer l'enregistrement
            self.interview_widget.enable_recording(True)
            self.video_player.set_idle()
        
        elif msg_type == "answer_saved":
            # Réponse sauvegardée
            transcript = msg_data.get("transcript")
            self.interview_widget.update_transcript(transcript)
            self.statusBar().showMessage("Réponse enregistrée", 3000)
        
        elif msg_type == "interview_completed":
            # Entretien terminé
            message = msg_data.get("message")
            QMessageBox.information(self, "Entretien terminé", message)
            self.close()
        
        elif msg_type == "error":
            # Erreur
            error_msg = msg_data.get("message")
            QMessageBox.critical(self, "Erreur", error_msg)
    
    def _on_error(self, error: str):
        """Callback erreur"""
        QMessageBox.critical(self, "Erreur", error)
        self.statusBar().showMessage(f"Erreur: {error}")
    
    def _start_recording(self):
        """Démarrer l'enregistrement audio"""
        self.audio_recorder.start_recording()
        self.video_player.set_listening()
        self.statusBar().showMessage("🎤 Enregistrement en cours...")
    
    def _stop_recording(self):
        """Arrêter l'enregistrement"""
        self.audio_recorder.stop_recording()
        self.statusBar().showMessage("⏸️ Enregistrement arrêté, envoi en cours...")
    
    def _on_audio_chunk(self, chunk: bytes):
        """Envoyer chunk audio au serveur"""
        if self.websocket_client:
            # Encoder en base64
            chunk_b64 = base64.b64encode(chunk).decode('utf-8')
            
            self.websocket_client.send_message({
                "type": "audio_chunk",
                "audio_data": chunk_b64
            })
    
    def _on_recording_stopped(self):
        """Recording arrêté"""
        if self.websocket_client:
            # Signaler fin de la réponse
            self.websocket_client.send_message({
                "type": "answer_complete"
            })
        
        self.interview_widget.enable_recording(False)
        self.video_player.set_idle()
    
    def _end_interview(self):
        """Terminer l'entretien"""
        reply = QMessageBox.question(
            self,
            "Confirmer",
            "Êtes-vous sûr de vouloir terminer l'entretien ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.websocket_client:
                self.websocket_client.send_message({
                    "type": "end_interview"
                })
    
    def closeEvent(self, event):
        """Gérer fermeture"""
        if self.websocket_client:
            self.websocket_client.disconnect_from_server()
        
        self.audio_recorder.cleanup()
        event.accept()