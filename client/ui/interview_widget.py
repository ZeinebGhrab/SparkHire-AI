"""
Interview Widget — SparkHire AI v6  ·  Clean SaaS Edition
Stripe / Linear aesthetic — white cards, soft shadows, strong hierarchy.
Functionality identical to v5.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QProgressBar, QFrame, QGraphicsDropShadowEffect,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QColor, QPainter, QBrush, QPen, QLinearGradient
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from client.ui.stark_theme import StarkTheme, T

# ── i18n ─────────────────────────────────────────────────────────────────────

TEXTS = {
    "ar": {
        "section":        "المقابلة الصوتية",
        "progress":       "السؤال {c} من {t}",
        "listen_title":   "استمع جيداً",
        "listen_sub":     "ستُطرح الأسئلة صوتياً فقط.\nاستمع للمحاور ثم أجب بوضوح.",
        "max_duration":   "مدة الإجابة القصوى : {m} دق {s} ث",
        "waiting":        "في انتظار السؤال…",
        "playing":        "السؤال قيد التشغيل",
        "ready":          "جاهز للإجابة",
        "start":          "ابدأ الإجابة",
        "stop":           "إيقاف التسجيل",
        "end":            "إنهاء المقابلة",
        "recording_left": "{s} ث متبقية",
        "time_up":        "انتهى الوقت — توقف التسجيل",
    },
    "fr": {
        "section":        "ENTRETIEN VOCAL",
        "progress":       "Question {c} / {t}",
        "listen_title":   "Écoutez attentivement",
        "listen_sub":     "Les questions sont posées uniquement en audio.\nÉcoutez l'avatar, puis répondez clairement.",
        "max_duration":   "Durée max : {m} min {s:02d} s",
        "waiting":        "En attente de la question…",
        "playing":        "Lecture en cours",
        "ready":          "Prêt à répondre",
        "start":          "Commencer à répondre",
        "stop":           "Arrêter l'enregistrement",
        "end":            "Terminer l'entretien",
        "recording_left": "{s} s restantes",
        "time_up":        "Temps écoulé — enregistrement arrêté",
    },
    "en": {
        "section":        "VOICE INTERVIEW",
        "progress":       "Question {c} of {t}",
        "listen_title":   "Listen carefully",
        "listen_sub":     "Questions are audio-only.\nListen to the avatar, then answer clearly.",
        "max_duration":   "Max response time: {m} min {s:02d} s",
        "waiting":        "Waiting for question…",
        "playing":        "Playing question",
        "ready":          "Ready to answer",
        "start":          "Start answering",
        "stop":           "Stop recording",
        "end":            "End interview",
        "recording_left": "{s} s left",
        "time_up":        "Time's up — recording stopped",
    },
}

DEFAULT_MAX_RECORDING_SECONDS = 90


# ── Utility Widgets ──────────────────────────────────────────────────────────

class PulseDot(QWidget):
    """Animated pulsing dot for status indicators."""

    def __init__(self, color: str = T.INDIGO_500, size: int = 8, parent=None):
        super().__init__(parent)
        self._color = QColor(color)
        self._alpha = 255
        self._delta = -6
        self._size  = size
        self.setFixedSize(size, size)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(40)

    def set_color(self, color: str):
        self._color = QColor(color)
        self.update()

    def _tick(self):
        self._alpha = max(55, min(255, self._alpha + self._delta))
        if self._alpha <= 55:   self._delta = 6
        elif self._alpha >= 255: self._delta = -6
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        glow = QColor(self._color)
        glow.setAlpha(max(0, self._alpha // 5))
        p.setBrush(QBrush(glow)); p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(0, 0, self._size, self._size)
        core = QColor(self._color)
        core.setAlpha(self._alpha)
        p.setBrush(QBrush(core))
        m = self._size // 4
        p.drawEllipse(m, m, self._size - 2 * m, self._size - 2 * m)


class StepBadge(QLabel):
    """Numbered step indicator."""

    def __init__(self, num: int, parent=None):
        super().__init__(str(num), parent)
        self.setFixedSize(24, 24)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        f = QFont(T.FONT, T.FS_SM); f.setBold(True)
        self.setFont(f)
        self._set_active(False)

    def _set_active(self, active: bool):
        if active:
            self.setStyleSheet(f"""
                QLabel {{
                    background: {T.INDIGO_500};
                    color: {T.TEXT_WHITE};
                    border-radius: 12px;
                    font-weight: 700;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QLabel {{
                    background: {T.INDIGO_100};
                    color: {T.INDIGO_500};
                    border-radius: 12px;
                    font-weight: 700;
                }}
            """)


def _shadow(blur=20, dy=4, alpha=14, r=0, g=0, b=0):
    """Soft neutral shadow — no color cast."""
    s = QGraphicsDropShadowEffect()
    s.setBlurRadius(blur)
    s.setOffset(0, dy)
    s.setColor(QColor(r, g, b, alpha))
    return s


def _label(text="", size=T.FS_BASE, bold=False, color=T.TEXT_700):
    lbl = QLabel(text)
    f = QFont(T.FONT, size); f.setBold(bold)
    lbl.setFont(f)
    lbl.setStyleSheet(f"color: {color}; background: transparent;")
    return lbl


def _divider(vertical=False):
    d = QFrame()
    if vertical:
        d.setFrameShape(QFrame.Shape.VLine)
        d.setFixedWidth(1)
    else:
        d.setFrameShape(QFrame.Shape.HLine)
        d.setFixedHeight(1)
    d.setStyleSheet(f"background: {T.BORDER}; border: none;")
    return d


# ═════════════════════════════════════════════════════════════════════════════
#  HEADER SECTION
# ═════════════════════════════════════════════════════════════════════════════

class _SectionHeader(QWidget):
    def __init__(self, text="", parent=None):
        super().__init__(parent)
        h = QHBoxLayout(self)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(T.SP_2)

        self._dot = PulseDot(T.INDIGO_500, 7)
        h.addWidget(self._dot)

        self._lbl = QLabel(text)
        f = QFont(T.FONT, T.FS_XS); f.setBold(True)
        self._lbl.setFont(f)
        self._lbl.setStyleSheet(f"""
            color: {T.TEXT_400};
            letter-spacing: 1.5px;
            background: transparent;
        """)
        h.addWidget(self._lbl)
        h.addStretch()

    def set_text(self, text):
        self._lbl.setText(text)

    def set_recording(self, recording: bool):
        self._dot.set_color(T.RED_400 if recording else T.INDIGO_500)


# ═════════════════════════════════════════════════════════════════════════════
#  PROGRESS CARD — thin, modern
# ═════════════════════════════════════════════════════════════════════════════

class _ProgressCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        # White card, very light border, soft shadow
        self.setStyleSheet(f"""
            QFrame {{
                background: {T.BG_CARD};
                border: 1px solid {T.BORDER};
                border-radius: {T.R_LG}px;
            }}
        """)
        self.setGraphicsEffect(_shadow(16, 4, 12))

        lay = QVBoxLayout(self)
        lay.setContentsMargins(T.SP_5, T.SP_4, T.SP_5, T.SP_4)
        lay.setSpacing(T.SP_3)

        # Top row: question label + percentage badge
        top = QHBoxLayout()
        top.setSpacing(T.SP_2)

        self._q_lbl = QLabel("—  /  —")
        f = QFont(T.FONT, T.FS_BASE); f.setBold(True)
        self._q_lbl.setFont(f)
        self._q_lbl.setStyleSheet(f"color: {T.TEXT_800}; background: transparent;")
        top.addWidget(self._q_lbl)
        top.addStretch()

        # Percentage badge — soft indigo pill
        self._pct_badge = QLabel("0%")
        f2 = QFont(T.FONT, T.FS_SM); f2.setBold(True)
        self._pct_badge.setFont(f2)
        self._pct_badge.setStyleSheet(f"""
            color: {T.INDIGO_600};
            background: {T.INDIGO_50};
            border-radius: {T.R_FULL}px;
            padding: 2px 10px;
        """)
        top.addWidget(self._pct_badge)
        lay.addLayout(top)

        # Progress bar — thin gradient, 4px height
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setStyleSheet(StarkTheme.progress_style())
        lay.addWidget(self.progress_bar)

        # Dot indicators
        self._dots_row = QHBoxLayout()
        self._dots_row.setSpacing(5)
        self._dots: list[QLabel] = []
        self._total_dots = 0
        lay.addLayout(self._dots_row)

    def update(self, current: int, total: int, pct: int):
        self._q_lbl.setText(f"Question {current} / {total}" if total > 0 else "— / —")
        self._pct_badge.setText(f"{pct}%")
        self.progress_bar.setValue(pct)

        if total != self._total_dots:
            for d in self._dots:
                d.deleteLater()
            self._dots.clear()
            self._total_dots = total
            for i in range(total):
                d = QLabel()
                d.setFixedSize(7, 7)
                d.setStyleSheet(f"""
                    QLabel {{
                        background: {T.BORDER};
                        border-radius: 3px;
                    }}
                """)
                self._dots.append(d)
                self._dots_row.addWidget(d)
            self._dots_row.addStretch()

        for i, d in enumerate(self._dots):
            if i < current:
                d.setStyleSheet(f"""
                    QLabel {{
                        background: {T.INDIGO_500};
                        border-radius: 3px;
                    }}
                """)
            else:
                d.setStyleSheet(f"""
                    QLabel {{
                        background: {T.BORDER};
                        border-radius: 3px;
                    }}
                """)


# ═════════════════════════════════════════════════════════════════════════════
#  INFO CARD — audio instruction card
# ═════════════════════════════════════════════════════════════════════════════

class _InfoCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Soft off-white background — feels like a content card
        self.setStyleSheet(f"""
            QFrame {{
                background: {T.BG_CARD};
                border: 1px solid {T.BORDER};
                border-radius: {T.R_XL}px;
            }}
        """)
        self.setGraphicsEffect(_shadow(20, 6, 14))

        lay = QVBoxLayout(self)
        lay.setContentsMargins(T.SP_6, T.SP_6, T.SP_6, T.SP_5)
        lay.setSpacing(T.SP_4)

        # ── Mic icon — centered, clean gradient bubble ─────────────
        icon_row = QHBoxLayout()
        icon_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        mic_wrap = QFrame()
        mic_wrap.setFixedSize(60, 60)
        mic_wrap.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 {T.INDIGO_500},stop:1 {T.VIOLET_500});
                border-radius: 16px;
            }}
        """)
        # Subtle indigo glow on mic icon
        mic_glow = QGraphicsDropShadowEffect()
        mic_glow.setBlurRadius(18); mic_glow.setOffset(0, 4)
        mic_glow.setColor(QColor(99, 102, 241, 50))
        mic_wrap.setGraphicsEffect(mic_glow)

        mic_inner = QVBoxLayout(mic_wrap)
        mic_inner.setContentsMargins(0, 0, 0, 0)
        mic_inner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mic_emoji = QLabel("🎤")
        mic_emoji.setFont(QFont("Segoe UI Emoji, Apple Color Emoji", 24))
        mic_emoji.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mic_inner.addWidget(mic_emoji)

        icon_row.addWidget(mic_wrap)
        lay.addLayout(icon_row)

        # ── Title — strong hierarchy ───────────────────────────────
        self._title = QLabel("Écoutez attentivement")
        f_title = QFont(T.FONT, T.FS_MD); f_title.setBold(True)
        self._title.setFont(f_title)
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title.setStyleSheet(f"color: {T.TEXT_900}; background: transparent;")
        lay.addWidget(self._title)

        # Light divider
        lay.addWidget(_divider())

        # ── Subtitle — readable, muted ─────────────────────────────
        self._sub = QLabel()
        f_sub = QFont(T.FONT_BODY, T.FS_SM)
        self._sub.setFont(f_sub)
        self._sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._sub.setWordWrap(True)
        self._sub.setStyleSheet(f"color: {T.TEXT_500}; background: transparent;")
        lay.addWidget(self._sub)

        # ── Duration badge — amber pill ────────────────────────────
        dur_row = QHBoxLayout()
        dur_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._dur_badge = QFrame()
        self._dur_badge.setFixedHeight(30)
        self._dur_badge.setVisible(False)
        db = QHBoxLayout(self._dur_badge)
        db.setContentsMargins(12, 0, 12, 0)
        db.setSpacing(5)

        clk = QLabel("⏱")
        clk.setFont(QFont("Segoe UI Emoji", 11))
        clk.setStyleSheet("background: transparent;")
        db.addWidget(clk)

        self._dur_lbl = QLabel()
        f_dur = QFont(T.FONT, T.FS_SM); f_dur.setBold(True)
        self._dur_lbl.setFont(f_dur)
        self._dur_lbl.setStyleSheet(f"color: {T.AMBER_600}; background: transparent;")
        db.addWidget(self._dur_lbl)

        self._dur_badge.setStyleSheet(f"""
            QFrame {{
                background: {T.AMBER_50};
                border: 1px solid {T.AMBER_200};
                border-radius: {T.R_FULL}px;
            }}
        """)
        dur_row.addWidget(self._dur_badge)
        lay.addLayout(dur_row)

        # ── Status pill ────────────────────────────────────────────
        pill_row = QHBoxLayout()
        pill_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._pill = QFrame()
        self._pill.setFixedHeight(34)
        pill_inner = QHBoxLayout(self._pill)
        pill_inner.setContentsMargins(14, 0, 18, 0)
        pill_inner.setSpacing(T.SP_2)

        self._pill_dot = PulseDot(T.TEXT_400, 7)
        pill_inner.addWidget(self._pill_dot)

        self._pill_lbl = QLabel("En attente")
        f_pill = QFont(T.FONT, T.FS_SM); f_pill.setBold(True)
        self._pill_lbl.setFont(f_pill)
        self._pill_lbl.setStyleSheet(f"color: {T.TEXT_500}; background: transparent;")
        pill_inner.addWidget(self._pill_lbl)

        self._set_pill("waiting")
        pill_row.addWidget(self._pill)
        lay.addLayout(pill_row)

        # ── Countdown ─────────────────────────────────────────────
        self._countdown = QLabel()
        f_cd = QFont(T.FONT, T.FS_BASE); f_cd.setBold(True)
        self._countdown.setFont(f_cd)
        self._countdown.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._countdown.setVisible(False)
        self._countdown.setStyleSheet(f"color: {T.RED_500}; background: transparent;")
        lay.addWidget(self._countdown)

    _PILL_STATES = {
        "waiting":   (T.TEXT_400,    T.BG_PAGE,      T.BORDER,        T.TEXT_500),
        "playing":   (T.AMBER_500,   T.AMBER_50,     T.AMBER_200,     T.AMBER_600),
        "ready":     (T.GREEN_500,   T.GREEN_50,     T.GREEN_200,     T.GREEN_700),
        "recording": (T.RED_400,     T.RED_50,       T.RED_200,       T.RED_600),
    }

    def _set_pill(self, state: str, text: str = ""):
        dot_c, bg, border, text_c = self._PILL_STATES.get(state, self._PILL_STATES["waiting"])
        self._pill_dot.set_color(dot_c)
        self._pill.setStyleSheet(f"""
            QFrame {{
                background: {bg};
                border: 1px solid {border};
                border-radius: {T.R_FULL}px;
            }}
        """)
        self._pill_lbl.setStyleSheet(
            f"color: {text_c}; font-weight: 600; background: transparent; letter-spacing: 0.2px;"
        )
        if text:
            self._pill_lbl.setText(text)

    def set_status(self, state: str, text: str = ""):
        self._set_pill(state, text)

    def set_title(self, t): self._title.setText(t)
    def set_sub(self, t): self._sub.setText(t)
    def set_duration_label(self, t):
        self._dur_lbl.setText(t)
        self._dur_badge.setVisible(bool(t))
    def set_countdown(self, text: str, color: str):
        self._countdown.setText(text)
        self._countdown.setStyleSheet(f"color: {color}; font-weight: 700; background: transparent;")
        self._countdown.setVisible(bool(text))
    def set_pill_text(self, text: str):
        self._pill_lbl.setText(text)


# ═════════════════════════════════════════════════════════════════════════════
#  MAIN INTERVIEW WIDGET
# ═════════════════════════════════════════════════════════════════════════════

class InterviewWidget(QWidget):
    start_recording = Signal()
    stop_recording  = Signal()
    end_interview   = Signal()

    def __init__(self, language: str = "fr", parent=None):
        super().__init__(parent)
        self._lang               = language
        self.is_recording        = False
        self._max_secs           = DEFAULT_MAX_RECORDING_SECONDS
        self._remaining          = DEFAULT_MAX_RECORDING_SECONDS

        self._countdown_timer = QTimer(self)
        self._countdown_timer.setInterval(1000)
        self._countdown_timer.timeout.connect(self._on_tick)

        self.setMinimumWidth(320)
        self.setMaximumWidth(440)

        root = QVBoxLayout(self)
        # 8px grid margins
        root.setContentsMargins(T.SP_2, T.SP_3, T.SP_2, T.SP_3)
        root.setSpacing(T.SP_3)

        # ── Section header ─────────────────────────────────────────
        self._header = _SectionHeader()
        root.addWidget(self._header)

        # ── Progress card ──────────────────────────────────────────
        self._progress_card = _ProgressCard()
        root.addWidget(self._progress_card)

        # ── Info card — vertically centered ───────────────────────
        self._info_card = _InfoCard()
        root.addStretch()
        root.addWidget(self._info_card)
        root.addStretch()

        # ── Record button — full width, prominent ─────────────────
        self.record_btn = self._build_record_btn()
        root.addWidget(self.record_btn)

        # ── End button — ghost / danger ────────────────────────────
        self.end_btn = QPushButton()
        self.end_btn.setMinimumHeight(38)
        self.end_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.end_btn.setStyleSheet(StarkTheme.get_button_style("danger"))
        self.end_btn.clicked.connect(self.end_interview.emit)
        root.addWidget(self.end_btn)

        self._apply()

    # ── Build record button ───────────────────────────────────────

    def _build_record_btn(self) -> QPushButton:
        btn = QPushButton()
        f = QFont(T.FONT, T.FS_MD); f.setBold(True)
        btn.setFont(f)
        btn.setMinimumHeight(56)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(StarkTheme.get_button_style("primary"))
        # Subtle indigo glow
        eff = QGraphicsDropShadowEffect()
        eff.setBlurRadius(20); eff.setOffset(0, 5)
        eff.setColor(QColor(99, 102, 241, 45))
        btn.setGraphicsEffect(eff)
        btn.clicked.connect(self._toggle_record)
        btn.setEnabled(False)
        return btn

    # ── i18n ──────────────────────────────────────────────────────

    def t(self, key, **kwargs):
        tpl = TEXTS.get(self._lang, TEXTS["fr"]).get(key, key)
        return tpl.format(**kwargs) if kwargs else tpl

    def set_language(self, lang: str):
        self._lang = lang
        self._apply()

    def _apply(self):
        self._header.set_text(self.t("section"))
        self._info_card.set_title(self.t("listen_title"))
        self._info_card.set_sub(self.t("listen_sub"))
        self._update_dur_label()
        self.record_btn.setText(
            self.t("stop") if self.is_recording else self.t("start")
        )
        self.end_btn.setText(self.t("end"))
        self._info_card.set_status("waiting", self.t("waiting"))
        ltr = Qt.LayoutDirection.RightToLeft if self._lang == "ar" \
              else Qt.LayoutDirection.LeftToRight
        self.setLayoutDirection(ltr)

    def _update_dur_label(self):
        m = self._max_secs // 60
        s = self._max_secs % 60
        self._info_card.set_duration_label(self.t("max_duration", m=m, s=s))

    # ── Record logic ──────────────────────────────────────────────

    def _toggle_record(self):
        if not self.is_recording:
            self._start_rec()
        else:
            self._stop_rec(auto=False)

    def _start_rec(self):
        self.is_recording  = True
        self._remaining    = self._max_secs
        self.start_recording.emit()
        self._header.set_recording(True)
        self._set_recording_style(True)
        self._info_card.set_status("recording", "● " + self.t("stop"))
        self._info_card.set_countdown(
            self.t("recording_left", s=self._remaining),
            T.RED_500
        )
        self._countdown_timer.start()

    def _stop_rec(self, auto: bool = False):
        self._countdown_timer.stop()
        self.is_recording = False
        self.stop_recording.emit()
        self._header.set_recording(False)
        self._set_recording_style(False)
        self.record_btn.setEnabled(False)
        self._info_card.set_countdown("", "")
        if auto:
            self._info_card.set_status("waiting", "")
            self._info_card.set_pill_text(self.t("time_up"))
        else:
            self._info_card.set_status("waiting", self.t("waiting"))

    def _on_tick(self):
        self._remaining -= 1
        s = self._remaining
        color = T.TEXT_600 if s > 30 else (T.AMBER_500 if s > 10 else T.RED_500)
        text = self.t("recording_left", s=s)
        self._info_card.set_countdown(text, color)
        self._info_card.set_pill_text(text)
        if s <= 0:
            self._stop_rec(auto=True)

    def _set_recording_style(self, recording: bool):
        if recording:
            self.record_btn.setText(self.t("stop"))
            self.record_btn.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 {T.RED_500},stop:1 {T.RED_600});
                    color: {T.TEXT_WHITE};
                    border: none;
                    border-radius: {T.R_LG}px;
                    padding: 15px 32px;
                    font-size: {T.FS_MD}px;
                    font-weight: 700;
                    font-family: {T.FONT};
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 {T.RED_600},stop:1 {T.RED_700});
                }}
                QPushButton:pressed {{
                    padding-top: 16px; padding-bottom: 14px;
                    background: {T.RED_700};
                }}
            """)
            eff = QGraphicsDropShadowEffect()
            eff.setBlurRadius(20); eff.setOffset(0, 5)
            eff.setColor(QColor(220, 38, 38, 55))
            self.record_btn.setGraphicsEffect(eff)
        else:
            self.record_btn.setText(self.t("start"))
            self.record_btn.setStyleSheet(StarkTheme.get_button_style("primary"))
            eff = QGraphicsDropShadowEffect()
            eff.setBlurRadius(20); eff.setOffset(0, 5)
            eff.setColor(QColor(99, 102, 241, 45))
            self.record_btn.setGraphicsEffect(eff)

    # ── Public API ────────────────────────────────────────────────

    def set_max_recording_seconds(self, seconds: int):
        self._max_secs   = max(10, seconds)
        self._remaining  = self._max_secs
        self._update_dur_label()

    def update_question(self, progress: dict):
        c = progress.get("current", 0)
        t = progress.get("total",   0)
        p = progress.get("percentage", 0)
        self._progress_card.update(c, t, p)
        self._info_card.set_status("playing", self.t("playing"))
        self.record_btn.setEnabled(False)
        self.record_btn.setText(self.t("start"))
        self.record_btn.setStyleSheet(StarkTheme.get_button_style("primary"))
        self._header.set_recording(False)

    def set_audio_playing(self):
        self._info_card.set_status("playing", self.t("playing"))
        self.record_btn.setEnabled(False)

    def set_ready_to_answer(self):
        self._info_card.set_status("ready", self.t("ready"))

    def enable_recording(self, enabled: bool):
        if enabled:
            self.record_btn.setEnabled(True)
            self._start_rec()
        else:
            if self.is_recording:
                self._stop_rec(auto=False)
            self.record_btn.setEnabled(False)
            self._info_card.set_status("waiting", self.t("waiting"))