"""
Fenêtre Principale - MULTILINGUE AR/FR/EN
Écran de sélection de langue élégant au démarrage.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QMessageBox, QLabel, QLineEdit, QPushButton, QFrame,
    QGraphicsDropShadowEffect, QStackedWidget, QButtonGroup
)
from PySide6.QtCore import Qt, QSize, QTimer, QPropertyAnimation, QEasingCurve, QRect
from PySide6.QtGui import QFont, QColor
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


# ============================================================
# TEXTES UI LOCALISÉS
# ============================================================

UI_TEXTS = {
    "ar": {
        "app_subtitle":        "مقابلة صوتية ذكية - وضع صوتي خالص",
        "choose_language":     "اختر لغة المقابلة",
        "choose_subtitle":     "سيتم إجراء المقابلة بالكامل باللغة المختارة",
        "enter_session":       "أدخل معرّف الجلسة",
        "session_placeholder": "session_xxxxxxxxxxxxx",
        "start_btn":           "بدء المقابلة",
        "connecting":          "جارٍ الاتصال...",
        "status_disconnected": "غير متصل",
        "status_connected":    "متصل",
        "status_validating":   "جارٍ التحقق",
        "waiting_connection":  "في انتظار الاتصال",
        "vocal_mode_active":   "الوضع الصوتي نشط",
        "vocal_mode_label":    "الوضع الصوتي",
        "welcome_status":      "مرحباً — استمع لرسالة الترحيب",
        "question_status":     "🔊 السؤال قيد التشغيل...",
        "answer_status":       "✅ يمكنك الإجابة",
        "answer_saved":        "✅ تم حفظ الإجابة",
        "generating_audio":    "⏳ توليد الصوت...",
        "end_confirm":         "هل تريد إنهاء المقابلة؟",
        "interview_complete":  "انتهت المقابلة",
        "thanks_message":      "شكراً لك! انتهت المقابلة.",
        "format_error":        "الصيغة المطلوبة: session_xxxxxxxxxxxxx",
        "error_title":         "خطأ",
        "end_title":           "إنهاء المقابلة",
        "back_btn":            "← رجوع",
        "language_name":       "العربية",
        "confirm_yes":         "نعم",
        "confirm_no":          "لا",
    },
    "fr": {
        "app_subtitle":        "Entretien Vocal Intelligent - Mode Vocal Pur",
        "choose_language":     "Choisissez la langue de l'entretien",
        "choose_subtitle":     "L'entretien se déroulera entièrement dans la langue choisie",
        "enter_session":       "Entrez votre identifiant de session",
        "session_placeholder": "session_xxxxxxxxxxxxx",
        "start_btn":           "DÉMARRER L'ENTRETIEN",
        "connecting":          "CONNEXION EN COURS...",
        "status_disconnected": "DÉCONNECTÉ",
        "status_connected":    "CONNECTÉ",
        "status_validating":   "VALIDATION",
        "waiting_connection":  "En attente de connexion",
        "vocal_mode_active":   "Mode vocal actif",
        "vocal_mode_label":    "MODE VOCAL",
        "welcome_status":      "🎧 Bienvenue — écoutez le message d'accueil",
        "question_status":     "🔊 Question en lecture...",
        "answer_status":       "✅ Vous pouvez répondre",
        "answer_saved":        "✅ Réponse enregistrée",
        "generating_audio":    "⏳ Génération audio...",
        "end_confirm":         "Confirmer la fin de l'entretien?",
        "interview_complete":  "Entretien Terminé",
        "thanks_message":      "Merci ! L'entretien est terminé.",
        "format_error":        "Format attendu: session_xxxxxxxxxxxxx",
        "error_title":         "Erreur",
        "end_title":           "Terminer",
        "back_btn":            "← Retour",
        "language_name":       "Français",
        "confirm_yes":         "Oui",
        "confirm_no":          "Non",
    },
    "en": {
        "app_subtitle":        "AI Voice Interview - Pure Vocal Mode",
        "choose_language":     "Choose your interview language",
        "choose_subtitle":     "The entire interview will be conducted in the selected language",
        "enter_session":       "Enter your session ID",
        "session_placeholder": "session_xxxxxxxxxxxxx",
        "start_btn":           "START INTERVIEW",
        "connecting":          "CONNECTING...",
        "status_disconnected": "DISCONNECTED",
        "status_connected":    "CONNECTED",
        "status_validating":   "VALIDATING",
        "waiting_connection":  "Waiting for connection",
        "vocal_mode_active":   "Vocal mode active",
        "vocal_mode_label":    "VOCAL MODE",
        "welcome_status":      "🎧 Welcome — listen to the welcome message",
        "question_status":     "🔊 Question playing...",
        "answer_status":       "✅ You may answer now",
        "answer_saved":        "✅ Answer saved",
        "generating_audio":    "⏳ Generating audio...",
        "end_confirm":         "Confirm end of interview?",
        "interview_complete":  "Interview Complete",
        "thanks_message":      "Thank you! The interview is complete.",
        "format_error":        "Expected format: session_xxxxxxxxxxxxx",
        "error_title":         "Error",
        "end_title":           "End Interview",
        "back_btn":            "← Back",
        "language_name":       "English",
        "confirm_yes":         "Yes",
        "confirm_no":          "No",
    },
}

LANGUAGE_OPTIONS = [
    {
        "code":    "ar",
        "flag":    "🇸🇦",
        "name":    "العربية",
        "sub":     "Arabic",
        "rtl":     True,
        "color":   "#1E7E34",
    },
    {
        "code":    "fr",
        "flag":    "🇫🇷",
        "name":    "Français",
        "sub":     "French",
        "rtl":     False,
        "color":   "#003189",
    },
    {
        "code":    "en",
        "flag":    "🇬🇧",
        "name":    "English",
        "sub":     "Anglais",
        "rtl":     False,
        "color":   "#C8102E",
    },
]


class LanguageCard(QFrame):
    """Carte cliquable de sélection de langue."""

    def __init__(self, lang_data: dict, on_select, parent=None):
        super().__init__(parent)
        self.lang_data = lang_data
        self.on_select = on_select
        self._selected = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(200, 220)
        self._apply_style(False)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 25, 20, 25)

        # Flag emoji (large)
        flag = QLabel(self.lang_data["flag"])
        flag.setFont(QFont("Segoe UI Emoji", 52))
        flag.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(flag)

        # Language name
        name = QLabel(self.lang_data["name"])
        name.setFont(QFont(StarkTheme.FONT_FAMILY_PRIMARY, 16, QFont.Weight.Bold))
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name.setStyleSheet("color: #1A1A2E; background: transparent;")
        layout.addWidget(name)

        # Subtitle
        sub = QLabel(self.lang_data["sub"])
        sub.setFont(QFont(StarkTheme.FONT_FAMILY_PRIMARY, 10))
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet("color: #7F8C8D; background: transparent;")
        layout.addWidget(sub)

    def _apply_style(self, selected: bool):
        color = self.lang_data["color"]
        if selected:
            self.setStyleSheet(f"""
                LanguageCard {{
                    background: white;
                    border: 3px solid {color};
                    border-radius: 20px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                LanguageCard {{
                    background: white;
                    border: 2px solid #E0E0E0;
                    border-radius: 20px;
                }}
                LanguageCard:hover {{
                    border: 2px solid {color};
                    background: #FAFAFA;
                }}
            """)

    def set_selected(self, selected: bool):
        self._selected = selected
        self._apply_style(selected)
        if selected:
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(25)
            shadow.setColor(QColor(self.lang_data["color"]))
            shadow.setOffset(0, 6)
            self.setGraphicsEffect(shadow)
        else:
            self.setGraphicsEffect(None)

    def mousePressEvent(self, event):
        self.on_select(self.lang_data["code"])
        super().mousePressEvent(event)


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.websocket_client = None
        self.audio_recorder = None
        self.session_id = None
        self.is_connecting = False
        self._session_token: int = 0

        # Langue sélectionnée (défaut français)
        self._language: str = "fr"
        self._lang_cards: dict = {}

        # ── Audio ──
        self._tmp_audio_path: str | None = None
        self._audio_play_start: float = 0.0
        self._audio_min_duration: float = 0.0
        self.audio_check_timer = None

        self._audio_sample_rate: int = -1
        self._audio_channels: int = -1
        self._audio_bits: int = -1

        self._pending_msg_type: str = ""
        self._pending_msg_data: dict = {}
        self._audio_chunks: list = []
        self._audio_total_chunks: int = 0

        pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=4096)
        self._audio_sample_rate = 22050
        self._audio_channels = 1
        self._audio_bits = 16
        logger.info(f"🎵 pygame.mixer initialisé: {self._audio_sample_rate}Hz")

        self._setup_ui()

    def t(self, key: str) -> str:
        """Traduction dans la langue courante."""
        return UI_TEXTS.get(self._language, UI_TEXTS["fr"]).get(key, key)

    # ================================================================
    # GESTION AUDIO
    # ================================================================

    def _ensure_audio_format(self, sample_rate: int, channels: int, bits: int):
        if (sample_rate == self._audio_sample_rate
                and channels == self._audio_channels
                and bits == self._audio_bits):
            return
        logger.info(f"Format audio: {self._audio_sample_rate}Hz → {sample_rate}Hz/{channels}ch/{bits}bit")
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
        except Exception:
            pass
        pygame.mixer.quit()
        pygame.mixer.init(frequency=sample_rate, size=-(bits), channels=channels, buffer=4096)
        self._audio_sample_rate = sample_rate
        self._audio_channels = channels
        self._audio_bits = bits
        logger.info(f"🎵 pygame.mixer reinitialisé: {sample_rate}Hz {channels}ch {bits}bit")

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
        self._audio_play_start = 0.0
        self._audio_min_duration = 0.0
        self._audio_sample_rate = -1
        self._audio_channels = -1
        self._audio_bits = -1
        self._audio_chunks = []
        self._audio_total_chunks = 0
        self._pending_msg_type = ""
        self._pending_msg_data = {}
        logger.info("🔄 Etat audio reinitialise")

    def _cleanup_tmp_file(self):
        if self._tmp_audio_path:
            try:
                os.unlink(self._tmp_audio_path)
            except Exception:
                pass
            self._tmp_audio_path = None

    def _reset_ui_for_new_session(self):
        # Retour à l'écran de sélection de langue
        self.stacked.setCurrentIndex(0)
        self.interview_container.setVisible(False)
        self.connect_btn.setEnabled(True)
        self.connect_btn.setText(self.t("start_btn"))
        self.session_input.setEnabled(True)
        self.session_input.clear()
        self.status_label.setText(self.t("status_disconnected"))
        self.status_label.setStyleSheet(f"color: {StarkTheme.WHITE}; letter-spacing: 1px;")
        self.status_detail.setText(self.t("waiting_connection"))
        self.statusBar().showMessage("🎧 " + self.t("vocal_mode_label"))
        if self.audio_recorder:
            try:
                self.audio_recorder.cleanup()
            except Exception:
                pass
            self.audio_recorder = None
        logger.info("🔄 UI reinitialisee")

    # ================================================================
    # UI PRINCIPALE
    # ================================================================

    def _setup_ui(self):
        self.setWindowTitle("Stark Recruitment AI - Entretien Vocal")
        self.showMaximized()
        self.setStyleSheet(f"QMainWindow {{ background: #F0F4F8; }}")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        main_layout.addWidget(self._create_header())

        # Stacked: 0 = langue, 1 = session ID, 2 = interview
        self.stacked = QStackedWidget()
        self.stacked.addWidget(self._create_language_screen())   # index 0
        self.stacked.addWidget(self._create_connection_widget())  # index 1
        main_layout.addWidget(self.stacked, stretch=1)

        self.interview_container = self._create_interview_container()
        self.interview_container.setVisible(False)
        main_layout.addWidget(self.interview_container)

        self._setup_statusbar()

    def _create_header(self) -> QWidget:
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #003E7E, stop:1 #0066CC);
                border-bottom: 3px solid {StarkTheme.ORANGE_ACCENT};
            }}
        """)
        header.setFixedHeight(80)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(StarkTheme.BLUE_DARK))
        shadow.setOffset(0, 3)
        header.setGraphicsEffect(shadow)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(40, 15, 40, 15)

        logo = QLabel()
        logo.setPixmap(StarkIcons.logo_stark().pixmap(QSize(50, 50)))
        layout.addWidget(logo)

        tw = QWidget()
        twl = QVBoxLayout(tw)
        twl.setContentsMargins(10, 0, 0, 0)
        twl.setSpacing(2)

        main_title = QLabel("STARK RECRUITMENT AI")
        main_title.setFont(QFont(StarkTheme.FONT_FAMILY_PRIMARY, 20, QFont.Weight.ExtraBold))
        main_title.setStyleSheet(f"color: {StarkTheme.WHITE}; letter-spacing: 2px;")
        twl.addWidget(main_title)

        self.header_subtitle = QLabel(self.t("app_subtitle"))
        self.header_subtitle.setFont(QFont(StarkTheme.FONT_FAMILY_PRIMARY, 10))
        self.header_subtitle.setStyleSheet(f"color: {StarkTheme.BLUE_EXTRA_LIGHT};")
        twl.addWidget(self.header_subtitle)

        layout.addWidget(tw)
        layout.addStretch()
        self.status_container = self._create_status_indicator()
        layout.addWidget(self.status_container)
        return header

    def _create_status_indicator(self) -> QWidget:
        container = QFrame()
        container.setStyleSheet(f"""
            QFrame {{
                background: rgba(255,255,255,0.1);
                border: 1px solid rgba(255,255,255,0.2);
                border-radius: {StarkTheme.RADIUS_MEDIUM};
                padding: 8px 15px;
            }}
        """)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(10)

        self.status_icon_label = QLabel()
        self.status_icon_label.setPixmap(StarkIcons.activity().pixmap(QSize(24, 24)))
        layout.addWidget(self.status_icon_label)

        stc = QWidget()
        stl = QVBoxLayout(stc)
        stl.setContentsMargins(0, 0, 0, 0)
        stl.setSpacing(0)

        self.status_label = QLabel(self.t("status_disconnected"))
        self.status_label.setFont(QFont(StarkTheme.FONT_FAMILY_PRIMARY, 11, QFont.Weight.Bold))
        self.status_label.setStyleSheet(f"color: {StarkTheme.WHITE}; letter-spacing: 1px;")
        stl.addWidget(self.status_label)

        self.status_detail = QLabel(self.t("waiting_connection"))
        self.status_detail.setFont(QFont(StarkTheme.FONT_FAMILY_PRIMARY, 8))
        self.status_detail.setStyleSheet(f"color: {StarkTheme.BLUE_EXTRA_LIGHT};")
        stl.addWidget(self.status_detail)

        layout.addWidget(stc)
        return container

    # ================================================================
    # ÉCRAN 1 : SÉLECTION DE LANGUE
    # ================================================================

    def _create_language_screen(self) -> QWidget:
        screen = QWidget()
        screen.setStyleSheet("QWidget { background: transparent; }")
        layout = QVBoxLayout(screen)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(40)
        layout.setContentsMargins(40, 40, 40, 40)

        # ─ Titre ─
        title = QLabel(self.t("choose_language"))
        title.setFont(QFont("Segoe UI", 28, QFont.Weight.ExtraBold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            color: #1A1A2E;
            letter-spacing: 1px;
        """)
        layout.addWidget(title)

        subtitle = QLabel(self.t("choose_subtitle"))
        subtitle.setFont(QFont(StarkTheme.FONT_FAMILY_PRIMARY, 12))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #7F8C8D;")
        layout.addWidget(subtitle)

        # ─ Cartes de langue ─
        cards_container = QWidget()
        cards_layout = QHBoxLayout(cards_container)
        cards_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cards_layout.setSpacing(30)

        self._lang_cards = {}
        for lang_data in LANGUAGE_OPTIONS:
            card = LanguageCard(lang_data, self._on_language_selected)
            self._lang_cards[lang_data["code"]] = card
            cards_layout.addWidget(card)

        layout.addWidget(cards_container)

        # ─ Bouton confirmer ─
        self.lang_confirm_btn = QPushButton("✓  Confirmer")
        self.lang_confirm_btn.setFont(QFont(StarkTheme.FONT_FAMILY_PRIMARY, 14, QFont.Weight.Bold))
        self.lang_confirm_btn.setFixedSize(280, 55)
        self.lang_confirm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lang_confirm_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {StarkTheme.ORANGE_ACCENT}, stop:1 {StarkTheme.ORANGE_LIGHT});
                color: white;
                border: none;
                border-radius: 27px;
                font-size: 15px;
                font-weight: bold;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{ background: {StarkTheme.ORANGE_LIGHT}; }}
            QPushButton:pressed {{ background: {StarkTheme.ORANGE_ACCENT}; }}
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(StarkTheme.ORANGE_ACCENT))
        shadow.setOffset(0, 6)
        self.lang_confirm_btn.setGraphicsEffect(shadow)
        self.lang_confirm_btn.clicked.connect(self._on_language_confirmed)
        layout.addWidget(self.lang_confirm_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        # Sélection par défaut
        self._on_language_selected("fr")
        return screen

    def _on_language_selected(self, code: str):
        self._language = code
        for c, card in self._lang_cards.items():
            card.set_selected(c == code)
        # Met à jour le texte du bouton confirmer
        lang_name = next(l["name"] for l in LANGUAGE_OPTIONS if l["code"] == code)
        self.lang_confirm_btn.setText(f"✓  {lang_name}")

    def _on_language_confirmed(self):
        """Passe à l'écran de saisie de session ID."""
        # Met à jour les textes de l'interface selon la langue
        self._update_ui_language()
        self.stacked.setCurrentIndex(1)

    def _update_ui_language(self):
        """Met à jour tous les textes de l'UI selon la langue choisie."""
        self.header_subtitle.setText(self.t("app_subtitle"))
        self.status_label.setText(self.t("status_disconnected"))
        self.status_detail.setText(self.t("waiting_connection"))
        # Boutons écran connexion
        self.connect_btn.setText(self.t("start_btn"))
        self.session_input.setPlaceholderText(self.t("session_placeholder"))
        self.back_btn.setText(self.t("back_btn"))
        # Titre écran connexion
        self.conn_title.setText(self.t("enter_session"))
        # Interview widget
        if hasattr(self, 'interview_widget'):
            self.interview_widget.set_language(self._language)
        self.statusBar().showMessage("🎧 " + self.t("vocal_mode_label"))

    # ================================================================
    # ÉCRAN 2 : SESSION ID
    # ================================================================

    def _create_connection_widget(self) -> QWidget:
        widget = QWidget()
        widget.setStyleSheet("QWidget { background: transparent; }")
        outer = QVBoxLayout(widget)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: white;
                border: 2px solid {StarkTheme.BLUE_EXTRA_LIGHT};
                border-radius: 24px;
            }}
        """)
        card.setFixedSize(560, 430)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setColor(QColor(StarkTheme.BLUE_PRIMARY))
        shadow.setOffset(0, 10)
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(55, 40, 55, 40)
        card_layout.setSpacing(18)

        # Icône
        icon_container = QFrame()
        icon_container.setStyleSheet(
            f"QFrame {{ background: {StarkTheme.BLUE_EXTRA_LIGHT}; border-radius: 40px; }}"
        )
        icon_container.setFixedSize(80, 80)
        il = QVBoxLayout(icon_container)
        il.setAlignment(Qt.AlignmentFlag.AlignCenter)
        shield_icon = QLabel()
        shield_icon.setPixmap(StarkIcons.headphones(StarkTheme.ORANGE_ACCENT).pixmap(QSize(50, 50)))
        il.addWidget(shield_icon)
        card_layout.addWidget(icon_container, alignment=Qt.AlignmentFlag.AlignCenter)

        # Titre
        self.conn_title = QLabel(self.t("enter_session"))
        self.conn_title.setFont(QFont(StarkTheme.FONT_FAMILY_PRIMARY, 16, QFont.Weight.Bold))
        self.conn_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.conn_title.setStyleSheet(f"color: {StarkTheme.BLUE_DARK};")
        card_layout.addWidget(self.conn_title)

        # Indicateur de langue choisie
        self.chosen_lang_label = QLabel()
        self.chosen_lang_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.chosen_lang_label.setFont(QFont(StarkTheme.FONT_FAMILY_PRIMARY, 11))
        self.chosen_lang_label.setStyleSheet(f"""
            color: {StarkTheme.GRAY_MEDIUM};
            background: {StarkTheme.GRAY_EXTRA_LIGHT};
            border-radius: 12px;
            padding: 5px 12px;
        """)
        self._refresh_chosen_lang_label()
        card_layout.addWidget(self.chosen_lang_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Input session
        self.session_input = QLineEdit()
        self.session_input.setPlaceholderText(self.t("session_placeholder"))
        self.session_input.setFont(QFont(StarkTheme.FONT_FAMILY_MONO, 12, QFont.Weight.Bold))
        self.session_input.setMinimumHeight(52)
        self.session_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.session_input.setStyleSheet(f"""
            QLineEdit {{
                background: {StarkTheme.GRAY_EXTRA_LIGHT};
                border: 2px solid {StarkTheme.GRAY_LIGHT};
                border-radius: {StarkTheme.RADIUS_MEDIUM};
                padding: {StarkTheme.SPACING_MD};
                color: {StarkTheme.GRAY_DARK};
            }}
            QLineEdit:focus {{
                border: 2px solid {StarkTheme.ORANGE_ACCENT};
                background: {StarkTheme.WHITE};
            }}
        """)
        card_layout.addWidget(self.session_input)

        # Bouton démarrer
        self.connect_btn = QPushButton(self.t("start_btn"))
        self.connect_btn.setFont(QFont(StarkTheme.FONT_FAMILY_PRIMARY, 13, QFont.Weight.Bold))
        self.connect_btn.setMinimumHeight(55)
        self.connect_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.connect_btn.setStyleSheet(StarkTheme.get_button_style("accent"))
        self.connect_btn.clicked.connect(self._connect_to_interview)
        card_layout.addWidget(self.connect_btn)

        # Bouton retour
        self.back_btn = QPushButton(self.t("back_btn"))
        self.back_btn.setFont(QFont(StarkTheme.FONT_FAMILY_PRIMARY, 10))
        self.back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.back_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {StarkTheme.GRAY_MEDIUM};
                border: none;
            }}
            QPushButton:hover {{ color: {StarkTheme.BLUE_PRIMARY}; }}
        """)
        self.back_btn.clicked.connect(lambda: self.stacked.setCurrentIndex(0))
        card_layout.addWidget(self.back_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        outer.addWidget(card)
        return widget

    def _refresh_chosen_lang_label(self):
        lang_data = next((l for l in LANGUAGE_OPTIONS if l["code"] == self._language), None)
        if lang_data and hasattr(self, 'chosen_lang_label'):
            self.chosen_lang_label.setText(f"{lang_data['flag']}  {lang_data['name']}")

    # ================================================================
    # INTERVIEW CONTAINER
    # ================================================================

    def _create_interview_container(self) -> QWidget:
        container = QWidget()
        container.setStyleSheet("QWidget { background: transparent; }")
        layout = QHBoxLayout(container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        self.video_player = VideoPlayerWidget()
        layout.addWidget(self.video_player, stretch=2)

        self.interview_widget = InterviewWidget(language=self._language)
        self.interview_widget.setMaximumWidth(450)
        self.interview_widget.start_recording.connect(self._on_start_recording)
        self.interview_widget.stop_recording.connect(self._on_stop_recording)
        self.interview_widget.end_interview.connect(self._on_end_interview)
        layout.addWidget(self.interview_widget, stretch=1)

        return container

    def _setup_statusbar(self):
        self.statusBar().setStyleSheet(f"""
            QStatusBar {{
                background: {StarkTheme.WHITE};
                color: {StarkTheme.GRAY_DARK};
                font-size: 11px; font-weight: bold;
                padding: 8px;
                border-top: 1px solid {StarkTheme.GRAY_LIGHT};
            }}
        """)
        self.statusBar().showMessage("🎧 " + self.t("vocal_mode_label"))

    # ================================================================
    # CONNEXION
    # ================================================================

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

        # Met à jour la langue de l'interview widget
        self.interview_widget.set_language(self._language)
        self._refresh_chosen_lang_label()

        self.session_id = session_id
        self.is_connecting = True
        self.connect_btn.setEnabled(False)
        self.connect_btn.setText(self.t("connecting"))
        self.session_input.setEnabled(False)

        ws_url = f"{settings.WEBSOCKET_URL}/ws/interview/{session_id}"
        self.websocket_client = WebSocketClient(ws_url)

        self.websocket_client.disconnected.connect(
            lambda code, reason: self._on_ws_disconnected(code, reason, current_token)
        )
        self.websocket_client.connected.connect(
            lambda: self._on_ws_connected(current_token)
        )
        self.websocket_client.message_received.connect(
            lambda data: self._on_ws_message(data, current_token)
        )
        self.websocket_client.error_occurred.connect(
            lambda err: self._on_ws_error(err, current_token)
        )

        self.websocket_client.connect_to_server()
        self.statusBar().showMessage("🔍 Connexion...")

    def _is_active(self, token: int) -> bool:
        return token == self._session_token

    def _on_ws_connected(self, token: int):
        if not self._is_active(token):
            return
        logger.info("✅ WebSocket connecté")
        self.status_label.setText(self.t("status_validating"))
        self.status_label.setStyleSheet(
            f"color: {StarkTheme.WARNING}; letter-spacing: 1px; font-weight: bold;"
        )

    def _on_ws_disconnected(self, code: int, reason: str, token: int):
        if not self._is_active(token):
            return
        if self.is_connecting:
            self._handle_connection_failure(reason or f"Code {code}")
            return
        logger.info(f"Session terminée (code={code})")
        self._reset_audio_state()
        self._reset_ui_for_new_session()

    def _on_ws_error(self, error: str, token: int):
        if not self._is_active(token):
            return
        self.statusBar().showMessage(f"❌ {error}")

    # ================================================================
    # MESSAGES WEBSOCKET
    # ================================================================

    def _on_ws_message(self, data: dict, token: int):
        if not self._is_active(token):
            return

        msg_type = data.get("type")
        msg_data = data.get("data", {})
        logger.info(f"📨 {msg_type}")

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
                self._pending_msg_type = msg_type
                self._pending_msg_data = msg_data
                self._audio_chunks = []
                self._audio_total_chunks = msg_data.get("total_chunks", 0)
                sr   = msg_data.get("sample_rate", 22050)
                ch   = msg_data.get("channels", 1)
                bits = msg_data.get("bits_per_sample", 16)
                self._ensure_audio_format(sr, ch, bits)
                logger.info(f"Chunked: {self._audio_total_chunks} @ {sr}Hz pour '{msg_type}'")
                return
            audio_b64 = msg_data.get("audio_data")
            if audio_b64:
                self._play_bytes_direct(base64.b64decode(audio_b64))
            self._finalize_message(msg_type, msg_data)
            return

        if msg_type == "audio_chunk_data":
            self._audio_chunks.append(msg_data.get("data", ""))
            idx, total = msg_data.get("chunk_index", 0), msg_data.get("total", 1)
            self.statusBar().showMessage(f"📦 Audio {idx + 1}/{total}...")
            return

        if msg_type == "audio_chunk_end":
            if self._audio_chunks:
                try:
                    pcm_bytes = b"".join(base64.b64decode(c) for c in self._audio_chunks)
                    logger.info(
                        f"✅ PCM: {len(self._audio_chunks)} chunks → "
                        f"{len(pcm_bytes):,} B @ {self._audio_sample_rate}Hz"
                    )
                    self._play_pcm(pcm_bytes)
                except Exception as e:
                    logger.error(f"❌ Assemblage PCM: {e}")
                    self.interview_widget.enable_recording(True)
            else:
                self.interview_widget.enable_recording(True)

            self._finalize_message(self._pending_msg_type, self._pending_msg_data)
            self._audio_chunks = []
            self._pending_msg_type = ""
            self._pending_msg_data = {}
            return

        if msg_type == "answer_saved":
            logger.info("✅ Réponse sauvegardée")
            self.statusBar().showMessage(self.t("answer_saved"))
            self.video_player.set_idle()

    def _finalize_message(self, msg_type: str, msg_data: dict):
        if msg_type == "welcome":
            self.is_connecting = False
            self.status_label.setText(self.t("status_connected"))
            self.status_label.setStyleSheet(
                f"color: {StarkTheme.SUCCESS}; letter-spacing: 1px; font-weight: bold;"
            )
            self.status_detail.setText(self.t("vocal_mode_active"))
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
            self.statusBar().showMessage("🎉 Terminé!")
            self._reset_audio_state()
            self._reset_ui_for_new_session()

    # ================================================================
    # LECTURE AUDIO
    # ================================================================

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

            bytes_per_sec = (
                self._audio_sample_rate * self._audio_channels * (self._audio_bits // 8)
            )
            theoretical_ms = (
                (len(pcm_bytes) / bytes_per_sec) * 1000 if bytes_per_sec > 0 else 3000
            )
            self._audio_min_duration = max(theoretical_ms * 0.9, 800)
            self._audio_play_start = time.monotonic() * 1000

            pygame.mixer.music.load(self._tmp_audio_path)
            pygame.mixer.music.play()

            logger.info(
                f"▶️ Lecture: {len(pcm_bytes):,} B "
                f"@ {self._audio_sample_rate}Hz {self._audio_channels}ch {self._audio_bits}bit "
                f"(~{theoretical_ms/1000:.1f}s)"
            )

            self.audio_check_timer = QTimer()
            self.audio_check_timer.timeout.connect(self._check_audio_finished)
            self.audio_check_timer.start(200)

        except Exception as e:
            logger.error(f"❌ _play_pcm: {e}")
            self._cleanup_tmp_file()
            self.interview_widget.enable_recording(True)

    def _check_audio_finished(self):
        now_ms = time.monotonic() * 1000
        elapsed_ms = now_ms - self._audio_play_start

        if elapsed_ms < self._audio_min_duration:
            return

        if not pygame.mixer.music.get_busy():
            logger.info(f"✅ Lecture terminée ({elapsed_ms/1000:.1f}s)")
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

    # ================================================================
    # ENREGISTREMENT
    # ================================================================

    def _on_start_recording(self):
        if self.audio_recorder:
            self.audio_recorder.start_recording()
            self.video_player.set_listening()
            self.statusBar().showMessage("🎤 Enregistrement...")

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
                "audio_data": base64.b64encode(audio_data).decode("utf-8"),
            })

    def _on_end_interview(self):
        reply = QMessageBox.question(
            self, self.t("end_title"), self.t("end_confirm"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes and self.websocket_client:
            self.websocket_client.send_message({"type": "end_interview"})

    # ================================================================
    # UTILITAIRES
    # ================================================================

    def _handle_connection_failure(self, msg: str):
        self.is_connecting = False
        self._reset_audio_state()
        self.connect_btn.setEnabled(True)
        self.connect_btn.setText(self.t("start_btn"))
        self.session_input.setEnabled(True)
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

    def _show_error_dialog(self, title: str, msg: str):
        b = QMessageBox(self)
        b.setIcon(QMessageBox.Icon.Critical)
        b.setWindowTitle(title)
        b.setText(msg)
        b.exec()

    def _show_info_dialog(self, title: str, msg: str):
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