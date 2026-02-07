from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtCore import QUrl, Qt
from pathlib import Path

class VideoPlayerWidget(QWidget):
    """Widget pour lire vidéo/audio de l'avatar"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        
        # Placeholder avatar (image statique pour l'instant)
        self.avatar_label = QLabel("🤖 Avatar")
        self.avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar_label.setStyleSheet("""
            QLabel {
                font-size: 100px;
                background-color: #ECF0F1;
                border-radius: 20px;
                min-height: 400px;
            }
        """)
        layout.addWidget(self.avatar_label)
        
        # Lecteur audio
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        
        # Label de statut
        self.status_label = QLabel("En attente...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #7F8C8D;
                padding: 10px;
            }
        """)
        layout.addWidget(self.status_label)
    
    def play_audio(self, audio_url: str):
        """Jouer un fichier audio"""
        self.status_label.setText("🔊 En train de parler...")
        self.player.setSource(QUrl.fromLocalFile(audio_url))
        self.player.play()
        
        # Retour au statut idle
        self.player.mediaStatusChanged.connect(self._on_playback_finished)
    
    def _on_playback_finished(self, status):
        """Callback fin de lecture"""
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.status_label.setText("✅ Prêt")
    
    def set_listening(self):
        """Mode écoute"""
        self.status_label.setText("👂 En écoute...")
        self.avatar_label.setText("👂")
    
    def set_speaking(self):
        """Mode parole"""
        self.status_label.setText("🗣️ En train de parler...")
        self.avatar_label.setText("🗣️")
    
    def set_idle(self):
        """Mode repos"""
        self.status_label.setText("💤 En attente...")
        self.avatar_label.setText("🤖")