from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QMessageBox, QLabel, QLineEdit, QPushButton, QFrame,
    QGraphicsDropShadowEffect, QStackedWidget
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor
import sys, os, base64, time, wave, tempfile, logging
from pathlib import Path
import pygame

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from client.ui.stark_theme import StarkTheme, T
from client.ui.icons import StarkIcons
from client.ui.video_player_widget import VideoPlayerWidget
from client.ui.interview_widget import InterviewWidget
from client.core.websocket_client import WebSocketClient
from client.core.audio_recorder import AudioRecorder
from client.core.video_recorder import VideoFrameCollector
from client.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── pygame init ───────────────────────────────────────────────────────────────
_MIXER_FREQUENCY = 22050
_MIXER_SIZE      = -16
_MIXER_CHANNELS  = 2
_MIXER_BUFFER    = 4096

pygame.mixer.pre_init(
    frequency=_MIXER_FREQUENCY, size=_MIXER_SIZE,
    channels=_MIXER_CHANNELS, buffer=_MIXER_BUFFER,
)
pygame.init()

# ── i18n ─────────────────────────────────────────────────────────────────────

UI_TEXTS = {
    "ar": {
        "app_title": "SparkHire AI", "app_subtitle": "مقابلة صوتية ذكية",
        "choose_language": "اختر لغة المقابلة",
        "choose_subtitle": "ستُجرى المقابلة بالكامل باللغة التي تختارها",
        "enter_session": "رمز الجلسة", "session_placeholder": "session_xxxxxxxxxxxxx",
        "start_btn": "بدء المقابلة", "connecting": "جارٍ الاتصال…",
        "status_disconnected": "غير متصل", "status_connected": "متصل",
        "status_validating": "التحقق…", "waiting_connection": "في انتظار الاتصال",
        "vocal_mode_active": "الوضع الصوتي نشط", "vocal_mode_label": "الوضع الصوتي",
        "welcome_status": "مرحباً", "question_status": "السؤال قيد التشغيل",
        "answer_status": "يمكنك الإجابة", "answer_saved": "تم حفظ الإجابة",
        "generating_audio": "توليد الصوت…", "end_confirm": "هل تريد إنهاء المقابلة؟",
        "interview_complete": "انتهت المقابلة", "thanks_message": "شكراً لك! انتهت المقابلة.",
        "format_error": "الصيغة المطلوبة: session_xxxxxxxxxxxxx",
        "error_title": "خطأ", "end_title": "إنهاء", "back_btn": "رجوع", "confirm_btn": "تأكيد",
        "welcome_back_status": "مرحباً بعودتك — نستأنف المقابلة",
        "camera_ok": "الكاميرا نشطة", "camera_off": "الكاميرا غير متوفرة",
    },
    "fr": {
        "app_title": "SparkHire AI", "app_subtitle": "Entretien vocal intelligent",
        "choose_language": "Choisissez votre langue",
        "choose_subtitle": "L'entretien se déroulera intégralement dans la langue sélectionnée",
        "enter_session": "Identifiant de session", "session_placeholder": "session_xxxxxxxxxxxxx",
        "start_btn": "Démarrer l'entretien", "connecting": "Connexion en cours…",
        "status_disconnected": "Déconnecté", "status_connected": "Connecté",
        "status_validating": "Validation…", "waiting_connection": "En attente",
        "vocal_mode_active": "Mode vocal actif", "vocal_mode_label": "SparkHire AI",
        "welcome_status": "Bienvenue — écoutez le message",
        "question_status": "Question en lecture",
        "answer_status": "Vous pouvez répondre", "answer_saved": "Réponse enregistrée",
        "generating_audio": "Génération audio…", "end_confirm": "Confirmer la fin de l'entretien ?",
        "interview_complete": "Entretien terminé", "thanks_message": "Merci ! L'entretien est terminé.",
        "format_error": "Format attendu : session_xxxxxxxxxxxxx",
        "error_title": "Erreur", "end_title": "Terminer", "back_btn": "Retour", "confirm_btn": "Confirmer",
        "welcome_back_status": "Bon retour — reprise de l'entretien",
        "camera_ok": "Caméra active", "camera_off": "Caméra non disponible",
    },
    "en": {
        "app_title": "SparkHire AI", "app_subtitle": "AI-powered voice interview",
        "choose_language": "Choose your language",
        "choose_subtitle": "The entire interview will be conducted in the selected language",
        "enter_session": "Session identifier", "session_placeholder": "session_xxxxxxxxxxxxx",
        "start_btn": "Start interview", "connecting": "Connecting…",
        "status_disconnected": "Disconnected", "status_connected": "Connected",
        "status_validating": "Validating…", "waiting_connection": "Waiting",
        "vocal_mode_active": "Vocal mode active", "vocal_mode_label": "SparkHire AI",
        "welcome_status": "Welcome — listen to greeting",
        "question_status": "Question playing",
        "answer_status": "You may answer", "answer_saved": "Answer saved",
        "generating_audio": "Generating audio…", "end_confirm": "Confirm end of interview?",
        "interview_complete": "Interview complete", "thanks_message": "Thank you! The interview is complete.",
        "format_error": "Expected: session_xxxxxxxxxxxxx",
        "error_title": "Error", "end_title": "End Interview", "back_btn": "Back", "confirm_btn": "Confirm",
        "welcome_back_status": "Welcome back — resuming interview",
        "camera_ok": "Camera active", "camera_off": "Camera unavailable",
    },
}

LANGUAGES = [
    {"code": "ar", "flag": "🇸🇦", "name": "العربية",  "native": "Arabic",  "color": T.TEAL_600,  "bg": T.TEAL_50,   "border": T.TEAL_200},
    {"code": "fr", "flag": "🇫🇷", "name": "Français", "native": "French",  "color": T.TEAL_700,  "bg": T.TEAL_100,  "border": T.TEAL_200},
    {"code": "en", "flag": "🇬🇧", "name": "English",  "native": "English", "color": T.CORAL_600, "bg": T.CORAL_100, "border": T.CORAL_200},
]


