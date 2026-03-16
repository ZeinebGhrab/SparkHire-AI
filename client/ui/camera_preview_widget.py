"""
CameraPreviewWidget — Overlay caméra picture-in-picture
Affiche un petit aperçu de la webcam dans le coin bas-gauche du lecteur vidéo.
Se connecte directement au signal frame_captured de VideoFrameCollector.
"""

import numpy as np
import cv2
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QGraphicsDropShadowEffect
from PySide6.QtCore    import Qt, QTimer, Signal, Slot
from PySide6.QtGui     import QImage, QPixmap, QColor, QPainter, QPen, QBrush, QFont

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from client.ui.stark_theme import T


# ── Dimensions et marges ─────────────────────────────────────────────────────
_W       = 176   # largeur preview
_H       = 132   # hauteur preview (ratio 4:3)
_MARGIN  = 14    # marge depuis les bords du parent
_RADIUS  = 12    # border-radius


class CameraPreviewWidget(QWidget):
    """
    Petit overlay caméra PiP (picture-in-picture).

    Utilisation :
        preview = CameraPreviewWidget(parent=video_player_widget)
        video_collector.frame_captured.connect(preview.on_frame)
        preview.set_recording(True)   # affiche le point rouge
        preview.show()
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Toujours au-dessus des autres enfants
        self.setWindowFlags(Qt.WindowType.SubWindow)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(_W + 4, _H + 4 + 22)   # +22 pour la barre de statut

        self._recording  = False
        self._has_camera = False
        self._blink      = True
        self._no_signal  = True   # True jusqu'au premier frame reçu

        # Timer clignotement point rouge
        self._blink_timer = QTimer(self)
        self._blink_timer.setInterval(600)
        self._blink_timer.timeout.connect(self._toggle_blink)

        self._build()
        self._show_placeholder()

    # ── Construction ─────────────────────────────────────────────────────────

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(2, 2, 2, 2)
        root.setSpacing(0)

        # Cadre principal
        self._frame = QFrame()
        self._frame.setFixedSize(_W, _H)
        self._frame.setStyleSheet(f"""
            QFrame {{
                background: {T.TEXT_900};
                border: 2px solid rgba(255,255,255,0.18);
                border-radius: {_RADIUS}px;
            }}
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(18)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 120))
        self._frame.setGraphicsEffect(shadow)

        frame_lay = QVBoxLayout(self._frame)
        frame_lay.setContentsMargins(0, 0, 0, 0)
        frame_lay.setSpacing(0)

        # Zone image
        self._img_lbl = QLabel()
        self._img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._img_lbl.setStyleSheet(f"""
            QLabel {{
                background: transparent;
                border-top-left-radius:  {_RADIUS - 2}px;
                border-top-right-radius: {_RADIUS - 2}px;
            }}
        """)
        self._img_lbl.setFixedSize(_W - 4, _H - 26)
        frame_lay.addWidget(self._img_lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        # Barre de statut interne (en bas du cadre)
        bar = QFrame()
        bar.setFixedHeight(24)
        bar.setStyleSheet(f"""
            QFrame {{
                background: rgba(15, 23, 42, 0.85);
                border-bottom-left-radius:  {_RADIUS - 2}px;
                border-bottom-right-radius: {_RADIUS - 2}px;
            }}
        """)
        bar_lay = self._bar_lay = self._make_status_bar(bar)
        frame_lay.addWidget(bar)

        root.addWidget(self._frame)

    def _make_status_bar(self, parent):
        from PySide6.QtWidgets import QHBoxLayout
        lay = QHBoxLayout(parent)
        lay.setContentsMargins(8, 0, 8, 0)
        lay.setSpacing(5)

        # Point indicateur
        self._dot_lbl = QLabel("●")
        self._dot_lbl.setFont(QFont("Segoe UI", 7))
        self._dot_lbl.setStyleSheet(f"color: {T.GREEN_500}; background: transparent;")
        lay.addWidget(self._dot_lbl)

        # Texte statut
        self._status_lbl = QLabel("Caméra active")
        self._status_lbl.setFont(QFont(T.FONT, 7, QFont.Weight.DemiBold))
        self._status_lbl.setStyleSheet("color: rgba(255,255,255,0.75); background: transparent;")
        lay.addWidget(self._status_lbl, stretch=1)

        # Badge REC
        self._rec_badge = QLabel(" ● REC ")
        self._rec_badge.setFont(QFont(T.FONT, 6, QFont.Weight.Bold))
        self._rec_badge.setStyleSheet(f"""
            color: white;
            background: {T.RED_600};
            border-radius: 4px;
            padding: 1px 4px;
        """)
        self._rec_badge.setVisible(False)
        lay.addWidget(self._rec_badge)

        return lay

    # ── Slots publics ─────────────────────────────────────────────────────────

    @Slot(bytes)
    def on_frame(self, jpeg_bytes: bytes):
        """
        Reçoit un frame JPEG depuis VideoFrameCollector.frame_captured.
        Décode et affiche dans le widget.
        """
        try:
            buf   = np.frombuffer(jpeg_bytes, dtype=np.uint8)
            frame = cv2.imdecode(buf, cv2.IMREAD_COLOR)
            if frame is None:
                return

            # Flip horizontal (effet miroir naturel)
            frame = cv2.flip(frame, 1)

            rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, c = rgb.shape
            target_w = _W - 4
            target_h = _H - 26

            # Resize en conservant le ratio
            ratio    = min(target_w / w, target_h / h)
            nw, nh   = int(w * ratio), int(h * ratio)
            resized  = cv2.resize(rgb, (nw, nh), interpolation=cv2.INTER_AREA)

            img = QImage(resized.data.tobytes(), nw, nh, nw * c, QImage.Format.Format_RGB888)
            self._img_lbl.setPixmap(QPixmap.fromImage(img))

            if self._no_signal:
                self._no_signal = False
                self._has_camera = True
                self._status_lbl.setText("Caméra active")
                self._dot_lbl.setStyleSheet(f"color: {T.GREEN_500}; background: transparent;")

        except Exception:
            pass

    def set_recording(self, recording: bool):
        """Allume/éteint l'indicateur REC rouge clignotant."""
        self._recording = recording
        self._rec_badge.setVisible(recording)
        if recording:
            self._blink_timer.start()
            self._status_lbl.setText("Enregistrement…")
            self._dot_lbl.setStyleSheet(f"color: {T.RED_500}; background: transparent;")
        else:
            self._blink_timer.stop()
            self._rec_badge.setVisible(False)
            if self._has_camera:
                self._status_lbl.setText("Caméra active")
                self._dot_lbl.setStyleSheet(f"color: {T.GREEN_500}; background: transparent;")

    def set_camera_unavailable(self):
        """Affiche l'état 'pas de caméra'."""
        self._has_camera = False
        self._status_lbl.setText("Pas de caméra")
        self._dot_lbl.setStyleSheet(f"color: {T.TEXT_400}; background: transparent;")
        self._show_placeholder()

    # ── Interne ───────────────────────────────────────────────────────────────

    def _toggle_blink(self):
        self._blink = not self._blink
        self._rec_badge.setVisible(self._blink and self._recording)

    def _show_placeholder(self):
        """Affiche un fond sombre avec icône caméra quand pas de signal."""
        w, h = _W - 4, _H - 26
        img  = np.zeros((h, w, 3), dtype=np.uint8)
        img[:, :] = (30, 41, 59)   # slate-800

        # Icône simple
        cx, cy = w // 2, h // 2
        cv2.rectangle(img, (cx - 22, cy - 14), (cx + 22, cy + 14), (100, 116, 139), -1)
        cv2.rectangle(img, (cx - 22, cy - 14), (cx + 22, cy + 14), (148, 163, 184), 1)
        pts = np.array([[cx + 22, cy - 8], [cx + 34, cy - 16], [cx + 34, cy + 16], [cx + 22, cy + 8]])
        cv2.fillPoly(img, [pts], (100, 116, 139))
        cv2.circle(img, (cx, cy), 7, (148, 163, 184), -1)
        cv2.circle(img, (cx, cy), 4, (30, 41, 59), -1)

        qt_img = QImage(img.tobytes(), w, h, w * 3, QImage.Format.Format_RGB888)
        self._img_lbl.setPixmap(QPixmap.fromImage(qt_img))

    # ── Positionnement dans le parent ─────────────────────────────────────────

    def reposition(self):
        """
        Place l'overlay dans le coin bas-gauche du widget parent.
        À appeler depuis resizeEvent() du parent.
        """
        if self.parent():
            pw = self.parent().width()
            ph = self.parent().height()
            x  = _MARGIN
            y  = ph - self.height() - _MARGIN
            self.move(x, y)