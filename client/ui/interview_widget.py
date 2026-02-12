from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QProgressBar, QTextEdit, QFrame
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont
from client.ui.icons import StarkIcons

class InterviewWidget(QWidget):
    """Widget de contrôles d'entretien - Design Stark Solutions"""
    
    # Palette Stark
    STARK_BLUE_PRIMARY = "#1565C0"
    STARK_BLUE_DARK = "#0D47A1"
    STARK_BLUE_LIGHT = "#42A5F5"
    STARK_ACCENT = "#FF6B35"
    STARK_BG_DARK = "#0A1929"
    STARK_BG_CARD = "#132F4C"
    STARK_SUCCESS = "#00E676"
    
    start_recording = Signal()
    stop_recording = Signal()
    end_interview = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)
        
        # Titre
        title = QLabel("CONTRÔLES")
        title.setFont(QFont("Arial", 14, QFont.Weight.ExtraBold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"""
            color: #FFFFFF;
            padding: 10px;
            background: {self.STARK_BLUE_PRIMARY};
            border-radius: 8px;
            letter-spacing: 2px;
        """)
        layout.addWidget(title)
        
        # Barre de progression Stark
        progress_container = QFrame()
        progress_container.setStyleSheet(f"""
            QFrame {{
                background: {self.STARK_BG_CARD};
                border: 2px solid {self.STARK_BLUE_PRIMARY};
                border-radius: 10px;
                padding: 10px;
            }}
        """)
        progress_layout = QVBoxLayout(progress_container)
        progress_layout.setSpacing(8)
        
        self.progress_label = QLabel("Question 0/0")
        self.progress_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_label.setStyleSheet(f"color: {self.STARK_BLUE_LIGHT};")
        progress_layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        self.progress_bar.setFixedHeight(28)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid {self.STARK_BLUE_PRIMARY};
                border-radius: 8px;
                text-align: center;
                background: {self.STARK_BG_DARK};
                color: #FFFFFF;
                font-weight: bold;
                font-size: 11px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {self.STARK_BLUE_PRIMARY}, 
                    stop:1 {self.STARK_BLUE_LIGHT});
                border-radius: 6px;
            }}
        """)
        progress_layout.addWidget(self.progress_bar)
        
        layout.addWidget(progress_container)
        
        # Zone de question
        question_container = QFrame()
        question_container.setStyleSheet(f"""
            QFrame {{
                background: {self.STARK_BG_CARD};
                border: 2px solid {self.STARK_BLUE_PRIMARY};
                border-radius: 12px;
                padding: 15px;
            }}
        """)
        question_layout = QVBoxLayout(question_container)
        question_layout.setSpacing(8)
        
        # Label avec icône
        question_header = QHBoxLayout()
        question_icon = QLabel()
        question_icon.setPixmap(StarkIcons.help_circle(self.STARK_ACCENT).pixmap(QSize(20, 20)))
        question_header.addWidget(question_icon)
        
        question_label = QLabel("QUESTION ACTUELLE")
        question_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        question_label.setStyleSheet(f"color: {self.STARK_BLUE_LIGHT}; letter-spacing: 1px;")
        question_header.addWidget(question_label)
        question_header.addStretch()
        question_layout.addLayout(question_header)
        
        self.question_text = QLabel("En attente de connexion...")
        self.question_text.setFont(QFont("Arial", 12, QFont.Weight.Medium))
        self.question_text.setWordWrap(True)
        self.question_text.setStyleSheet(f"""
            color: #FFFFFF;
            padding: 10px;
            background: {self.STARK_BG_DARK};
            border-radius: 8px;
        """)
        self.question_text.setMinimumHeight(100)
        question_layout.addWidget(self.question_text)
        
        layout.addWidget(question_container)
        
        # Zone de transcription
        transcript_header = QHBoxLayout()
        transcript_icon = QLabel()
        transcript_icon.setPixmap(StarkIcons.file_text(self.STARK_BLUE_LIGHT).pixmap(QSize(20, 20)))
        transcript_header.addWidget(transcript_icon)
        
        transcript_label = QLabel("TRANSCRIPTION")
        transcript_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        transcript_label.setStyleSheet(f"color: {self.STARK_BLUE_LIGHT}; letter-spacing: 1px;")
        transcript_header.addWidget(transcript_label)
        transcript_header.addStretch()
        layout.addLayout(transcript_header)
        
        self.transcript_text = QTextEdit()
        self.transcript_text.setReadOnly(True)
        self.transcript_text.setMaximumHeight(120)
        self.transcript_text.setPlaceholderText("Votre réponse apparaîtra ici...")
        self.transcript_text.setStyleSheet(f"""
            QTextEdit {{
                background: {self.STARK_BG_DARK};
                border: 2px solid {self.STARK_BLUE_PRIMARY};
                border-radius: 10px;
                padding: 12px;
                color: #FFFFFF;
                font-size: 11px;
                font-family: 'Courier New';
            }}
        """)
        layout.addWidget(self.transcript_text)
        
        # Spacer
        layout.addStretch()
        
        # Bouton Répondre avec icône
        self.record_button = QPushButton()
        self._update_record_button_style(False)
        self.record_button.setFont(QFont("Arial", 11, QFont.Weight.ExtraBold))
        self.record_button.setMinimumHeight(55)
        self.record_button.setIcon(StarkIcons.microphone())
        self.record_button.setIconSize(QSize(24, 24))
        self.record_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.record_button.clicked.connect(self._on_record_clicked)
        layout.addWidget(self.record_button)
        
        # Bouton Terminer avec icône
        self.end_button = QPushButton(" TERMINER")
        self.end_button.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.end_button.setMinimumHeight(45)
        self.end_button.setIcon(StarkIcons.power())
        self.end_button.setIconSize(QSize(20, 20))
        self.end_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.end_button.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {self.STARK_ACCENT}, 
                    stop:1 #C0392B);
                color: white;
                border: none;
                border-radius: 10px;
                padding: 12px;
                font-size: 10px;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #FF8555, 
                    stop:1 #D35400);
            }}
            QPushButton:pressed {{
                background: #A93226;
            }}
        """)
        self.end_button.clicked.connect(self.end_interview.emit)
        layout.addWidget(self.end_button)
        
        # État
        self.is_recording = False
    
    def _update_record_button_style(self, is_recording: bool):
        """Mettre à jour le style du bouton d'enregistrement"""
        if is_recording:
            self.record_button.setText(" ARRÊTER")
            self.record_button.setIcon(StarkIcons.stop_circle())
            self.record_button.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {self.STARK_ACCENT}, 
                        stop:1 #C0392B);
                    color: white;
                    border: none;
                    border-radius: 12px;
                    padding: 15px;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #FF8555, 
                        stop:1 #D35400);
                }}
            """)
        else:
            self.record_button.setText(" RÉPONDRE")
            self.record_button.setIcon(StarkIcons.microphone())
            self.record_button.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {self.STARK_SUCCESS}, 
                        stop:1 #16A085);
                    color: white;
                    border: none;
                    border-radius: 12px;
                    padding: 15px;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #2ECC71, 
                        stop:1 #1ABC9C);
                }}
                QPushButton:pressed {{
                    background: #229954;
                }}
                QPushButton:disabled {{
                    background: rgba(127, 140, 141, 0.5);
                }}
            """)
    
    def _on_record_clicked(self):
        """Toggle recording"""
        if not self.is_recording:
            self.start_recording.emit()
            self.is_recording = True
            self._update_record_button_style(True)
        else:
            self.stop_recording.emit()
            self.is_recording = False
            self._update_record_button_style(False)
    
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