# ── Utility helpers ───────────────────────────────────────────────────────────

def _shadow(blur=20, dy=4, alpha=20, r=79, g=70, b=229):
    s = QGraphicsDropShadowEffect()
    s.setBlurRadius(blur); s.setOffset(0, dy)
    s.setColor(QColor(r, g, b, alpha)); return s

def _soft_shadow(blur=24, dy=6, alpha=18):
    """Soft neutral shadow — no color tint."""
    s = QGraphicsDropShadowEffect()
    s.setBlurRadius(blur); s.setOffset(0, dy)
    s.setColor(QColor(0, 0, 0, alpha)); return s

def _label(text, size=T.FS_BASE, bold=False, color=T.TEXT_700):
    lbl = QLabel(text)
    f = QFont(T.FONT, size); f.setBold(bold)
    lbl.setFont(f)
    lbl.setStyleSheet(f"color: {color}; background: transparent;")
    return lbl

def _divider():
    d = QFrame(); d.setFrameShape(QFrame.Shape.HLine); d.setFixedHeight(1)
    d.setStyleSheet(f"background: {T.BORDER}; border: none;"); return d


# ── Language Card ─────────────────────────────────────────────────────────────

class LanguageCard(QFrame):
    def __init__(self, data, on_select, parent=None):
        super().__init__(parent)
        self._data     = data
        self._on_select = on_select
        self._selected  = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(210, 220)
        self._build()
        self._refresh()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.setSpacing(T.SP_3)
        lay.setContentsMargins(T.SP_5, T.SP_6, T.SP_5, T.SP_5)

        # Flag bubble — clean circle
        flag_wrap = QFrame()
        flag_wrap.setFixedSize(80, 80)
        flag_wrap.setStyleSheet(f"""
            QFrame {{
                background: {T.BG_PAGE};
                border: none;
                border-radius: 40px;
            }}
        """)
        flag_inner = QVBoxLayout(flag_wrap)
        flag_inner.setContentsMargins(0, 0, 0, 0)
        flag_inner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        flag = QLabel(self._data["flag"])
        flag.setFont(QFont("Segoe UI Emoji, Apple Color Emoji, Noto Color Emoji", 36))
        flag.setAlignment(Qt.AlignmentFlag.AlignCenter)
        flag.setStyleSheet("background: transparent;")
        flag_inner.addWidget(flag)
        lay.addWidget(flag_wrap, alignment=Qt.AlignmentFlag.AlignCenter)

        # Language name — strong weight
        name = _label(self._data["name"], T.FS_LG, True, T.TEXT_900)
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(name)

        # Native tag — soft pill
        tag = QLabel(self._data["native"])
        tag.setFont(QFont(T.FONT, T.FS_SM))
        tag.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tag.setStyleSheet(f"""
            color: {T.TEXT_500};
            background: {T.BG_PAGE};
            border-radius: {T.R_FULL}px;
            padding: 3px 12px;
        """)
        lay.addWidget(tag, alignment=Qt.AlignmentFlag.AlignCenter)

    def _refresh(self):
        c = self._data
        if self._selected:
            self.setStyleSheet(f"""
                LanguageCard {{
                    background: {T.BG_CARD};
                    border: 2px solid {c['color']};
                    border-radius: {T.R_XL}px;
                }}
            """)
            # Soft indigo glow when selected
            eff = _shadow(40, 10, 45, *self._hex_rgb(c['color']))
            self.setGraphicsEffect(eff)
        else:
            self.setStyleSheet(f"""
                LanguageCard {{
                    background: {T.BG_CARD};
                    border: 1px solid {T.BORDER};
                    border-radius: {T.R_XL}px;
                }}
                LanguageCard:hover {{
                    background: {T.BG_HOVER};
                    border-color: {T.BORDER_HOVER};
                }}
            """)
            self.setGraphicsEffect(_soft_shadow(16, 4, 10))

    @staticmethod
    def _hex_rgb(h):
        h = h.lstrip("#")
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

    def set_selected(self, v):
        self._selected = v; self._refresh()

    def mousePressEvent(self, e):
        self._on_select(self._data["code"]); super().mousePressEvent(e)


# ── Status Chip ───────────────────────────────────────────────────────────────

class StatusChip(QFrame):
    """Connection status indicator — clean pill."""

    STATES = {
        "disconnected": (T.TEXT_400,    "●", T.BG_PAGE,  T.BORDER,     T.TEXT_500),
        "validating":   (T.AMBER_500,   "◌", T.AMBER_50, T.AMBER_200,  T.AMBER_600),
        "connected":    (T.TEAL_500,    "●", T.TEAL_50,  T.TEAL_200,   T.TEAL_700),
        "error":        (T.RED_500,     "●", T.RED_50,   T.RED_200,    T.RED_600),
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(36)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 0, 16, 0)
        lay.setSpacing(8)

        self._dot = QLabel("●")
        f = QFont(T.FONT, 8); self._dot.setFont(f)
        lay.addWidget(self._dot)

        col = QVBoxLayout(); col.setSpacing(0)
        self.lbl_main = QLabel("Déconnecté")
        f2 = QFont(T.FONT, T.FS_SM); f2.setBold(True)
        self.lbl_main.setFont(f2)

        self.lbl_detail = QLabel("En attente")
        f3 = QFont(T.FONT, T.FS_2XS)
        self.lbl_detail.setFont(f3)
        self.lbl_detail.setStyleSheet(f"color: {T.TEXT_400}; background: transparent;")

        col.addWidget(self.lbl_main)
        col.addWidget(self.lbl_detail)
        lay.addLayout(col)
        self.set_state("disconnected")

    def set_state(self, state):
        dot_c, dot_txt, bg, border, text_c = self.STATES.get(state, self.STATES["disconnected"])
        self._dot.setText(dot_txt)
        self._dot.setStyleSheet(f"color: {dot_c}; background: transparent;")
        self.lbl_main.setStyleSheet(f"color: {text_c}; font-weight: 600; background: transparent;")
        self.setStyleSheet(f"""
            QFrame {{
                background: {bg};
                border: none;
                border-radius: {T.R_FULL}px;
            }}
        """)


