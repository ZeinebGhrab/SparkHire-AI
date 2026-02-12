import cv2
import pygame
import numpy as np
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QHBoxLayout
from PySide6.QtCore import Qt, QTimer, Slot, QSize
from PySide6.QtGui import QImage, QPixmap, QPainter, QLinearGradient, QColor
from pathlib import Path
from client.ui.icons import StarkIcons

class VideoPlayerWidget(QWidget):
    """
    Moteur de rendu Avatar RH - Design Stark Solutions
    """
    
    # Palette Stark
    STARK_BLUE_PRIMARY = "#1565C0"
    STARK_BLUE_DARK = "#0D47A1"
    STARK_BLUE_LIGHT = "#42A5F5"
    STARK_ACCENT = "#FF6B35"
    STARK_BG_DARK = "#0A1929"
    STARK_SUCCESS = "#00E676"
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Layout principal
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Container pour l'avatar
        avatar_container = QFrame()
        avatar_container.setStyleSheet("QFrame { background: transparent; }")
        container_layout = QVBoxLayout(avatar_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        # Zone d'affichage de l'avatar
        self.avatar_display = QLabel()
        self.avatar_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar_display.setStyleSheet(f"""
            QLabel {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {self.STARK_BG_DARK},
                    stop:1 {self.STARK_BLUE_DARK});
                border: none;
                border-radius: 15px;
            }}
        """)
        self.avatar_display.setMinimumSize(800, 600)
        self.avatar_display.setScaledContents(False)
        container_layout.addWidget(self.avatar_display)
        
        # Barre de statut Stark avec icônes
        status_overlay = QFrame()
        status_overlay.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {self.STARK_BLUE_DARK},
                    stop:0.5 {self.STARK_BLUE_PRIMARY},
                    stop:1 {self.STARK_BLUE_DARK});
                border-radius: 12px;
                padding: 8px 20px;
            }}
        """)
        status_layout = QHBoxLayout(status_overlay)
        status_layout.setContentsMargins(15, 8, 15, 8)
        status_layout.setSpacing(10)
        
        # Icône d'état
        self.status_icon = QLabel()
        self.status_icon.setPixmap(StarkIcons.user_check(self.STARK_BLUE_LIGHT).pixmap(QSize(24, 24)))
        status_layout.addWidget(self.status_icon)
        
        self.status_label = QLabel("Agent RH : Initialisation...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("""
            color: #FFFFFF;
            font-size: 13px;
            font-weight: bold;
            letter-spacing: 1px;
            background: transparent;
        """)
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        
        container_layout.addWidget(status_overlay)
        
        self.layout.addWidget(avatar_container)
        
        # Initialisation Pygame
        pygame.init()
        
        # Chemins des vidéos
        self.base_path = Path(__file__).resolve().parent.parent.parent
        self.video_dir = self.base_path / "assets" / "videos"
        
        self.video_paths = {
            "idle": str(self.video_dir / "rh_idle.mp4"),
            "speaking": str(self.video_dir / "rh_speaking.mp4"),
            "listening": str(self.video_dir / "rh_listening.mp4")
        }
        
        # Contrôle vidéo
        self.cap = None
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_frame)
        self.current_state = "idle"
        
        # Démarrage
        self.set_idle()
    
    def _load_video(self, state):
        """Charger la vidéo correspondant à l'état"""
        if self.cap:
            self.cap.release()
        
        path = self.video_paths.get(state)
        
        if not Path(path).exists():
            print(f"⚠️ Vidéo manquante : {path}")
            self._show_placeholder(state)
            return
        
        self.cap = cv2.VideoCapture(path)
        self.current_state = state
        
        # Démarrer le rendu à 30 FPS
        if not self.timer.isActive():
            self.timer.start(33)
    
    def _show_placeholder(self, state):
        """Afficher un placeholder avec gradient Stark"""
        placeholder_size = (800, 600)
        placeholder = np.zeros((placeholder_size[1], placeholder_size[0], 3), dtype=np.uint8)
        
        # Gradient Stark
        for y in range(placeholder_size[1]):
            ratio = y / placeholder_size[1]
            # Interpolation entre STARK_BG_DARK et STARK_BLUE_DARK
            r = int(10 + ratio * 3)
            g = int(25 + ratio * 46)
            b = int(41 + ratio * 120)
            placeholder[y, :] = (b, g, r)  # BGR pour OpenCV
        
        # Convertir en QImage
        h, w, ch = placeholder.shape
        bytes_per_line = ch * w
        qt_img = QImage(placeholder.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_img)
        
        self.avatar_display.setPixmap(pixmap.scaled(
            self.avatar_display.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        ))
        
        self.status_label.setText(f"Vidéo '{state}' non disponible")
    
    @Slot()
    def _update_frame(self):
        """Boucle de rendu principale"""
        if self.cap is None or not self.cap.isOpened():
            return
        
        ret, frame = self.cap.read()
        
        if not ret:
            # Boucle infinie
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            return
        
        try:
            # Conversion BGR vers RGB
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Traitement Pygame
            pg_surface = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
            
            # Extraction pour Qt
            buffer = pygame.surfarray.array3d(pg_surface).swapaxes(0, 1)
            buffer = np.ascontiguousarray(buffer)
            
            h, w, ch = buffer.shape
            bytes_per_line = ch * w
            
            # Image Qt
            qt_img = QImage(buffer.data, w, h, bytes_per_line, QImage.Format_RGB888)
            
            # Affichage
            pixmap = QPixmap.fromImage(qt_img)
            
            scaled_pixmap = pixmap.scaled(
                self.avatar_display.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            
            self.avatar_display.setPixmap(scaled_pixmap)
        
        except Exception as e:
            print(f"Erreur rendu frame: {e}")
    
    # === MÉTHODES DE CONTRÔLE ===
    
    def set_idle(self):
        """Avatar en mode attente"""
        self.status_icon.setPixmap(StarkIcons.user_check(self.STARK_BLUE_LIGHT).pixmap(QSize(24, 24)))
        self.status_label.setText("Agent RH : Prêt à vous écouter")
        self.status_label.setStyleSheet(f"""
            color: {self.STARK_SUCCESS};
            font-size: 13px;
            font-weight: bold;
            letter-spacing: 1px;
            background: transparent;
        """)
        self._load_video("idle")
    
    def set_speaking(self):
        """Avatar en train de parler"""
        self.status_icon.setPixmap(StarkIcons.message_circle(self.STARK_BLUE_LIGHT).pixmap(QSize(24, 24)))
        self.status_label.setText("Agent RH : Analyse de votre profil...")
        self.status_label.setStyleSheet(f"""
            color: {self.STARK_BLUE_LIGHT};
            font-size: 13px;
            font-weight: bold;
            letter-spacing: 1px;
            background: transparent;
        """)
        self._load_video("speaking")
    
    def set_listening(self):
        """Avatar en écoute active"""
        self.status_icon.setPixmap(StarkIcons.headphones(self.STARK_ACCENT).pixmap(QSize(24, 24)))
        self.status_label.setText("Agent RH : Écoute attentive en cours...")
        self.status_label.setStyleSheet(f"""
            color: {self.STARK_ACCENT};
            font-size: 13px;
            font-weight: bold;
            letter-spacing: 1px;
            background: transparent;
        """)
        self._load_video("listening")
    
    def resizeEvent(self, event):
        """Ajuster l'affichage lors du redimensionnement"""
        super().resizeEvent(event)
        if hasattr(self, 'cap') and self.cap and self.cap.isOpened():
            pass
    
    def closeEvent(self, event):
        """Nettoyage"""
        self.timer.stop()
        if self.cap:
            self.cap.release()
        pygame.quit()
        super().closeEvent(event)