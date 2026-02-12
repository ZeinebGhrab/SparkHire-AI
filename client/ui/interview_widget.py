"""
Widget d'Interview - Design Professionnel Stark Solutions
Utilise la palette de couleurs officielle de stark-solutions.online
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QProgressBar, QTextEdit, QFrame, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont, QColor
import sys
from pathlib import Path

# Import du thème et des icônes
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from .stark_theme import StarkTheme
from .icons import StarkIcons


class InterviewWidget(QWidget):
    """
    Widget de contrôles d'entretien - Design Professionnel Stark Solutions
    Utilise la charte graphique officielle stark-solutions.online
    """
    
    start_recording = Signal()
    stop_recording = Signal()
    end_interview = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.is_recording = False
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(StarkTheme.SPACING_MD)
        
        # ========== EN-TÊTE ==========
        header = self._create_header()
        layout.addWidget(header)
        
        # ========== PROGRESSION ==========
        progress_card = self._create_progress_card()
        layout.addWidget(progress_card)
        
        # ========== QUESTION ACTUELLE ==========
        question_card = self._create_question_card()
        layout.addWidget(question_card)
        
        # ========== TRANSCRIPTION ==========
        transcript_card = self._create_transcript_card()
        layout.addWidget(transcript_card)
        
        layout.addStretch()
        
        # ========== BOUTONS D'ACTION ==========
        self.record_button = self._create_record_button()
        layout.addWidget(self.record_button)
        
        self.end_button = self._create_end_button()
        layout.addWidget(self.end_button)
    
    def _create_header(self) -> QWidget:
        """Créer l'en-tête du widget"""
        header = QLabel("PANNEAU DE CONTRÔLE")
        header.setFont(QFont(StarkTheme.FONT_FAMILY_PRIMARY, 14, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet(f"""
            QLabel {{
                color: {StarkTheme.WHITE};
                background: {StarkTheme.GRADIENT_HEADER};
                padding: {StarkTheme.SPACING_MD};
                border-radius: {StarkTheme.RADIUS_MEDIUM};
                letter-spacing: 2px;
            }}
        """)
        
        # Ombre
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(StarkTheme.BLUE_PRIMARY))
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
        card_layout.setSpacing(StarkTheme.SPACING_MD)
        
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
    
    def _create_question_card(self) -> QFrame:
        """Créer la carte de question"""
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
        card_layout.setSpacing(StarkTheme.SPACING_MD)
        
        # Header avec icône
        header_layout = QHBoxLayout()
        
        icon_label = QLabel()
        icon_label.setPixmap(StarkIcons.help_circle().pixmap(QSize(20, 20)))
        header_layout.addWidget(icon_label)
        
        title = QLabel("QUESTION ACTUELLE")
        title.setFont(QFont(StarkTheme.FONT_FAMILY_PRIMARY, 11, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {StarkTheme.BLUE_PRIMARY}; letter-spacing: 1px;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        card_layout.addLayout(header_layout)
        
        # Texte de la question
        self.question_text = QLabel("En attente de connexion...")
        self.question_text.setFont(QFont(StarkTheme.FONT_FAMILY_PRIMARY, 13))
        self.question_text.setWordWrap(True)
        self.question_text.setStyleSheet(f"""
            QLabel {{
                color: {StarkTheme.GRAY_DARK};
                padding: {StarkTheme.SPACING_MD};
                background: {StarkTheme.GRAY_EXTRA_LIGHT};
                border: 1px solid {StarkTheme.GRAY_LIGHT};
                border-radius: {StarkTheme.RADIUS_MEDIUM};
                line-height: 1.6;
            }}
        """)
        self.question_text.setMinimumHeight(100)
        card_layout.addWidget(self.question_text)
        
        return card
    
    def _create_transcript_card(self) -> QFrame:
        """Créer la carte de transcription"""
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
        card_layout.setSpacing(StarkTheme.SPACING_MD)
        
        # Header
        header_layout = QHBoxLayout()
        
        icon_label = QLabel()
        icon_label.setPixmap(StarkIcons.file_text().pixmap(QSize(20, 20)))
        header_layout.addWidget(icon_label)
        
        title = QLabel("TRANSCRIPTION")
        title.setFont(QFont(StarkTheme.FONT_FAMILY_PRIMARY, 11, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {StarkTheme.BLUE_PRIMARY}; letter-spacing: 1px;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        card_layout.addLayout(header_layout)
        
        # Zone de texte
        self.transcript_text = QTextEdit()
        self.transcript_text.setReadOnly(True)
        self.transcript_text.setMaximumHeight(120)
        self.transcript_text.setPlaceholderText("Votre réponse apparaîtra ici...")
        self.transcript_text.setStyleSheet(f"""
            QTextEdit {{
                background: {StarkTheme.GRAY_EXTRA_LIGHT};
                border: 1px solid {StarkTheme.GRAY_LIGHT};
                border-radius: {StarkTheme.RADIUS_MEDIUM};
                padding: {StarkTheme.SPACING_MD};
                color: {StarkTheme.GRAY_DARK};
                font-size: 11px;
                font-family: {StarkTheme.FONT_FAMILY_MONO};
            }}
        """)
        card_layout.addWidget(self.transcript_text)
        
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
        
        # Ombre
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
    
    def update_question(self, question_text: str, progress: dict):
        """Mettre à jour la question"""
        self.question_text.setText(question_text)
        self.progress_label.setText(f"Question {progress['current']}/{progress['total']}")
        self.progress_bar.setValue(progress['percentage'])
    
    def update_transcript(self, transcript: str):
        """Mettre à jour la transcription"""
        self.transcript_text.setPlainText(transcript)
    
    def enable_recording(self, enabled: bool):
        """Activer/désactiver l'enregistrement"""
        self.record_button.setEnabled(enabled)