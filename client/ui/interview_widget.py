"""
Widget d'Interview - MODE VOCAL PUR - MULTILINGUE AR/FR/EN
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton,
    QLabel, QProgressBar, QFrame, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont, QColor
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from client.ui.stark_theme import StarkTheme
from client.ui.icons import StarkIcons


# ============================================================
# TEXTES LOCALISÉS DU WIDGET D'INTERVIEW
# ============================================================

WIDGET_TEXTS = {
    "ar": {
        "vocal_mode":       "الوضع الصوتي",
        "progress":         "السؤال {current}/{total}",
        "listen_title":     "استمع بعناية",
        "listen_sub":       "ستُطرح عليك الأسئلة صوتياً فقط.\nاستمع جيداً للصورة الرمزية، ثم أجب بوضوح.",
        "waiting":          "🔊 في انتظار السؤال...",
        "playing":          "🔊 يُشغَّل السؤال...",
        "ready":            "✅ جاهز للإجابة",
        "start_answer":     " ابدأ الإجابة",
        "stop_answer":      " إيقاف التسجيل",
        "end_interview":    " إنهاء المقابلة",
    },
    "fr": {
        "vocal_mode":       "MODE VOCAL",
        "progress":         "Question {current}/{total}",
        "listen_title":     "ÉCOUTEZ ATTENTIVEMENT",
        "listen_sub":       "Les questions vous seront posées uniquement en vocal.\nÉcoutez bien l'avatar, puis répondez clairement.",
        "waiting":          "🔊 En attente de la question...",
        "playing":          "🔊 Question en cours de lecture...",
        "ready":            "✅ Prêt à répondre",
        "start_answer":     " COMMENCER À RÉPONDRE",
        "stop_answer":      " ARRÊTER L'ENREGISTREMENT",
        "end_interview":    " TERMINER L'ENTRETIEN",
    },
    "en": {
        "vocal_mode":       "VOCAL MODE",
        "progress":         "Question {current}/{total}",
        "listen_title":     "LISTEN CAREFULLY",
        "listen_sub":       "Questions will be asked in audio only.\nListen to the avatar, then answer clearly.",
        "waiting":          "🔊 Waiting for the question...",
        "playing":          "🔊 Question playing...",
        "ready":            "✅ Ready to answer",
        "start_answer":     " START ANSWERING",
        "stop_answer":      " STOP RECORDING",
        "end_interview":    " END INTERVIEW",
    },
}


class InterviewWidget(QWidget):
    """
    Widget de contrôles d'entretien - MODE VOCAL PUR - MULTILINGUE
    """

    start_recording = Signal()
    stop_recording = Signal()
    end_interview = Signal()

    def __init__(self, language: str = "fr", parent=None):
        super().__init__(parent)
        self._language = language
        self.is_recording = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(StarkTheme.SPACING_MD_INT)

        # En-tête
        self.header_label = QLabel()
        self.header_label.setFont(QFont(StarkTheme.FONT_FAMILY_PRIMARY, 14, QFont.Weight.Bold))
        self.header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.header_label.setStyleSheet(f"""
            QLabel {{
                color: {StarkTheme.WHITE};
                background: {StarkTheme.GRADIENT_ACCENT};
                padding: {StarkTheme.SPACING_MD};
                border-radius: {StarkTheme.RADIUS_MEDIUM};
                letter-spacing: 2px;
            }}
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(StarkTheme.ORANGE_ACCENT))
        shadow.setOffset(0, 3)
        self.header_label.setGraphicsEffect(shadow)
        layout.addWidget(self.header_label)

        # Progression
        progress_card = self._create_progress_card()
        layout.addWidget(progress_card)

        # Indicateur vocal
        vocal_card = self._create_vocal_indicator()
        layout.addWidget(vocal_card)

        layout.addStretch()

        # Bouton enregistrement
        self.record_button = self._create_record_button()
        layout.addWidget(self.record_button)

        # Bouton fin
        self.end_button = self._create_end_button()
        layout.addWidget(self.end_button)

        # Appliquer la langue initiale
        self._apply_language()

    def t(self, key: str) -> str:
        return WIDGET_TEXTS.get(self._language, WIDGET_TEXTS["fr"]).get(key, key)

    def set_language(self, language: str):
        """Changer la langue de l'interface."""
        self._language = language
        self._apply_language()

    def _apply_language(self):
        """Met à jour tous les textes selon la langue courante."""
        self.header_label.setText(self.t("vocal_mode"))
        self.listen_title.setText(self.t("listen_title"))
        self.listen_sub.setText(self.t("listen_sub"))
        self.audio_status.setText(self.t("waiting"))
        self._update_audio_status_style("waiting")
        if self.is_recording:
            self.record_button.setText(self.t("stop_answer"))
        else:
            self.record_button.setText(self.t("start_answer"))
        self.end_button.setText(self.t("end_interview"))
        # RTL pour l'arabe
        if self._language == "ar":
            self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        else:
            self.setLayoutDirection(Qt.LayoutDirection.LeftToRight)

    def _create_progress_card(self) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {StarkTheme.WHITE};
                border: 2px solid {StarkTheme.BLUE_EXTRA_LIGHT};
                border-radius: {StarkTheme.RADIUS_LARGE};
                padding: {StarkTheme.SPACING_LG};
            }}
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(StarkTheme.SPACING_MD_INT)

        self.progress_label = QLabel("Question 0/0")
        self.progress_label.setFont(QFont(StarkTheme.FONT_FAMILY_PRIMARY, 12, QFont.Weight.Bold))
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_label.setStyleSheet(f"color: {StarkTheme.BLUE_PRIMARY}; letter-spacing: 1px;")
        card_layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        self.progress_bar.setFixedHeight(28)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                border-radius: {StarkTheme.RADIUS_MEDIUM};
                text-align: center;
                background: {StarkTheme.GRAY_EXTRA_LIGHT};
                color: {StarkTheme.WHITE};
                font-weight: bold;
                font-size: 12px;
            }}
            QProgressBar::chunk {{
                background: {StarkTheme.GRADIENT_PRIMARY};
                border-radius: {StarkTheme.RADIUS_MEDIUM};
            }}
        """)
        card_layout.addWidget(self.progress_bar)
        return card

    def _create_vocal_indicator(self) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {StarkTheme.WHITE};
                border: 2px solid {StarkTheme.ORANGE_ACCENT};
                border-radius: {StarkTheme.RADIUS_LARGE};
                padding: {StarkTheme.SPACING_XL};
            }}
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(StarkTheme.SPACING_LG_INT)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon_label = QLabel()
        icon_label.setPixmap(StarkIcons.headphones(StarkTheme.ORANGE_ACCENT).pixmap(QSize(80, 80)))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(icon_label)

        self.listen_title = QLabel()
        self.listen_title.setFont(QFont(StarkTheme.FONT_FAMILY_PRIMARY, 18, QFont.Weight.ExtraBold))
        self.listen_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.listen_title.setStyleSheet(f"color: {StarkTheme.ORANGE_ACCENT}; letter-spacing: 2px;")
        card_layout.addWidget(self.listen_title)

        self.listen_sub = QLabel()
        self.listen_sub.setFont(QFont(StarkTheme.FONT_FAMILY_PRIMARY, 12))
        self.listen_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.listen_sub.setWordWrap(True)
        self.listen_sub.setStyleSheet(f"""
            color: {StarkTheme.GRAY_DARK};
            padding: {StarkTheme.SPACING_MD};
            line-height: 1.6;
        """)
        card_layout.addWidget(self.listen_sub)

        self.audio_status = QLabel()
        self.audio_status.setFont(QFont(StarkTheme.FONT_FAMILY_PRIMARY, 11, QFont.Weight.Bold))
        self.audio_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._update_audio_status_style("waiting")
        card_layout.addWidget(self.audio_status)

        return card

    def _create_record_button(self) -> QPushButton:
        btn = QPushButton()
        btn.setFont(QFont(StarkTheme.FONT_FAMILY_PRIMARY, 12, QFont.Weight.Bold))
        btn.setMinimumHeight(55)
        btn.setIcon(StarkIcons.microphone())
        btn.setIconSize(QSize(24, 24))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(StarkTheme.get_button_style("primary"))
        btn.clicked.connect(self._on_record_clicked)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(StarkTheme.BLUE_PRIMARY))
        shadow.setOffset(0, 5)
        btn.setGraphicsEffect(shadow)
        return btn

    def _create_end_button(self) -> QPushButton:
        btn = QPushButton()
        btn.setFont(QFont(StarkTheme.FONT_FAMILY_PRIMARY, 11, QFont.Weight.Bold))
        btn.setMinimumHeight(45)
        btn.setIcon(StarkIcons.power())
        btn.setIconSize(QSize(20, 20))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {StarkTheme.GRADIENT_ACCENT};
                color: {StarkTheme.WHITE};
                border: none;
                border-radius: {StarkTheme.RADIUS_MEDIUM};
                padding: 12px;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{ background: {StarkTheme.ORANGE_LIGHT}; }}
            QPushButton:pressed {{ background: {StarkTheme.ORANGE_ACCENT}; }}
        """)
        btn.clicked.connect(self.end_interview.emit)
        return btn

    def _on_record_clicked(self):
        if not self.is_recording:
            self.start_recording.emit()
            self.is_recording = True
            self._update_record_button(True)
        else:
            self.stop_recording.emit()
            self.is_recording = False
            self._update_record_button(False)

    def _update_record_button(self, is_recording: bool):
        if is_recording:
            self.record_button.setText(self.t("stop_answer"))
            self.record_button.setIcon(StarkIcons.stop_circle())
            self.record_button.setStyleSheet(f"""
                QPushButton {{
                    background: {StarkTheme.ERROR};
                    color: {StarkTheme.WHITE};
                    border: none;
                    border-radius: {StarkTheme.RADIUS_MEDIUM};
                    padding: 15px;
                    font-size: {StarkTheme.FONT_SIZE_MEDIUM};
                    font-weight: bold;
                    letter-spacing: 1px;
                }}
                QPushButton:hover {{ background: #C0392B; }}
            """)
        else:
            self.record_button.setText(self.t("start_answer"))
            self.record_button.setIcon(StarkIcons.microphone())
            self.record_button.setStyleSheet(StarkTheme.get_button_style("primary"))

    def _update_audio_status_style(self, state: str):
        """state: 'waiting' | 'playing' | 'ready'"""
        styles = {
            "waiting": (StarkTheme.BLUE_PRIMARY, StarkTheme.BLUE_EXTRA_LIGHT),
            "playing": (StarkTheme.ORANGE_ACCENT, StarkTheme.ORANGE_LIGHT),
            "ready":   ("#27AE60", "#E8F5E9"),
        }
        color, bg = styles.get(state, styles["waiting"])
        self.audio_status.setStyleSheet(f"""
            color: {color};
            background: {bg};
            padding: {StarkTheme.SPACING_MD};
            border-radius: {StarkTheme.RADIUS_MEDIUM};
            font-weight: bold;
        """)
        if state == "waiting":
            self.audio_status.setText(self.t("waiting"))

    def update_question(self, progress: dict):
        current = progress.get("current", 0)
        total   = progress.get("total", 0)
        pct     = progress.get("percentage", 0)
        self.progress_label.setText(
            self.t("progress").format(current=current, total=total)
        )
        self.progress_bar.setValue(pct)
        self.audio_status.setText(self.t("playing"))
        self._update_audio_status_style("playing")

    def set_audio_playing(self):
        self.audio_status.setText(self.t("playing"))
        self._update_audio_status_style("playing")

    def set_ready_to_answer(self):
        self.audio_status.setText(self.t("ready"))
        self._update_audio_status_style("ready")

    def enable_recording(self, enabled: bool):
        self.record_button.setEnabled(enabled)
        if enabled:
            self.set_ready_to_answer()