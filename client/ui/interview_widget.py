from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QProgressBar, QTextEdit, QFrame, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal, QSize, QTimer, QPropertyAnimation, QEasingCurve, QPoint
from PySide6.QtGui import QFont, QColor
from client.ui.icons import StarkIcons

class InterviewWidget(QWidget):
    """Widget de contrôles - Design Fluide et Créatif"""
    
    # Palette Stark améliorée
    STARK_BLUE_PRIMARY = "#1565C0"
    STARK_BLUE_DARK = "#0D47A1"
    STARK_BLUE_LIGHT = "#42A5F5"
    STARK_BLUE_GLOW = "#64B5F6"
    STARK_ACCENT = "#FF6B35"
    STARK_ACCENT_GLOW = "#FF8555"
    STARK_BG_DARK = "#0A1929"
    STARK_BG_CARD = "#132F4C"
    STARK_SUCCESS = "#00E676"
    STARK_SUCCESS_GLOW = "#00FF88"
    
    start_recording = Signal()
    stop_recording = Signal()
    end_interview = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.is_recording = False
        self.pulse_animation = None
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)
        
        # Titre avec effet néon
        title = QLabel("CONTRÔLES")
        title.setFont(QFont("Arial", 14, QFont.Weight.ExtraBold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"""
            color: #FFFFFF;
            padding: 12px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {self.STARK_BLUE_PRIMARY},
                stop:0.5 {self.STARK_BLUE_LIGHT},
                stop:1 {self.STARK_BLUE_PRIMARY});
            border-radius: 12px;
            letter-spacing: 3px;
            text-shadow: 0 0 10px {self.STARK_BLUE_GLOW};
        """)
        
        # Ombre lumineuse
        title_shadow = QGraphicsDropShadowEffect()
        title_shadow.setBlurRadius(15)
        title_shadow.setColor(QColor(self.STARK_BLUE_GLOW))
        title_shadow.setOffset(0, 3)
        title.setGraphicsEffect(title_shadow)
        
        layout.addWidget(title)
        
        # Barre de progression avec effet liquide
        progress_container = QFrame()
        progress_container.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(19, 47, 76, 0.7),
                    stop:1 rgba(13, 71, 161, 0.5));
                border: 2px solid rgba(66, 165, 245, 0.4);
                border-radius: 15px;
                padding: 15px;
            }}
        """)
        
        progress_shadow = QGraphicsDropShadowEffect()
        progress_shadow.setBlurRadius(20)
        progress_shadow.setColor(QColor(21, 101, 192, 80))
        progress_shadow.setOffset(0, 5)
        progress_container.setGraphicsEffect(progress_shadow)
        
        progress_layout = QVBoxLayout(progress_container)
        progress_layout.setSpacing(10)
        
        self.progress_label = QLabel("Question 0/0")
        self.progress_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_label.setStyleSheet(f"""
            color: {self.STARK_BLUE_GLOW};
            letter-spacing: 2px;
            text-shadow: 0 0 8px {self.STARK_BLUE_GLOW};
        """)
        progress_layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        self.progress_bar.setFixedHeight(32)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                border-radius: 16px;
                text-align: center;
                background: rgba(10, 25, 41, 0.8);
                color: #FFFFFF;
                font-weight: bold;
                font-size: 12px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {self.STARK_SUCCESS},
                    stop:0.5 {self.STARK_BLUE_LIGHT},
                    stop:1 {self.STARK_ACCENT});
                border-radius: 16px;
                box-shadow: 0 0 15px {self.STARK_SUCCESS_GLOW};
            }}
        """)
        progress_layout.addWidget(self.progress_bar)
        
        layout.addWidget(progress_container)
        
        # Zone de question avec glassmorphism
        question_container = QFrame()
        question_container.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(19, 47, 76, 0.6),
                    stop:1 rgba(10, 25, 41, 0.8));
                border: 2px solid rgba(66, 165, 245, 0.3);
                border-radius: 18px;
                padding: 18px;
            }}
        """)
        
        question_shadow = QGraphicsDropShadowEffect()
        question_shadow.setBlurRadius(25)
        question_shadow.setColor(QColor(self.STARK_BLUE_PRIMARY))
        question_shadow.setOffset(0, 8)
        question_container.setGraphicsEffect(question_shadow)
        
        question_layout = QVBoxLayout(question_container)
        question_layout.setSpacing(12)
        
        # Header avec icône
        question_header = QHBoxLayout()
        question_icon = QLabel()
        question_icon.setPixmap(StarkIcons.help_circle(self.STARK_ACCENT_GLOW).pixmap(QSize(22, 22)))
        question_header.addWidget(question_icon)
        
        question_label = QLabel("QUESTION ACTUELLE")
        question_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        question_label.setStyleSheet(f"""
            color: {self.STARK_BLUE_LIGHT};
            letter-spacing: 2px;
        """)
        question_header.addWidget(question_label)
        question_header.addStretch()
        question_layout.addLayout(question_header)
        
        self.question_text = QLabel("En attente de connexion...")
        self.question_text.setFont(QFont("Arial", 12, QFont.Weight.Medium))
        self.question_text.setWordWrap(True)
        self.question_text.setStyleSheet(f"""
            color: #FFFFFF;
            padding: 15px;
            background: rgba(10, 25, 41, 0.6);
            border: 1px solid rgba(66, 165, 245, 0.2);
            border-radius: 12px;
            line-height: 1.6;
        """)
        self.question_text.setMinimumHeight(110)
        question_layout.addWidget(self.question_text)
        
        layout.addWidget(question_container)
        
        # Zone de transcription
        transcript_header = QHBoxLayout()
        transcript_icon = QLabel()
        transcript_icon.setPixmap(StarkIcons.file_text(self.STARK_SUCCESS).pixmap(QSize(20, 20)))
        transcript_header.addWidget(transcript_icon)
        
        transcript_label = QLabel("TRANSCRIPTION")
        transcript_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        transcript_label.setStyleSheet(f"""
            color: {self.STARK_SUCCESS};
            letter-spacing: 2px;
        """)
        transcript_header.addWidget(transcript_label)
        transcript_header.addStretch()
        layout.addLayout(transcript_header)
        
        self.transcript_text = QTextEdit()
        self.transcript_text.setReadOnly(True)
        self.transcript_text.setMaximumHeight(130)
        self.transcript_text.setPlaceholderText("Votre réponse apparaîtra ici...")
        self.transcript_text.setStyleSheet(f"""
            QTextEdit {{
                background: rgba(10, 25, 41, 0.7);
                border: 2px solid rgba(0, 230, 118, 0.3);
                border-radius: 12px;
                padding: 15px;
                color: #FFFFFF;
                font-size: 11px;
                font-family: 'Courier New';
                line-height: 1.5;
            }}
            QTextEdit::placeholder {{
                color: rgba(255, 255, 255, 0.4);
            }}
        """)
        
        transcript_shadow = QGraphicsDropShadowEffect()
        transcript_shadow.setBlurRadius(15)
        transcript_shadow.setColor(QColor(0, 230, 118, 50))
        transcript_shadow.setOffset(0, 5)
        self.transcript_text.setGraphicsEffect(transcript_shadow)
        
        layout.addWidget(self.transcript_text)
        
        layout.addStretch()
        
        # Bouton Répondre avec animation pulse
        self.record_button = QPushButton()
        self.record_button.setFont(QFont("Arial", 12, QFont.Weight.ExtraBold))
        self.record_button.setMinimumHeight(60)
        self.record_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.record_button.clicked.connect(self._on_record_clicked)
        self._update_record_button_style(False)
        
        layout.addWidget(self.record_button)
        
        # Bouton Terminer
        self.end_button = QPushButton(" TERMINER")
        self.end_button.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.end_button.setMinimumHeight(50)
        self.end_button.setIcon(StarkIcons.power())
        self.end_button.setIconSize(QSize(22, 22))
        self.end_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.end_button.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {self.STARK_ACCENT}, 
                    stop:1 #C0392B);
                color: white;
                border: none;
                border-radius: 12px;
                padding: 12px;
                letter-spacing: 2px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {self.STARK_ACCENT_GLOW}, 
                    stop:1 #D35400);
                transform: translateY(-2px);
            }}
            QPushButton:pressed {{
                background: #A93226;
                transform: translateY(0px);
            }}
        """)
        
        end_shadow = QGraphicsDropShadowEffect()
        end_shadow.setBlurRadius(15)
        end_shadow.setColor(QColor(self.STARK_ACCENT))
        end_shadow.setOffset(0, 5)
        self.end_button.setGraphicsEffect(end_shadow)
        
        self.end_button.clicked.connect(self.end_interview.emit)
        layout.addWidget(self.end_button)
    
    def _update_record_button_style(self, is_recording: bool):
        """Mettre à jour le style du bouton avec animations"""
        if is_recording:
            self.record_button.setText(" ARRÊTER L'ENREGISTREMENT")
            self.record_button.setIcon(StarkIcons.stop_circle())
            self.record_button.setIconSize(QSize(26, 26))
            self.record_button.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {self.STARK_ACCENT}, 
                        stop:0.5 #E74C3C,
                        stop:1 {self.STARK_ACCENT});
                    color: white;
                    border: none;
                    border-radius: 15px;
                    padding: 18px;
                    letter-spacing: 2px;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {self.STARK_ACCENT_GLOW}, 
                        stop:1 #EC7063);
                }}
            """)
            
            # Animation pulse
            self._start_pulse_animation()
            
        else:
            self.record_button.setText(" COMMENCER À RÉPONDRE")
            self.record_button.setIcon(StarkIcons.microphone())
            self.record_button.setIconSize(QSize(26, 26))
            self.record_button.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {self.STARK_SUCCESS}, 
                        stop:0.5 {self.STARK_BLUE_LIGHT},
                        stop:1 {self.STARK_SUCCESS});
                    color: white;
                    border: none;
                    border-radius: 15px;
                    padding: 18px;
                    letter-spacing: 2px;
                    text-shadow: 0 2px 4px rgba(0,0,0,0.3);
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {self.STARK_SUCCESS_GLOW}, 
                        stop:1 #1ABC9C);
                    transform: translateY(-3px);
                }}
                QPushButton:pressed {{
                    background: #229954;
                    transform: translateY(0px);
                }}
                QPushButton:disabled {{
                    background: rgba(127, 140, 141, 0.4);
                    color: rgba(255, 255, 255, 0.5);
                }}
            """)
            
            # Arrêter pulse
            self._stop_pulse_animation()
        
        # Ombre dynamique
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        if is_recording:
            shadow.setColor(QColor(self.STARK_ACCENT))
        else:
            shadow.setColor(QColor(self.STARK_SUCCESS))
        shadow.setOffset(0, 8)
        self.record_button.setGraphicsEffect(shadow)
    
    def _start_pulse_animation(self):
        """Démarrer l'animation pulse pour l'enregistrement"""
        if not hasattr(self, 'pulse_timer'):
            self.pulse_timer = QTimer()
            self.pulse_state = False
            self.pulse_timer.timeout.connect(self._pulse_effect)
        
        self.pulse_timer.start(800)
    
    def _stop_pulse_animation(self):
        """Arrêter l'animation pulse"""
        if hasattr(self, 'pulse_timer'):
            self.pulse_timer.stop()
    
    def _pulse_effect(self):
        """Effet de pulse"""
        if self.pulse_state:
            self.record_button.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {self.STARK_ACCENT}, 
                        stop:0.5 #E74C3C,
                        stop:1 {self.STARK_ACCENT});
                    color: white;
                    border: 3px solid {self.STARK_ACCENT_GLOW};
                    border-radius: 15px;
                    padding: 18px;
                    letter-spacing: 2px;
                }}
            """)
        else:
            self.record_button.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {self.STARK_ACCENT}, 
                        stop:0.5 #E74C3C,
                        stop:1 {self.STARK_ACCENT});
                    color: white;
                    border: none;
                    border-radius: 15px;
                    padding: 18px;
                    letter-spacing: 2px;
                }}
            """)
        
        self.pulse_state = not self.pulse_state
    
    def _on_record_clicked(self):
        """Toggle recording avec animation"""
        if not self.is_recording:
            self.start_recording.emit()
            self.is_recording = True
            self._update_record_button_style(True)
        else:
            self.stop_recording.emit()
            self.is_recording = False
            self._update_record_button_style(False)
    
    def update_question(self, question_text: str, progress: dict):
        """Mettre à jour la question avec animation"""
        self.question_text.setText(question_text)
        self.progress_label.setText(f"Question {progress['current']}/{progress['total']}")
        self.progress_bar.setValue(progress['percentage'])
    
    def update_transcript(self, transcript: str):
        """Mettre à jour la transcription"""
        self.transcript_text.setPlainText(transcript)
    
    def enable_recording(self, enabled: bool):
        """Activer/désactiver l'enregistrement"""
        self.record_button.setEnabled(enabled)