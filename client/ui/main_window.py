from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QMessageBox, QLabel, QLineEdit, QPushButton, QFrame,
    QGraphicsDropShadowEffect, QStackedWidget,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor, QPainter, QBrush
import sys, os, base64, time, wave, tempfile, logging
from pathlib import Path
import pygame

sys.path.insert(0,str(Path(__file__).parent.parent.parent))
from client.ui.stark_theme import StarkTheme, T
from client.ui.icons import StarkIcons
from client.ui.video_player_widget import VideoPlayerWidget
from client.ui.interview_widget import InterviewWidget
from client.core.websocket_client import WebSocketClient
from client.core.audio_recorder import AudioRecorder
from client.core.video_recorder import VideoFrameCollector
from client.config import settings

logging.basicConfig(level=logging.INFO)
logger=logging.getLogger(__name__)

_MF=22050; _MS=-16; _MC=2; _MB=4096
pygame.mixer.pre_init(frequency=_MF,size=_MS,channels=_MC,buffer=_MB)
pygame.init()

UI_TEXTS={
    "ar":{"app_title":"SPARKHIRE AI","app_subtitle":"مقابلة صوتية ذكية","choose_language":"اختر لغة المقابلة","choose_subtitle":"ستُجرى المقابلة بالكامل باللغة التي تختارها","enter_session":"معرّف الجلسة","session_placeholder":"session_xxxxxxxxxxxxx","start_btn":"بدء المقابلة","connecting":"جارٍ الاتصال…","status_disconnected":"غير متصل","status_connected":"متصل","status_validating":"التحقق","waiting_connection":"في انتظار الاتصال","vocal_mode_active":"الوضع الصوتي نشط","vocal_mode_label":"الوضع الصوتي","welcome_status":"مرحباً","question_status":"السؤال قيد التشغيل","answer_status":"يمكنك الإجابة","answer_saved":"تم حفظ الإجابة","generating_audio":"توليد الصوت…","end_confirm":"هل تريد إنهاء المقابلة؟","interview_complete":"انتهت المقابلة","thanks_message":"شكراً لك! انتهت المقابلة.","format_error":"الصيغة المطلوبة: session_xxxxxxxxxxxxx","error_title":"خطأ","end_title":"إنهاء","back_btn":"رجوع","confirm_btn":"تأكيد","welcome_back_status":"مرحباً بعودتك — نستأنف المقابلة","camera_ok":"الكاميرا جاهزة","camera_off":"الكاميرا غير متوفرة","facial_score":""},
    "fr":{"app_title":"SPARKHIRE AI","app_subtitle":"Entretien vocal intelligent","choose_language":"Choisissez votre langue","choose_subtitle":"L'entretien se déroulera intégralement dans la langue sélectionnée","enter_session":"Identifiant de session","session_placeholder":"session_xxxxxxxxxxxxx","start_btn":"Démarrer l'entretien","connecting":"Connexion en cours…","status_disconnected":"Déconnecté","status_connected":"Connecté","status_validating":"Validation…","waiting_connection":"En attente","vocal_mode_active":"Mode vocal actif","vocal_mode_label":"Mode Vocal","welcome_status":"Bienvenue — écoutez le message","question_status":"Question en lecture","answer_status":"Vous pouvez répondre","answer_saved":"Réponse enregistrée","generating_audio":"Génération audio…","end_confirm":"Confirmer la fin de l'entretien ?","interview_complete":"Entretien terminé","thanks_message":"Merci ! L'entretien est terminé.","format_error":"Format attendu : session_xxxxxxxxxxxxx","error_title":"Erreur","end_title":"Terminer","back_btn":"Retour","confirm_btn":"Confirmer","welcome_back_status":"Bon retour — reprise de l'entretien","camera_ok":"Caméra active 🎥","camera_off":"Caméra non disponible ⚠️","facial_score":""},
    "en":{"app_title":"SPARKHIRE AI","app_subtitle":"AI-powered voice interview","choose_language":"Choose your language","choose_subtitle":"The entire interview will be conducted in the selected language","enter_session":"Session identifier","session_placeholder":"session_xxxxxxxxxxxxx","start_btn":"Start interview","connecting":"Connecting…","status_disconnected":"Disconnected","status_connected":"Connected","status_validating":"Validating…","waiting_connection":"Waiting","vocal_mode_active":"Vocal mode active","vocal_mode_label":"Vocal Mode","welcome_status":"Welcome — listen to greeting","question_status":"Question playing","answer_status":"You may answer","answer_saved":"Answer saved","generating_audio":"Generating audio…","end_confirm":"Confirm end of interview?","interview_complete":"Interview complete","thanks_message":"Thank you! The interview is complete.","format_error":"Expected: session_xxxxxxxxxxxxx","error_title":"Error","end_title":"End Interview","back_btn":"Back","confirm_btn":"Confirm","welcome_back_status":"Welcome back — resuming interview","camera_ok":"Camera active 🎥","camera_off":"Camera unavailable ⚠️","facial_score":""},
}

