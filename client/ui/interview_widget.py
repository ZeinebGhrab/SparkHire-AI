from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QProgressBar, QTextEdit, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

class InterviewWidget(QWidget):
    """Widget compact pour les contrôles d'entretien - Design Professionnel"""
    
    start_recording = Signal()
    stop_recording = Signal()
    end_interview = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)
        
        # Titre compact
        title = QLabel("CONTRÔLES")
        title.setFont(QFont("Arial", 14, QFont.Weight.ExtraBold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            color: #ffffff;
            padding: 10px;
            background: rgba(233, 69, 96, 30);
            border-radius: 8px;
            letter-spacing: 2px;
        """)
        layout.addWidget(title)
        
        # Barre de progression moderne
        progress_container = QFrame()
        progress_container.setStyleSheet("""
            QFrame {
                background: rgba(15, 52, 96, 80);
                border-radius: 10px;
                padding: 10px;
            }
        """)
        progress_layout = QVBoxLayout(progress_container)
        progress_layout.setSpacing(8)
        
        self.progress_label = QLabel("Question 0/0")
        self.progress_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_label.setStyleSheet("color: #ffffff;")
        progress_layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        self.progress_bar.setFixedHeight(28)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid rgba(233, 69, 96, 150);
                border-radius: 8px;
                text-align: center;
                background: rgba(0, 0, 0, 50);
                color: #ffffff;
                font-weight: bold;
                font-size: 11px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #e94560, stop:1 #0f3460);
                border-radius: 6px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)
        
        layout.addWidget(progress_container)
        
        # Zone de question compacte
        question_container = QFrame()
        question_container.setStyleSheet("""
            QFrame {
                background: rgba(48, 43, 99, 100);
                border: 2px solid rgba(233, 69, 96, 80);
                border-radius: 12px;
                padding: 15px;
            }
        """)
        question_layout = QVBoxLayout(question_container)
        question_layout.setSpacing(8)
        
        question_label = QLabel("❓ QUESTION ACTUELLE")
        question_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        question_label.setStyleSheet("color: rgba(255, 255, 255, 150); letter-spacing: 1px;")
        question_layout.addWidget(question_label)
        
        self.question_text = QLabel("En attente de connexion...")
        self.question_text.setFont(QFont("Arial", 12, QFont.Weight.Medium))
        self.question_text.setWordWrap(True)
        self.question_text.setStyleSheet("""
            color: #ffffff;
            padding: 10px;
            background: rgba(0, 0, 0, 30);
            border-radius: 8px;
        """)
        self.question_text.setMinimumHeight(100)
        question_layout.addWidget(self.question_text)
        
        layout.addWidget(question_container)
        
        # Zone de transcription compacte
        transcript_label = QLabel("📝 TRANSCRIPTION")
        transcript_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        transcript_label.setStyleSheet("color: rgba(255, 255, 255, 150); letter-spacing: 1px;")
        layout.addWidget(transcript_label)
        
        self.transcript_text = QTextEdit()
        self.transcript_text.setReadOnly(True)
        self.transcript_text.setMaximumHeight(120)
        self.transcript_text.setPlaceholderText("Votre réponse apparaîtra ici...")
        self.transcript_text.setStyleSheet("""
            QTextEdit {
                background: rgba(0, 0, 0, 40);
                border: 2px solid rgba(233, 69, 96, 100);
                border-radius: 10px;
                padding: 12px;
                color: #ffffff;
                font-size: 11px;
                font-family: 'Courier New';
            }
        """)
        layout.addWidget(self.transcript_text)
        
        # Spacer pour pousser les boutons en bas
        layout.addStretch()
        
        # Boutons de contrôle modernes
        self.record_button = QPushButton("🎤 RÉPONDRE")
        self.record_button.setFont(QFont("Arial", 11, QFont.Weight.ExtraBold))
        self.record_button.setMinimumHeight(55)
        self.record_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.record_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #27ae60, stop:1 #16a085);
                color: white;
                border: none;
                border-radius: 12px;
                padding: 15px;
                font-size: 12px;
                letter-spacing: 2px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2ecc71, stop:1 #1abc9c);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #229954, stop:1 #138d75);
            }
            QPushButton:disabled {
                background: rgba(127, 140, 141, 100);
            }
        """)
        self.record_button.clicked.connect(self._on_record_clicked)
        layout.addWidget(self.record_button)
        
        self.end_button = QPushButton("⏹️ TERMINER")
        self.end_button.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.end_button.setMinimumHeight(45)
        self.end_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.end_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #e74c3c, stop:1 #c0392b);
                color: white;
                border: none;
                border-radius: 10px;
                padding: 12px;
                font-size: 10px;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ec7063, stop:1 #d35400);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #a93226, stop:1 #922b21);
            }
        """)
        self.end_button.clicked.connect(self.end_interview.emit)
        layout.addWidget(self.end_button)
        
        # État
        self.is_recording = False
    
    def _on_record_clicked(self):
        """Toggle recording avec animation"""
        if not self.is_recording:
            self.start_recording.emit()
            self.is_recording = True
            self.record_button.setText("⏹️ ARRÊTER")
            self.record_button.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #e74c3c, stop:1 #c0392b);
                    color: white;
                    border: none;
                    border-radius: 12px;
                    padding: 15px;
                    animation: pulse 1.5s infinite;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #ec7063, stop:1 #d35400);
                }
            """)
        else:
            self.stop_recording.emit()
            self.is_recording = False
            self.record_button.setText("🎤 RÉPONDRE")
            self.record_button.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #27ae60, stop:1 #16a085);
                    color: white;
                    border: none;
                    border-radius: 12px;
                    padding: 15px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #2ecc71, stop:1 #1abc9c);
                }
            """)
    
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