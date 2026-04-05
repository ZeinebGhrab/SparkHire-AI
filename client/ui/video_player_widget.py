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


def _sh(blur=24, dy=6, alpha=16, r=0, g=0, b=0):
    """Soft neutral shadow — clean, no color cast."""
    s = QGraphicsDropShadowEffect()
    s.setBlurRadius(blur); s.setOffset(0, dy)
    s.setColor(QColor(r, g, b, alpha)); return s


class _PulseDot(QWidget):
    def __init__(self, color: str, parent=None):
        super().__init__(parent)
        self._c = QColor(color); self._a = 255; self._d = -5
        self.setFixedSize(8, 8)
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
        p.drawEllipse(1, 1, 6, 6)


class VideoPlayerWidget(QWidget):
    """Clean embedded video card with modern status bar."""

    def __init__(self, parent=None):
        super().__init__(parent)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Outer card wrapper — embedded, clean ──────────────────
        wrapper = QFrame()
        wrapper.setObjectName("videoWrapper")
        wrapper.setStyleSheet(f"""
            #videoWrapper {{
                background: {T.BG_CARD};
                border: none;
                border-radius: 24px;
            }}
        """)
        # Soft shadow — feels embedded, not floating
        wrapper.setGraphicsEffect(_sh(40, 10, 14))

        wrap_lay = QVBoxLayout(wrapper)
        wrap_lay.setContentsMargins(0, 0, 0, 0)
        wrap_lay.setSpacing(0)

        # ── Top bar — clean dark gradient ─────────────────────────
        top_bar = QFrame()
        top_bar.setFixedHeight(54)
        top_bar.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 {T.TEAL_900},stop:0.5 {T.TEAL_800},stop:1 #0B6B62);
                border-top-left-radius:  23px;
                border-top-right-radius: 23px;
            }}
        """)
        top_lay = QHBoxLayout(top_bar)
        top_lay.setContentsMargins(20, 0, 20, 0)
        top_lay.setSpacing(10)

        # Agent avatar — subtle glass button
        avatar_dot = QFrame()
        avatar_dot.setFixedSize(34, 34)
        avatar_dot.setStyleSheet(f"""
            QFrame {{
                background: rgba(255,255,255,0.18);
                border: none;
                border-radius: 10px;
            }}
        """)
        av_lay = QVBoxLayout(avatar_dot)
        av_lay.setContentsMargins(0, 0, 0, 0)
        av_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        av_e = QLabel("🤖")
        av_e.setFont(QFont("Segoe UI Emoji", 13))
        av_e.setAlignment(Qt.AlignmentFlag.AlignCenter)
        av_lay.addWidget(av_e)
        top_lay.addWidget(avatar_dot)
        top_lay.addSpacing(6)

        name_col = QVBoxLayout()
        name_col.setSpacing(1)
        agent_name = QLabel("SparkHire Agent RH")
        f_an = QFont(T.FONT, 11); f_an.setBold(True)
        agent_name.setFont(f_an)
        agent_name.setStyleSheet("color: rgba(255,255,255,0.96); background: transparent; letter-spacing: 0.1px;")
        name_col.addWidget(agent_name)

        self._agent_status = QLabel("En attente…")
        self._agent_status.setFont(QFont(T.FONT, 9))
        self._agent_status.setStyleSheet("color: rgba(255,255,255,0.65); background: transparent; letter-spacing: 0.3px;")
        name_col.addWidget(self._agent_status)
        top_lay.addLayout(name_col)
        top_lay.addStretch()

        # LIVE badge — refined pill
        self._live_badge = QFrame()
        self._live_badge.setFixedHeight(24)
        lb_lay = QHBoxLayout(self._live_badge)
        lb_lay.setContentsMargins(8, 0, 10, 0)
        lb_lay.setSpacing(5)
        self._live_dot = _PulseDot("rgba(255,255,255,0.8)")
        lb_lay.addWidget(self._live_dot)
        live_txt = QLabel("LIVE")
        live_txt.setFont(QFont(T.FONT, 7, QFont.Weight.Bold))
        live_txt.setStyleSheet("color: rgba(255,255,255,0.85); background: transparent; letter-spacing: 1px;")
        lb_lay.addWidget(live_txt)
        self._live_badge.setStyleSheet(f"""
            QFrame {{
                background: rgba(255,255,255,0.15);
                border: none;
                border-radius: {T.R_FULL}px;
            }}
        """)
        top_lay.addWidget(self._live_badge)

        wrap_lay.addWidget(top_bar)

        # ── Video area — clean gradient placeholder ────────────────
        self.avatar_display = QLabel()
        self.avatar_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Very subtle gradient background — soft, not harsh
        self.avatar_display.setStyleSheet(f"""
            QLabel {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #E8F9F5,
                    stop:0.5 #F5F4EF,
                    stop:1 #EAF6F2);
                border: none;
            }}
        """)
        self.avatar_display.setMinimumSize(800, 500)
        wrap_lay.addWidget(self.avatar_display, stretch=1)

        # ── Bottom status bar — clean white bar ───────────────────
        bar = QFrame()
        bar.setObjectName("statusBar")
        bar.setFixedHeight(60)
        bar.setStyleSheet(f"""
            #statusBar {{
                background: #FEFEFE;
                border-top: 1px solid {T.BG_PAGE};
                border-bottom-left-radius:  23px;
                border-bottom-right-radius: 23px;
            }}
        """)

        bar_lay = QHBoxLayout(bar)
        bar_lay.setContentsMargins(20, 0, 20, 0)
        bar_lay.setSpacing(12)

        # State icon — soft colored container
        self._ic_cont = QFrame()
        self._ic_cont.setFixedSize(40, 40)
        self._ic_cont.setStyleSheet(f"""
            QFrame {{
                background: {T.GREEN_50};
                border: none;
                border-radius: 12px;
            }}
        """)
        ic_inner = QVBoxLayout(self._ic_cont)
        ic_inner.setContentsMargins(0, 0, 0, 0)
        ic_inner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._ic_lbl = QLabel()
        self._ic_lbl.setPixmap(
            StarkIcons.user_check(T.GREEN_600).pixmap(QSize(20, 20))
        )
        ic_inner.addWidget(self._ic_lbl)
        bar_lay.addWidget(self._ic_cont)

        text_col = QVBoxLayout()
        text_col.setSpacing(1)

        self._status_main = QLabel("Agent RH : Prêt à vous écouter")
        f_sm = QFont(T.FONT, T.FS_BASE); f_sm.setBold(True)
        self._status_main.setFont(f_sm)
        self._status_main.setStyleSheet(f"color: {T.TEXT_900}; background: transparent; letter-spacing: -0.1px;")

        self._status_sub = QLabel("Intelligence Artificielle · SparkHire")
        self._status_sub.setFont(QFont(T.FONT_BODY, T.FS_XS))
        self._status_sub.setStyleSheet(
            f"color: {T.TEXT_400}; letter-spacing: 0.5px; background: transparent;"
        )

        text_col.addWidget(self._status_main)
        text_col.addWidget(self._status_sub)
        bar_lay.addLayout(text_col, stretch=1)

        self._dot = _PulseDot(T.GREEN_500)
        bar_lay.addWidget(self._dot)

        # State badge — minimal pill
        self._state_badge = QLabel("Disponible")
        f_badge = QFont(T.FONT, T.FS_XS); f_badge.setBold(True)
        self._state_badge.setFont(f_badge)
        self._state_badge.setStyleSheet(f"""
            color: {T.GREEN_700};
            background: {T.GREEN_50};
            border: none;
            border-radius: {T.R_FULL}px;
            padding: 3px 12px;
        """)
        bar_lay.addWidget(self._state_badge)

        wrap_lay.addWidget(bar)
        root.addWidget(wrapper)

        # ── pygame init ───────────────────────────────────────────
        if not pygame.get_init():
            pygame.display.init()

        self.base_path   = Path(__file__).resolve().parent.parent.parent
        self.video_dir   = self.base_path / "assets" / "videos"
        self.video_paths = {
            "idle":      str(self.video_dir / "rh_idle.mp4"),
            "speaking":  str(self.video_dir / "rh_speaking.mp4"),
            "listening": str(self.video_dir / "rh_listening.mp4"),
        }
        self.cap           = None
        self.timer         = QTimer()
        self.timer.timeout.connect(self._update_frame)
        self.current_state = "idle"

        # ── PiP camera overlay — parent = zone vidéo pure ────────
        from client.ui.camera_preview_widget import CameraPreviewWidget
        self._camera_preview = CameraPreviewWidget(parent=self.avatar_display)
        self._camera_preview.hide()

        self.set_idle()

    @property
    def camera_preview(self):
        return self._camera_preview

    # ── Video playback ────────────────────────────────────────────

    def _load_video(self, state: str):
        if self.cap: self.cap.release()
        p = self.video_paths.get(state, "")
        if not Path(p).exists():
            self._show_placeholder(state); return
        self.cap = cv2.VideoCapture(p)
        self.current_state = state
        if not self.timer.isActive(): self.timer.start(33)

    def _show_placeholder(self, state: str):
        w, h = 800, 500
        img = np.zeros((h, w, 3), dtype=np.uint8)
        for y in range(h):
            t_ = y / h
            img[y, :, 0] = int(240 + t_ * 10)
            img[y, :, 1] = int(244 + t_ * 8)
            img[y, :, 2] = 255
        txt = f"[{state.upper()}]"
        cv2.putText(img, txt, (w // 2 - 80, h // 2 + 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (79, 70, 229), 2, cv2.LINE_AA)
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
            pg    = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
            buf   = np.ascontiguousarray(pygame.surfarray.array3d(pg).swapaxes(0, 1))
            h, w, ch = buf.shape
            qt = QImage(buf.data, w, h, ch * w, QImage.Format_RGB888)
            self.avatar_display.setPixmap(
                QPixmap.fromImage(qt).scaled(
                    self.avatar_display.size(),
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        except Exception:
            pass

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if hasattr(self, "_camera_preview") and hasattr(self, "avatar_display"):
            self.avatar_display.resizeEvent(e)
            self._camera_preview.reposition()

    # ── State helpers ─────────────────────────────────────────────

    def _apply_bar_state(
        self, icon_pix, main_text, main_color,
        badge_text, badge_color, badge_bg, badge_border,
        dot_color, ic_bg, ic_border, agent_status,
    ):
        self._ic_lbl.setPixmap(icon_pix)
        self._ic_cont.setStyleSheet(f"""
            QFrame {{
                background: {ic_bg};
                border: none;
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
            border: none;
            border-radius: {T.R_FULL}px;
            padding: 3px 12px;
        """)
        self._dot.set_color(dot_color)
        self._agent_status.setText(agent_status)

    # ── Public API ────────────────────────────────────────────────

    def set_idle(self):
        self._apply_bar_state(
            StarkIcons.user_check(T.GREEN_600).pixmap(QSize(20, 20)),
            "Agent RH : Prêt à vous écouter", T.TEXT_900,
            "Disponible", T.GREEN_700, T.GREEN_100, T.GREEN_200,
            T.GREEN_500, T.GREEN_100, T.GREEN_200,
            "En attente de votre réponse",
        )
        self._load_video("idle")

    def set_speaking(self):
        self._apply_bar_state(
            StarkIcons.message_circle(T.TEAL_600).pixmap(QSize(20, 20)),
            "Agent RH : Analyse en cours…", T.TEAL_900,
            "En cours", T.TEAL_700, T.TEAL_100, T.TEAL_200,
            T.TEAL_500, T.TEAL_100, T.TEAL_200,
            "Traitement de votre profil",
        )
        self._load_video("speaking")

    def set_listening(self):
        self._apply_bar_state(
            StarkIcons.headphones(T.AMBER_600).pixmap(QSize(20, 20)),
            "Agent RH : Écoute active…", T.TEXT_900,
            "Enregistrement", T.AMBER_700, T.AMBER_100, T.AMBER_200,
            T.AMBER_500, T.AMBER_100, T.AMBER_200,
            "Enregistrement de votre réponse",
        )
        self._load_video("listening")

    def closeEvent(self, e):
        self.timer.stop()
        if self.cap: self.cap.release()
        super().closeEvent(e)