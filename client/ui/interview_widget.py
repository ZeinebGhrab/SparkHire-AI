"""
Widget d'Interview - MODE VOCAL PUR
Les questions ne sont PAS affichées à l'écran, uniquement en audio
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QProgressBar, QTextEdit, QFrame, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont, QColor
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from client.ui.stark_theme import StarkTheme
from client.ui.icons import StarkIcons


class InterviewWidget(QWidget):
    """
    Widget de contrôles d'entretien - MODE VOCAL PUR
    Affiche uniquement la progression, pas le texte des questions
    """
    
    start_recording = Signal()
    stop_recording = Signal()
    end_interview = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.is_recording = False
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(StarkTheme.SPACING_MD_INT)  
        
        # ========== EN-TÊTE ==========
        header = self._create_header()
        layout.addWidget(header)
        
        # ========== PROGRESSION ==========
        progress_card = self._create_progress_card()
        layout.addWidget(progress_card)
        
        # ========== INDICATEUR VOCAL ==========
        vocal_indicator = self._create_vocal_indicator()
        layout.addWidget(vocal_indicator)
        
        # ========== TRANSCRIPTION (optionnelle, cachée par défaut) ==========
        # SUPPRIMÉ - Pas de transcription affichée en mode vocal pur
        
        layout.addStretch()
        
        # ========== BOUTONS D'ACTION ==========
        self.record_button = self._create_record_button()
        layout.addWidget(self.record_button)
        
        self.end_button = self._create_end_button()
        layout.addWidget(self.end_button)
    
    def _create_header(self) -> QWidget:
        """Créer l'en-tête du widget"""
        header = QLabel("MODE VOCAL")
        header.setFont(QFont(StarkTheme.FONT_FAMILY_PRIMARY, 14, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet(f"""
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
        header.setGraphicsEffect(shadow)
        
        return header
    
    def _create_progress_card(self) -> QFrame:
        """Créer la carte de progression"""
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
        
        # Label progression
        self.progress_label = QLabel("Question 0/0")
        self.progress_label.setFont(QFont(StarkTheme.FONT_FAMILY_PRIMARY, 12, QFont.Weight.Bold))
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_label.setStyleSheet(f"""
            color: {StarkTheme.BLUE_PRIMARY};
            letter-spacing: 1px;
        """)
        card_layout.addWidget(self.progress_label)
        
        # Barre de progression
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
        """Créer l'indicateur de mode vocal"""
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
        
        # Icône principale
        icon_label = QLabel()
        icon_label.setPixmap(StarkIcons.headphones(StarkTheme.ORANGE_ACCENT).pixmap(QSize(80, 80)))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(icon_label)
        
        # Message principal
        message = QLabel("ÉCOUTEZ ATTENTIVEMENT")
        message.setFont(QFont(StarkTheme.FONT_FAMILY_PRIMARY, 18, QFont.Weight.ExtraBold))
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message.setStyleSheet(f"""
            color: {StarkTheme.ORANGE_ACCENT};
            letter-spacing: 2px;
        """)
        card_layout.addWidget(message)
        
        # Instructions
        instructions = QLabel(
            "Les questions vous seront posées uniquement en vocal.\n"
            "Écoutez bien l'avatar, puis répondez clairement."
        )
        instructions.setFont(QFont(StarkTheme.FONT_FAMILY_PRIMARY, 12))
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instructions.setWordWrap(True)
        instructions.setStyleSheet(f"""
            color: {StarkTheme.GRAY_DARK};
            padding: {StarkTheme.SPACING_MD};
            line-height: 1.6;
        """)
        card_layout.addWidget(instructions)
        
        # Statut de l'audio
        self.audio_status = QLabel("🔊 En attente de la question...")
        self.audio_status.setFont(QFont(StarkTheme.FONT_FAMILY_PRIMARY, 11, QFont.Weight.Bold))
        self.audio_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.audio_status.setStyleSheet(f"""
            color: {StarkTheme.BLUE_PRIMARY};
            background: {StarkTheme.BLUE_EXTRA_LIGHT};
            padding: {StarkTheme.SPACING_MD};
            border-radius: {StarkTheme.RADIUS_MEDIUM};
        """)
        card_layout.addWidget(self.audio_status)
        
        return card
    
    def _create_record_button(self) -> QPushButton:
        """Créer le bouton d'enregistrement"""
        btn = QPushButton(" COMMENCER À RÉPONDRE")
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
        """Créer le bouton de fin"""
        btn = QPushButton(" TERMINER L'ENTRETIEN")
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
            QPushButton:hover {{
                background: {StarkTheme.ORANGE_LIGHT};
            }}
            QPushButton:pressed {{
                background: {StarkTheme.ORANGE_ACCENT};
            }}
        """)
        btn.clicked.connect(self.end_interview.emit)
        
        return btn
    
    def _on_record_clicked(self):
        """Toggle recording"""
        if not self.is_recording:
            self.start_recording.emit()
            self.is_recording = True
            self._update_record_button(True)
        else:
            self.stop_recording.emit()
            self.is_recording = False
            self._update_record_button(False)
    
    def _update_record_button(self, is_recording: bool):
        """Mettre à jour l'apparence du bouton"""
        if is_recording:
            self.record_button.setText(" ARRÊTER L'ENREGISTREMENT")
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
                QPushButton:hover {{
                    background: #C0392B;
                }}
            """)
        else:
            self.record_button.setText(" COMMENCER À RÉPONDRE")
            self.record_button.setIcon(StarkIcons.microphone())
            self.record_button.setStyleSheet(StarkTheme.get_button_style("primary"))
    
    def update_question(self, progress: dict):
        """
        Mettre à jour UNIQUEMENT la progression (pas de texte de question)
        Mode vocal pur: seule la progression est affichée
        """
        self.progress_label.setText(f"Question {progress['current']}/{progress['total']}")
        self.progress_bar.setValue(progress['percentage'])
        self.audio_status.setText("🔊 Question en cours de lecture...")
        self.audio_status.setStyleSheet(f"""
            color: {StarkTheme.ORANGE_ACCENT};
            background: {StarkTheme.ORANGE_LIGHT};
            padding: {StarkTheme.SPACING_MD};
            border-radius: {StarkTheme.RADIUS_MEDIUM};
            font-weight: bold;
        """)
    
    def set_audio_playing(self):
        """Indiquer que l'audio est en cours de lecture"""
        self.audio_status.setText("🔊 Écoutez la question...")
        self.audio_status.setStyleSheet(f"""
            color: {StarkTheme.ORANGE_ACCENT};
            background: {StarkTheme.ORANGE_LIGHT};
            padding: {StarkTheme.SPACING_MD};
            border-radius: {StarkTheme.RADIUS_MEDIUM};
            font-weight: bold;
        """)
    
    def set_ready_to_answer(self):
        """Indiquer que le candidat peut répondre"""
        self.audio_status.setText("✅ Prêt à répondre")
        self.audio_status.setStyleSheet(f"""
            color: {StarkTheme.SUCCESS};
            background: #E8F5E9;
            padding: {StarkTheme.SPACING_MD};
            border-radius: {StarkTheme.RADIUS_MEDIUM};
            font-weight: bold;
        """)
    
    def enable_recording(self, enabled: bool):
        """Activer/désactiver l'enregistrement"""
        self.record_button.setEnabled(enabled)
        
        if enabled:
            self.set_ready_to_answer()