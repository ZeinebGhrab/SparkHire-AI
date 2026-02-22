"""
Interview Widget — Premium Redesign
Dark glassmorphism with animated status indicators and refined typography.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QProgressBar, QFrame, QGraphicsDropShadowEffect,
    QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QSize, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtGui import QFont, QColor, QLinearGradient, QPainter, QPen, QBrush
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from client.ui.stark_theme import StarkTheme
from client.ui.icons import StarkIcons


# ── Localised strings ────────────────────────────────────────────────────────

WIDGET_TEXTS = {
    "ar": {
        "vocal_mode":    "وضع صوتي",
        "progress":      "السؤال {current} من {total}",
        "listen_title":  "استمع جيداً",
        "listen_sub":    "ستُطرح الأسئلة صوتياً فقط.\nاستمع للمحاور ثم أجب بوضوح.",
        "waiting":       "في انتظار السؤال…",
        "playing":       "السؤال قيد التشغيل",
        "ready":         "جاهز للإجابة",
        "start_answer":  "ابدأ الإجابة",
        "stop_answer":   "إيقاف التسجيل",
        "end_interview": "إنهاء المقابلة",
    },
    "fr": {
        "vocal_mode":    "Mode Vocal",
        "progress":      "Question {current} / {total}",
        "listen_title":  "Écoutez attentivement",
        "listen_sub":    "Les questions sont posées uniquement en audio.\nÉcoutez l'avatar, puis répondez clairement.",
        "waiting":       "En attente de la question…",
        "playing":       "Lecture en cours",
        "ready":         "Prêt à répondre",
        "start_answer":  "Commencer à répondre",
        "stop_answer":   "Arrêter l'enregistrement",
        "end_interview": "Terminer l'entretien",
    },
    "en": {
        "vocal_mode":    "Vocal Mode",
        "progress":      "Question {current} of {total}",
        "listen_title":  "Listen carefully",
        "listen_sub":    "Questions are audio-only.\nListen to the avatar, then answer clearly.",
        "waiting":       "Waiting for question…",
        "playing":       "Playing question",
        "ready":         "Ready to answer",
        "start_answer":  "Start answering",
        "stop_answer":   "Stop recording",
        "end_interview": "End interview",
    },
}

# ── Pulsing dot widget ─────────────────────────────────────────────────────

class _PulseDot(QWidget):
    """Animated colored dot."""

    def __init__(self, color: str = "#10B981", parent=None):
        super().__init__(parent)
        self._color = QColor(color)
        self._alpha = 255
        self.setFixedSize(10, 10)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._dir = -4
        self._timer.start(40)

    def set_color(self, color: str):
        self._color = QColor(color)
        self.update()

    def _tick(self):
        self._alpha += self._dir
        if self._alpha <= 80:
            self._dir = 4
        elif self._alpha >= 255:
            self._dir = -4
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = QColor(self._color)
        c.setAlpha(self._alpha)
        p.setBrush(QBrush(c))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(0, 0, 10, 10)


# ── Thin separator ─────────────────────────────────────────────────────────

class _Divider(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(1)
        self.setStyleSheet(f"background: {StarkTheme.BG_BORDER};")


# ── Main widget ───────────────────────────────────────────────────────────

class InterviewWidget(QWidget):
    start_recording = Signal()
    stop_recording  = Signal()
    end_interview   = Signal()

    def __init__(self, language: str = "fr", parent=None):
        super().__init__(parent)
        self._language   = language
        self.is_recording = False
        self.setMinimumWidth(360)
        self.setMaximumWidth(460)

        self.setStyleSheet(f"QWidget {{ background: transparent; }}")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        # ── Badge header ──────────────────────────────────────────────────
        self._badge = self._make_badge()
        root.addWidget(self._badge)

        # ── Progress card ────────────────────────────────────────────────
        prog_card = self._make_progress_card()
        root.addWidget(prog_card)

        # ── Status card ───────────────────────────────────────────────────
        status_card = self._make_status_card()
        root.addWidget(status_card)

        root.addStretch(1)

        # ── Record button ─────────────────────────────────────────────────
        self.record_btn = self._make_record_btn()
        root.addWidget(self.record_btn)

        # ── End button ────────────────────────────────────────────────────
        self.end_btn = self._make_end_btn()
        root.addWidget(self.end_btn)

        self._apply_language()

    # ── Translations ─────────────────────────────────────────────────────

    def t(self, key: str) -> str:
        return WIDGET_TEXTS.get(self._language, WIDGET_TEXTS["fr"]).get(key, key)

    def set_language(self, language: str):
        self._language = language
        self._apply_language()

    def _apply_language(self):
        self._badge_label.setText(self.t("vocal_mode").upper())
        self._listen_title.setText(self.t("listen_title"))
        self._listen_sub.setText(self.t("listen_sub"))
        self._set_status("waiting")
        self.record_btn.setText(
            self.t("stop_answer") if self.is_recording else self.t("start_answer")
        )
        self.end_btn.setText(self.t("end_interview"))
        dir_ = (Qt.LayoutDirection.RightToLeft if self._language == "ar"
                else Qt.LayoutDirection.LeftToRight)
        self.setLayoutDirection(dir_)

    # ── Build badge ───────────────────────────────────────────────────────

    def _make_badge(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet("QWidget { background: transparent; }")
        h = QHBoxLayout(w)
        h.setContentsMargins(4, 0, 4, 0)
        h.setSpacing(8)

        self._dot = _PulseDot(StarkTheme.BLUE_ELECTRIC)
        h.addWidget(self._dot)

        self._badge_label = QLabel()
        self._badge_label.setFont(QFont(StarkTheme.FONT_BODY, 9, QFont.Weight.Bold))
        self._badge_label.setStyleSheet(f"color: {StarkTheme.BLUE_SOFT}; letter-spacing: 2px;")
        h.addWidget(self._badge_label)
        h.addStretch()
        return w

    # ── Build progress card ───────────────────────────────────────────────

    def _make_progress_card(self) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {StarkTheme.GLASS_BG};
                border: 1px solid {StarkTheme.GLASS_BORDER};
                border-radius: {StarkTheme.R_LG};
            }}
        """)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(18, 14, 18, 14)
        lay.setSpacing(10)

        row = QHBoxLayout()
        row.setSpacing(0)

        self.progress_label = QLabel("—  /  —")
        self.progress_label.setFont(QFont(StarkTheme.FONT_BODY, 12, QFont.Weight.Bold))
        self.progress_label.setStyleSheet(f"color: {StarkTheme.TEXT_PRIMARY};")
        row.addWidget(self.progress_label)
        row.addStretch()

        self._pct_label = QLabel("0%")
        self._pct_label.setFont(QFont(StarkTheme.FONT_BODY, 11, QFont.Weight.DemiBold))
        self._pct_label.setStyleSheet(f"color: {StarkTheme.BLUE_ELECTRIC};")
        row.addWidget(self._pct_label)

        lay.addLayout(row)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setStyleSheet(StarkTheme.progress_style())
        lay.addWidget(self.progress_bar)

        return card

    # ── Build status card ─────────────────────────────────────────────────

    def _make_status_card(self) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {StarkTheme.GRADIENT_CARD};
                border: 1px solid {StarkTheme.BG_BORDER};
                border-radius: {StarkTheme.R_XL};
            }}
        """)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(24, 22, 24, 22)
        lay.setSpacing(14)

        # Title
        self._listen_title = QLabel()
        self._listen_title.setFont(QFont(StarkTheme.FONT_BODY, 15, QFont.Weight.Bold))
        self._listen_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._listen_title.setStyleSheet(f"color: {StarkTheme.TEXT_PRIMARY};")
        lay.addWidget(self._listen_title)

        lay.addWidget(_Divider())

        # Sub-text
        self._listen_sub = QLabel()
        self._listen_sub.setFont(QFont(StarkTheme.FONT_BODY, 11))
        self._listen_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._listen_sub.setWordWrap(True)
        self._listen_sub.setStyleSheet(
            f"color: {StarkTheme.TEXT_SECONDARY}; line-height: 1.6;"
        )
        lay.addWidget(self._listen_sub)

        # Status pill
        pill_wrap = QHBoxLayout()
        pill_wrap.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._status_pill = QFrame()
        self._status_pill.setFixedHeight(34)
        pill_inner = QHBoxLayout(self._status_pill)
        pill_inner.setContentsMargins(14, 0, 14, 0)
        pill_inner.setSpacing(8)

        self._status_dot = _PulseDot(StarkTheme.BLUE_ELECTRIC)
        pill_inner.addWidget(self._status_dot)

        self._status_text = QLabel()
        self._status_text.setFont(QFont(StarkTheme.FONT_BODY, 11, QFont.Weight.DemiBold))
        pill_inner.addWidget(self._status_text)

        pill_wrap.addWidget(self._status_pill)
        lay.addLayout(pill_wrap)
        return card

    # ── Build record button ───────────────────────────────────────────────

    def _make_record_btn(self) -> QPushButton:
        btn = QPushButton()
        btn.setFont(QFont(StarkTheme.FONT_BODY, 13, QFont.Weight.Bold))
        btn.setMinimumHeight(52)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(StarkTheme.get_button_style("primary"))
        btn.clicked.connect(self._on_record_click)
        return btn

    # ── Build end button ──────────────────────────────────────────────────

    def _make_end_btn(self) -> QPushButton:
        btn = QPushButton()
        btn.setFont(QFont(StarkTheme.FONT_BODY, 11, QFont.Weight.DemiBold))
        btn.setMinimumHeight(42)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(StarkTheme.get_button_style("danger"))
        btn.clicked.connect(self.end_interview.emit)
        return btn

    # ── Internal ──────────────────────────────────────────────────────────

    def _on_record_click(self):
        if not self.is_recording:
            self.start_recording.emit()
            self.is_recording = True
            self._update_record_btn(True)
        else:
            self.stop_recording.emit()
            self.is_recording = False
            self._update_record_btn(False)

    def _update_record_btn(self, recording: bool):
        if recording:
            self.record_btn.setText(self.t("stop_answer"))
            self.record_btn.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(239, 68, 68, 0.15);
                    color: {StarkTheme.ERROR};
                    border: 1px solid rgba(239, 68, 68, 0.4);
                    border-radius: {StarkTheme.R_MD};
                    padding: 14px 24px;
                    font-size: {StarkTheme.FS_MD};
                    font-weight: 700;
                    letter-spacing: 1px;
                }}
                QPushButton:hover {{
                    background: {StarkTheme.ERROR};
                    color: white;
                    border: 1px solid {StarkTheme.ERROR};
                }}
                QPushButton:pressed {{ padding-top: 15px; padding-bottom: 13px; }}
            """)
            self._dot.set_color(StarkTheme.ERROR)
            self._set_status("recording")
        else:
            self.record_btn.setText(self.t("start_answer"))
            self.record_btn.setStyleSheet(StarkTheme.get_button_style("primary"))
            self._dot.set_color(StarkTheme.BLUE_ELECTRIC)

    def _set_status(self, state: str):
        cfg = {
            "waiting":   (StarkTheme.TEXT_MUTED,       StarkTheme.BG_SURFACE,
                          StarkTheme.BG_BORDER,         StarkTheme.TEXT_MUTED),
            "playing":   (StarkTheme.AMBER,             "rgba(245,158,11,0.10)",
                          "rgba(245,158,11,0.30)",       StarkTheme.AMBER),
            "ready":     (StarkTheme.SUCCESS,           StarkTheme.SUCCESS_GLOW,
                          "rgba(16,185,129,0.30)",       StarkTheme.SUCCESS),
            "recording": (StarkTheme.ERROR,             StarkTheme.ERROR_GLOW,
                          "rgba(239,68,68,0.30)",        StarkTheme.ERROR),
        }
        dot_c, bg, border, text_c = cfg.get(state, cfg["waiting"])

        self._status_dot.set_color(dot_c)
        self._status_pill.setStyleSheet(f"""
            QFrame {{
                background: {bg};
                border: 1px solid {border};
                border-radius: {StarkTheme.R_FULL};
            }}
        """)
        self._status_text.setStyleSheet(
            f"color: {text_c}; font-weight: 600; background: transparent;"
        )

        text_map = {
            "waiting":   self.t("waiting"),
            "playing":   self.t("playing"),
            "ready":     self.t("ready"),
            "recording": self.t("stop_answer"),
        }
        self._status_text.setText(text_map.get(state, ""))

    # ── Public API ────────────────────────────────────────────────────────

    def update_question(self, progress: dict):
        current = progress.get("current", 0)
        total   = progress.get("total", 0)
        pct     = progress.get("percentage", 0)
        self.progress_label.setText(
            self.t("progress").format(current=current, total=total)
        )
        self._pct_label.setText(f"{pct}%")
        self.progress_bar.setValue(pct)
        self._set_status("playing")

    def set_audio_playing(self):
        self._set_status("playing")

    def set_ready_to_answer(self):
        self._set_status("ready")

    def enable_recording(self, enabled: bool):
        self.record_btn.setEnabled(enabled)
        if enabled:
            self.set_ready_to_answer()