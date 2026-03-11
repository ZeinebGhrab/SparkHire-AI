"""
Interview Widget — Professional Light UI
Cards blancs propres · badges pills · statuts colorés · QSS complet
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QProgressBar, QFrame, QGraphicsDropShadowEffect,
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QColor, QPainter, QBrush
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from client.ui.stark_theme import StarkTheme, T
from client.ui.icons import StarkIcons


# ── i18n ─────────────────────────────────────────────────────────────────────

TEXTS = {
    "ar": {
        "section":       "الوضع الصوتي",
        "progress":      "السؤال {c} من {t}",
        "listen_title":  "استمع جيداً",
        "listen_sub":    "ستُطرح الأسئلة صوتياً فقط.\nاستمع للمحاور ثم أجب بوضوح.",
        "waiting":       "في انتظار السؤال…",
        "playing":       "السؤال قيد التشغيل",
        "ready":         "جاهز للإجابة",
        "start":         "ابدأ الإجابة",
        "stop":          "إيقاف التسجيل",
        "end":           "إنهاء المقابلة",
    },
    "fr": {
        "section":       "MODE VOCAL",
        "progress":      "Question {c} / {t}",
        "listen_title":  "Écoutez attentivement",
        "listen_sub":    "Les questions sont posées uniquement en audio.\nÉcoutez l'avatar, puis répondez clairement.",
        "waiting":       "En attente de la question…",
        "playing":       "Lecture en cours",
        "ready":         "Prêt à répondre",
        "start":         "Commencer à répondre",
        "stop":          "Arrêter l'enregistrement",
        "end":           "Terminer l'entretien",
    },
    "en": {
        "section":       "VOCAL MODE",
        "progress":      "Question {c} of {t}",
        "listen_title":  "Listen carefully",
        "listen_sub":    "Questions are audio-only.\nListen to the avatar, then answer clearly.",
        "waiting":       "Waiting for question…",
        "playing":       "Playing question",
        "ready":         "Ready to answer",
        "start":         "Start answering",
        "stop":          "Stop recording",
        "end":           "End interview",
    },
}


# ── Pulsing indicator ─────────────────────────────────────────────────────────

class _Dot(QWidget):
    def __init__(self, color: str = T.CYAN_500, parent=None):
        super().__init__(parent)
        self._c = QColor(color)
        self._a = 255
        self._d = -5
        self.setFixedSize(9, 9)
        t = QTimer(self)
        t.timeout.connect(self._tick)
        t.start(45)

    def set_color(self, c: str):
        self._c = QColor(c); self.update()

    def _tick(self):
        self._a += self._d
        if self._a <= 70: self._d = 5
        elif self._a >= 255: self._d = -5
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = QColor(self._c); c.setAlpha(self._a)
        p.setBrush(QBrush(c)); p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(0, 0, 9, 9)


def _sh(blur=18, dy=4, alpha=22):
    s = QGraphicsDropShadowEffect()
    s.setBlurRadius(blur); s.setOffset(0, dy)
    s.setColor(QColor(100, 116, 139, alpha))
    return s


def _lbl(text="", size=T.FS_BASE, bold=False, color=T.TEXT_800):
    l = QLabel(text)
    f = QFont(T.FONT, size); f.setBold(bold)
    l.setFont(f)
    l.setStyleSheet(f"color: {color}; background: transparent;")
    return l


def _sep():
    s = QFrame(); s.setFrameShape(QFrame.Shape.HLine)
    s.setFixedHeight(1)
    s.setStyleSheet(f"background: {T.BORDER}; border: none;")
    return s


# ── InterviewWidget ───────────────────────────────────────────────────────────

class InterviewWidget(QWidget):
    start_recording = Signal()
    stop_recording  = Signal()
    end_interview   = Signal()

    def __init__(self, language: str = "fr", parent=None):
        super().__init__(parent)
        self._lang = language
        self.is_recording = False
        self.setMinimumWidth(360)
        self.setMaximumWidth(460)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(T.SP_3)

        root.addWidget(self._make_header_badge())
        root.addWidget(self._make_progress_card())
        root.addWidget(self._make_instruction_card())
        root.addStretch()
        self.record_btn = self._make_record_btn()
        root.addWidget(self.record_btn)
        self.end_btn = self._make_end_btn()
        root.addWidget(self.end_btn)

        self._apply()

    def t(self, k): return TEXTS.get(self._lang, TEXTS["fr"]).get(k, k)

    def set_language(self, lang: str):
        self._lang = lang; self._apply()

    def _apply(self):
        self._sect_lbl.setText(self.t("section"))
        self._inst_title.setText(self.t("listen_title"))
        self._inst_sub.setText(self.t("listen_sub"))
        self.record_btn.setText(self.t("stop") if self.is_recording else self.t("start"))
        self.end_btn.setText(self.t("end"))
        self._set_status("waiting")
        ltr = Qt.LayoutDirection.RightToLeft if self._lang == "ar" else Qt.LayoutDirection.LeftToRight
        self.setLayoutDirection(ltr)

    # ── Build: header badge ───────────────────────────────────────────────────

    def _make_header_badge(self) -> QWidget:
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(2, 0, 2, 0)
        h.setSpacing(T.SP_2)
        self._dot = _Dot(T.CYAN_500)
        h.addWidget(self._dot)
        self._sect_lbl = _lbl("", T.FS_XS, bold=True, color=T.CYAN_600)
        self._sect_lbl.setStyleSheet(f"color: {T.CYAN_600}; letter-spacing: 2px; background: transparent;")
        h.addWidget(self._sect_lbl)
        h.addStretch()
        return w

    # ── Build: progress card ──────────────────────────────────────────────────

    def _make_progress_card(self) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {T.BG_CARD};
                border: 1px solid {T.BORDER};
                border-radius: {T.R_MD}px;
            }}
        """)
        card.setGraphicsEffect(_sh(16, 3))

        lay = QVBoxLayout(card)
        lay.setContentsMargins(T.SP_4, T.SP_3, T.SP_4, T.SP_3)
        lay.setSpacing(T.SP_2)

        row = QHBoxLayout()
        self._prog_lbl = _lbl("—  /  —", T.FS_BASE, bold=True, color=T.TEXT_800)
        row.addWidget(self._prog_lbl)
        row.addStretch()
        self._pct_lbl = _lbl("0 %", T.FS_SM, bold=True, color=T.CYAN_600)
        row.addWidget(self._pct_lbl)
        lay.addLayout(row)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setStyleSheet(StarkTheme.progress_style())
        lay.addWidget(self.progress_bar)

        return card

    # ── Build: instruction + status card ─────────────────────────────────────

    def _make_instruction_card(self) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {T.BG_CARD};
                border: 1px solid {T.BORDER};
                border-radius: {T.R_LG}px;
            }}
        """)
        card.setGraphicsEffect(_sh(20, 4))

        lay = QVBoxLayout(card)
        lay.setContentsMargins(T.SP_5, T.SP_5, T.SP_5, T.SP_5)
        lay.setSpacing(T.SP_3)

        # Mic icon badge
        mic_cont = QFrame()
        mic_cont.setFixedSize(50, 50)
        mic_cont.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 {T.CYAN_50},stop:1 {T.BLUE_50});
                border: 1px solid {T.CYAN_200};
                border-radius: 12px;
            }}
        """)
        mic_inner = QVBoxLayout(mic_cont)
        mic_inner.setContentsMargins(0, 0, 0, 0)
        mic_inner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mic_e = QLabel("🎤")
        mic_e.setFont(QFont("Segoe UI Emoji, Apple Color Emoji", 24))
        mic_e.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mic_inner.addWidget(mic_e)
        lay.addWidget(mic_cont, alignment=Qt.AlignmentFlag.AlignCenter)

        # Title
        self._inst_title = _lbl("", T.FS_LG, bold=True, color=T.TEXT_900)
        self._inst_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self._inst_title)

        lay.addWidget(_sep())

        # Sub
        self._inst_sub = _lbl("", T.FS_SM, color=T.TEXT_600)
        self._inst_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._inst_sub.setWordWrap(True)
        lay.addWidget(self._inst_sub)

        lay.addSpacing(T.SP_2)

        # Status pill
        pill_row = QHBoxLayout()
        pill_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._pill = QFrame()
        self._pill.setFixedHeight(34)
        p_lay = QHBoxLayout(self._pill)
        p_lay.setContentsMargins(14, 0, 18, 0)
        p_lay.setSpacing(T.SP_2)
        self._pill_dot = _Dot(T.TEXT_400)
        p_lay.addWidget(self._pill_dot)
        self._pill_lbl = _lbl("", T.FS_SM, bold=True, color=T.TEXT_600)
        p_lay.addWidget(self._pill_lbl)
        pill_row.addWidget(self._pill)
        lay.addLayout(pill_row)

        return card

    # ── Buttons ───────────────────────────────────────────────────────────────

    def _make_record_btn(self) -> QPushButton:
        btn = QPushButton()
        btn.setFont(QFont(T.FONT, T.FS_MD, QFont.Weight.Bold))
        btn.setMinimumHeight(54)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(StarkTheme.get_button_style("primary"))
        s = QGraphicsDropShadowEffect(); s.setBlurRadius(22); s.setOffset(0, 6)
        s.setColor(QColor(6, 182, 212, 70)); btn.setGraphicsEffect(s)
        btn.clicked.connect(self._toggle_record)
        return btn

    def _make_end_btn(self) -> QPushButton:
        btn = QPushButton()
        btn.setFont(QFont(T.FONT, T.FS_SM, QFont.Weight.DemiBold))
        btn.setMinimumHeight(42)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(StarkTheme.get_button_style("danger"))
        btn.clicked.connect(self.end_interview.emit)
        return btn

    # ── Logic ─────────────────────────────────────────────────────────────────

    def _toggle_record(self):
        if not self.is_recording:
            self.is_recording = True
            self.start_recording.emit()
            self._set_recording_style(True)
            self._set_status("recording")
        else:
            self.is_recording = False
            self.stop_recording.emit()
            self._set_recording_style(False)
            self._set_status("waiting")

    def _set_recording_style(self, recording: bool):
        if recording:
            self.record_btn.setText(self.t("stop"))
            self.record_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {T.RED_50};
                    color: {T.RED_600};
                    border: 1px solid #FECACA;
                    border-radius: {T.R_MD}px;
                    padding: 12px 28px;
                    font-size: {T.FS_MD}px;
                    font-weight: 700;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 {T.RED_500},stop:1 {T.RED_600});
                    color: white; border: none;
                }}
                QPushButton:pressed {{
                    background: {T.RED_700};
                    padding-top: 13px; padding-bottom: 11px;
                }}
            """)
            self._dot.set_color(T.RED_500)
        else:
            self.record_btn.setText(self.t("start"))
            self.record_btn.setStyleSheet(StarkTheme.get_button_style("primary"))
            self._dot.set_color(T.CYAN_500)

    # ─────────────────────────────────────────────────────────────────────────
    #  STATUS PILL — 4 états
    # ─────────────────────────────────────────────────────────────────────────

    _STATUS_CFG = {
        #  state       : (dot_color,  bg,           border,          text_color,   text_key)
        "waiting"   : (T.TEXT_400,   T.BG_PAGE,    T.BORDER,        T.TEXT_400,   "waiting"),
        "playing"   : (T.AMBER_500,  T.AMBER_50,   T.AMBER_100,     T.AMBER_500,  "playing"),
        "ready"     : (T.GREEN_500,  T.GREEN_50,   T.GREEN_100,     T.GREEN_700,  "ready"),
        "recording" : (T.RED_500,    T.RED_50,     T.RED_100,       T.RED_600,    "stop"),
    }

    def _set_status(self, state: str):
        dot_c, bg, border, text_c, text_k = self._STATUS_CFG.get(
            state, self._STATUS_CFG["waiting"]
        )
        self._pill_dot.set_color(dot_c)
        self._pill.setStyleSheet(f"""
            QFrame {{
                background: {bg};
                border: 1px solid {border};
                border-radius: {T.R_FULL}px;
            }}
        """)
        self._pill_lbl.setText(self.t(text_k))
        self._pill_lbl.setStyleSheet(
            f"color: {text_c}; font-weight: 600; background: transparent;"
        )

    # ── Public API ────────────────────────────────────────────────────────────

    def update_question(self, progress: dict):
        c = progress.get("current", 0)
        t = progress.get("total", 0)
        p = progress.get("percentage", 0)
        self._prog_lbl.setText(self.t("progress").format(c=c, t=t))
        self._pct_lbl.setText(f"{p} %")
        self.progress_bar.setValue(p)
        self._set_status("playing")

    def set_audio_playing(self):
        self._set_status("playing")

    def set_ready_to_answer(self):
        self._set_status("ready")

    def enable_recording(self, enabled: bool):
        self.record_btn.setEnabled(enabled)
        if enabled:
            self.set_ready_to_answer()