LANGUAGES=[
    {"code":"ar","flag":"🇸🇦","name":"العربية","native":"Arabic","accent":T.TEAL_500,"g0":T.TEAL_50,"g1":T.TEAL_100},
    {"code":"fr","flag":"🇫🇷","name":"Français","native":"French","accent":T.CYAN_500,"g0":T.CYAN_50,"g1":T.CYAN_100},
    {"code":"en","flag":"🇬🇧","name":"English","native":"English","accent":T.CYAN_400,"g0":"rgba(0,200,224,0.06)","g1":"rgba(0,200,224,0.12)"},
]


def _sh(blur=24,dy=10,a=18,r=0,g=200,b=224):
    s=QGraphicsDropShadowEffect(); s.setBlurRadius(blur); s.setOffset(0,dy)
    s.setColor(QColor(r,g,b,a)); return s

def _lbl(text,size=T.FS_BASE,bold=False,color=T.TEXT_700):
    l=QLabel(text); f=QFont(T.FONT,size); f.setBold(bold)
    l.setFont(f); l.setStyleSheet(f"color:{color};background:transparent;"); return l

def _div():
    d=QFrame(); d.setFrameShape(QFrame.Shape.HLine); d.setFixedHeight(1)
    d.setStyleSheet(f"background:{T.BORDER};border:none;"); return d

def _hex_rgb(h):
    h=h.lstrip("#"); return int(h[:2],16),int(h[2:4],16),int(h[4:6],16)

