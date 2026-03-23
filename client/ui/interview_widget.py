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

TEXTS = {
    "ar": {
        "section":"الوضع الصوتي","progress":"السؤال {c} من {t}",
        "listen_title":"استمع جيداً",
        "listen_sub":"ستُطرح الأسئلة صوتياً فقط.\nاستمع للمحاور ثم أجب بوضوح.",
        "max_duration":"مدة الإجابة القصوى : {m} دق {s} ث",
        "waiting":"في انتظار السؤال…","playing":"السؤال قيد التشغيل",
        "ready":"جاهز للإجابة","start":"ابدأ الإجابة","stop":"إيقاف التسجيل",
        "end":"إنهاء المقابلة","recording_left":"{s} ث متبقية",
        "time_up":"انتهى الوقت — توقف التسجيل تلقائياً",
    },
    "fr": {
        "section":"MODE VOCAL","progress":"Question {c} / {t}",
        "listen_title":"Écoutez attentivement",
        "listen_sub":"Les questions sont posées uniquement en audio.\nÉcoutez l'avatar, puis répondez clairement.",
        "max_duration":"Durée max : {m} min {s:02d} s",
        "waiting":"En attente de la question…","playing":"Lecture en cours",
        "ready":"Prêt à répondre","start":"Commencer à répondre","stop":"Arrêter l'enregistrement",
        "end":"Terminer l'entretien","recording_left":"{s} s restantes",
        "time_up":"Temps écoulé — enregistrement arrêté automatiquement",
    },
    "en": {
        "section":"VOCAL MODE","progress":"Question {c} of {t}",
        "listen_title":"Listen carefully",
        "listen_sub":"Questions are audio-only.\nListen to the avatar, then answer clearly.",
        "max_duration":"Max response time: {m} min {s:02d} s",
        "waiting":"Waiting for question…","playing":"Playing question",
        "ready":"Ready to answer","start":"Start answering","stop":"Stop recording",
        "end":"End interview","recording_left":"{s} s left",
        "time_up":"Time's up — recording stopped automatically",
    },
}

DEFAULT_MAX_RECORDING_SECONDS = 90


# ── Helpers ────────────────────────────────────────────────────────────────────

