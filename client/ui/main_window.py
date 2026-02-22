"""
Main Window — Premium Redesign
Dark glassmorphism with refined language selection and session ID screen.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QMessageBox, QLabel, QLineEdit, QPushButton, QFrame,
    QGraphicsDropShadowEffect, QStackedWidget, QSizePolicy
)
from PySide6.QtCore import (
    Qt, QSize, QTimer, QPropertyAnimation, QEasingCurve, QRect
)
from PySide6.QtGui import QFont, QColor, QLinearGradient, QPainter, QPainterPath
import sys
import os
import base64
import io
import time
import wave
import tempfile
import logging
from pathlib import Path
import pygame

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from client.ui.stark_theme import StarkTheme
from client.ui.icons import StarkIcons
from client.ui.video_player_widget import VideoPlayerWidget
from client.ui.interview_widget import InterviewWidget
from client.core.websocket_client import WebSocketClient
from client.core.audio_recorder import AudioRecorder
from client.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ── Localised UI strings ──────────────────────────────────────────────────────

UI_TEXTS = {
    "ar": {
        "app_title":           "STARK RECRUITMENT AI",
        "app_subtitle":        "مقابلة صوتية ذكية",
        "choose_language":     "اختر لغة المقابلة",
        "choose_subtitle":     "ستُجرى المقابلة بالكامل باللغة التي تختارها",
        "enter_session":       "أدخل معرّف الجلسة",
        "session_placeholder": "session_xxxxxxxxxxxxx",
        "start_btn":           "بدء المقابلة",
        "connecting":          "جارٍ الاتصال…",
        "status_disconnected": "غير متصل",
        "status_connected":    "متصل",
        "status_validating":   "جارٍ التحقق",
        "waiting_connection":  "في انتظار الاتصال",
        "vocal_mode_active":   "الوضع الصوتي نشط",
        "vocal_mode_label":    "الوضع الصوتي",
        "welcome_status":      "مرحباً — استمع لرسالة الترحيب",
        "question_status":     "السؤال قيد التشغيل",
        "answer_status":       "يمكنك الإجابة",
        "answer_saved":        "تم حفظ الإجابة",
        "generating_audio":    "توليد الصوت…",
        "end_confirm":         "هل تريد إنهاء المقابلة؟",
        "interview_complete":  "انتهت المقابلة",
        "thanks_message":      "شكراً لك! انتهت المقابلة.",
        "format_error":        "الصيغة المطلوبة: session_xxxxxxxxxxxxx",
        "error_title":         "خطأ",
        "end_title":           "إنهاء المقابلة",
        "back_btn":            "رجوع",
        "confirm_btn":         "تأكيد اللغة",
    },
    "fr": {
        "app_title":           "STARK RECRUITMENT AI",
        "app_subtitle":        "Entretien vocal intelligent",
        "choose_language":     "Choisissez votre langue",
        "choose_subtitle":     "L'entretien se déroulera intégralement dans la langue sélectionnée",
        "enter_session":       "Identifiant de session",
        "session_placeholder": "session_xxxxxxxxxxxxx",
        "start_btn":           "Démarrer l'entretien",
        "connecting":          "Connexion en cours…",
        "status_disconnected": "Déconnecté",
        "status_connected":    "Connecté",
        "status_validating":   "Validation",
        "waiting_connection":  "En attente de connexion",
        "vocal_mode_active":   "Mode vocal actif",
        "vocal_mode_label":    "Mode Vocal",
        "welcome_status":      "Bienvenue — écoutez le message d'accueil",
        "question_status":     "Question en lecture",
        "answer_status":       "Vous pouvez répondre",
        "answer_saved":        "Réponse enregistrée",
        "generating_audio":    "Génération audio…",
        "end_confirm":         "Confirmer la fin de l'entretien ?",
        "interview_complete":  "Entretien terminé",
        "thanks_message":      "Merci ! L'entretien est terminé.",
        "format_error":        "Format attendu : session_xxxxxxxxxxxxx",
        "error_title":         "Erreur",
        "end_title":           "Terminer",
        "back_btn":            "Retour",
        "confirm_btn":         "Confirmer",
    },
    "en": {
        "app_title":           "STARK RECRUITMENT AI",
        "app_subtitle":        "AI-powered voice interview",
        "choose_language":     "Choose your language",
        "choose_subtitle":     "The entire interview will be conducted in the selected language",
        "enter_session":       "Session identifier",
        "session_placeholder": "session_xxxxxxxxxxxxx",
        "start_btn":           "Start interview",
        "connecting":          "Connecting…",
        "status_disconnected": "Disconnected",
        "status_connected":    "Connected",
        "status_validating":   "Validating",
        "waiting_connection":  "Waiting for connection",
        "vocal_mode_active":   "Vocal mode active",
        "vocal_mode_label":    "Vocal Mode",
        "welcome_status":      "Welcome — listen to the greeting",
        "question_status":     "Question playing",
        "answer_status":       "You may answer",
        "answer_saved":        "Answer saved",
        "generating_audio":    "Generating audio…",
        "end_confirm":         "Confirm end of interview?",
        "interview_complete":  "Interview complete",
        "thanks_message":      "Thank you! The interview is complete.",
        "format_error":        "Expected format: session_xxxxxxxxxxxxx",
        "error_title":         "Error",
        "end_title":           "End Interview",
        "back_btn":            "Back",
        "confirm_btn":         "Confirm",
    },
}

LANGUAGE_OPTIONS = [
    {"code": "ar", "flag": "🇸🇦", "name": "العربية",  "sub": "Arabic",   "accent": "#059669"},
    {"code": "fr", "flag": "🇫🇷", "name": "Français", "sub": "French",   "accent": "#2563EB"},
    {"code": "en", "flag": "🇬🇧", "name": "English",  "sub": "Anglais",  "accent": "#DC2626"},
]


# ── Language card ─────────────────────────────────────────────────────────────

class LanguageCard(QFrame):
    def __init__(self, lang_data: dict, on_select, parent=None):
        super().__init__(parent)
        self.lang_data = lang_data
        self.on_select = on_select
        self._selected = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(190, 210)
        self._build()
        self._style(False)

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.setSpacing(10)
        lay.setContentsMargins(16, 20, 16, 20)

        flag = QLabel(self.lang_data["flag"])
        flag.setFont(QFont("Segoe UI Emoji, Apple Color Emoji, Noto Color Emoji", 44))
        flag.setAlignment(Qt.AlignmentFlag.AlignCenter)
        flag.setStyleSheet("background: transparent;")
        lay.addWidget(flag)

        name = QLabel(self.lang_data["name"])
        name.setFont(QFont(StarkTheme.FONT_BODY, 15, QFont.Weight.Bold))
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name.setStyleSheet(f"color: {StarkTheme.TEXT_PRIMARY}; background: transparent;")
        lay.addWidget(name)

        sub = QLabel(self.lang_data["sub"])
        sub.setFont(QFont(StarkTheme.FONT_BODY, 10))
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet(f"color: {StarkTheme.TEXT_MUTED}; background: transparent;")
        lay.addWidget(sub)

    def _style(self, selected: bool):
        acc = self.lang_data["accent"]
        if selected:
            self.setStyleSheet(f"""
                LanguageCard {{
                    background: rgba(14,165,233,0.08);
                    border: 2px solid {acc};
                    border-radius: {StarkTheme.R_XL};
                }}
            """)
            sh = QGraphicsDropShadowEffect()
            sh.setBlurRadius(30)
            sh.setColor(QColor(acc))
            sh.setOffset(0, 4)
            self.setGraphicsEffect(sh)
        else:
            self.setStyleSheet(f"""
                LanguageCard {{
                    background: {StarkTheme.BG_SURFACE};
                    border: 1px solid {StarkTheme.BG_BORDER};
                    border-radius: {StarkTheme.R_XL};
                }}
                LanguageCard:hover {{
                    background: {StarkTheme.BG_ELEVATED};
                    border: 1px solid {StarkTheme.GLASS_BORDER};
                }}
            """)
            self.setGraphicsEffect(None)

    def set_selected(self, s: bool):
        self._selected = s
        self._style(s)

    def mousePressEvent(self, e):
        self.on_select(self.lang_data["code"])
        super().mousePressEvent(e)


# ── Separator line ────────────────────────────────────────────────────────────

class _HSep(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(1)
        self.setStyleSheet(f"background: {StarkTheme.BG_BORDER};")


# ── Main window ───────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.websocket_client = None
        self.audio_recorder   = None
        self.session_id       = None
        self.is_connecting    = False
        self._session_token   = 0
        self._language        = "fr"
        self._lang_cards      = {}

        # Audio state
        self._tmp_audio_path   = None
        self._audio_play_start = 0.0
        self._audio_min_duration = 0.0
        self.audio_check_timer = None
        self._audio_sample_rate = -1
        self._audio_channels    = -1
        self._audio_bits        = -1
        self._pending_msg_type  = ""
        self._pending_msg_data  = {}
        self._audio_chunks      = []
        self._audio_total_chunks = 0

        pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=4096)
        self._audio_sample_rate = 22050
        self._audio_channels    = 1
        self._audio_bits        = 16

        self._setup_ui()

    def t(self, key: str) -> str:
        return UI_TEXTS.get(self._language, UI_TEXTS["fr"]).get(key, key)

    # ── UI build ──────────────────────────────────────────────────────────────

    def _setup_ui(self):
        self.setWindowTitle("Stark Recruitment AI")
        self.showMaximized()
        self.setStyleSheet(StarkTheme.global_stylesheet())

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_header())

        self.stacked = QStackedWidget()
        self.stacked.setStyleSheet("QStackedWidget { background: transparent; }")
        self.stacked.addWidget(self._build_language_screen())   # 0
        self.stacked.addWidget(self._build_session_screen())    # 1
        root.addWidget(self.stacked, stretch=1)

        self.interview_container = self._build_interview_container()
        self.interview_container.setVisible(False)
        root.addWidget(self.interview_container)

        self._setup_statusbar()

    # ── Header ────────────────────────────────────────────────────────────────

    def _build_header(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background: {StarkTheme.BG_VOID};
                border-bottom: 1px solid {StarkTheme.BG_BORDER};
            }}
        """)
        frame.setFixedHeight(70)

        lay = QHBoxLayout(frame)
        lay.setContentsMargins(28, 0, 28, 0)
        lay.setSpacing(0)

        # Left: logo + title
        left = QHBoxLayout()
        left.setSpacing(14)

        logo = QLabel("◈")
        logo.setFont(QFont(StarkTheme.FONT_BODY, 26, QFont.Weight.Black))
        logo.setStyleSheet(f"color: {StarkTheme.BLUE_ELECTRIC};")
        left.addWidget(logo)

        title_col = QVBoxLayout()
        title_col.setSpacing(1)

        t1 = QLabel(self.t("app_title"))
        t1.setFont(QFont(StarkTheme.FONT_BODY, 14, QFont.Weight.Black))
        t1.setStyleSheet(f"color: {StarkTheme.TEXT_PRIMARY}; letter-spacing: 3px;")
        title_col.addWidget(t1)

        self.header_subtitle = QLabel(self.t("app_subtitle"))
        self.header_subtitle.setFont(QFont(StarkTheme.FONT_BODY, 9))
        self.header_subtitle.setStyleSheet(f"color: {StarkTheme.TEXT_MUTED}; letter-spacing: 1px;")
        title_col.addWidget(self.header_subtitle)

        left.addLayout(title_col)

        lay.addLayout(left)
        lay.addStretch()

        # Right: status chip
        self.status_chip = self._build_status_chip()
        lay.addWidget(self.status_chip)

        return frame

    def _build_status_chip(self) -> QFrame:
        chip = QFrame()
        chip.setFixedHeight(36)
        chip.setStyleSheet(f"""
            QFrame {{
                background: {StarkTheme.BG_SURFACE};
                border: 1px solid {StarkTheme.BG_BORDER};
                border-radius: {StarkTheme.R_FULL};
            }}
        """)
        lay = QHBoxLayout(chip)
        lay.setContentsMargins(14, 0, 14, 0)
        lay.setSpacing(8)

        self._status_dot_w = QLabel("●")
        self._status_dot_w.setFont(QFont(StarkTheme.FONT_BODY, 8))
        self._status_dot_w.setStyleSheet(f"color: {StarkTheme.TEXT_MUTED};")
        lay.addWidget(self._status_dot_w)

        col = QVBoxLayout()
        col.setSpacing(0)

        self.status_label = QLabel(self.t("status_disconnected"))
        self.status_label.setFont(QFont(StarkTheme.FONT_BODY, 10, QFont.Weight.DemiBold))
        self.status_label.setStyleSheet(f"color: {StarkTheme.TEXT_SECONDARY};")
        col.addWidget(self.status_label)

        self.status_detail = QLabel(self.t("waiting_connection"))
        self.status_detail.setFont(QFont(StarkTheme.FONT_BODY, 8))
        self.status_detail.setStyleSheet(f"color: {StarkTheme.TEXT_MUTED};")
        col.addWidget(self.status_detail)

        lay.addLayout(col)
        return chip

    def _set_chip_state(self, state: str):
        """state: disconnected | validating | connected | error"""
        cfg = {
            "disconnected": (StarkTheme.TEXT_MUTED,    StarkTheme.TEXT_SECONDARY),
            "validating":   (StarkTheme.AMBER,         StarkTheme.AMBER),
            "connected":    (StarkTheme.SUCCESS,       StarkTheme.SUCCESS),
            "error":        (StarkTheme.ERROR,         StarkTheme.ERROR),
        }
        dot_c, text_c = cfg.get(state, cfg["disconnected"])
        self._status_dot_w.setStyleSheet(f"color: {dot_c};")
        self.status_label.setStyleSheet(f"color: {text_c}; font-weight: 600;")

    # ── Screen 0: Language ────────────────────────────────────────────────────

    def _build_language_screen(self) -> QWidget:
        scr = QWidget()
        scr.setStyleSheet("QWidget { background: transparent; }")

        lay = QVBoxLayout(scr)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.setSpacing(32)
        lay.setContentsMargins(40, 40, 40, 40)

        # Heading
        heading = QLabel(self.t("choose_language"))
        heading.setFont(QFont(StarkTheme.FONT_BODY, 26, QFont.Weight.Black))
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        heading.setStyleSheet(f"color: {StarkTheme.TEXT_PRIMARY}; letter-spacing: -0.5px;")
        lay.addWidget(heading)

        sub = QLabel(self.t("choose_subtitle"))
        sub.setFont(QFont(StarkTheme.FONT_BODY, 12))
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet(f"color: {StarkTheme.TEXT_MUTED};")
        lay.addWidget(sub)

        # Cards row
        cards_row = QWidget()
        cards_row.setStyleSheet("QWidget { background: transparent; }")
        cr = QHBoxLayout(cards_row)
        cr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cr.setSpacing(20)

        self._lang_cards = {}
        for ld in LANGUAGE_OPTIONS:
            card = LanguageCard(ld, self._on_language_selected)
            self._lang_cards[ld["code"]] = card
            cr.addWidget(card)

        lay.addWidget(cards_row)

        # Confirm button
        self.lang_confirm_btn = QPushButton(self.t("confirm_btn"))
        self.lang_confirm_btn.setFont(QFont(StarkTheme.FONT_BODY, 13, QFont.Weight.Bold))
        self.lang_confirm_btn.setFixedSize(260, 52)
        self.lang_confirm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lang_confirm_btn.setStyleSheet(StarkTheme.get_button_style("primary"))
        sh = QGraphicsDropShadowEffect()
        sh.setBlurRadius(24)
        sh.setColor(QColor(StarkTheme.BLUE_ELECTRIC))
        sh.setOffset(0, 6)
        self.lang_confirm_btn.setGraphicsEffect(sh)
        self.lang_confirm_btn.clicked.connect(self._on_language_confirmed)
        lay.addWidget(self.lang_confirm_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self._on_language_selected("fr")
        return scr

    def _on_language_selected(self, code: str):
        self._language = code
        for c, card in self._lang_cards.items():
            card.set_selected(c == code)
        ld = next(l for l in LANGUAGE_OPTIONS if l["code"] == code)
        if hasattr(self, "lang_confirm_btn"):
            self.lang_confirm_btn.setText(f"✓  {ld['name']}")

    def _on_language_confirmed(self):
        self._update_ui_language()
        self.stacked.setCurrentIndex(1)

    def _update_ui_language(self):
        self.header_subtitle.setText(self.t("app_subtitle"))
        self.status_label.setText(self.t("status_disconnected"))
        self.status_detail.setText(self.t("waiting_connection"))
        self.connect_btn.setText(self.t("start_btn"))
        self.session_input.setPlaceholderText(self.t("session_placeholder"))
        self.back_btn.setText(f"← {self.t('back_btn')}")
        self.conn_title.setText(self.t("enter_session"))
        if hasattr(self, "interview_widget"):
            self.interview_widget.set_language(self._language)
        self.statusBar().showMessage(self.t("vocal_mode_label"))
        self._refresh_lang_pill()

    # ── Screen 1: Session ID ──────────────────────────────────────────────────

    def _build_session_screen(self) -> QWidget:
        outer = QWidget()
        outer.setStyleSheet("QWidget { background: transparent; }")
        wrap = QVBoxLayout(outer)
        wrap.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QFrame()
        card.setFixedWidth(520)
        card.setStyleSheet(f"""
            QFrame {{
                background: {StarkTheme.BG_SURFACE};
                border: 1px solid {StarkTheme.BG_BORDER};
                border-radius: {StarkTheme.R_2XL};
            }}
        """)
        sh = QGraphicsDropShadowEffect()
        sh.setBlurRadius(50)
        sh.setColor(QColor(StarkTheme.BLUE_ELECTRIC))
        sh.setOffset(0, 12)
        card.setGraphicsEffect(sh)

        lay = QVBoxLayout(card)
        lay.setContentsMargins(48, 40, 48, 40)
        lay.setSpacing(20)

        # Icon
        icon_w = QLabel("🎙")
        icon_w.setFont(QFont("Segoe UI Emoji, Apple Color Emoji", 44))
        icon_w.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_w.setStyleSheet("background: transparent;")
        lay.addWidget(icon_w)

        # Title
        self.conn_title = QLabel(self.t("enter_session"))
        self.conn_title.setFont(QFont(StarkTheme.FONT_BODY, 16, QFont.Weight.Bold))
        self.conn_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.conn_title.setStyleSheet(f"color: {StarkTheme.TEXT_PRIMARY};")
        lay.addWidget(self.conn_title)

        # Language pill
        self.lang_pill_container = QHBoxLayout()
        self.lang_pill_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lang_pill_w = QFrame()
        self.lang_pill_w.setFixedHeight(30)
        pill_lay = QHBoxLayout(self.lang_pill_w)
        pill_lay.setContentsMargins(14, 0, 14, 0)
        pill_lay.setSpacing(6)
        self.lang_pill_label = QLabel()
        self.lang_pill_label.setFont(QFont(StarkTheme.FONT_BODY, 10))
        self.lang_pill_label.setStyleSheet(
            f"color: {StarkTheme.BLUE_SOFT}; background: transparent;"
        )
        pill_lay.addWidget(self.lang_pill_label)
        self.lang_pill_w.setStyleSheet(f"""
            QFrame {{
                background: rgba(14,165,233,0.10);
                border: 1px solid {StarkTheme.GLASS_BORDER};
                border-radius: {StarkTheme.R_FULL};
            }}
        """)
        self.lang_pill_container.addWidget(self.lang_pill_w)
        lay.addLayout(self.lang_pill_container)
        self._refresh_lang_pill()

        lay.addWidget(_HSep())

        # Input
        self.session_input = QLineEdit()
        self.session_input.setPlaceholderText(self.t("session_placeholder"))
        self.session_input.setFont(QFont(StarkTheme.FONT_MONO, 12))
        self.session_input.setMinimumHeight(50)
        self.session_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.session_input.setStyleSheet(StarkTheme.input_style())
        lay.addWidget(self.session_input)

        # Connect button
        self.connect_btn = QPushButton(self.t("start_btn"))
        self.connect_btn.setFont(QFont(StarkTheme.FONT_BODY, 13, QFont.Weight.Bold))
        self.connect_btn.setMinimumHeight(52)
        self.connect_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.connect_btn.setStyleSheet(StarkTheme.get_button_style("accent"))
        self.connect_btn.clicked.connect(self._connect_to_interview)
        lay.addWidget(self.connect_btn)

        # Back button
        self.back_btn = QPushButton(f"← {self.t('back_btn')}")
        self.back_btn.setFont(QFont(StarkTheme.FONT_BODY, 10))
        self.back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.back_btn.setStyleSheet(StarkTheme.get_button_style("ghost"))
        self.back_btn.clicked.connect(lambda: self.stacked.setCurrentIndex(0))
        lay.addWidget(self.back_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        wrap.addWidget(card)
        return outer

    def _refresh_lang_pill(self):
        ld = next((l for l in LANGUAGE_OPTIONS if l["code"] == self._language), None)
        if ld and hasattr(self, "lang_pill_label"):
            self.lang_pill_label.setText(f"{ld['flag']}  {ld['name']}")

    # ── Interview container ───────────────────────────────────────────────────

    def _build_interview_container(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet("QWidget { background: transparent; }")
        lay = QHBoxLayout(w)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(16)

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
        self.statusBar().setStyleSheet(f"""
            QStatusBar {{
                background: {StarkTheme.BG_VOID};
                color: {StarkTheme.TEXT_MUTED};
                font-size: {StarkTheme.FS_SM};
                padding: 6px 16px;
                border-top: 1px solid {StarkTheme.BG_BORDER};
            }}
        """)
        self.statusBar().showMessage(self.t("vocal_mode_label"))

    # ═══════════════════════════════════════════════════════════════════
    # CONNECTION LOGIC (unchanged from original — only UI state updates)
    # ═══════════════════════════════════════════════════════════════════

    def _ensure_audio_format(self, sample_rate, channels, bits):
        if (sample_rate == self._audio_sample_rate and channels == self._audio_channels
                and bits == self._audio_bits):
            return
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
        except Exception:
            pass
        pygame.mixer.quit()
        pygame.mixer.init(frequency=sample_rate, size=-bits, channels=channels, buffer=4096)
        self._audio_sample_rate = sample_rate
        self._audio_channels    = channels
        self._audio_bits        = bits

    def _reset_audio_state(self):
        if self.audio_check_timer:
            self.audio_check_timer.stop()
            self.audio_check_timer = None
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
        except Exception:
            pass
        self._cleanup_tmp_file()
        self._audio_play_start   = 0.0
        self._audio_min_duration = 0.0
        self._audio_sample_rate  = -1
        self._audio_channels     = -1
        self._audio_bits         = -1
        self._audio_chunks       = []
        self._audio_total_chunks = 0
        self._pending_msg_type   = ""
        self._pending_msg_data   = {}

    def _cleanup_tmp_file(self):
        if self._tmp_audio_path:
            try:
                os.unlink(self._tmp_audio_path)
            except Exception:
                pass
            self._tmp_audio_path = None

    def _reset_ui_for_new_session(self):
        self.stacked.setVisible(True)
        self.stacked.setCurrentIndex(0)
        self.interview_container.setVisible(False)
        self.connect_btn.setEnabled(True)
        self.connect_btn.setText(self.t("start_btn"))
        self.session_input.setEnabled(True)
        self.session_input.clear()
        self.status_label.setText(self.t("status_disconnected"))
        self.status_detail.setText(self.t("waiting_connection"))
        self._set_chip_state("disconnected")
        self.statusBar().showMessage(self.t("vocal_mode_label"))
        if self.audio_recorder:
            try:
                self.audio_recorder.cleanup()
            except Exception:
                pass
            self.audio_recorder = None

    def _connect_to_interview(self):
        if self.is_connecting:
            return
        session_id = self.session_input.text().strip()
        if not session_id or not session_id.startswith("session_"):
            self._show_error_dialog(self.t("error_title"), self.t("format_error"))
            return

        if self.websocket_client:
            try:
                self.websocket_client.disconnected.disconnect()
                self.websocket_client.connected.disconnect()
                self.websocket_client.message_received.disconnect()
                self.websocket_client.error_occurred.disconnect()
            except Exception:
                pass
            try:
                self.websocket_client.disconnect_from_server()
            except Exception:
                pass
            self.websocket_client = None

        self._session_token += 1
        current_token = self._session_token
        self._reset_audio_state()
        self.interview_widget.set_language(self._language)
        self._refresh_lang_pill()

        self.session_id    = session_id
        self.is_connecting = True
        self.connect_btn.setEnabled(False)
        self.connect_btn.setText(self.t("connecting"))
        self.session_input.setEnabled(False)
        self._set_chip_state("validating")
        self.status_label.setText(self.t("status_validating"))

        ws_url = f"{settings.WEBSOCKET_URL}/ws/interview/{session_id}?lang={self._language}"
        self.websocket_client = WebSocketClient(ws_url)

        self.websocket_client.disconnected.connect(
            lambda c, r: self._on_ws_disconnected(c, r, current_token))
        self.websocket_client.connected.connect(
            lambda: self._on_ws_connected(current_token))
        self.websocket_client.message_received.connect(
            lambda d: self._on_ws_message(d, current_token))
        self.websocket_client.error_occurred.connect(
            lambda e: self._on_ws_error(e, current_token))

        self.websocket_client.connect_to_server()
        self.statusBar().showMessage("Connexion…")

    def _is_active(self, token): return token == self._session_token

    def _on_ws_connected(self, token):
        if not self._is_active(token): return
        self._set_chip_state("validating")
        self.status_label.setText(self.t("status_validating"))

    def _on_ws_disconnected(self, code, reason, token):
        if not self._is_active(token): return
        if self.is_connecting:
            self._handle_connection_failure(reason or f"Code {code}")
            return
        self._reset_audio_state()
        self._reset_ui_for_new_session()

    def _on_ws_error(self, error, token):
        if not self._is_active(token): return
        self.statusBar().showMessage(f"Erreur : {error}")

    # ── WebSocket message handler ─────────────────────────────────────────────

    def _on_ws_message(self, data: dict, token: int):
        if not self._is_active(token): return
        msg_type = data.get("type")
        msg_data = data.get("data", {})

        if msg_type == "error":
            err = msg_data.get("message", "Erreur")
            if msg_data.get("error_type") == "SESSION_INVALID":
                self._handle_connection_failure(err)
            else:
                self._show_error_dialog(self.t("error_title"), err)
            return

        if msg_type == "question_loading":
            self.interview_widget.update_question(msg_data.get("progress", {}))
            self.statusBar().showMessage(self.t("generating_audio"))
            self.video_player.set_speaking()
            return

        if msg_type in ("welcome", "question", "interview_completed"):
            if msg_data.get("audio_mode") == "chunked":
                self._pending_msg_type   = msg_type
                self._pending_msg_data   = msg_data
                self._audio_chunks       = []
                self._audio_total_chunks = msg_data.get("total_chunks", 0)
                sr   = msg_data.get("sample_rate", 22050)
                ch   = msg_data.get("channels", 1)
                bits = msg_data.get("bits_per_sample", 16)
                self._ensure_audio_format(sr, ch, bits)
                return
            audio_b64 = msg_data.get("audio_data")
            if audio_b64:
                self._play_bytes_direct(base64.b64decode(audio_b64))
            self._finalize_message(msg_type, msg_data)
            return

        if msg_type == "audio_chunk_data":
            self._audio_chunks.append(msg_data.get("data", ""))
            return

        if msg_type == "audio_chunk_end":
            if self._audio_chunks:
                try:
                    pcm = b"".join(base64.b64decode(c) for c in self._audio_chunks)
                    self._play_pcm(pcm)
                except Exception as e:
                    logger.error(f"PCM error: {e}")
                    self.interview_widget.enable_recording(True)
            else:
                self.interview_widget.enable_recording(True)
            self._finalize_message(self._pending_msg_type, self._pending_msg_data)
            self._audio_chunks       = []
            self._pending_msg_type   = ""
            self._pending_msg_data   = {}
            return

        if msg_type == "answer_saved":
            self.statusBar().showMessage(self.t("answer_saved"))
            self.video_player.set_idle()
            self._set_chip_state("connected")

    def _finalize_message(self, msg_type, msg_data):
        if msg_type == "welcome":
            self.is_connecting = False
            self.status_label.setText(self.t("status_connected"))
            self.status_detail.setText(self.t("vocal_mode_active"))
            self._set_chip_state("connected")
            self.stacked.setVisible(False)
            self.interview_container.setVisible(True)
            if not self.audio_recorder:
                self.audio_recorder = AudioRecorder()
                self.audio_recorder.audio_chunk_ready.connect(self._on_audio_chunk)
            self.video_player.set_speaking()
            self.statusBar().showMessage(self.t("welcome_status"))

        elif msg_type == "question":
            self.interview_widget.update_question(msg_data.get("progress", {}))
            self.interview_widget.set_audio_playing()
            self.video_player.set_speaking()
            self.statusBar().showMessage(self.t("question_status"))

        elif msg_type == "interview_completed":
            self._show_info_dialog(self.t("interview_complete"), self.t("thanks_message"))
            self.statusBar().showMessage("✓ Terminé")
            self._reset_audio_state()
            self._reset_ui_for_new_session()

    # ── Audio playback ────────────────────────────────────────────────────────

    def _play_pcm(self, pcm_bytes: bytes):
        try:
            if self.audio_check_timer:
                self.audio_check_timer.stop()
                self.audio_check_timer = None
            try:
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()
            except Exception:
                pass
            self._cleanup_tmp_file()

            tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            self._tmp_audio_path = tmp.name
            tmp.close()

            with wave.open(self._tmp_audio_path, "wb") as wf:
                wf.setnchannels(self._audio_channels)
                wf.setsampwidth(self._audio_bits // 8)
                wf.setframerate(self._audio_sample_rate)
                wf.writeframes(pcm_bytes)

            bps = self._audio_sample_rate * self._audio_channels * (self._audio_bits // 8)
            theoretical_ms = (len(pcm_bytes) / bps * 1000) if bps > 0 else 3000
            self._audio_min_duration = max(theoretical_ms * 0.9, 800)
            self._audio_play_start   = time.monotonic() * 1000

            pygame.mixer.music.load(self._tmp_audio_path)
            pygame.mixer.music.play()

            self.audio_check_timer = QTimer()
            self.audio_check_timer.timeout.connect(self._check_audio_finished)
            self.audio_check_timer.start(200)
        except Exception as e:
            logger.error(f"_play_pcm: {e}")
            self._cleanup_tmp_file()
            self.interview_widget.enable_recording(True)

    def _check_audio_finished(self):
        elapsed_ms = time.monotonic() * 1000 - self._audio_play_start
        if elapsed_ms < self._audio_min_duration:
            return
        if not pygame.mixer.music.get_busy():
            if self.audio_check_timer:
                self.audio_check_timer.stop()
                self.audio_check_timer = None
            try:
                pygame.mixer.music.unload()
            except Exception:
                pass
            self._cleanup_tmp_file()
            self.video_player.set_idle()
            if self.websocket_client:
                self.websocket_client.send_message({"type": "audio_finished"})
            self.interview_widget.enable_recording(True)
            self.statusBar().showMessage(self.t("answer_status"))

    def _play_bytes_direct(self, audio_bytes: bytes):
        if audio_bytes[:4] == b"RIFF":
            import struct
            fmt_idx  = audio_bytes.find(b"fmt ", 12)
            data_idx = audio_bytes.find(b"data", 12)
            if fmt_idx != -1 and data_idx != -1:
                sr  = struct.unpack_from("<I", audio_bytes, fmt_idx + 12)[0]
                ch  = struct.unpack_from("<H", audio_bytes, fmt_idx + 10)[0]
                bps = struct.unpack_from("<H", audio_bytes, fmt_idx + 22)[0]
                self._ensure_audio_format(sr, ch, bps)
                self._play_pcm(audio_bytes[data_idx + 8:])
                return
        self._play_pcm(audio_bytes)

    # ── Recording ─────────────────────────────────────────────────────────────

    def _on_start_recording(self):
        if self.audio_recorder:
            self.audio_recorder.start_recording()
            self.video_player.set_listening()
            self.statusBar().showMessage("● Enregistrement…")

    def _on_stop_recording(self):
        if self.audio_recorder:
            self.audio_recorder.stop_recording()
            if self.websocket_client:
                self.websocket_client.send_message({"type": "answer_complete"})
            self.video_player.set_idle()
            self.interview_widget.enable_recording(False)

    def _on_audio_chunk(self, audio_data: bytes):
        if self.websocket_client:
            self.websocket_client.send_message({
                "type":       "audio_chunk",
                "audio_data": base64.b64encode(audio_data).decode(),
            })

    def _on_end_interview(self):
        reply = QMessageBox.question(
            self, self.t("end_title"), self.t("end_confirm"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes and self.websocket_client:
            self.websocket_client.send_message({"type": "end_interview"})

    # ── Error helpers ─────────────────────────────────────────────────────────

    def _handle_connection_failure(self, msg: str):
        self.is_connecting = False
        self._reset_audio_state()
        self.connect_btn.setEnabled(True)
        self.connect_btn.setText(self.t("start_btn"))
        self.session_input.setEnabled(True)
        self._set_chip_state("error")
        self.status_label.setText(self.t("status_disconnected"))
        if self.websocket_client:
            try:
                self.websocket_client.disconnected.disconnect()
                self.websocket_client.connected.disconnect()
                self.websocket_client.message_received.disconnect()
                self.websocket_client.error_occurred.disconnect()
            except Exception:
                pass
            try:
                self.websocket_client.disconnect_from_server()
            except Exception:
                pass
            self.websocket_client = None
        self._show_error_dialog(self.t("error_title"), msg)

    def _show_error_dialog(self, title, msg):
        b = QMessageBox(self)
        b.setIcon(QMessageBox.Icon.Critical)
        b.setWindowTitle(title)
        b.setText(msg)
        b.exec()

    def _show_info_dialog(self, title, msg):
        b = QMessageBox(self)
        b.setIcon(QMessageBox.Icon.Information)
        b.setWindowTitle(title)
        b.setText(msg)
        b.exec()

    def closeEvent(self, event):
        if self.websocket_client:
            try:
                self.websocket_client.disconnected.disconnect()
                self.websocket_client.connected.disconnect()
                self.websocket_client.message_received.disconnect()
                self.websocket_client.error_occurred.disconnect()
            except Exception:
                pass
            self.websocket_client.disconnect_from_server()
        if self.audio_recorder:
            self.audio_recorder.cleanup()
        if self.audio_check_timer:
            self.audio_check_timer.stop()
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
        except Exception:
            pass
        self._cleanup_tmp_file()
        try:
            pygame.mixer.quit()
        except Exception:
            pass
        super().closeEvent(event)