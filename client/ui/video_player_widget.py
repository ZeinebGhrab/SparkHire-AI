import sys
import cv2
import pygame
import numpy as np
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer, Slot
from PySide6.QtGui import QImage, QPixmap
from pathlib import Path

class VideoPlayerWidget(QWidget):
    """
    Moteur de rendu Avatar RH "Humain Réel".
    Utilise OpenCV pour la lecture, Pygame pour le traitement, 
    et PySide6 pour l'affichage final.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 1. Interface Utilisateur (UI)
        self.layout = QVBoxLayout(self)
        
        # Zone d'affichage de l'image
        self.avatar_display = QLabel()
        self.avatar_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar_display.setStyleSheet("""
            background-color: #000000; 
            border: 2px solid #3498DB;
            border-radius: 15px;
        """)
        self.avatar_display.setMinimumHeight(400)
        self.layout.addWidget(self.avatar_display)
        
        # Label de statut
        self.status_label = QLabel("Initialisation de l'agent RH...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-size: 14px; color: #BDC3C7; font-weight: bold; padding: 5px;")
        self.layout.addWidget(self.status_label)

        # 2. Initialisation Pygame (moteur interne)
        pygame.init()
        
        # 3. Gestion automatique des chemins (Assets)
        # On remonte de 'client/ui/' vers la racine pour trouver 'assets/'
        self.base_path = Path(__file__).resolve().parent.parent.parent
        self.video_dir = self.base_path / "assets" / "videos"
        
        self.video_paths = {
            "idle": str(self.video_dir / "rh_idle.mp4"),
            "speaking": str(self.video_dir / "rh_speaking.mp4"),
            "listening": str(self.video_dir / "rh_listening.mp4")
        }
        
        # 4. Contrôle Vidéo
        self.cap = None
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_frame)
        
        # Lancement de l'état initial
        self.set_idle()

    def _load_video(self, state):
        """Charge le fichier MP4 correspondant à l'état"""
        if self.cap:
            self.cap.release()
        
        path = self.video_paths.get(state)
        
        if not Path(path).exists():
            print(f"⚠️ Erreur : Vidéo manquante à l'emplacement : {path}")
            self.status_label.setText("Fichier vidéo introuvable")
            return

        self.cap = cv2.VideoCapture(path)
        
        # Déclenchement de la boucle de rendu (~30 images par seconde)
        if not self.timer.isActive():
            self.timer.start(33) 

    @Slot()
    def _update_frame(self):
        """
        Boucle de rendu principale. 
        C'est ici que la conversion se fait de manière sécurisée.
        """
        if self.cap is None or not self.cap.isOpened():
            return

        ret, frame = self.cap.read()
        
        if not ret:
            # Recommencer la vidéo (Boucle infinie)
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            return

        # A. Traitement OpenCV : BGR vers RGB
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # B. Passage par Pygame (pour d'éventuels filtres ou dessins)
        pg_surface = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
        
        # C. Extraction des données Pygame pour Qt
        buffer = pygame.surfarray.array3d(pg_surface).swapaxes(0, 1)
        
        # --- FIX POUR BUFFERERROR : Forcer la mémoire contiguë ---
        buffer = np.ascontiguousarray(buffer)
        
        h, w, ch = buffer.shape
        
        # D. Création de l'image PySide6
        qt_img = QImage(buffer.data, w, h, ch * w, QImage.Format_RGB888)
        
        # E. Mise à jour de l'affichage avec redimensionnement fluide
        pixmap = QPixmap.fromImage(qt_img)
        self.avatar_display.setPixmap(pixmap.scaled(
            self.avatar_display.size(), 
            Qt.AspectRatioMode.KeepAspectRatioByExpanding, 
            Qt.TransformationMode.SmoothTransformation
        ))

    # --- MÉTHODES DE CONTRÔLE ---

    def set_idle(self):
        """Avatar qui respire/attend"""
        self.status_label.setText("🤖 RH : Prêt")
        self._load_video("idle")

    def set_speaking(self):
        """Avatar qui parle"""
        self.status_label.setText("🗣️ RH : Analyse de votre profil...")
        self._load_video("speaking")

    def set_listening(self):
        """Avatar qui écoute (hochement de tête)"""
        self.status_label.setText("👂 RH : Je vous écoute...")
        self._load_video("listening")

    def closeEvent(self, event):
        """Nettoyage à la fermeture"""
        self.timer.stop()
        if self.cap:
            self.cap.release()
        pygame.quit()
        super().closeEvent(event)