class _PulseDot(QWidget):
    def __init__(self, color=T.CYAN_500, size=9, parent=None):
        super().__init__(parent)
        self._c=QColor(color); self._a=255; self._d=-5; self._sz=size
        self.setFixedSize(size+4, size+4)
        t=QTimer(self); t.timeout.connect(self._tick); t.start(42)

    def set_color(self, c): self._c=QColor(c); self.update()

    def _tick(self):
        self._a+=self._d
        if self._a<=60: self._d=5
        elif self._a>=255: self._d=-5
        self.update()

    def paintEvent(self, _):
        p=QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        s=self._sz; off=2
        halo=QColor(self._c); halo.setAlpha(max(0, self._a//6))
        p.setBrush(QBrush(halo)); p.setPen(Qt.PenStyle.NoPen); p.drawEllipse(0,0,s+4,s+4)
        core=QColor(self._c); core.setAlpha(self._a)
        p.setBrush(QBrush(core)); p.drawEllipse(off,off,s,s)


def _sh(blur=20, dy=8, alpha=20, r=0, g=200, b=224):
    s=QGraphicsDropShadowEffect(); s.setBlurRadius(blur); s.setOffset(0,dy)
    s.setColor(QColor(r,g,b,alpha)); return s


def _sh2(blur=6, dy=2, alpha=12):
    s=QGraphicsDropShadowEffect(); s.setBlurRadius(blur); s.setOffset(0,dy)
    s.setColor(QColor(0,0,0,alpha)); return s


def _lbl(text="", size=T.FS_BASE, w=400, color=T.TEXT_700):
    l=QLabel(text); f=QFont(T.FONT,size)
    f.setWeight(QFont.Weight.Bold if w>=700 else QFont.Weight.DemiBold if w>=600 else QFont.Weight.Normal)
    l.setFont(f); l.setStyleSheet(f"color:{color};background:transparent;"); return l


def _sep():
    s=QFrame(); s.setFrameShape(QFrame.Shape.HLine); s.setFixedHeight(1)
    s.setStyleSheet(f"background:{T.BORDER};border:none;"); return s


def _glass_card_qss(radius=T.R_LG):
    return f"""QFrame {{
        background: {T.BG_CARD};
        border: 1px solid {T.BORDER_GLASS};
        border-radius: {radius}px;
    }}"""


class _StatusPill(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(36)
        lay=QHBoxLayout(self); lay.setContentsMargins(16,0,20,0); lay.setSpacing(9)
        self.dot=_PulseDot(T.TEXT_300, 8); lay.addWidget(self.dot)
        self.label=QLabel()
        self.label.setFont(QFont(T.FONT,T.FS_SM,QFont.Weight.Bold))
        self.label.setStyleSheet("background:transparent;")
        lay.addWidget(self.label)
        self._apply("waiting","—")

    def _apply(self, state, text):
        cfg={
            "waiting": (T.TEXT_300,  T.BG_CARD,     T.BORDER,      T.TEXT_300),
            "playing": (T.AMBER_500, T.AMBER_50,    T.AMBER_100,   T.AMBER_600),
            "ready":   (T.TEAL_500,  T.GREEN_50,    T.GREEN_100,   T.TEAL_700),
            "recording":(T.RED_500,  T.RED_50,      T.RED_100,     T.RED_600),
        }
        dc,bg,bd,tc=cfg.get(state,cfg["waiting"])
        self.dot.set_color(dc)
        self.setStyleSheet(f"QFrame{{background:{bg};border:1px solid {bd};border-radius:{T.R_FULL}px;}}")
        self.label.setText(text)
        self.label.setStyleSheet(f"color:{tc};font-weight:700;background:transparent;")


# ═════════════════════════════════════════════════════════════════════════════
class InterviewWidget(QWidget):
    start_recording = Signal()
    stop_recording  = Signal()
    end_interview   = Signal()

    def __init__(self, language="fr", parent=None):
        super().__init__(parent)
        self._lang=language; self.is_recording=False
        self._max_recording_secs=DEFAULT_MAX_RECORDING_SECONDS
        self._remaining_secs=DEFAULT_MAX_RECORDING_SECONDS
        self._countdown_timer=QTimer(self); self._countdown_timer.setInterval(1000)
        self._countdown_timer.timeout.connect(self._on_countdown_tick)
        self.setMinimumWidth(360); self.setMaximumWidth(460)
        root=QVBoxLayout(self); root.setContentsMargins(0,0,0,0); root.setSpacing(T.SP_3)
        root.addWidget(self._make_header())
        root.addWidget(self._make_progress_card())
        root.addWidget(self._make_instr_card())
        root.addStretch()
        self.record_btn=self._make_record_btn(); root.addWidget(self.record_btn)
        self.end_btn=self._make_end_btn(); root.addWidget(self.end_btn)
        self._apply()

    def t(self,k,**kw):
        tpl=TEXTS.get(self._lang,TEXTS["fr"]).get(k,k)
        return tpl.format(**kw) if kw else tpl

    def set_language(self,lang): self._lang=lang; self._apply()

    def _apply(self):
        self._sect_lbl.setText(self.t("section"))
        self._inst_title.setText(self.t("listen_title"))
        self._inst_sub.setText(self.t("listen_sub"))
        self._update_dur()
        self.record_btn.setText(self.t("stop") if self.is_recording else self.t("start"))
        self.end_btn.setText(self.t("end"))
        self._pill._apply("waiting","—")
        ltr=Qt.LayoutDirection.RightToLeft if self._lang=="ar" else Qt.LayoutDirection.LeftToRight
        self.setLayoutDirection(ltr)

    def _update_dur(self):
        m=self._max_recording_secs//60; s=self._max_recording_secs%60
        self._max_dur_lbl.setText(self.t("max_duration",m=m,s=s))

    def _make_header(self):
        w=QWidget(); h=QHBoxLayout(w); h.setContentsMargins(2,0,2,0); h.setSpacing(T.SP_2)
        self._dot=_PulseDot(T.CYAN_500); h.addWidget(self._dot)
        self._sect_lbl=QLabel()
        self._sect_lbl.setFont(QFont(T.FONT,T.FS_XS,QFont.Weight.Bold))
        self._sect_lbl.setStyleSheet(f"color:{T.CYAN_500};letter-spacing:3px;background:transparent;text-transform:uppercase;")
        h.addWidget(self._sect_lbl); h.addStretch(); return w

    def _make_progress_card(self):
        card=QFrame(); card.setObjectName("pc")
        card.setStyleSheet(_glass_card_qss(T.R_LG))
        card.setGraphicsEffect(_sh(22,8,18))
        lay=QVBoxLayout(card); lay.setContentsMargins(T.SP_5,T.SP_4,T.SP_5,T.SP_4); lay.setSpacing(T.SP_3)
        row=QHBoxLayout()
        self._prog_lbl=_lbl("",T.FS_SM,600,T.TEXT_300)
        self._pct_lbl=_lbl("",T.FS_SM,900,T.CYAN_500)
        row.addWidget(self._prog_lbl); row.addStretch(); row.addWidget(self._pct_lbl)
        lay.addLayout(row)
        self.progress_bar=QProgressBar()
        self.progress_bar.setRange(0,100); self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False); self.progress_bar.setFixedHeight(8)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar{{background:{T.CYAN_50};border-radius:4px;border:none;}}
            QProgressBar::chunk{{
                background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {T.CYAN_500},stop:1 {T.TEAL_400});
                border-radius:4px;
            }}
        """)
        lay.addWidget(self.progress_bar); return card

    def _make_instr_card(self):
        card=QFrame(); card.setObjectName("ic")
        card.setStyleSheet(_glass_card_qss(T.R_LG))
        lay=QVBoxLayout(card); lay.setContentsMargins(T.SP_5,T.SP_5,T.SP_5,T.SP_5); lay.setSpacing(T.SP_3)

        mic=QFrame(); mic.setFixedSize(54,54)
        mic.setStyleSheet(f"""QFrame{{
            background:{T.BG_CARD};border:1.5px solid {T.BORDER_MID};
            border-radius:16px;
        }}""")
        mic.setGraphicsEffect(_sh(14,4,16))
        ml=QVBoxLayout(mic); ml.setContentsMargins(0,0,0,0); ml.setAlignment(Qt.AlignmentFlag.AlignCenter)
        me=QLabel("🎤"); me.setFont(QFont("Segoe UI Emoji,Apple Color Emoji",22))
        me.setAlignment(Qt.AlignmentFlag.AlignCenter); ml.addWidget(me)
        lay.addWidget(mic,alignment=Qt.AlignmentFlag.AlignCenter)

        self._inst_title=_lbl("",T.FS_LG,800,T.TEXT_900)
        self._inst_title.setAlignment(Qt.AlignmentFlag.AlignCenter); lay.addWidget(self._inst_title)
        lay.addWidget(_sep())
        self._inst_sub=_lbl("",T.FS_SM,400,T.TEXT_400)
        self._inst_sub.setAlignment(Qt.AlignmentFlag.AlignCenter); self._inst_sub.setWordWrap(True)
        lay.addWidget(self._inst_sub)

        dr=QHBoxLayout(); dr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._dur_badge=QFrame(); self._dur_badge.setFixedHeight(28)
        self._dur_badge.setStyleSheet(f"""QFrame{{
            background:{T.AMBER_50};border:1px solid {T.AMBER_100};border-radius:{T.R_FULL}px;
        }}""")
        dbl=QHBoxLayout(self._dur_badge); dbl.setContentsMargins(12,0,12,0); dbl.setSpacing(5)
        ck=QLabel("⏱"); ck.setFont(QFont("Segoe UI Emoji",11)); ck.setStyleSheet("background:transparent;")
        dbl.addWidget(ck)
        self._max_dur_lbl=QLabel()
        self._max_dur_lbl.setFont(QFont(T.FONT,T.FS_SM,QFont.Weight.Bold))
        self._max_dur_lbl.setStyleSheet(f"color:{T.AMBER_600};background:transparent;")
        dbl.addWidget(self._max_dur_lbl)
        dr.addWidget(self._dur_badge); lay.addLayout(dr); self._dur_badge.setVisible(False)
        lay.addSpacing(T.SP_2)

        pr=QHBoxLayout(); pr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._pill=_StatusPill(); pr.addWidget(self._pill); lay.addLayout(pr)

        self._cdown=_lbl("",T.FS_SM,700,T.RED_600)
        self._cdown.setAlignment(Qt.AlignmentFlag.AlignCenter); self._cdown.setVisible(False)
        lay.addWidget(self._cdown); return card

    def _make_record_btn(self):
        btn=QPushButton()
        btn.setFont(QFont(T.FONT,T.FS_MD,QFont.Weight.Bold))
        btn.setMinimumHeight(56); btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(StarkTheme.get_button_style("primary"))
        s=QGraphicsDropShadowEffect(); s.setBlurRadius(28); s.setOffset(0,10)
        s.setColor(QColor(0,200,224,95)); btn.setGraphicsEffect(s)
        btn.clicked.connect(self._toggle_record); btn.setEnabled(False); return btn

    def _make_end_btn(self):
        btn=QPushButton()
        btn.setFont(QFont(T.FONT,T.FS_SM,QFont.Weight.DemiBold))
        btn.setMinimumHeight(44); btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(StarkTheme.get_button_style("danger"))
        btn.clicked.connect(self.end_interview.emit); return btn

    def _toggle_record(self):
        if not self.is_recording: self._start_rec()
        else: self._stop_rec()

    def _start_rec(self):
        self.is_recording=True; self._remaining_secs=self._max_recording_secs
        self.start_recording.emit(); self._set_rec_style(True)
        self._pill._apply("recording",self.t("stop"))
        self._cdown.setVisible(True); self._update_cdown(); self._countdown_timer.start()

    def _stop_rec(self, auto=False):
        self._countdown_timer.stop(); self.is_recording=False; self.stop_recording.emit()
        self._set_rec_style(False); self.record_btn.setEnabled(False); self._cdown.setVisible(False)
        if auto:
            self._pill._apply("waiting","—")
            self._pill.label.setText(self.t("time_up"))
            self._pill.label.setStyleSheet(f"color:{T.RED_500};font-weight:700;background:transparent;")
        else:
            self._pill._apply("waiting","—")

    def _on_countdown_tick(self):
        self._remaining_secs-=1; self._update_cdown()
        if self._remaining_secs<=0: self._stop_rec(auto=True)

    def _update_cdown(self):
        s=self._remaining_secs
        c=T.TEXT_400 if s>30 else (T.AMBER_500 if s>10 else T.RED_500)
        self._cdown.setText(self.t("recording_left",s=s))
        self._cdown.setStyleSheet(f"color:{c};font-weight:800;background:transparent;")
        self._pill.label.setText(self.t("recording_left",s=s))
        self._pill.label.setStyleSheet(f"color:{T.RED_500};font-weight:700;background:transparent;")

    def _set_rec_style(self, recording):
        if recording:
            self.record_btn.setText(self.t("stop"))
            self.record_btn.setStyleSheet(f"""
                QPushButton{{
                    background:{T.RED_50};color:{T.RED_500};
                    border:1.5px solid {T.RED_100};border-radius:{T.R_MD}px;
                    padding:14px 36px;font-size:{T.FS_MD}px;font-weight:700;
                }}
                QPushButton:hover{{
                    background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {T.RED_500},stop:1 {T.RED_600});
                    color:#fff;border:none;
                }}
                QPushButton:pressed{{background:{T.RED_700};color:#fff;border:none;}}
            """)
            s=QGraphicsDropShadowEffect(); s.setBlurRadius(28); s.setOffset(0,10)
            s.setColor(QColor(255,77,106,95)); self.record_btn.setGraphicsEffect(s)
            self._dot.set_color(T.RED_500)
        else:
            self.record_btn.setText(self.t("start"))
            self.record_btn.setStyleSheet(StarkTheme.get_button_style("primary"))
            s=QGraphicsDropShadowEffect(); s.setBlurRadius(28); s.setOffset(0,10)
            s.setColor(QColor(0,200,224,95)); self.record_btn.setGraphicsEffect(s)
            self._dot.set_color(T.CYAN_500)

    # ── API publique ──────────────────────────────────────────────────────────
    def set_max_recording_seconds(self,seconds):
        self._max_recording_secs=max(10,seconds); self._remaining_secs=self._max_recording_secs
        self._update_dur(); self._dur_badge.setVisible(True)

    def update_question(self,progress):
        c=progress.get("current",0); t=progress.get("total",0); p=progress.get("percentage",0)
        self._prog_lbl.setText(self.t("progress",c=c,t=t)); self._pct_lbl.setText(f"{p}%")
        self.progress_bar.setValue(p); self._pill._apply("playing",self.t("playing"))
        self.record_btn.setEnabled(False); self.record_btn.setText(self.t("start"))
        self.record_btn.setStyleSheet(StarkTheme.get_button_style("primary"))
        self._dot.set_color(T.CYAN_500)

    def set_audio_playing(self): self._pill._apply("playing",self.t("playing")); self.record_btn.setEnabled(False)
    def set_ready_to_answer(self): self._pill._apply("ready",self.t("ready"))

    def enable_recording(self,enabled):
        if enabled: self.record_btn.setEnabled(True); self._start_rec()
        else:
            if self.is_recording: self._stop_rec()
            self.record_btn.setEnabled(False); self._pill._apply("waiting","—")