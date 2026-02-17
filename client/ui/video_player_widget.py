import cv2
import pygame
import numpy as np
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QHBoxLayout, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, QTimer, Slot, QSize
from PySide6.QtGui import QFont, QImage, QPixmap, QColor
from pathlib import Path
from client.ui.icons import StarkIcons


class VideoPlayerWidget(QWidget):
    """
    Moteur de rendu Avatar RH - Design Fluide et Créatif
    Avec animations, effets de glow et transitions douces
    CORRECTIF: Suppression de text-shadow (non supporté par Qt stylesheets)
    """

    # Palette Stark
    STARK_BLUE_PRIMARY = "#1565C0"
    STARK_BLUE_DARK = "#0D47A1"
    STARK_BLUE_LIGHT = "#42A5F5"
    STARK_BLUE_GLOW = "#64B5F6"
    STARK_ACCENT = "#FF6B35"
    STARK_ACCENT_GLOW = "#FF8555"
    STARK_BG_DARK = "#0A1929"
    STARK_SUCCESS = "#00E676"
    STARK_SUCCESS_GLOW = "#00FF88"

    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # Container principal
        avatar_container = QFrame()
        avatar_container.setStyleSheet("QFrame { background: transparent; }")
        container_layout = QVBoxLayout(avatar_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Zone d'affichage
        self.avatar_display = QLabel()
        self.avatar_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar_display.setStyleSheet(f"""
            QLabel {{
                background: qradialgradient(cx:0.5, cy:0.5, radius:1,
                    fx:0.5, fy:0.5,
                    stop:0 {self.STARK_BG_DARK},
                    stop:0.7 {self.STARK_BLUE_DARK},
                    stop:1 {self.STARK_BG_DARK});
                border: none;
                border-radius: 20px;
            }}
        """)
        self.avatar_display.setMinimumSize(800, 600)
        self.avatar_display.setScaledContents(False)

        # Effet de glow
        self.avatar_shadow = QGraphicsDropShadowEffect()
        self.avatar_shadow.setBlurRadius(35)
        self.avatar_shadow.setColor(QColor(self.STARK_BLUE_GLOW))
        self.avatar_shadow.setOffset(0, 0)
        self.avatar_display.setGraphicsEffect(self.avatar_shadow)

        container_layout.addWidget(self.avatar_display)

        # Barre de statut
        status_overlay = QFrame()
        status_overlay.setObjectName("statusOverlay")
        status_overlay.setStyleSheet(f"""
            #statusOverlay {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(13, 71, 161, 0.85),
                    stop:0.5 rgba(21, 101, 192, 0.75),
                    stop:1 rgba(13, 71, 161, 0.85));
                border: 2px solid rgba(100, 181, 246, 0.4);
                border-radius: 18px;
                padding: 12px 25px;
            }}
        """)

        status_shadow = QGraphicsDropShadowEffect()
        status_shadow.setBlurRadius(20)
        status_shadow.setColor(QColor(self.STARK_BLUE_PRIMARY))
        status_shadow.setOffset(0, 5)
        status_overlay.setGraphicsEffect(status_shadow)

        status_layout = QHBoxLayout(status_overlay)
        status_layout.setContentsMargins(15, 10, 15, 10)
        status_layout.setSpacing(15)

        # Icône d'état
        self.status_icon = QLabel()
        self.status_icon.setPixmap(StarkIcons.user_check(self.STARK_BLUE_LIGHT).pixmap(QSize(28, 28)))
        status_layout.addWidget(self.status_icon)

        # Texte de statut — SANS text-shadow (non supporté Qt)
        self.status_label = QLabel("Agent RH : Initialisation...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.status_label.setStyleSheet("""
            color: #FFFFFF;
            font-size: 14px;
            font-weight: bold;
            letter-spacing: 1px;
            background: transparent;
        """)
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()

        # Indicateur pulse
        self.pulse_indicator = QLabel("●")
        self.pulse_indicator.setFont(QFont("Arial", 18))
        self.pulse_indicator.setStyleSheet(f"""
            color: {self.STARK_SUCCESS};
            background: transparent;
        """)
        status_layout.addWidget(self.pulse_indicator)

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

        # Timer pulse
        self.pulse_timer = QTimer()
        self.pulse_timer.timeout.connect(self._animate_pulse)
        self.pulse_state = False
        self.pulse_timer.start(1000)

        self.set_idle()

    def _load_video(self, state):
        """Charger la vidéo"""
        if self.cap:
            self.cap.release()

        path = self.video_paths.get(state)

        if not Path(path).exists():
            print(f"⚠️ Vidéo manquante : {path}")
            self._show_placeholder(state)
            return

        self.cap = cv2.VideoCapture(path)
        self.current_state = state

        if not self.timer.isActive():
            self.timer.start(33)  # 30 FPS

    def _show_placeholder(self, state):
        """Placeholder avec gradient"""
        placeholder_size = (800, 600)
        placeholder = np.zeros((placeholder_size[1], placeholder_size[0], 3), dtype=np.uint8)

        center_x, center_y = placeholder_size[0] // 2, placeholder_size[1] // 2
        max_distance = np.sqrt(center_x**2 + center_y**2)

        for y in range(placeholder_size[1]):
            for x in range(placeholder_size[0]):
                distance = np.sqrt((x - center_x)**2 + (y - center_y)**2)
                ratio = distance / max_distance
                r = int(10 + ratio * 3)
                g = int(25 + ratio * 96)
                b = int(41 + ratio * 151)
                placeholder[y, x] = (b, g, r)

        cv2.putText(placeholder, f"Mode: {state}", (center_x - 100, center_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        h, w, ch = placeholder.shape
        bytes_per_line = ch * w
        qt_img = QImage(placeholder.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_img)

        self.avatar_display.setPixmap(pixmap.scaled(
            self.avatar_display.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        ))

    @Slot()
    def _update_frame(self):
        """Boucle de rendu"""
        if self.cap is None or not self.cap.isOpened():
            return

        ret, frame = self.cap.read()

        if not ret:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            return

        try:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pg_surface = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
            buffer = pygame.surfarray.array3d(pg_surface).swapaxes(0, 1)
            buffer = np.ascontiguousarray(buffer)

            h, w, ch = buffer.shape
            bytes_per_line = ch * w

            qt_img = QImage(buffer.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_img)

            scaled_pixmap = pixmap.scaled(
                self.avatar_display.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )

            self.avatar_display.setPixmap(scaled_pixmap)

        except Exception as e:
            print(f"Erreur rendu: {e}")

    def _animate_pulse(self):
        """Animation du pulse indicator"""
        if self.pulse_state:
            self.pulse_indicator.setStyleSheet(f"""
                color: {self.STARK_SUCCESS_GLOW};
                background: transparent;
            """)
        else:
            self.pulse_indicator.setStyleSheet(f"""
                color: {self.STARK_SUCCESS};
                background: transparent;
            """)

        self.pulse_state = not self.pulse_state

    def _update_glow_color(self, color: str):
        """Mettre à jour la couleur du glow"""
        self.avatar_shadow.setColor(QColor(color))

    # === MÉTHODES DE CONTRÔLE ===

    def set_idle(self):
        """Mode attente"""
        self.status_icon.setPixmap(StarkIcons.user_check(self.STARK_SUCCESS).pixmap(QSize(28, 28)))
        self.status_label.setText("Agent RH : Prêt à vous écouter")
        self.status_label.setStyleSheet("""
            color: #00E676;
            font-size: 14px;
            font-weight: bold;
            letter-spacing: 1px;
            background: transparent;
        """)
        self._update_glow_color(self.STARK_SUCCESS)
        self._load_video("idle")

    def set_speaking(self):
        """Mode parole"""
        self.status_icon.setPixmap(StarkIcons.message_circle(self.STARK_BLUE_LIGHT).pixmap(QSize(28, 28)))
        self.status_label.setText("Agent RH : Analyse de votre profil...")
        self.status_label.setStyleSheet("""
            color: #42A5F5;
            font-size: 14px;
            font-weight: bold;
            letter-spacing: 1px;
            background: transparent;
        """)
        self._update_glow_color(self.STARK_BLUE_GLOW)
        self._load_video("speaking")

    def set_listening(self):
        """Mode écoute"""
        self.status_icon.setPixmap(StarkIcons.headphones(self.STARK_ACCENT_GLOW).pixmap(QSize(28, 28)))
        self.status_label.setText("Agent RH : Écoute attentive en cours...")
        self.status_label.setStyleSheet("""
            color: #FF8555;
            font-size: 14px;
            font-weight: bold;
            letter-spacing: 1px;
            background: transparent;
        """)
        self._update_glow_color(self.STARK_ACCENT_GLOW)
        self._load_video("listening")

    def resizeEvent(self, event):
        """Ajustement responsive"""
        super().resizeEvent(event)

    def closeEvent(self, event):
        """Nettoyage"""
        self.timer.stop()
        self.pulse_timer.stop()
        if self.cap:
            self.cap.release()
        pygame.quit()
        super().closeEvent(event)