# ═════════════════════════════════════════════════════════════════════════════
#  MAIN WINDOW
# ═════════════════════════════════════════════════════════════════════════════

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.websocket_client = None
        self.audio_recorder   = None
        self.session_id       = None
        self.is_connecting    = False
        self._session_token   = 0
        self._language        = "fr"
        self._lang_cards: dict = {}

        # Audio state
        self._tmp_audio_path     = None
        self._audio_play_start   = 0.0
        self._audio_min_duration = 0.0
        self.audio_check_timer   = None
        self._audio_sample_rate  = -1
        self._audio_channels     = -1
        self._audio_bits         = -1
        self._pending_msg_type   = ""
        self._pending_msg_data   = {}
        self._audio_chunks: list = []
        self._audio_total_chunks = 0

        # Video state
        self._video_collector: VideoFrameCollector | None = None
        self._facial_enabled: bool = getattr(settings, "FACIAL_ANALYSIS_ENABLED", True)
        self._camera_available: bool = False
        self._camera_lbl: QLabel | None = None

        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init(
                    frequency=_MIXER_FREQUENCY, size=_MIXER_SIZE,
                    channels=_MIXER_CHANNELS, buffer=_MIXER_BUFFER,
                )
            except Exception as e:
                logger.error(f"pygame mixer init: {e}")

        self._init_video_collector()
        self._setup_ui()

    # ── Video collector ───────────────────────────────────────────

    def _init_video_collector(self):
        if not self._facial_enabled:
            return
        fps = getattr(settings, "FACIAL_CAPTURE_FPS", 2.0)
        self._video_collector = VideoFrameCollector(
            camera_index=0, target_fps=fps, jpeg_quality=70, max_width=640,
        )
        self._video_collector.camera_ready.connect(self._on_camera_ready)
        self._video_collector.camera_error.connect(self._on_camera_error)
        self._video_collector.frame_captured.connect(self._on_video_frame)
        available = self._video_collector.is_camera_available(0)
        self._camera_available = available

    def _update_camera_indicator(self, available: bool):
        if self._camera_lbl is None:
            return
        if not self._facial_enabled:
            self._camera_lbl.setVisible(False)
            return
        if available:
            self._camera_lbl.setText("🎥")
            self._camera_lbl.setToolTip(self.t("camera_ok"))
            self._camera_lbl.setStyleSheet(f"color: {T.GREEN_600}; background: transparent; font-size: 15px;")
        else:
            self._camera_lbl.setText("⚠️")
            self._camera_lbl.setToolTip(self.t("camera_off"))
            self._camera_lbl.setStyleSheet(f"color: {T.AMBER_500}; background: transparent; font-size: 15px;")

    def _on_camera_ready(self, ok: bool):
        self._camera_available = ok
        self._update_camera_indicator(ok)
        if ok and self._facial_enabled:
            self.video_player.camera_preview.show()
            self.video_player.camera_preview.reposition()
        else:
            self.video_player.camera_preview.set_camera_unavailable()

    def _on_camera_error(self, msg: str):
        logger.warning(f"Caméra: {msg}")
        self._camera_available = False
        self._update_camera_indicator(False)

    def _on_video_frame(self, jpeg_bytes: bytes):
        self.video_player.camera_preview.on_frame(jpeg_bytes)
        if not self.websocket_client:
            return
        try:
            b64 = base64.b64encode(jpeg_bytes).decode()
            self.websocket_client.send_message({"type": "video_frame", "data": {"frame": b64}})
        except Exception as e:
            logger.debug(f"Frame vidéo: {e}")

    def t(self, key, **kwargs):
        tpl = UI_TEXTS.get(self._language, UI_TEXTS["fr"]).get(key, key)
        return tpl.format(**kwargs) if kwargs else tpl

    # ═══════════════════════════════════════════════════════════
    #  UI BUILD
    # ═══════════════════════════════════════════════════════════

    def _setup_ui(self):
        self.setWindowTitle("SparkHire AI — Intelligent Voice Interview")
        self.showMaximized()

        root_w = QWidget()
        root_w.setObjectName("appRoot")
        root_w.setStyleSheet(f"""
            #appRoot {{
                background: {T.BG_PAGE};
            }}
        """)
        self.setCentralWidget(root_w)
        self.setStyleSheet(StarkTheme.global_stylesheet())

        root = QVBoxLayout(root_w)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_header())

        self.stacked = QStackedWidget()
        self.stacked.addWidget(self._build_language_screen())
        self.stacked.addWidget(self._build_session_screen())
        root.addWidget(self.stacked, stretch=1)

        self.interview_container = self._build_interview_container()
        self.interview_container.setVisible(False)
        root.addWidget(self.interview_container, stretch=1)

        self._setup_statusbar()

    def _build_header(self) -> QFrame:
        hdr = QFrame()
        hdr.setObjectName("mainHeader")
        hdr.setFixedHeight(68)
        hdr.setStyleSheet(f"""
            #mainHeader {{
                background: {T.BG_CARD};
                border-bottom: 1.5px solid {T.BORDER};
            }}
        """)

        lay = QHBoxLayout(hdr)
        lay.setContentsMargins(28, 0, 24, 0)
        lay.setSpacing(0)

        # Logo — image depuis assets/, fallback gradient si absent
        from PySide6.QtGui import QPixmap
        _logo_path = Path(__file__).resolve().parent.parent.parent / "assets" / "pictures" / "logo.jpg"
        logo = QLabel()
        logo.setFixedSize(36, 36)
        if _logo_path.exists():
            _pix = QPixmap(str(_logo_path)).scaled(
                36, 36,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            logo.setPixmap(_pix)
            logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            logo.setStyleSheet("background: transparent;")
        else:
            # Fallback : gradient teal avec ⚡
            logo = QFrame()
            logo.setFixedSize(36, 36)
            logo.setStyleSheet(f"""
                QFrame {{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                        stop:0 {T.TEAL_400},stop:1 {T.TEAL_700});
                    border-radius: 10px;
                }}
            """)
            _fl = QVBoxLayout(logo)
            _fl.setContentsMargins(0, 0, 0, 0)
            _fl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            _sp = QLabel("⚡")
            _sp.setFont(QFont("Segoe UI Emoji", 16))
            _sp.setAlignment(Qt.AlignmentFlag.AlignCenter)
            _fl.addWidget(_sp)
        logo.setGraphicsEffect(_shadow(16, 3, 30))

        lay.addWidget(logo)
        lay.addSpacing(12)

        # Title
        title_col = QVBoxLayout()
        title_col.setSpacing(1)

        t1 = QLabel("SparkHire")
        f1 = QFont(T.FONT, T.FS_LG)
        f1.setBold(True)
        t1.setFont(f1)
        t1.setStyleSheet(f"""
            color: {T.TEAL_700};
            background: transparent;
            letter-spacing: -0.5px;
        """)

        t2 = QLabel("AI")
        f2 = QFont(T.FONT, T.FS_LG)
        f2.setBold(True)
        t2.setFont(f2)
        t2.setStyleSheet(f"color: {T.CORAL_500}; background: transparent;")

        # Combined on one row
        title_row = QHBoxLayout()
        title_row.setSpacing(4)
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.addWidget(t1)
        title_row.addWidget(t2)
        title_row.addStretch()

        self._header_subtitle = QLabel(self.t("app_subtitle"))
        self._header_subtitle.setFont(QFont(T.FONT_BODY, T.FS_XS))
        self._header_subtitle.setStyleSheet(f"color: {T.TEXT_400}; background: transparent; letter-spacing: 0.3px;")

        title_col.addLayout(title_row)
        title_col.addWidget(self._header_subtitle)
        lay.addLayout(title_col)

        lay.addStretch()

        # Camera indicator
        self._camera_lbl = QLabel("")
        self._camera_lbl.setFont(QFont("Segoe UI Emoji", 14))
        self._camera_lbl.setStyleSheet("background: transparent;")
        self._camera_lbl.setVisible(self._facial_enabled)
        self._update_camera_indicator(self._camera_available)
        lay.addWidget(self._camera_lbl)
        lay.addSpacing(12)

        # Separator
        sep = QFrame()
        sep.setFixedSize(1, 24)
        sep.setStyleSheet(f"background: {T.BORDER_HOVER}; border: none; opacity: 0.5;")
        lay.addWidget(sep)
        lay.addSpacing(12)

        self.status_chip = StatusChip()
        lay.addWidget(self.status_chip)

        return hdr

    # ── Language selection screen ─────────────────────────────────

    def _build_language_screen(self) -> QWidget:
        pg = QWidget()
        root = QVBoxLayout(pg)
        root.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.setContentsMargins(T.SP_10, T.SP_8, T.SP_10, T.SP_8)
        root.setSpacing(0)

        # Eyebrow tag
        tag_row = QHBoxLayout()
        tag_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tag = QLabel("SÉLECTION DE LA LANGUE")
        tag.setFont(QFont(T.FONT, T.FS_2XS))
        tag.setStyleSheet(f"""
            color: {T.TEAL_700};
            background: {T.TEAL_50};
            border: none;
            border-radius: {T.R_FULL}px;
            padding: 4px 14px;
            letter-spacing: 2.5px;
            font-weight: 700;
        """)
        tag_row.addWidget(tag)
        root.addLayout(tag_row)
        root.addSpacing(T.SP_5)

        # Heading
        h1 = QLabel(self.t("choose_language"))
        f_h1 = QFont(T.FONT, T.FS_3XL)
        f_h1.setBold(True)
        h1.setFont(f_h1)
        h1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        h1.setStyleSheet(f"color: {T.TEXT_900}; background: transparent; letter-spacing: -0.5px;")
        root.addWidget(h1)
        root.addSpacing(T.SP_2)

        # Subtitle
        sub = QLabel(self.t("choose_subtitle"))
        sub.setFont(QFont(T.FONT_BODY, T.FS_MD))
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet(f"color: {T.TEXT_500}; background: transparent;")
        root.addWidget(sub)
        root.addSpacing(T.SP_10)

        # Language cards
        cards_row = QHBoxLayout()
        cards_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cards_row.setSpacing(24)
        self._lang_cards = {}
        for ld in LANGUAGES:
            card = LanguageCard(ld, self._on_lang_select)
            self._lang_cards[ld["code"]] = card
            cards_row.addWidget(card)
        root.addLayout(cards_row)
        root.addSpacing(T.SP_10)

        # Confirm button
        self._confirm_btn = QPushButton("Continuer  →")
        f_btn = QFont(T.FONT, T.FS_MD)
        f_btn.setBold(True)
        self._confirm_btn.setFont(f_btn)
        self._confirm_btn.setFixedSize(260, 56)
        self._confirm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._confirm_btn.setStyleSheet(StarkTheme.get_button_style("primary"))
        eff = _shadow(28, 8, 55)
        self._confirm_btn.setGraphicsEffect(eff)
        self._confirm_btn.clicked.connect(self._on_lang_confirmed)

        btn_row = QHBoxLayout()
        btn_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btn_row.addWidget(self._confirm_btn)
        root.addLayout(btn_row)

        self._on_lang_select("fr")
        return pg

    def _on_lang_select(self, code: str):
        self._language = code
        for c, card in self._lang_cards.items():
            card.set_selected(c == code)
        if hasattr(self, "_confirm_btn"):
            ld = next(l for l in LANGUAGES if l["code"] == code)
            self._confirm_btn.setText(f"Continuer en {ld['name']}  →")

    def _on_lang_confirmed(self):
        self._sync_texts()
        self.stacked.setCurrentIndex(1)

    # ── Session entry screen ──────────────────────────────────────

    def _build_session_screen(self) -> QWidget:
        outer = QWidget()
        outer_lay = QVBoxLayout(outer)
        outer_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer_lay.setContentsMargins(0, 0, 0, 0)

        # ── Main card ─────────────────────────────────────────────
        card = QFrame()
        card.setFixedWidth(500)
        card.setStyleSheet(f"""
            QFrame {{
                background: {T.BG_CARD};
                border: none;
                border-radius: 26px;
            }}
        """)
        card.setGraphicsEffect(_shadow(60, 16, 22))

        lay = QVBoxLayout(card)
        lay.setContentsMargins(T.SP_10, T.SP_10, T.SP_10, T.SP_10)
        lay.setSpacing(0)

        # Icon
        icon_frame = QFrame()
        icon_frame.setFixedSize(72, 72)
        icon_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 {T.TEAL_400},stop:1 {T.TEAL_700});
                border-radius: 20px;
            }}
        """)
        icon_frame.setGraphicsEffect(_shadow(20, 5, 70))
        icon_inner = QVBoxLayout(icon_frame)
        icon_inner.setContentsMargins(0, 0, 0, 0)
        icon_inner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        key_e = QLabel("🔐")
        key_e.setFont(QFont("Segoe UI Emoji, Apple Color Emoji", 28))
        key_e.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_inner.addWidget(key_e)

        icon_row = QHBoxLayout()
        icon_row.addStretch()
        icon_row.addWidget(icon_frame)
        icon_row.addStretch()
        lay.addLayout(icon_row)
        lay.addSpacing(T.SP_5)

        # Title
        self._session_title = _label(self.t("enter_session"), T.FS_2XL, True, T.TEXT_900)
        self._session_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self._session_title)
        lay.addSpacing(T.SP_2)

        # Language pill
        pill_row = QHBoxLayout()
        pill_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lang_pill = QFrame()
        self._lang_pill.setFixedHeight(30)
        pill_inner = QHBoxLayout(self._lang_pill)
        pill_inner.setContentsMargins(14, 0, 14, 0)
        pill_inner.setSpacing(6)
        self._pill_lbl = QLabel()
        f_pill = QFont(T.FONT, T.FS_XS); f_pill.setBold(True)
        self._pill_lbl.setFont(f_pill)
        self._pill_lbl.setStyleSheet(f"color: {T.TEAL_700}; background: transparent; letter-spacing: 0.3px;")
        pill_inner.addWidget(self._pill_lbl)
        self._lang_pill.setStyleSheet(f"""
            QFrame {{
                background: {T.TEAL_50};
                border: none;
                border-radius: {T.R_FULL}px;
            }}
        """)
        pill_row.addWidget(self._lang_pill)
        lay.addLayout(pill_row)
        self._refresh_pill()
        lay.addSpacing(T.SP_6)

        # Separator
        lay.addWidget(_divider())
        lay.addSpacing(T.SP_6)

        # Input
        self._session_input = QLineEdit()
        self._session_input.setPlaceholderText(self.t("session_placeholder"))
        self._session_input.setFont(QFont(T.FONT_MONO, T.FS_MD))
        self._session_input.setMinimumHeight(52)
        self._session_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._session_input.setStyleSheet(StarkTheme.input_style())
        lay.addWidget(self._session_input)
        lay.addSpacing(T.SP_4)

        # Connect button
        self._connect_btn = QPushButton(self.t("start_btn"))
        f_conn = QFont(T.FONT, T.FS_MD); f_conn.setBold(True)
        self._connect_btn.setFont(f_conn)
        self._connect_btn.setMinimumHeight(58)
        self._connect_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._connect_btn.setStyleSheet(StarkTheme.get_button_style("accent"))
        self._connect_btn.setGraphicsEffect(_shadow(26, 8, 45, 13, 148, 136))
        self._connect_btn.clicked.connect(self._connect_to_interview)
        lay.addWidget(self._connect_btn)
        lay.addSpacing(T.SP_3)

        # Back button
        self._back_btn = QPushButton(f"← {self.t('back_btn')}")
        self._back_btn.setFont(QFont(T.FONT, T.FS_SM))
        self._back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._back_btn.setStyleSheet(StarkTheme.get_button_style("ghost"))
        self._back_btn.clicked.connect(lambda: self.stacked.setCurrentIndex(0))
        lay.addWidget(self._back_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        outer_lay.addWidget(card)
        return outer

    def _refresh_pill(self):
        ld = next((l for l in LANGUAGES if l["code"] == self._language), None)
        if ld and hasattr(self, "_pill_lbl"):
            self._pill_lbl.setText(f"{ld['flag']}  {ld['name']}")

    # ── Interview container ───────────────────────────────────────

    def _build_interview_container(self) -> QWidget:
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(T.SP_4, T.SP_4, T.SP_4, T.SP_4)
        lay.setSpacing(T.SP_4)

        self.video_player = VideoPlayerWidget()
        lay.addWidget(self.video_player, stretch=2)

        right_panel = QWidget()
        right_panel.setMaximumWidth(440)
        right_panel.setMinimumWidth(320)
        right_lay = QVBoxLayout(right_panel)
        right_lay.setContentsMargins(0, 0, 0, 0)
        right_lay.setSpacing(0)

        self.interview_widget = InterviewWidget(language=self._language)
        self.interview_widget.start_recording.connect(self._on_start_recording)
        self.interview_widget.stop_recording.connect(self._on_stop_recording)
        self.interview_widget.end_interview.connect(self._on_end_interview)
        right_lay.addWidget(self.interview_widget)

        lay.addWidget(right_panel, stretch=1)
        return w

    def _setup_statusbar(self):
        sb = self.statusBar()
        sb.setFixedHeight(26)
        sb.showMessage(self.t("vocal_mode_label"))

    def _sync_texts(self):
        self._header_subtitle.setText(self.t("app_subtitle"))
        self.status_chip.lbl_main.setText(self.t("status_disconnected"))
        self.status_chip.lbl_detail.setText(self.t("waiting_connection"))
        if hasattr(self, "_connect_btn"):
            self._connect_btn.setText(self.t("start_btn"))
        if hasattr(self, "_session_input"):
            self._session_input.setPlaceholderText(self.t("session_placeholder"))
        if hasattr(self, "_back_btn"):
            self._back_btn.setText(f"← {self.t('back_btn')}")
        if hasattr(self, "_session_title"):
            self._session_title.setText(self.t("enter_session"))
        if hasattr(self, "interview_widget"):
            self.interview_widget.set_language(self._language)
        self.statusBar().showMessage(self.t("vocal_mode_label"))
        self._refresh_pill()
        self._update_camera_indicator(self._camera_available)

    # ══════════════════════════════════════════════════════════════
    #  AUDIO
    # ══════════════════════════════════════════════════════════════

    def _ensure_audio_format(self, sr, ch, bits):
        sr   = sr   if sr   > 0 else _MIXER_FREQUENCY
        ch   = ch   if ch   > 0 else _MIXER_CHANNELS
        bits = bits if bits > 0 else 16
        if sr == self._audio_sample_rate and ch == self._audio_channels and bits == self._audio_bits:
            return
        try:
            pygame.mixer.music.stop(); pygame.mixer.music.unload()
        except Exception:
            pass
        try:
            pygame.mixer.quit()
            pygame.mixer.init(frequency=sr, size=-bits, channels=ch, buffer=4096)
            self._audio_sample_rate, self._audio_channels, self._audio_bits = sr, ch, bits
        except Exception as e:
            logger.error(f"pygame mixer: {e}")
            try:
                pygame.mixer.init(frequency=_MIXER_FREQUENCY, size=_MIXER_SIZE,
                                  channels=_MIXER_CHANNELS, buffer=_MIXER_BUFFER)
                self._audio_sample_rate = _MIXER_FREQUENCY
                self._audio_channels    = _MIXER_CHANNELS
                self._audio_bits        = 16
            except Exception as e2:
                logger.error(f"pygame fallback: {e2}")

    def _reset_audio_state(self):
        if self.audio_check_timer:
            self.audio_check_timer.stop(); self.audio_check_timer = None
        try: pygame.mixer.music.stop(); pygame.mixer.music.unload()
        except Exception: pass
        self._cleanup_tmp_file()
        self._audio_play_start = self._audio_min_duration = 0.0
        self._audio_sample_rate = self._audio_channels = self._audio_bits = -1
        self._audio_chunks = []; self._audio_total_chunks = 0
        self._pending_msg_type = ""; self._pending_msg_data = {}

    def _cleanup_tmp_file(self):
        if self._tmp_audio_path:
            try: os.unlink(self._tmp_audio_path)
            except Exception: pass
            self._tmp_audio_path = None

    def _reset_ui_for_new_session(self):
        if self._video_collector and self._video_collector.is_capturing:
            self._video_collector.stop_capture()
        self.video_player.camera_preview.hide()
        self.video_player.camera_preview.set_recording(False)
        self.stacked.setVisible(True); self.stacked.setCurrentIndex(0)
        self.interview_container.setVisible(False)
        self._connect_btn.setEnabled(True); self._connect_btn.setText(self.t("start_btn"))
        self._session_input.setEnabled(True); self._session_input.clear()
        self.status_chip.lbl_main.setText(self.t("status_disconnected"))
        self.status_chip.set_state("disconnected")
        self.statusBar().showMessage(self.t("vocal_mode_label"))
        if self.audio_recorder:
            try: self.audio_recorder.cleanup()
            except Exception: pass
            self.audio_recorder = None

    # ══════════════════════════════════════════════════════════════
    #  CONNECTION
    # ══════════════════════════════════════════════════════════════

    def _connect_to_interview(self):
        if self.is_connecting: return
        session_id = self._session_input.text().strip()
        if not session_id or not session_id.startswith("session_"):
            self._show_error(self.t("error_title"), self.t("format_error")); return

        if self.websocket_client:
            try:
                self.websocket_client.disconnected.disconnect()
                self.websocket_client.connected.disconnect()
                self.websocket_client.message_received.disconnect()
                self.websocket_client.error_occurred.disconnect()
            except Exception: pass
            try: self.websocket_client.disconnect_from_server()
            except Exception: pass
            self.websocket_client = None

        self._session_token += 1
        tok = self._session_token
        self._reset_audio_state()
        self.interview_widget.set_language(self._language)
        self._refresh_pill()

        self.session_id = session_id
        self.is_connecting = True
        self._connect_btn.setEnabled(False); self._connect_btn.setText(self.t("connecting"))
        self._session_input.setEnabled(False)
        self.status_chip.set_state("validating")
        self.status_chip.lbl_main.setText(self.t("status_validating"))

        ws_url = f"{settings.WEBSOCKET_URL}/ws/interview/{session_id}?lang={self._language}"
        self.websocket_client = WebSocketClient(ws_url)
        self.websocket_client.disconnected.connect(lambda c, r: self._on_ws_disconnected(c, r, tok))
        self.websocket_client.connected.connect(lambda: self._on_ws_connected(tok))
        self.websocket_client.message_received.connect(lambda d: self._on_ws_message(d, tok))
        self.websocket_client.error_occurred.connect(lambda e: self._on_ws_error(e, tok))
        self.websocket_client.connect_to_server()
        self.statusBar().showMessage("Connexion en cours…")

    def _is_active(self, tok): return tok == self._session_token

    def _on_ws_connected(self, tok):
        if not self._is_active(tok): return
        self.status_chip.set_state("validating")
        self.status_chip.lbl_main.setText(self.t("status_validating"))

    def _on_ws_disconnected(self, code, reason, tok):
        if not self._is_active(tok): return
        if self.is_connecting:
            self._handle_conn_failure(reason or f"Code {code}"); return
        self._reset_audio_state(); self._reset_ui_for_new_session()

    def _on_ws_error(self, error, tok):
        if not self._is_active(tok): return
        self.statusBar().showMessage(f"Erreur : {error}")

    def _on_ws_message(self, data: dict, tok: int):
        if not self._is_active(tok): return
        mt = data.get("type"); md = data.get("data", {})

        if mt == "error":
            err = md.get("message", "Erreur")
            if md.get("error_type") == "SESSION_INVALID":
                self._handle_conn_failure(err)
            else:
                self._show_error(self.t("error_title"), err)
            return

        if mt == "question_loading":
            self.interview_widget.update_question(md.get("progress", {}))
            self.statusBar().showMessage(self.t("generating_audio"))
            self.video_player.set_speaking(); return

        if mt in ("welcome", "welcome_back", "question", "interview_completed"):
            if md.get("audio_mode") == "chunked":
                self._pending_msg_type = mt; self._pending_msg_data = md
                self._audio_chunks = []; self._audio_total_chunks = md.get("total_chunks", 0)
                sr   = md.get("sample_rate", _MIXER_FREQUENCY)
                ch   = md.get("channels", _MIXER_CHANNELS)
                bits = md.get("bits_per_sample", 16)
                self._ensure_audio_format(sr, ch, bits)
                if mt == "question":
                    self.interview_widget.set_max_recording_seconds(md.get("max_duration", 90))
                    self.interview_widget.enable_recording(False)
                return
            ab = md.get("audio_data")
            if ab: self._play_bytes_direct(base64.b64decode(ab))
            self._finalize_msg(mt, md); return

        if mt == "audio_chunk_data":
            self._audio_chunks.append(md.get("data", "")); return

        if mt == "audio_chunk_end":
            if self._audio_chunks:
                try: self._play_pcm(b"".join(base64.b64decode(c) for c in self._audio_chunks))
                except Exception as e: logger.error(e); self.interview_widget.enable_recording(True)
            else:
                self.interview_widget.enable_recording(True)
            self._finalize_msg(self._pending_msg_type, self._pending_msg_data)
            self._audio_chunks = []; self._pending_msg_type = ""; self._pending_msg_data = {}; return

        if mt == "answer_saved":
            self.statusBar().showMessage(self.t("answer_saved"))
            self.video_player.set_idle(); self.status_chip.set_state("connected"); return

        if mt == "answer_evaluated":
            self.statusBar().showMessage(self.t("answer_saved")); return

    def _finalize_msg(self, mt, md):
        if mt == "welcome":
            self._on_session_started(md)

        elif mt == "welcome_back":
            self.is_connecting = False
            self.status_chip.lbl_main.setText(self.t("status_connected"))
            self.status_chip.lbl_detail.setText(self.t("vocal_mode_active"))
            self.status_chip.set_state("connected")
            self.stacked.setVisible(False); self.interview_container.setVisible(True)
            if not self.audio_recorder:
                self.audio_recorder = AudioRecorder()
                self.audio_recorder.audio_chunk_ready.connect(self._on_audio_chunk)
            idx = md.get("current_question_index", 0)
            total = md.get("total_questions", 0)
            if total > 0:
                self.interview_widget.update_question({
                    "current": idx + 1, "total": total,
                    "percentage": int((idx + 1) / total * 100),
                })
            self.video_player.set_speaking()
            self.statusBar().showMessage(self.t("welcome_back_status"))
            if self._camera_available and self._facial_enabled:
                self.video_player.camera_preview.show()
                self.video_player.camera_preview.reposition()

        elif mt == "question":
            self.interview_widget.set_max_recording_seconds(md.get("max_duration", 90))
            self.interview_widget.update_question(md.get("progress", {}))
            self.interview_widget.set_audio_playing()
            self.video_player.set_speaking()
            self.statusBar().showMessage(self.t("question_status"))

        elif mt == "interview_completed":
            if self._video_collector and self._video_collector.is_capturing:
                self._video_collector.stop_capture()
            self._show_info(self.t("interview_complete"), self.t("thanks_message"))
            self.statusBar().showMessage("✓ " + self.t("interview_complete"))
            self._reset_audio_state(); self._reset_ui_for_new_session()

    def _on_session_started(self, md):
        self.is_connecting = False
        self.status_chip.lbl_main.setText(self.t("status_connected"))
        self.status_chip.lbl_detail.setText(self.t("vocal_mode_active"))
        self.status_chip.set_state("connected")
        self.stacked.setVisible(False); self.interview_container.setVisible(True)
        if not self.audio_recorder:
            self.audio_recorder = AudioRecorder()
            self.audio_recorder.audio_chunk_ready.connect(self._on_audio_chunk)
        self.video_player.set_speaking()
        self.statusBar().showMessage(self.t("welcome_status"))
        if self._camera_available and self._facial_enabled:
            self.video_player.camera_preview.show()
            self.video_player.camera_preview.reposition()

    def _play_pcm(self, pcm: bytes):
        try:
            if self.audio_check_timer: self.audio_check_timer.stop(); self.audio_check_timer = None
            try: pygame.mixer.music.stop(); pygame.mixer.music.unload()
            except Exception: pass
            self._cleanup_tmp_file()
            tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            self._tmp_audio_path = tmp.name; tmp.close()
            sr   = self._audio_sample_rate if self._audio_sample_rate > 0 else _MIXER_FREQUENCY
            ch   = self._audio_channels    if self._audio_channels    > 0 else _MIXER_CHANNELS
            bits = self._audio_bits        if self._audio_bits        > 0 else 16
            with wave.open(self._tmp_audio_path, "wb") as wf:
                wf.setnchannels(ch); wf.setsampwidth(bits // 8)
                wf.setframerate(sr); wf.writeframes(pcm)
            bps = sr * ch * (bits // 8)
            self._audio_min_duration = max((len(pcm) / bps * 1000) if bps > 0 else 3000, 800) * 0.9
            self._audio_play_start   = time.monotonic() * 1000
            pygame.mixer.music.load(self._tmp_audio_path)
            pygame.mixer.music.play()
            self.audio_check_timer = QTimer()
            self.audio_check_timer.timeout.connect(self._check_audio)
            self.audio_check_timer.start(200)
        except Exception as e:
            logger.error(f"_play_pcm: {e}")
            self._cleanup_tmp_file(); self.interview_widget.enable_recording(True)

    def _check_audio(self):
        if (time.monotonic() * 1000 - self._audio_play_start) < self._audio_min_duration: return
        if not pygame.mixer.music.get_busy():
            if self.audio_check_timer: self.audio_check_timer.stop(); self.audio_check_timer = None
            try: pygame.mixer.music.unload()
            except Exception: pass
            self._cleanup_tmp_file(); self.video_player.set_idle()
            if self.websocket_client: self.websocket_client.send_message({"type": "audio_finished"})
            self.interview_widget.enable_recording(True)
            self.statusBar().showMessage(self.t("answer_status"))

    def _play_bytes_direct(self, audio: bytes):
        if audio[:4] == b"RIFF":
            import struct
            fi = audio.find(b"fmt ", 12); di = audio.find(b"data", 12)
            if fi != -1 and di != -1:
                self._ensure_audio_format(
                    struct.unpack_from("<I", audio, fi + 12)[0],
                    struct.unpack_from("<H", audio, fi + 10)[0],
                    struct.unpack_from("<H", audio, fi + 22)[0],
                )
                self._play_pcm(audio[di + 8:]); return
        self._play_pcm(audio)

    def _on_start_recording(self):
        if self.audio_recorder:
            self.audio_recorder.start_recording()
            self.video_player.set_listening()
            self.statusBar().showMessage("● REC")
        if (self._video_collector and self._facial_enabled
                and self._camera_available and not self._video_collector.is_capturing):
            if self._video_collector.start_capture():
                logger.info("Capture vidéo démarrée")
        self.video_player.camera_preview.set_recording(True)

    def _on_stop_recording(self):
        if self.audio_recorder:
            self.audio_recorder.stop_recording()
        if self._video_collector and self._video_collector.is_capturing:
            self._video_collector.stop_capture()
        self.video_player.camera_preview.set_recording(False)
        if self.websocket_client:
            self.websocket_client.send_message({"type": "answer_complete"})
        self.video_player.set_idle()
        self.interview_widget.enable_recording(False)

    def _on_audio_chunk(self, audio_data: bytes):
        if self.websocket_client:
            self.websocket_client.send_message({
                "type": "audio_chunk",
                "audio_data": base64.b64encode(audio_data).decode()
            })

    def _on_end_interview(self):
        r = QMessageBox.question(
            self, self.t("end_title"), self.t("end_confirm"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if r == QMessageBox.StandardButton.Yes and self.websocket_client:
            if self._video_collector and self._video_collector.is_capturing:
                self._video_collector.stop_capture()
            self.websocket_client.send_message({"type": "end_interview"})

    def _handle_conn_failure(self, msg: str):
        self.is_connecting = False; self._reset_audio_state()
        self._connect_btn.setEnabled(True); self._connect_btn.setText(self.t("start_btn"))
        self._session_input.setEnabled(True)
        self.status_chip.set_state("error")
        self.status_chip.lbl_main.setText(self.t("status_disconnected"))
        if self.websocket_client:
            try:
                self.websocket_client.disconnected.disconnect()
                self.websocket_client.connected.disconnect()
                self.websocket_client.message_received.disconnect()
                self.websocket_client.error_occurred.disconnect()
            except Exception: pass
            try: self.websocket_client.disconnect_from_server()
            except Exception: pass
            self.websocket_client = None
        self._show_error(self.t("error_title"), msg)

    def _show_error(self, title, msg):
        b = QMessageBox(self); b.setIcon(QMessageBox.Icon.Critical)
        b.setWindowTitle(title); b.setText(msg); b.exec()

    def _show_info(self, title, msg):
        b = QMessageBox(self); b.setIcon(QMessageBox.Icon.Information)
        b.setWindowTitle(title); b.setText(msg); b.exec()

    def closeEvent(self, event):
        if self._video_collector: self._video_collector.cleanup()
        if self.websocket_client:
            try:
                self.websocket_client.disconnected.disconnect()
                self.websocket_client.connected.disconnect()
                self.websocket_client.message_received.disconnect()
                self.websocket_client.error_occurred.disconnect()
            except Exception: pass
            self.websocket_client.disconnect_from_server()
        if self.audio_recorder: self.audio_recorder.cleanup()
        if self.audio_check_timer: self.audio_check_timer.stop()
        try: pygame.mixer.music.stop(); pygame.mixer.music.unload()
        except Exception: pass
        self._cleanup_tmp_file()
        try: pygame.quit()
        except Exception: pass
        super().closeEvent(event)