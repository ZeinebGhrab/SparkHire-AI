"""
Video Player Widget — Professional Light UI
Zone vidéo sobre · barre de statut card blanche propre · indicateurs colorés
"""

import cv2
import pygame
import numpy as np
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QHBoxLayout,
    QGraphicsDropShadowEffect,
)
from PySide6.QtCore import Qt, QTimer, Slot, QSize
from PySide6.QtGui import QFont, QImage, QPixmap, QColor, QPainter, QBrush
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from client.ui.stark_theme import T
from client.ui.icons import StarkIcons


def _sh(blur=20, dy=5, alpha=25, r=100, g=116, b=139):
    s = QGraphicsDropShadowEffect()
    s.setBlurRadius(blur); s.setOffset(0, dy)
    s.setColor(QColor(r, g, b, alpha)); return s


class _Dot(QWidget):
    """Petit point animé."""
    def __init__(self, color: str, parent=None):
        super().__init__(parent)
        self._c = QColor(color); self._a = 255; self._d = -5
        self.setFixedSize(10, 10)
        t = QTimer(self); t.timeout.connect(self._tick); t.start(50)

    def set_color(self, c: str): self._c = QColor(c); self.update()

    def _tick(self):
        self._a += self._d
        if self._a <= 60: self._d = 5
        elif self._a >= 255: self._d = -5
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = QColor(self._c); c.setAlpha(self._a)
        p.setBrush(QBrush(c)); p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(0, 0, 10, 10)