def _icon_badge(emoji,size=62):
    c=QFrame(); c.setFixedSize(size,size)
    c.setStyleSheet(f"""QFrame{{
        background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 {T.CYAN_500},stop:1 {T.TEAL_500});
        border:none;border-radius:{size//3}px;
    }}""")
    c.setGraphicsEffect(_sh(18,6,40))
    l=QVBoxLayout(c); l.setContentsMargins(0,0,0,0); l.setAlignment(Qt.AlignmentFlag.AlignCenter)
    e=QLabel(emoji); e.setFont(QFont("Segoe UI Emoji,Apple Color Emoji",size*5//8))
    e.setAlignment(Qt.AlignmentFlag.AlignCenter); l.addWidget(e); return c


class LanguageCard(QFrame):
    def __init__(self,data,on_select,parent=None):
        super().__init__(parent)
        self._data=data; self._on_select=on_select; self._selected=False
        self.setCursor(Qt.CursorShape.PointingHandCursor); self.setFixedSize(196,216)
        self._build(); self._refresh()

    def _build(self):
        lay=QVBoxLayout(self); lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.setSpacing(T.SP_2); lay.setContentsMargins(T.SP_5,T.SP_6,T.SP_5,T.SP_6)
        flag=QLabel(self._data["flag"])
        flag.setFont(QFont("Segoe UI Emoji,Apple Color Emoji,Noto Color Emoji",42))
        flag.setAlignment(Qt.AlignmentFlag.AlignCenter); flag.setStyleSheet("background:transparent;")
        lay.addWidget(flag); lay.addSpacing(T.SP_2)
        name=_lbl(self._data["name"],T.FS_LG,True,T.TEXT_900)
        name.setAlignment(Qt.AlignmentFlag.AlignCenter); lay.addWidget(name)
        nat=_lbl(self._data["native"],T.FS_SM,False,T.TEXT_300)
        nat.setAlignment(Qt.AlignmentFlag.AlignCenter); lay.addWidget(nat)

    def _refresh(self):
        acc=self._data["accent"]; g0=self._data["g0"]; g1=self._data["g1"]
        if self._selected:
            self.setStyleSheet(f"""LanguageCard{{
                background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 {g0},stop:1 {g1});
                border:1.5px solid {acc};border-radius:{T.R_LG}px;
            }}""")
            try: r,g,b=_hex_rgb(acc)
            except Exception: r,g,b=0,200,224
            self.setGraphicsEffect(_sh(28,12,45,r,g,b))
        else:
            self.setStyleSheet(f"""
                LanguageCard{{background:{T.BG_CARD};border:1px solid {T.BORDER_GLASS};border-radius:{T.R_LG}px;}}
                LanguageCard:hover{{background:{T.BG_HOVER};border:1px solid {T.BORDER_MID};}}
            """)
            self.setGraphicsEffect(_sh(18,8,14))

    def set_selected(self,v): self._selected=v; self._refresh()
    def mousePressEvent(self,e): self._on_select(self._data["code"]); super().mousePressEvent(e)


class StatusChip(QFrame):
    STATES={
        "disconnected":(T.TEXT_300,"●",T.BG_CARD,T.BORDER),
        "validating":(T.AMBER_500,"◌",T.AMBER_50,T.AMBER_100),
        "connected":(T.TEAL_500,"●",T.GREEN_50,T.GREEN_100),
        "error":(T.RED_500,"●",T.RED_50,T.RED_100),
    }
    def __init__(self,parent=None):
        super().__init__(parent); self.setFixedHeight(40)
        lay=QHBoxLayout(self); lay.setContentsMargins(14,0,18,0); lay.setSpacing(8)
        self._dot=QLabel("●"); self._dot.setFont(QFont(T.FONT,9)); lay.addWidget(self._dot)
        vl=QVBoxLayout(); vl.setSpacing(1)
        self.lbl_main=QLabel("Déconnecté"); self.lbl_main.setFont(QFont(T.FONT,10,QFont.Weight.DemiBold))
        self.lbl_detail=QLabel("En attente"); self.lbl_detail.setFont(QFont(T.FONT,8))
        self.lbl_detail.setStyleSheet(f"color:{T.TEXT_300};background:transparent;")
        vl.addWidget(self.lbl_main); vl.addWidget(self.lbl_detail); lay.addLayout(vl)
        self.set_state("disconnected")

    def set_state(self,state):
        c,d,bg,bd=self.STATES.get(state,self.STATES["disconnected"])
        self._dot.setText(d); self._dot.setStyleSheet(f"color:{c};background:transparent;")
        self.lbl_main.setStyleSheet(f"color:{c};font-weight:600;background:transparent;")
        self.setStyleSheet(f"QFrame{{background:{bg};border:1px solid {bd};border-radius:{T.R_FULL}px;}}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.websocket_client=None; self.audio_recorder=None; self.session_id=None
        self.is_connecting=False; self._session_token=0; self._language="fr"; self._lang_cards={}
        self._tmp_audio_path=None; self._audio_play_start=0.0; self._audio_min_duration=0.0
        self.audio_check_timer=None; self._audio_sample_rate=-1; self._audio_channels=-1; self._audio_bits=-1
        self._pending_msg_type=""; self._pending_msg_data={}; self._audio_chunks=[]; self._audio_total_chunks=0
        self._video_collector=None
        self._facial_enabled=getattr(settings,"FACIAL_ANALYSIS_ENABLED",True)
        self._camera_available=False; self._camera_lbl=None
        if not pygame.mixer.get_init():
            try: pygame.mixer.init(frequency=_MF,size=_MS,channels=_MC,buffer=_MB)
            except Exception as e: logger.error(f"mixer:{e}")
        self._init_video_collector(); self._setup_ui()

    def _init_video_collector(self):
        if not self._facial_enabled: self._update_camera_indicator(False); return
        fps=getattr(settings,"FACIAL_CAPTURE_FPS",2.0)
        self._video_collector=VideoFrameCollector(camera_index=0,target_fps=fps,jpeg_quality=70,max_width=640)
        self._video_collector.camera_ready.connect(self._on_camera_ready)
        self._video_collector.camera_error.connect(self._on_camera_error)
        self._video_collector.frame_captured.connect(self._on_video_frame)
        available=self._video_collector.is_camera_available(0)
        self._camera_available=available; self._update_camera_indicator(available)

    def _update_camera_indicator(self,ok):
        if self._camera_lbl is None: return
        if not self._facial_enabled: self._camera_lbl.setVisible(False); return
        self._camera_lbl.setText("🎥" if ok else "⚠️")
        self._camera_lbl.setToolTip(self.t("camera_ok" if ok else "camera_off"))
        self._camera_lbl.setStyleSheet(f"color:{T.TEAL_600 if ok else T.RED_500};background:transparent;font-size:16px;")

    def _on_camera_ready(self,ok):
        self._camera_available=ok; self._update_camera_indicator(ok)
        if ok and self._facial_enabled: self.video_player.camera_preview.show(); self.video_player.camera_preview.reposition()
        else: self.video_player.camera_preview.set_camera_unavailable()

    def _on_camera_error(self,msg): self._camera_available=False; self._update_camera_indicator(False)

    def _on_video_frame(self,jpeg_bytes):
        self.video_player.camera_preview.on_frame(jpeg_bytes)
        if not self.websocket_client: return
        try: self.websocket_client.send_message({"type":"video_frame","data":{"frame":base64.b64encode(jpeg_bytes).decode()}})
        except Exception as e: logger.debug(f"vf:{e}")

    def t(self,k,**kw):
        tpl=UI_TEXTS.get(self._language,UI_TEXTS["fr"]).get(k,k)
        return tpl.format(**kw) if kw else tpl

    # ── UI ────────────────────────────────────────────────────────────────────
    def _setup_ui(self):
        self.setWindowTitle("SparkHire AI"); self.showMaximized()
        rw=QWidget(); rw.setObjectName("root")
        rw.setStyleSheet(f"#root{{background:{T.BG_GRADIENT};}}")
        self.setCentralWidget(rw); self.setStyleSheet(StarkTheme.global_stylesheet())
        root=QVBoxLayout(rw); root.setContentsMargins(0,0,0,0); root.setSpacing(0)
        root.addWidget(self._build_header())
        self.stacked=QStackedWidget()
        self.stacked.addWidget(self._build_language_screen())
        self.stacked.addWidget(self._build_session_screen())
        root.addWidget(self.stacked,stretch=1)
        self.interview_container=self._build_interview_container()
        self.interview_container.setVisible(False); root.addWidget(self.interview_container)
        self._setup_statusbar()

    def _build_header(self):
        hdr=QFrame(); hdr.setObjectName("hdr"); hdr.setFixedHeight(68)
        hdr.setStyleSheet(f"#hdr{{background:{T.BG_HEADER};border-bottom:1px solid {T.BORDER};}}")
        lay=QHBoxLayout(hdr); lay.setContentsMargins(28,0,24,0); lay.setSpacing(0)

        badge=QFrame(); badge.setFixedSize(42,42)
        badge.setStyleSheet(f"""QFrame{{
            background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 {T.CYAN_500},stop:1 {T.TEAL_500});
            border-radius:13px;border:none;
        }}""")
        bi=QVBoxLayout(badge); bi.setContentsMargins(0,0,0,0); bi.setAlignment(Qt.AlignmentFlag.AlignCenter)
        st=QLabel("✦"); st.setFont(QFont("Segoe UI Emoji",17))
        st.setStyleSheet("color:white;background:transparent;")
        st.setAlignment(Qt.AlignmentFlag.AlignCenter); bi.addWidget(st)
        badge.setGraphicsEffect(_sh(18,6,45))

        tc=QVBoxLayout(); tc.setSpacing(2)
        t1=_lbl(self.t("app_title"),T.FS_MD,True,T.CYAN_600)
        t1.setStyleSheet(f"color:{T.CYAN_600};background:transparent;letter-spacing:2.5px;font-weight:900;")
        self._header_subtitle=_lbl(self.t("app_subtitle"),T.FS_SM,False,T.TEXT_300)
        tc.addWidget(t1); tc.addWidget(self._header_subtitle)

        left=QHBoxLayout(); left.setSpacing(14); left.addWidget(badge); left.addLayout(tc)
        lay.addLayout(left); lay.addStretch()

        self._camera_lbl=QLabel("")
        self._camera_lbl.setFont(QFont("Segoe UI Emoji",16))
        self._camera_lbl.setStyleSheet("background:transparent;"); self._camera_lbl.setVisible(self._facial_enabled)
        lay.addWidget(self._camera_lbl); lay.addSpacing(14)
        self.status_chip=StatusChip(); lay.addWidget(self.status_chip); return hdr

    def _build_language_screen(self):
        pg=QWidget(); lay=QVBoxLayout(pg)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter); lay.setSpacing(0)
        lay.setContentsMargins(T.SP_10,T.SP_12,T.SP_10,T.SP_10)

        # Tag pill
        tag_w=QWidget(); tl=QHBoxLayout(tag_w); tl.setContentsMargins(0,0,0,0)
        tl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tag_f=QFrame(); tag_f.setFixedHeight(30)
        tag_f.setStyleSheet(f"""QFrame{{
            background:{T.CYAN_50};border:1px solid {T.BORDER_MID};border-radius:{T.R_FULL}px;
        }}""")
        tfl=QHBoxLayout(tag_f); tfl.setContentsMargins(12,0,14,0); tfl.setSpacing(6)
        tdot=QLabel("●"); tdot.setFont(QFont(T.FONT,7))
        tdot.setStyleSheet(f"color:{T.CYAN_500};background:transparent;")
        tfl.addWidget(tdot)
        ttxt=QLabel("SÉLECTION DE LA LANGUE")
        ttxt.setFont(QFont(T.FONT,T.FS_XS,QFont.Weight.Bold))
        ttxt.setStyleSheet(f"color:{T.CYAN_600};letter-spacing:1.5px;background:transparent;")
        tfl.addWidget(ttxt); tl.addWidget(tag_f)
        lay.addWidget(tag_w); lay.addSpacing(T.SP_4)

        # Titre héro — typo 900
        h1=QLabel()
        h1.setFont(QFont(T.FONT,T.FS_3XL))
        h1.setStyleSheet(f"""
            color:{T.TEXT_900};background:transparent;
            font-weight:900;letter-spacing:-1.5px;
        """)
        h1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        h1.setText(self.t("choose_language"))
        lay.addWidget(h1); lay.addSpacing(T.SP_2)

        sub=_lbl(self.t("choose_subtitle"),T.FS_MD,False,T.TEXT_400)
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter); lay.addWidget(sub); lay.addSpacing(T.SP_10)

        cw=QWidget(); cr=QHBoxLayout(cw)
        cr.setAlignment(Qt.AlignmentFlag.AlignCenter); cr.setSpacing(20); cr.setContentsMargins(0,0,0,0)
        self._lang_cards={}
        for ld in LANGUAGES:
            card=LanguageCard(ld,self._on_lang_select)
            self._lang_cards[ld["code"]]=card; cr.addWidget(card)
        lay.addWidget(cw); lay.addSpacing(T.SP_10)

        self._confirm_btn=QPushButton("Continuer en Français  →")
        self._confirm_btn.setFont(QFont(T.FONT,T.FS_MD,QFont.Weight.Bold))
        self._confirm_btn.setFixedSize(300,58); self._confirm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._confirm_btn.setStyleSheet(StarkTheme.get_button_style("primary"))
        s=QGraphicsDropShadowEffect(); s.setBlurRadius(32); s.setOffset(0,12)
        s.setColor(QColor(0,200,224,100)); self._confirm_btn.setGraphicsEffect(s)
        self._confirm_btn.clicked.connect(self._on_lang_confirmed)
        lay.addWidget(self._confirm_btn,alignment=Qt.AlignmentFlag.AlignCenter)
        self._on_lang_select("fr"); return pg

    def _on_lang_select(self,code):
        self._language=code
        for c,card in self._lang_cards.items(): card.set_selected(c==code)
        ld=next(l for l in LANGUAGES if l["code"]==code)
        if hasattr(self,"_confirm_btn"): self._confirm_btn.setText(f"Continuer en {ld['name']}  →")

    def _on_lang_confirmed(self): self._sync_texts(); self.stacked.setCurrentIndex(1)

    def _sync_texts(self):
        self._header_subtitle.setText(self.t("app_subtitle"))
        self.status_chip.lbl_main.setText(self.t("status_disconnected"))
        self.status_chip.lbl_detail.setText(self.t("waiting_connection"))
        if hasattr(self,"_connect_btn"):     self._connect_btn.setText(self.t("start_btn"))
        if hasattr(self,"_session_input"):   self._session_input.setPlaceholderText(self.t("session_placeholder"))
        if hasattr(self,"_back_btn"):        self._back_btn.setText(f"← {self.t('back_btn')}")
        if hasattr(self,"_session_title"):   self._session_title.setText(self.t("enter_session"))
        if hasattr(self,"interview_widget"): self.interview_widget.set_language(self._language)
        self.statusBar().showMessage(self.t("vocal_mode_label"))
        self._refresh_pill(); self._update_camera_indicator(self._camera_available)

    def _build_session_screen(self):
        outer=QWidget(); ol=QVBoxLayout(outer)
        ol.setAlignment(Qt.AlignmentFlag.AlignCenter); ol.setContentsMargins(0,0,0,0)

        # Carte glass principale
        card=QFrame(); card.setFixedWidth(500)
        card.setStyleSheet(f"""QFrame{{
            background:rgba(255,255,255,0.82);
            border:1px solid rgba(255,255,255,0.90);
            border-radius:{T.R_XL}px;
        }}""")
        card.setGraphicsEffect(_sh(50,18,16))

        lay=QVBoxLayout(card); lay.setContentsMargins(T.SP_12,T.SP_10,T.SP_12,T.SP_10)
        lay.setSpacing(T.SP_5); lay.setAlignment(Qt.AlignmentFlag.AlignTop)

        lay.addWidget(_icon_badge("🔑",62),alignment=Qt.AlignmentFlag.AlignCenter)
        lay.addSpacing(T.SP_1)

        self._session_title=_lbl(self.t("enter_session"),T.FS_2XL,True,T.TEXT_900)
        self._session_title.setStyleSheet(f"color:{T.TEXT_900};font-weight:900;letter-spacing:-0.5px;background:transparent;")
        self._session_title.setAlignment(Qt.AlignmentFlag.AlignCenter); lay.addWidget(self._session_title)

        # Pill langue
        pr=QHBoxLayout(); pr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lang_pill=QFrame(); self._lang_pill.setFixedHeight(34)
        self._lang_pill.setStyleSheet(f"""QFrame{{
            background:{T.CYAN_50};border:1px solid {T.BORDER_MID};border-radius:{T.R_FULL}px;
        }}""")
        pi=QHBoxLayout(self._lang_pill); pi.setContentsMargins(18,0,18,0)
        self._pill_lbl=QLabel(); self._pill_lbl.setFont(QFont(T.FONT,T.FS_SM,QFont.Weight.Bold))
        self._pill_lbl.setStyleSheet(f"color:{T.CYAN_600};background:transparent;")
        pi.addWidget(self._pill_lbl); pr.addWidget(self._lang_pill)
        lay.addLayout(pr); self._refresh_pill()
        lay.addWidget(_div())

        # Input
        self._session_input=QLineEdit()
        self._session_input.setPlaceholderText(self.t("session_placeholder"))
        self._session_input.setFont(QFont(T.FONT_MONO,T.FS_MD))
        self._session_input.setMinimumHeight(52); self._session_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._session_input.setStyleSheet(StarkTheme.input_style()); lay.addWidget(self._session_input)

        # Bouton démarrer (coral→orange)
        self._connect_btn=QPushButton(f"{self.t('start_btn')}  →")
        self._connect_btn.setFont(QFont(T.FONT,T.FS_MD,QFont.Weight.Bold))
        self._connect_btn.setMinimumHeight(56); self._connect_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._connect_btn.setStyleSheet(StarkTheme.get_button_style("accent"))
        s=QGraphicsDropShadowEffect(); s.setBlurRadius(28); s.setOffset(0,10)
        s.setColor(QColor(255,107,107,95)); self._connect_btn.setGraphicsEffect(s)
        self._connect_btn.clicked.connect(self._connect_to_interview); lay.addWidget(self._connect_btn)

        self._back_btn=QPushButton(f"← {self.t('back_btn')}")
        self._back_btn.setFont(QFont(T.FONT,T.FS_SM)); self._back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._back_btn.setStyleSheet(StarkTheme.get_button_style("ghost"))
        self._back_btn.clicked.connect(lambda:self.stacked.setCurrentIndex(0))
        lay.addWidget(self._back_btn,alignment=Qt.AlignmentFlag.AlignCenter)
        ol.addWidget(card); return outer

    def _refresh_pill(self):
        ld=next((l for l in LANGUAGES if l["code"]==self._language),None)
        if ld and hasattr(self,"_pill_lbl"): self._pill_lbl.setText(f"{ld['flag']}  {ld['name']}")

    def _build_interview_container(self):
        w=QWidget(); lay=QHBoxLayout(w)
        lay.setContentsMargins(T.SP_4,T.SP_4,T.SP_4,T.SP_4); lay.setSpacing(T.SP_4)
        self.video_player=VideoPlayerWidget(); lay.addWidget(self.video_player,stretch=2)
        self.interview_widget=InterviewWidget(language=self._language)
        self.interview_widget.setMaximumWidth(460)
        self.interview_widget.start_recording.connect(self._on_start_recording)
        self.interview_widget.stop_recording.connect(self._on_stop_recording)
        self.interview_widget.end_interview.connect(self._on_end_interview)
        lay.addWidget(self.interview_widget,stretch=1); return w

    def _setup_statusbar(self):
        self.statusBar().setFixedHeight(26); self.statusBar().showMessage(self.t("vocal_mode_label"))

    # ── Audio helpers ─────────────────────────────────────────────────────────
    def _ensure_audio_format(self,sr,ch,bits):
        sr=sr if sr>0 else _MF; ch=ch if ch>0 else _MC; bits=bits if bits>0 else 16
        if sr==self._audio_sample_rate and ch==self._audio_channels and bits==self._audio_bits: return
        try: pygame.mixer.music.stop(); pygame.mixer.music.unload()
        except Exception: pass
        try:
            pygame.mixer.quit(); pygame.mixer.init(frequency=sr,size=-bits,channels=ch,buffer=4096)
            self._audio_sample_rate,self._audio_channels,self._audio_bits=sr,ch,bits
        except Exception as e:
            logger.error(f"mixer:{e}")
            try: pygame.mixer.init(frequency=_MF,size=_MS,channels=_MC,buffer=_MB)
            except Exception: pass

    def _reset_audio_state(self):
        if self.audio_check_timer: self.audio_check_timer.stop(); self.audio_check_timer=None
        try: pygame.mixer.music.stop(); pygame.mixer.music.unload()
        except Exception: pass
        self._cleanup_tmp()
        self._audio_play_start=self._audio_min_duration=0.0
        self._audio_sample_rate=self._audio_channels=self._audio_bits=-1
        self._audio_chunks=[]; self._audio_total_chunks=0
        self._pending_msg_type=""; self._pending_msg_data={}

    def _cleanup_tmp(self):
        if self._tmp_audio_path:
            try: os.unlink(self._tmp_audio_path)
            except Exception: pass
            self._tmp_audio_path=None

    def _reset_ui_for_new_session(self):
        if self._video_collector and self._video_collector.is_capturing: self._video_collector.stop_capture()
        self.video_player.camera_preview.hide(); self.video_player.camera_preview.set_recording(False)
        self.stacked.setVisible(True); self.stacked.setCurrentIndex(0)
        self.interview_container.setVisible(False)
        self._connect_btn.setEnabled(True); self._connect_btn.setText(f"{self.t('start_btn')}  →")
        self._session_input.setEnabled(True); self._session_input.clear()
        self.status_chip.lbl_main.setText(self.t("status_disconnected"))
        self.status_chip.set_state("disconnected"); self.statusBar().showMessage(self.t("vocal_mode_label"))
        if self.audio_recorder:
            try: self.audio_recorder.cleanup()
            except Exception: pass
            self.audio_recorder=None

    # ── WebSocket ─────────────────────────────────────────────────────────────
    def _connect_to_interview(self):
        if self.is_connecting: return
        sid=self._session_input.text().strip()
        if not sid or not sid.startswith("session_"): self._show_error(self.t("error_title"),self.t("format_error")); return
        if self.websocket_client:
            try:
                self.websocket_client.disconnected.disconnect(); self.websocket_client.connected.disconnect()
                self.websocket_client.message_received.disconnect(); self.websocket_client.error_occurred.disconnect()
            except Exception: pass
            try: self.websocket_client.disconnect_from_server()
            except Exception: pass
            self.websocket_client=None
        self._session_token+=1; tok=self._session_token
        self._reset_audio_state(); self.interview_widget.set_language(self._language); self._refresh_pill()
        self.session_id=sid; self.is_connecting=True
        self._connect_btn.setEnabled(False); self._connect_btn.setText(self.t("connecting"))
        self._session_input.setEnabled(False); self.status_chip.set_state("validating")
        self.status_chip.lbl_main.setText(self.t("status_validating"))
        ws_url=f"{settings.WEBSOCKET_URL}/ws/interview/{sid}?lang={self._language}"
        self.websocket_client=WebSocketClient(ws_url)
        self.websocket_client.disconnected.connect(lambda c,r:self._on_ws_disconnected(c,r,tok))
        self.websocket_client.connected.connect(lambda:self._on_ws_connected(tok))
        self.websocket_client.message_received.connect(lambda d:self._on_ws_message(d,tok))
        self.websocket_client.error_occurred.connect(lambda e:self._on_ws_error(e,tok))
        self.websocket_client.connect_to_server(); self.statusBar().showMessage("Connexion…")

    def _is_active(self,tok): return tok==self._session_token
    def _on_ws_connected(self,tok):
        if not self._is_active(tok): return
        self.status_chip.set_state("validating"); self.status_chip.lbl_main.setText(self.t("status_validating"))
    def _on_ws_disconnected(self,code,reason,tok):
        if not self._is_active(tok): return
        if self.is_connecting: self._handle_conn_failure(reason or f"Code {code}"); return
        self._reset_audio_state(); self._reset_ui_for_new_session()
    def _on_ws_error(self,error,tok):
        if not self._is_active(tok): return
        self.statusBar().showMessage(f"Erreur:{error}")

    def _on_ws_message(self,data,tok):
        if not self._is_active(tok): return
        mt=data.get("type"); md=data.get("data",{})
        if mt=="error":
            err=md.get("message","Erreur")
            if md.get("error_type")=="SESSION_INVALID": self._handle_conn_failure(err)
            else: self._show_error(self.t("error_title"),err)
            return
        if mt=="question_loading":
            self.interview_widget.update_question(md.get("progress",{}))
            self.statusBar().showMessage(self.t("generating_audio"))
            self.video_player.set_speaking(); return
        if mt in ("welcome","welcome_back","question","interview_completed"):
            if md.get("audio_mode")=="chunked":
                self._pending_msg_type=mt; self._pending_msg_data=md
                self._audio_chunks=[]; self._audio_total_chunks=md.get("total_chunks",0)
                self._ensure_audio_format(md.get("sample_rate",_MF),md.get("channels",_MC),md.get("bits_per_sample",16))
                if mt=="question":
                    self.interview_widget.set_max_recording_seconds(md.get("max_duration",90))
                    self.interview_widget.enable_recording(False)
                return
            ab=md.get("audio_data")
            if ab: self._play_bytes_direct(base64.b64decode(ab))
            self._finalize_msg(mt,md); return
        if mt=="audio_chunk_data": self._audio_chunks.append(md.get("data","")); return
        if mt=="audio_chunk_end":
            if self._audio_chunks:
                try: self._play_pcm(b"".join(base64.b64decode(c) for c in self._audio_chunks))
                except Exception as e: logger.error(e); self.interview_widget.enable_recording(True)
            else: self.interview_widget.enable_recording(True)
            self._finalize_msg(self._pending_msg_type,self._pending_msg_data)
            self._audio_chunks=[]; self._pending_msg_type=""; self._pending_msg_data={}; return
        if mt=="answer_saved":
            self.statusBar().showMessage(self.t("answer_saved"))
            self.video_player.set_idle(); self.status_chip.set_state("connected"); return
        if mt=="answer_evaluated": self.statusBar().showMessage(self.t("answer_saved")); return

    def _finalize_msg(self,mt,md):
        if mt=="welcome": self._on_session_started(md)
        elif mt=="welcome_back":
            self.is_connecting=False
            self.status_chip.lbl_main.setText(self.t("status_connected"))
            self.status_chip.lbl_detail.setText(self.t("vocal_mode_active"))
            self.status_chip.set_state("connected")
            self.stacked.setVisible(False); self.interview_container.setVisible(True)
            if not self.audio_recorder:
                self.audio_recorder=AudioRecorder(); self.audio_recorder.audio_chunk_ready.connect(self._on_audio_chunk)
            idx=md.get("current_question_index",0); total=md.get("total_questions",0)
            if total>0: self.interview_widget.update_question({"current":idx+1,"total":total,"percentage":int((idx+1)/total*100)})
            self.video_player.set_speaking(); self.statusBar().showMessage(self.t("welcome_back_status"))
            if self._camera_available and self._facial_enabled: self.video_player.camera_preview.show(); self.video_player.camera_preview.reposition()
        elif mt=="question":
            self.interview_widget.set_max_recording_seconds(md.get("max_duration",90))
            self.interview_widget.update_question(md.get("progress",{}))
            self.interview_widget.set_audio_playing(); self.video_player.set_speaking()
            self.statusBar().showMessage(self.t("question_status"))
        elif mt=="interview_completed":
            if self._video_collector and self._video_collector.is_capturing: self._video_collector.stop_capture()
            self._show_info(self.t("interview_complete"),self.t("thanks_message"))
            self.statusBar().showMessage("✓ Terminé"); self._reset_audio_state(); self._reset_ui_for_new_session()

    def _on_session_started(self,md):
        self.is_connecting=False
        self.status_chip.lbl_main.setText(self.t("status_connected"))
        self.status_chip.lbl_detail.setText(self.t("vocal_mode_active"))
        self.status_chip.set_state("connected")
        self.stacked.setVisible(False); self.interview_container.setVisible(True)
        if not self.audio_recorder:
            self.audio_recorder=AudioRecorder(); self.audio_recorder.audio_chunk_ready.connect(self._on_audio_chunk)
        self.video_player.set_speaking(); self.statusBar().showMessage(self.t("welcome_status"))
        if self._camera_available and self._facial_enabled: self.video_player.camera_preview.show(); self.video_player.camera_preview.reposition()

    def _play_pcm(self,pcm):
        try:
            if self.audio_check_timer: self.audio_check_timer.stop(); self.audio_check_timer=None
            try: pygame.mixer.music.stop(); pygame.mixer.music.unload()
            except Exception: pass
            self._cleanup_tmp()
            tmp=tempfile.NamedTemporaryFile(suffix=".wav",delete=False)
            self._tmp_audio_path=tmp.name; tmp.close()
            sr=self._audio_sample_rate if self._audio_sample_rate>0 else _MF
            ch=self._audio_channels if self._audio_channels>0 else _MC
            bits=self._audio_bits if self._audio_bits>0 else 16
            with wave.open(self._tmp_audio_path,"wb") as wf:
                wf.setnchannels(ch); wf.setsampwidth(bits//8); wf.setframerate(sr); wf.writeframes(pcm)
            bps=sr*ch*(bits//8)
            self._audio_min_duration=max((len(pcm)/bps*1000) if bps>0 else 3000,800)*0.9
            self._audio_play_start=time.monotonic()*1000
            pygame.mixer.music.load(self._tmp_audio_path); pygame.mixer.music.play()
            self.audio_check_timer=QTimer(); self.audio_check_timer.timeout.connect(self._check_audio); self.audio_check_timer.start(200)
        except Exception as e: logger.error(f"pcm:{e}"); self._cleanup_tmp(); self.interview_widget.enable_recording(True)

    def _check_audio(self):
        if (time.monotonic()*1000-self._audio_play_start)<self._audio_min_duration: return
        if not pygame.mixer.music.get_busy():
            if self.audio_check_timer: self.audio_check_timer.stop(); self.audio_check_timer=None
            try: pygame.mixer.music.unload()
            except Exception: pass
            self._cleanup_tmp(); self.video_player.set_idle()
            if self.websocket_client: self.websocket_client.send_message({"type":"audio_finished"})
            self.interview_widget.enable_recording(True); self.statusBar().showMessage(self.t("answer_status"))

    def _play_bytes_direct(self,audio):
        if audio[:4]==b"RIFF":
            import struct
            fi=audio.find(b"fmt ",12); di=audio.find(b"data",12)
            if fi!=-1 and di!=-1:
                self._ensure_audio_format(struct.unpack_from("<I",audio,fi+12)[0],struct.unpack_from("<H",audio,fi+10)[0],struct.unpack_from("<H",audio,fi+22)[0])
                self._play_pcm(audio[di+8:]); return
        self._play_pcm(audio)

    def _on_start_recording(self):
        if self.audio_recorder: self.audio_recorder.start_recording(); self.video_player.set_listening(); self.statusBar().showMessage("● Enregistrement…")
        if self._video_collector and self._facial_enabled and self._camera_available and not self._video_collector.is_capturing:
            if self._video_collector.start_capture(): logger.info("Capture vidéo OK")
        self.video_player.camera_preview.set_recording(True)

    def _on_stop_recording(self):
        if self.audio_recorder: self.audio_recorder.stop_recording()
        if self._video_collector and self._video_collector.is_capturing: self._video_collector.stop_capture()
        self.video_player.camera_preview.set_recording(False)
        if self.websocket_client: self.websocket_client.send_message({"type":"answer_complete"})
        self.video_player.set_idle(); self.interview_widget.enable_recording(False)

    def _on_audio_chunk(self,audio_data):
        if self.websocket_client: self.websocket_client.send_message({"type":"audio_chunk","audio_data":base64.b64encode(audio_data).decode()})

    def _on_end_interview(self):
        r=QMessageBox.question(self,self.t("end_title"),self.t("end_confirm"),QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)
        if r==QMessageBox.StandardButton.Yes and self.websocket_client:
            if self._video_collector and self._video_collector.is_capturing: self._video_collector.stop_capture()
            self.websocket_client.send_message({"type":"end_interview"})

    def _handle_conn_failure(self,msg):
        self.is_connecting=False; self._reset_audio_state()
        self._connect_btn.setEnabled(True); self._connect_btn.setText(f"{self.t('start_btn')}  →")
        self._session_input.setEnabled(True); self.status_chip.set_state("error")
        self.status_chip.lbl_main.setText(self.t("status_disconnected"))
        if self.websocket_client:
            try:
                self.websocket_client.disconnected.disconnect(); self.websocket_client.connected.disconnect()
                self.websocket_client.message_received.disconnect(); self.websocket_client.error_occurred.disconnect()
            except Exception: pass
            try: self.websocket_client.disconnect_from_server()
            except Exception: pass
            self.websocket_client=None
        self._show_error(self.t("error_title"),msg)

    def _show_error(self,title,msg):
        b=QMessageBox(self); b.setIcon(QMessageBox.Icon.Critical); b.setWindowTitle(title); b.setText(msg); b.exec()
    def _show_info(self,title,msg):
        b=QMessageBox(self); b.setIcon(QMessageBox.Icon.Information); b.setWindowTitle(title); b.setText(msg); b.exec()

    def closeEvent(self,event):
        if self._video_collector: self._video_collector.cleanup()
        if self.websocket_client:
            try:
                self.websocket_client.disconnected.disconnect(); self.websocket_client.connected.disconnect()
                self.websocket_client.message_received.disconnect(); self.websocket_client.error_occurred.disconnect()
            except Exception: pass
            self.websocket_client.disconnect_from_server()
        if self.audio_recorder: self.audio_recorder.cleanup()
        if self.audio_check_timer: self.audio_check_timer.stop()
        try: pygame.mixer.music.stop(); pygame.mixer.music.unload()
        except Exception: pass
        self._cleanup_tmp()
        try: pygame.quit()
        except Exception: pass
        super().closeEvent(event)