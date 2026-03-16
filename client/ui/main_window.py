"""
Main Window — Professional Light UI
Design · QSS complet · Palette slate/cyan/amber

Overlay caméra PiP intégré :
  + CameraPreviewWidget affiché dans le coin bas-gauche du VideoPlayerWidget
  + Badge REC clignotant pendant l'enregistrement
  + Caché entre les sessions
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QMessageBox, QLabel, QLineEdit, QPushButton, QFrame,
    QGraphicsDropShadowEffect, QStackedWidget,
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

# ── pygame pre_init ───────────────────────────────────────────────────────────
_MIXER_FREQUENCY = 22050
_MIXER_SIZE      = -16
_MIXER_CHANNELS  = 2
_MIXER_BUFFER    = 4096

pygame.mixer.pre_init(
    frequency=_MIXER_FREQUENCY,
    size=_MIXER_SIZE,
    channels=_MIXER_CHANNELS,
    buffer=_MIXER_BUFFER,
)
pygame.init()

# ── i18n ─────────────────────────────────────────────────────────────────────

UI_TEXTS = {
    "ar": {
        "app_title": "STARK RECRUITMENT AI", "app_subtitle": "مقابلة صوتية ذكية",
        "choose_language": "اختر لغة المقابلة",
        "choose_subtitle": "ستُجرى المقابلة بالكامل باللغة التي تختارها",
        "enter_session": "معرّف الجلسة", "session_placeholder": "session_xxxxxxxxxxxxx",
        "start_btn": "بدء المقابلة", "connecting": "جارٍ الاتصال…",
        "status_disconnected": "غير متصل", "status_connected": "متصل",
        "status_validating": "التحقق", "waiting_connection": "في انتظار الاتصال",
        "vocal_mode_active": "الوضع الصوتي نشط", "vocal_mode_label": "الوضع الصوتي",
        "welcome_status": "مرحباً", "question_status": "السؤال قيد التشغيل",
        "answer_status": "يمكنك الإجابة", "answer_saved": "تم حفظ الإجابة",
        "generating_audio": "توليد الصوت…", "end_confirm": "هل تريد إنهاء المقابلة؟",
        "interview_complete": "انتهت المقابلة", "thanks_message": "شكراً لك! انتهت المقابلة.",
        "format_error": "الصيغة المطلوبة: session_xxxxxxxxxxxxx",
        "error_title": "خطأ", "end_title": "إنهاء", "back_btn": "رجوع", "confirm_btn": "تأكيد",
        "welcome_back_status": "مرحباً بعودتك — نستأنف المقابلة",
        "camera_ok": "الكاميرا جاهزة", "camera_off": "الكاميرا غير متوفرة",
        "facial_score": "الثقة: {c}/10 | التوتر: {s}/10 | التواصل: {e}%",
    },
    "fr": {
        "app_title": "STARK RECRUITMENT AI", "app_subtitle": "Entretien vocal intelligent",
        "choose_language": "Choisissez votre langue",
        "choose_subtitle": "L'entretien se déroulera intégralement dans la langue sélectionnée",
        "enter_session": "Identifiant de session", "session_placeholder": "session_xxxxxxxxxxxxx",
        "start_btn": "Démarrer l'entretien", "connecting": "Connexion en cours…",
        "status_disconnected": "Déconnecté", "status_connected": "Connecté",
        "status_validating": "Validation…", "waiting_connection": "En attente",
        "vocal_mode_active": "Mode vocal actif", "vocal_mode_label": "Mode Vocal",
        "welcome_status": "Bienvenue — écoutez le message", "question_status": "Question en lecture",
        "answer_status": "Vous pouvez répondre", "answer_saved": "Réponse enregistrée",
        "generating_audio": "Génération audio…", "end_confirm": "Confirmer la fin de l'entretien ?",
        "interview_complete": "Entretien terminé", "thanks_message": "Merci ! L'entretien est terminé.",
        "format_error": "Format attendu : session_xxxxxxxxxxxxx",
        "error_title": "Erreur", "end_title": "Terminer", "back_btn": "Retour", "confirm_btn": "Confirmer",
        "welcome_back_status": "Bon retour — reprise de l'entretien",
        "camera_ok": "Caméra active 🎥", "camera_off": "Caméra non disponible ⚠️",
        "facial_score": "Confiance: {c}/10 | Stress: {s}/10 | Contact: {e}%",
    },
    "en": {
        "app_title": "STARK RECRUITMENT AI", "app_subtitle": "AI-powered voice interview",
        "choose_language": "Choose your language",
        "choose_subtitle": "The entire interview will be conducted in the selected language",
        "enter_session": "Session identifier", "session_placeholder": "session_xxxxxxxxxxxxx",
        "start_btn": "Start interview", "connecting": "Connecting…",
        "status_disconnected": "Disconnected", "status_connected": "Connected",
        "status_validating": "Validating…", "waiting_connection": "Waiting",
        "vocal_mode_active": "Vocal mode active", "vocal_mode_label": "Vocal Mode",
        "welcome_status": "Welcome — listen to greeting", "question_status": "Question playing",
        "answer_status": "You may answer", "answer_saved": "Answer saved",
        "generating_audio": "Generating audio…", "end_confirm": "Confirm end of interview?",
        "interview_complete": "Interview complete", "thanks_message": "Thank you! The interview is complete.",
        "format_error": "Expected: session_xxxxxxxxxxxxx",
        "error_title": "Error", "end_title": "End Interview", "back_btn": "Back", "confirm_btn": "Confirm",
        "welcome_back_status": "Welcome back — resuming interview",
        "camera_ok": "Camera active 🎥", "camera_off": "Camera unavailable ⚠️",
        "facial_score": "Confidence: {c}/10 | Stress: {s}/10 | Contact: {e}%",
    },
}

LANGUAGES = [
    {"code": "ar", "flag": "🇸🇦", "name": "العربية",  "native": "Arabic",  "accent": T.GREEN_600},
    {"code": "fr", "flag": "🇫🇷", "name": "Français", "native": "French",  "accent": T.CYAN_600},
    {"code": "en", "flag": "🇬🇧", "name": "English",  "native": "English", "accent": T.BLUE_600},
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _shadow(blur=20, dy=4, alpha=30, r=100, g=116, b=139):
    s = QGraphicsDropShadowEffect()
    s.setBlurRadius(blur); s.setOffset(0, dy)
    s.setColor(QColor(r, g, b, alpha)); return s


def _divider():
    d = QFrame(); d.setFrameShape(QFrame.Shape.HLine)
    d.setFixedHeight(1)
    d.setStyleSheet(f"background: {T.BORDER}; border: none;"); return d


def _label(text, size=T.FS_BASE, bold=False, color=T.TEXT_800):
    lbl = QLabel(text); f = QFont(T.FONT, size); f.setBold(bold)
    lbl.setFont(f); lbl.setStyleSheet(f"color: {color}; background: transparent;"); return lbl


def _icon_badge(emoji, size=56, bg0=T.CYAN_100, bg1=T.BLUE_100, border=T.CYAN_200):
    cont = QFrame(); cont.setFixedSize(size, size)
    cont.setStyleSheet(f"""
        QFrame {{
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 {bg0},stop:1 {bg1});
            border: 1px solid {border}; border-radius: {size // 4}px;
        }}
    """)
    lay = QVBoxLayout(cont); lay.setContentsMargins(0,0,0,0)
    lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
    e = QLabel(emoji); e.setFont(QFont("Segoe UI Emoji, Apple Color Emoji", size * 5 // 8))
    e.setAlignment(Qt.AlignmentFlag.AlignCenter); lay.addWidget(e)
    cont.setGraphicsEffect(_shadow(16, 4, 20, 6, 182, 212)); return cont


def _hex_to_rgb(h):
    h = h.lstrip("#"); return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


# ── Language Card ─────────────────────────────────────────────────────────────

class LanguageCard(QFrame):
    def __init__(self, data, on_select, parent=None):
        super().__init__(parent)
        self._data = data; self._on_select = on_select; self._selected = False
        self.setCursor(Qt.CursorShape.PointingHandCursor); self.setFixedSize(200, 210)
        self._build(); self._refresh()

    def _build(self):
        lay = QVBoxLayout(self); lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.setSpacing(T.SP_2); lay.setContentsMargins(T.SP_5, T.SP_6, T.SP_5, T.SP_6)
        flag = QLabel(self._data["flag"])
        flag.setFont(QFont("Segoe UI Emoji, Apple Color Emoji, Noto Color Emoji", 44))
        flag.setAlignment(Qt.AlignmentFlag.AlignCenter); flag.setStyleSheet("background: transparent;")
        lay.addWidget(flag); lay.addSpacing(T.SP_2)
        name = _label(self._data["name"], T.FS_LG, bold=True, color=T.TEXT_900)
        name.setAlignment(Qt.AlignmentFlag.AlignCenter); lay.addWidget(name)
        native = _label(self._data["native"], T.FS_SM, color=T.TEXT_400)
        native.setAlignment(Qt.AlignmentFlag.AlignCenter); lay.addWidget(native)

    def _refresh(self):
        acc = self._data["accent"]
        if self._selected:
            self.setStyleSheet(f"LanguageCard {{ background: {T.BG_SELECTED}; border: 2px solid {acc}; border-radius: {T.R_LG}px; }}")
            self.setGraphicsEffect(_shadow(24, 6, 25, *_hex_to_rgb(acc)))
        else:
            self.setStyleSheet(f"LanguageCard {{ background: {T.BG_CARD}; border: 1px solid {T.BORDER}; border-radius: {T.R_LG}px; }} LanguageCard:hover {{ background: {T.BG_HOVER}; border: 1px solid {T.BORDER_HOVER}; }}")
            self.setGraphicsEffect(_shadow(14, 3, 18))

    def set_selected(self, v): self._selected = v; self._refresh()
    def mousePressEvent(self, e): self._on_select(self._data["code"]); super().mousePressEvent(e)


# ── Status Chip ───────────────────────────────────────────────────────────────

class StatusChip(QFrame):
    STATES = {
        "disconnected": (T.TEXT_400, "●", T.BG_PAGE,   T.BORDER),
        "validating":   (T.AMBER_500,"◌", T.AMBER_50,  "#FDE68A"),
        "connected":    (T.GREEN_600,"●", T.GREEN_50,  "#BBF7D0"),
        "error":        (T.RED_600,  "●", T.RED_50,    "#FECACA"),
    }

    def __init__(self, parent=None):
        super().__init__(parent); self.setFixedHeight(36)
        self._lay = QHBoxLayout(self); self._lay.setContentsMargins(12, 0, 16, 0); self._lay.setSpacing(8)
        self._dot = QLabel("●"); self._dot.setFont(QFont(T.FONT, 9)); self._lay.addWidget(self._dot)
        vlay = QVBoxLayout(); vlay.setSpacing(0)
        self.lbl_main   = QLabel("Déconnecté"); self.lbl_main.setFont(QFont(T.FONT, 10, QFont.Weight.DemiBold))
        self.lbl_detail = QLabel("En attente"); self.lbl_detail.setFont(QFont(T.FONT, 8))
        self.lbl_detail.setStyleSheet(f"color: {T.TEXT_400}; background: transparent;")
        vlay.addWidget(self.lbl_main); vlay.addWidget(self.lbl_detail); self._lay.addLayout(vlay)
        self.set_state("disconnected")

    def set_state(self, state):
        color, dot, bg, border = self.STATES.get(state, self.STATES["disconnected"])
        self._dot.setText(dot); self._dot.setStyleSheet(f"color: {color}; background: transparent;")
        self.lbl_main.setStyleSheet(f"color: {color}; font-weight: 600; background: transparent;")
        self.setStyleSheet(f"QFrame {{ background: {bg}; border: 1px solid {border}; border-radius: {T.R_FULL}px; }}")


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

        # Capture vidéo
        self._video_collector: VideoFrameCollector | None = None
        self._facial_enabled: bool = getattr(settings, "FACIAL_ANALYSIS_ENABLED", True)
        self._camera_available: bool = False
        self._camera_lbl: QLabel | None = None

        # Vérification pygame mixer
        if not pygame.mixer.get_init():
            logger.warning("pygame mixer non initialisé — tentative de ré-initialisation")
            try:
                pygame.mixer.init(
                    frequency=_MIXER_FREQUENCY, size=_MIXER_SIZE,
                    channels=_MIXER_CHANNELS, buffer=_MIXER_BUFFER,
                )
            except Exception as e:
                logger.error(f"pygame mixer init échoué : {e}")
        else:
            freq, size, ch = pygame.mixer.get_init()
            logger.info(f"pygame mixer OK | frequency={freq} size={size} channels={ch}")

        self._init_video_collector()  # DOIT être avant _setup_ui
        self._setup_ui()

    # ── Init VideoFrameCollector ──────────────────────────────────────────────

    def _init_video_collector(self):
        if not self._facial_enabled:
            logger.info("Analyse faciale désactivée (FACIAL_ANALYSIS_ENABLED=false)")
            self._update_camera_indicator(available=False)
            return

        fps = getattr(settings, "FACIAL_CAPTURE_FPS", 2.0)
        self._video_collector = VideoFrameCollector(
            camera_index=0,
            target_fps=fps,
            jpeg_quality=70,
            max_width=640,
        )
        self._video_collector.camera_ready.connect(self._on_camera_ready)
        self._video_collector.camera_error.connect(self._on_camera_error)
        # Connecter ici — avant _setup_ui, donc disponible pour _build_interview_container
        self._video_collector.frame_captured.connect(self._on_video_frame)

        available = self._video_collector.is_camera_available(0)
        self._camera_available = available
        self._update_camera_indicator(available)
        logger.info(f"Caméra index=0 : {'disponible ✓' if available else 'non disponible ✗'}")

    def _update_camera_indicator(self, available: bool):
        if self._camera_lbl is None:
            return
        if not self._facial_enabled:
            self._camera_lbl.setVisible(False)
            return
        if available:
            self._camera_lbl.setText("🎥")
            self._camera_lbl.setToolTip(self.t("camera_ok"))
            self._camera_lbl.setStyleSheet("color: #16A34A; background: transparent; font-size: 16px;")
        else:
            self._camera_lbl.setText("⚠️")
            self._camera_lbl.setToolTip(self.t("camera_off"))
            self._camera_lbl.setStyleSheet("color: #DC2626; background: transparent; font-size: 16px;")

    def _on_camera_ready(self, ok: bool):
        self._camera_available = ok
        self._update_camera_indicator(ok)
        # Mettre à jour l'overlay si la session est déjà active
        if ok and self._facial_enabled:
            self.video_player.camera_preview.show()
            self.video_player.camera_preview.reposition()
        else:
            self.video_player.camera_preview.set_camera_unavailable()

    def _on_camera_error(self, msg: str):
        logger.warning(f"Caméra : {msg}")
        self._camera_available = False
        self._update_camera_indicator(False)

    # ── Frame vidéo → WebSocket + overlay PiP ────────────────────────────────

    def _on_video_frame(self, jpeg_bytes: bytes):
        # Afficher dans l'overlay PiP
        self.video_player.camera_preview.on_frame(jpeg_bytes)

        # Envoyer au serveur pour analyse faciale
        if not self.websocket_client:
            return
        try:
            b64 = base64.b64encode(jpeg_bytes).decode()
            self.websocket_client.send_message({
                "type": "video_frame",
                "data": {"frame": b64},
            })
        except Exception as e:
            logger.debug(f"Envoi frame vidéo: {e}")

    def t(self, key, **kwargs):
        tpl = UI_TEXTS.get(self._language, UI_TEXTS["fr"]).get(key, key)
        return tpl.format(**kwargs) if kwargs else tpl

    # ═══════════════════════════════════════════════════════════════════════
    #  UI BUILD
    # ═══════════════════════════════════════════════════════════════════════

    def _setup_ui(self):
        self.setWindowTitle("Stark Recruitment AI")
        self.showMaximized()

        root_w = QWidget(); root_w.setObjectName("appRoot")
        root_w.setStyleSheet(f"""
            #appRoot {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 {T.BG_APP}, stop:0.55 #FFFFFF, stop:1 {T.CYAN_50});
            }}
        """)
        self.setCentralWidget(root_w)
        self.setStyleSheet(StarkTheme.global_stylesheet())

        root = QVBoxLayout(root_w); root.setContentsMargins(0,0,0,0); root.setSpacing(0)
        root.addWidget(self._build_header())

        self.stacked = QStackedWidget()
        self.stacked.addWidget(self._build_language_screen())
        self.stacked.addWidget(self._build_session_screen())
        root.addWidget(self.stacked, stretch=1)

        self.interview_container = self._build_interview_container()
        self.interview_container.setVisible(False)
        root.addWidget(self.interview_container)
        self._setup_statusbar()

    def _build_header(self):
        hdr = QFrame(); hdr.setObjectName("mainHeader"); hdr.setFixedHeight(68)
        hdr.setStyleSheet(f"#mainHeader {{ background: {T.BG_CARD}; border-bottom: 1px solid {T.BORDER}; }}")
        lay = QHBoxLayout(hdr); lay.setContentsMargins(28,0,24,0); lay.setSpacing(0)

        badge = QFrame(); badge.setFixedSize(40, 40)
        badge.setStyleSheet(f"QFrame {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 {T.CYAN_500},stop:1 {T.BLUE_600}); border-radius: 10px; }}")
        bi = QVBoxLayout(badge); bi.setContentsMargins(0,0,0,0); bi.setAlignment(Qt.AlignmentFlag.AlignCenter)
        star = QLabel("⭐"); star.setFont(QFont("Segoe UI Emoji, Apple Color Emoji", 20))
        star.setAlignment(Qt.AlignmentFlag.AlignCenter); bi.addWidget(star)
        badge.setGraphicsEffect(_shadow(18, 4, 40, 6, 182, 212))

        title_col = QVBoxLayout(); title_col.setSpacing(1)
        t1 = _label(self.t("app_title"), T.FS_MD, bold=True, color=T.TEXT_900)
        t1.setStyleSheet(f"color: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {T.CYAN_600},stop:1 {T.BLUE_700}); background: transparent; letter-spacing: 1px;")
        self._header_subtitle = _label(self.t("app_subtitle"), T.FS_SM, color=T.TEXT_400)
        title_col.addWidget(t1); title_col.addWidget(self._header_subtitle)

        left = QHBoxLayout(); left.setSpacing(14); left.addWidget(badge); left.addLayout(title_col)
        lay.addLayout(left); lay.addStretch()

        # Indicateur caméra
        self._camera_lbl = QLabel("")
        self._camera_lbl.setFont(QFont("Segoe UI Emoji", 16))
        self._camera_lbl.setStyleSheet("background: transparent;")
        self._camera_lbl.setToolTip(self.t("camera_off"))
        self._camera_lbl.setVisible(self._facial_enabled)
        lay.addWidget(self._camera_lbl)
        lay.addSpacing(12)

        self.status_chip = StatusChip(); lay.addWidget(self.status_chip)
        return hdr

    def _build_language_screen(self):
        pg = QWidget(); lay = QVBoxLayout(pg)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter); lay.setSpacing(0)
        lay.setContentsMargins(T.SP_10, T.SP_12, T.SP_10, T.SP_10)

        tag = _label("SÉLECTION DE LA LANGUE", T.FS_XS, bold=True, color=T.CYAN_600)
        tag.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tag.setStyleSheet(f"color: {T.CYAN_600}; letter-spacing: 2px; background: transparent;")
        lay.addWidget(tag); lay.addSpacing(T.SP_3)

        h1 = _label(self.t("choose_language"), T.FS_3XL, bold=True, color=T.TEXT_900)
        h1.setAlignment(Qt.AlignmentFlag.AlignCenter); lay.addWidget(h1); lay.addSpacing(T.SP_2)

        sub = _label(self.t("choose_subtitle"), T.FS_MD, color=T.TEXT_600)
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter); lay.addWidget(sub); lay.addSpacing(T.SP_10)

        cards_w = QWidget(); cr = QHBoxLayout(cards_w)
        cr.setAlignment(Qt.AlignmentFlag.AlignCenter); cr.setSpacing(20); cr.setContentsMargins(0,0,0,0)
        self._lang_cards = {}
        for ld in LANGUAGES:
            card = LanguageCard(ld, self._on_lang_select)
            self._lang_cards[ld["code"]] = card; cr.addWidget(card)
        lay.addWidget(cards_w); lay.addSpacing(T.SP_10)

        self._confirm_btn = QPushButton(f"✓  Français")
        self._confirm_btn.setFont(QFont(T.FONT, T.FS_MD, QFont.Weight.Bold))
        self._confirm_btn.setFixedSize(260, 56); self._confirm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._confirm_btn.setStyleSheet(StarkTheme.get_button_style("primary"))
        self._confirm_btn.setGraphicsEffect(_shadow(28, 8, 50, 6, 182, 212))
        self._confirm_btn.clicked.connect(self._on_lang_confirmed)
        lay.addWidget(self._confirm_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        self._on_lang_select("fr"); return pg

    def _on_lang_select(self, code):
        self._language = code
        for c, card in self._lang_cards.items(): card.set_selected(c == code)
        ld = next(l for l in LANGUAGES if l["code"] == code)
        if hasattr(self, "_confirm_btn"): self._confirm_btn.setText(f"✓  {ld['name']}")

    def _on_lang_confirmed(self):
        self._sync_texts(); self.stacked.setCurrentIndex(1)

    def _sync_texts(self):
        self._header_subtitle.setText(self.t("app_subtitle"))
        self.status_chip.lbl_main.setText(self.t("status_disconnected"))
        self.status_chip.lbl_detail.setText(self.t("waiting_connection"))
        if hasattr(self, "_connect_btn"): self._connect_btn.setText(self.t("start_btn"))
        if hasattr(self, "_session_input"): self._session_input.setPlaceholderText(self.t("session_placeholder"))
        if hasattr(self, "_back_btn"): self._back_btn.setText(f"← {self.t('back_btn')}")
        if hasattr(self, "_session_title"): self._session_title.setText(self.t("enter_session"))
        if hasattr(self, "interview_widget"): self.interview_widget.set_language(self._language)
        self.statusBar().showMessage(self.t("vocal_mode_label"))
        self._refresh_pill()
        self._update_camera_indicator(self._camera_available)

    def _build_session_screen(self):
        outer = QWidget(); outer_lay = QVBoxLayout(outer)
        outer_lay.setAlignment(Qt.AlignmentFlag.AlignCenter); outer_lay.setContentsMargins(0,0,0,0)

        card = QFrame(); card.setFixedWidth(500)
        card.setStyleSheet(f"QFrame {{ background: {T.BG_CARD}; border: 1px solid {T.BORDER}; border-radius: {T.R_XL}px; }}")
        card.setGraphicsEffect(_shadow(40, 12, 45))

        lay = QVBoxLayout(card); lay.setContentsMargins(T.SP_12, T.SP_10, T.SP_12, T.SP_10)
        lay.setSpacing(T.SP_5); lay.setAlignment(Qt.AlignmentFlag.AlignTop)

        lay.addWidget(_icon_badge("🔑", 64, T.CYAN_100, T.BLUE_100, T.CYAN_200), alignment=Qt.AlignmentFlag.AlignCenter)
        lay.addSpacing(T.SP_1)

        self._session_title = _label(self.t("enter_session"), T.FS_2XL, bold=True, color=T.TEXT_900)
        self._session_title.setAlignment(Qt.AlignmentFlag.AlignCenter); lay.addWidget(self._session_title)

        pill_row = QHBoxLayout(); pill_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lang_pill = QFrame(); self._lang_pill.setFixedHeight(30)
        pill_inner = QHBoxLayout(self._lang_pill); pill_inner.setContentsMargins(14,0,14,0)
        self._pill_lbl = QLabel(); self._pill_lbl.setFont(QFont(T.FONT, T.FS_SM, QFont.Weight.Bold))
        self._pill_lbl.setStyleSheet(f"color: {T.CYAN_700}; background: transparent;")
        pill_inner.addWidget(self._pill_lbl)
        self._lang_pill.setStyleSheet(f"QFrame {{ background: {T.CYAN_50}; border: 1px solid {T.CYAN_200}; border-radius: {T.R_FULL}px; }}")
        pill_row.addWidget(self._lang_pill); lay.addLayout(pill_row); self._refresh_pill()

        lay.addWidget(_divider())

        self._session_input = QLineEdit()
        self._session_input.setPlaceholderText(self.t("session_placeholder"))
        self._session_input.setFont(QFont(T.FONT_MONO, T.FS_MD))
        self._session_input.setMinimumHeight(50)
        self._session_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._session_input.setStyleSheet(StarkTheme.input_style())
        lay.addWidget(self._session_input)

        self._connect_btn = QPushButton(self.t("start_btn"))
        self._connect_btn.setFont(QFont(T.FONT, T.FS_MD, QFont.Weight.Bold))
        self._connect_btn.setMinimumHeight(54); self._connect_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._connect_btn.setStyleSheet(StarkTheme.get_button_style("accent"))
        self._connect_btn.setGraphicsEffect(_shadow(26, 8, 55, 245, 158, 11))
        self._connect_btn.clicked.connect(self._connect_to_interview); lay.addWidget(self._connect_btn)

        self._back_btn = QPushButton(f"← {self.t('back_btn')}")
        self._back_btn.setFont(QFont(T.FONT, T.FS_SM)); self._back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._back_btn.setStyleSheet(StarkTheme.get_button_style("ghost"))
        self._back_btn.clicked.connect(lambda: self.stacked.setCurrentIndex(0))
        lay.addWidget(self._back_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        outer_lay.addWidget(card); return outer

    def _refresh_pill(self):
        ld = next((l for l in LANGUAGES if l["code"] == self._language), None)
        if ld and hasattr(self, "_pill_lbl"):
            self._pill_lbl.setText(f"{ld['flag']}  {ld['name']}")

    def _build_interview_container(self):
        w = QWidget(); lay = QHBoxLayout(w)
        lay.setContentsMargins(T.SP_4, T.SP_4, T.SP_4, T.SP_4); lay.setSpacing(T.SP_4)

        self.video_player = VideoPlayerWidget()
        lay.addWidget(self.video_player, stretch=2)

        self.interview_widget = InterviewWidget(language=self._language)
        self.interview_widget.setMaximumWidth(460)
        self.interview_widget.start_recording.connect(self._on_start_recording)
        self.interview_widget.stop_recording.connect(self._on_stop_recording)
        self.interview_widget.end_interview.connect(self._on_end_interview)
        lay.addWidget(self.interview_widget, stretch=1)
        return w

    def _setup_statusbar(self):
        self.statusBar().setFixedHeight(28)
        self.statusBar().showMessage(self.t("vocal_mode_label"))

    # ═══════════════════════════════════════════════════════════════════════
    #  AUDIO
    # ═══════════════════════════════════════════════════════════════════════

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
            logger.error(f"pygame mixer réinit : {e}")
            try:
                pygame.mixer.init(frequency=_MIXER_FREQUENCY, size=_MIXER_SIZE,
                                  channels=_MIXER_CHANNELS, buffer=_MIXER_BUFFER)
                self._audio_sample_rate = _MIXER_FREQUENCY
                self._audio_channels    = _MIXER_CHANNELS
                self._audio_bits        = 16
            except Exception as e2:
                logger.error(f"pygame mixer fallback : {e2}")

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
        # Arrêter la capture vidéo
        if self._video_collector and self._video_collector.is_capturing:
            self._video_collector.stop_capture()

        # Cacher et réinitialiser l'overlay caméra
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

    # ═══════════════════════════════════════════════════════════════════════
    #  CONNECTION
    # ═══════════════════════════════════════════════════════════════════════

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

        self.session_id    = session_id
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
        self.statusBar().showMessage("Connexion…")

    def _is_active(self, tok): return tok == self._session_token

    def _on_ws_connected(self, tok):
        if not self._is_active(tok): return
        self.status_chip.set_state("validating")
        self.status_chip.lbl_main.setText(self.t("status_validating"))

    def _on_ws_disconnected(self, code, reason, tok):
        if not self._is_active(tok): return
        if self.is_connecting: self._handle_conn_failure(reason or f"Code {code}"); return
        self._reset_audio_state(); self._reset_ui_for_new_session()

    def _on_ws_error(self, error, tok):
        if not self._is_active(tok): return
        self.statusBar().showMessage(f"Erreur : {error}")

    def _on_ws_message(self, data: dict, tok: int):
        if not self._is_active(tok): return
        mt = data.get("type"); md = data.get("data", {})

        if mt == "error":
            err = md.get("message", "Erreur")
            if md.get("error_type") == "SESSION_INVALID": self._handle_conn_failure(err)
            else: self._show_error(self.t("error_title"), err)
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
                    max_dur = md.get("max_duration", 90)
                    self.interview_widget.set_max_recording_seconds(max_dur)
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
            else: self.interview_widget.enable_recording(True)
            self._finalize_msg(self._pending_msg_type, self._pending_msg_data)
            self._audio_chunks = []; self._pending_msg_type = ""; self._pending_msg_data = {}; return

        if mt == "answer_saved":
            self.statusBar().showMessage(self.t("answer_saved"))
            self.video_player.set_idle(); self.status_chip.set_state("connected"); return

        if mt == "answer_evaluated":
            # Afficher le résultat dans le panneau interview_widget
            self.interview_widget.show_evaluation(md)
            # Transmettre les métriques faciales à l'overlay PiP
            facial = md.get("facial")
            if facial and facial.get("frames_with_face", 0) > 0:
                self.video_player.camera_preview.set_facial_result(facial)
                msg = self.t(
                    "facial_score",
                    c=facial.get("confidence_score", 0),
                    s=facial.get("stress_score", 0),
                    e=int(facial.get("eye_contact_ratio", 0) * 100),
                )
                self.statusBar().showMessage(f"✓ {self.t('answer_saved')} | {msg}")
            return

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

            # Afficher l'overlay caméra PiP
            if self._camera_available and self._facial_enabled:
                self.video_player.camera_preview.show()
                self.video_player.camera_preview.reposition()

        elif mt == "question":
            max_dur = md.get("max_duration", 90)
            self.interview_widget.set_max_recording_seconds(max_dur)
            self.interview_widget.update_question(md.get("progress", {}))
            self.interview_widget.set_audio_playing()
            self.video_player.set_speaking()
            self.statusBar().showMessage(self.t("question_status"))

        elif mt == "interview_completed":
            # Arrêter la capture vidéo
            if self._video_collector and self._video_collector.is_capturing:
                self._video_collector.stop_capture()
            self._show_info(self.t("interview_complete"), self.t("thanks_message"))
            self.statusBar().showMessage("✓ Terminé")
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

        # Afficher l'overlay caméra PiP dès que la session démarre
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
            logger.error(f"_play_pcm : {e}")
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

    # ── Enregistrement audio + capture vidéo ─────────────────────────────────

    def _on_start_recording(self):
        if self.audio_recorder:
            self.audio_recorder.start_recording()
            self.video_player.set_listening()
            self.statusBar().showMessage("● Enregistrement…")

        # Démarrer la capture caméra
        if (
            self._video_collector
            and self._facial_enabled
            and self._camera_available
            and not self._video_collector.is_capturing
        ):
            ok = self._video_collector.start_capture()
            if ok:
                logger.info("Capture vidéo démarrée pour analyse faciale")
            else:
                logger.warning("Impossible de démarrer la capture vidéo")

        # Badge REC sur l'overlay PiP
        self.video_player.camera_preview.set_recording(True)

    def _on_stop_recording(self):
        if self.audio_recorder:
            self.audio_recorder.stop_recording()

        # Arrêter la capture caméra
        if self._video_collector and self._video_collector.is_capturing:
            self._video_collector.stop_capture()
            logger.info("Capture vidéo arrêtée")

        # Éteindre badge REC
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
        r = QMessageBox.question(self, self.t("end_title"), self.t("end_confirm"),
                                 QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
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
        if self._video_collector:
            self._video_collector.cleanup()
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