class VideoPlayerWidget(QWidget):
    """Lecteur avatar + barre de statut card blanche propre."""

    def __init__(self, parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Wrapper carte ─────────────────────────────────────────────────────
        wrapper = QFrame()
        wrapper.setObjectName("videoWrapper")
        wrapper.setStyleSheet(f"""
            #videoWrapper {{
                background: {T.BG_CARD};
                border: 1px solid {T.BORDER};
                border-radius: {T.R_XL}px;
            }}
        """)
        wrapper.setGraphicsEffect(_sh(32, 8, 35))
        wrap_lay = QVBoxLayout(wrapper)
        wrap_lay.setContentsMargins(0, 0, 0, 0)
        wrap_lay.setSpacing(0)

        # ── Zone vidéo ───────────────────────────────────────────────────────
        self.avatar_display = QLabel()
        self.avatar_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar_display.setStyleSheet(f"""
            QLabel {{
                background: qlineargradient(x1:0.5,y1:0,x2:0.5,y2:1,
                    stop:0 {T.BLUE_50},stop:0.4 #FFFFFF,stop:1 {T.CYAN_50});
                border: none;
                border-top-left-radius:  {T.R_XL}px;
                border-top-right-radius: {T.R_XL}px;
            }}
        """)
        self.avatar_display.setMinimumSize(800, 540)
        wrap_lay.addWidget(self.avatar_display, stretch=1)

        # ── Barre de statut ───────────────────────────────────────────────────
        bar = QFrame()
        bar.setObjectName("statusBar")
        bar.setFixedHeight(62)
        bar.setStyleSheet(f"""
            #statusBar {{
                background: {T.BG_CARD};
                border-top: 1px solid {T.BORDER};
                border-bottom-left-radius:  {T.R_XL}px;
                border-bottom-right-radius: {T.R_XL}px;
            }}
        """)

        bar_lay = QHBoxLayout(bar)
        bar_lay.setContentsMargins(T.SP_5, 0, T.SP_5, 0)
        bar_lay.setSpacing(T.SP_3)

        # Icône badge
        self._ic_cont = QFrame()
        self._ic_cont.setFixedSize(40, 40)
        self._ic_cont.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 {T.CYAN_50},stop:1 {T.BLUE_50});
                border: 1px solid {T.CYAN_200};
                border-radius: 10px;
            }}
        """)
        ic_inner = QVBoxLayout(self._ic_cont)
        ic_inner.setContentsMargins(0, 0, 0, 0)
        ic_inner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._ic_lbl = QLabel()
        self._ic_lbl.setPixmap(
            StarkIcons.user_check(T.GREEN_600).pixmap(QSize(22, 22))
        )
        ic_inner.addWidget(self._ic_lbl)
        bar_lay.addWidget(self._ic_cont)

        # Texte
        text_col = QVBoxLayout()
        text_col.setSpacing(1)
        self._status_main = QLabel("Agent RH : Prêt à vous écouter")
        self._status_main.setFont(QFont(T.FONT, T.FS_BASE, QFont.Weight.Bold))
        self._status_main.setStyleSheet(f"color: {T.TEXT_800}; background: transparent;")

        self._status_sub = QLabel("Intelligence Vocal Intelligence")
        self._status_sub.setFont(QFont(T.FONT, T.FS_XS))
        self._status_sub.setStyleSheet(f"color: {T.TEXT_400}; letter-spacing: 0.5px; background: transparent;")

        text_col.addWidget(self._status_main)
        text_col.addWidget(self._status_sub)
        bar_lay.addLayout(text_col, stretch=1)

        # Indicateur animé
        self._dot = _Dot(T.GREEN_500)
        bar_lay.addWidget(self._dot)

        # Badge état
        self._state_badge = QLabel("En attente")
        self._state_badge.setFont(QFont(T.FONT, T.FS_XS, QFont.Weight.Bold))
        self._state_badge.setStyleSheet(f"""
            color: {T.GREEN_700};
            background: {T.GREEN_50};
            border: 1px solid {T.GREEN_100};
            border-radius: {T.R_FULL}px;
            padding: 3px 10px;
        """)
        bar_lay.addWidget(self._state_badge)

        wrap_lay.addWidget(bar)
        root.addWidget(wrapper)

        # ── Init ──────────────────────────────────────────────────────────────
        pygame.init()
        self.base_path  = Path(__file__).resolve().parent.parent.parent
        self.video_dir  = self.base_path / "assets" / "videos"
        self.video_paths = {
            "idle":      str(self.video_dir / "rh_idle.mp4"),
            "speaking":  str(self.video_dir / "rh_speaking.mp4"),
            "listening": str(self.video_dir / "rh_listening.mp4"),
        }
        self.cap           = None
        self.timer         = QTimer()
        self.timer.timeout.connect(self._update_frame)
        self.current_state = "idle"
        self.set_idle()

    # ── Video ─────────────────────────────────────────────────────────────────

    def _load_video(self, state: str):
        if self.cap: self.cap.release()
        p = self.video_paths.get(state, "")
        if not Path(p).exists():
            self._show_placeholder(state); return
        self.cap = cv2.VideoCapture(p)
        self.current_state = state
        if not self.timer.isActive(): self.timer.start(33)

    def _show_placeholder(self, state: str):
        w, h = 800, 540
        img = np.full((h, w, 3), 248, dtype=np.uint8)  # #F8FAFC
        # Dégradé vertical léger
        for y in range(h):
            t_ = y / h
            img[y, :, 0] = int(239 + t_ * 16)   # R
            img[y, :, 1] = int(246 + t_ * 9)    # G
            img[y, :, 2] = 255                   # B

        txt = f"[{state.upper()}]"
        cv2.putText(img, txt, (w // 2 - 60, h // 2), cv2.FONT_HERSHEY_SIMPLEX,
                    1.2, (71, 85, 105), 2, cv2.LINE_AA)

        qt = QImage(img.data, w, h, 3 * w, QImage.Format_RGB888)
        self.avatar_display.setPixmap(
            QPixmap.fromImage(qt).scaled(
                self.avatar_display.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    @Slot()
    def _update_frame(self):
        if not self.cap or not self.cap.isOpened(): return
        ret, frame = self.cap.read()
        if not ret: self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0); return
        try:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pg = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
            buf = np.ascontiguousarray(pygame.surfarray.array3d(pg).swapaxes(0, 1))
            h, w, ch = buf.shape
            qt = QImage(buf.data, w, h, ch * w, QImage.Format_RGB888)
            self.avatar_display.setPixmap(
                QPixmap.fromImage(qt).scaled(
                    self.avatar_display.size(),
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        except Exception as e: print(f"[video] {e}")

    # ── Helpers d'état ────────────────────────────────────────────────────────

    def _apply_state(
        self,
        icon_pix,
        main_text: str,
        main_color: str,
        badge_text: str,
        badge_color: str,
        badge_bg: str,
        badge_border: str,
        dot_color: str,
        ic_bg0: str,
        ic_bg1: str,
        ic_border: str,
    ):
        self._ic_lbl.setPixmap(icon_pix)
        self._ic_cont.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 {ic_bg0},stop:1 {ic_bg1});
                border: 1px solid {ic_border};
                border-radius: 10px;
            }}
        """)
        self._status_main.setText(main_text)
        self._status_main.setStyleSheet(
            f"color: {main_color}; font-weight: 700; background: transparent;"
        )
        self._state_badge.setText(badge_text)
        self._state_badge.setStyleSheet(f"""
            color: {badge_color};
            background: {badge_bg};
            border: 1px solid {badge_border};
            border-radius: {T.R_FULL}px;
            padding: 3px 10px;
        """)
        self._dot.set_color(dot_color)

    # ── Public ────────────────────────────────────────────────────────────────

    def set_idle(self):
        self._apply_state(
            StarkIcons.user_check(T.GREEN_600).pixmap(QSize(22, 22)),
            "Agent RH : Prêt à vous écouter", T.TEXT_800,
            "Disponible", T.GREEN_700, T.GREEN_50, T.GREEN_100,
            T.GREEN_500,
            T.GREEN_50, "#DCFCE7", T.GREEN_100,
        )
        self._load_video("idle")

    def set_speaking(self):
        self._apply_state(
            StarkIcons.message_circle(T.CYAN_600).pixmap(QSize(22, 22)),
            "Agent RH : Analyse de votre profil…", T.CYAN_700,
            "En cours", T.CYAN_700, T.CYAN_50, T.CYAN_200,
            T.CYAN_500,
            T.CYAN_50, T.BLUE_50, T.CYAN_200,
        )
        self._load_video("speaking")

    def set_listening(self):
        self._apply_state(
            StarkIcons.headphones(T.AMBER_500).pixmap(QSize(22, 22)),
            "Agent RH : Écoute attentive en cours…", T.TEXT_800,
            "Écoute…", T.AMBER_500, T.AMBER_50, T.AMBER_100,
            T.AMBER_500,
            T.AMBER_50, "#FEF3C7", T.AMBER_100,
        )
        self._load_video("listening")

    def resizeEvent(self, e): super().resizeEvent(e)

    def closeEvent(self, e):
        self.timer.stop()
        if self.cap: self.cap.release()
        pygame.quit()
        super().closeEvent(e)