from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QProgressBar, QTextEdit
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

class InterviewWidget(QWidget):
    """Widget pour l'interface d'entretien"""
    
    start_recording = Signal()
    stop_recording = Signal()
    end_interview = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        
        # Titre
        title = QLabel("🎤 Entretien Vocal")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #2C3E50; padding: 20px;")
        layout.addWidget(title)
        
        # Barre de progression
        progress_layout = QHBoxLayout()
        
        self.progress_label = QLabel("Question 0/0")
        self.progress_label.setFont(QFont("Arial", 12))
        progress_layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #3498DB;
                border-radius: 5px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #3498DB;
            }
        """)
        progress_layout.addWidget(self.progress_bar)
        
        layout.addLayout(progress_layout)
        
        # Zone de question
        question_container = QWidget()
        question_container.setStyleSheet("""
            QWidget {
                background-color: #ECF0F1;
                border-radius: 10px;
                padding: 20px;
            }
        """)
        question_layout = QVBoxLayout(question_container)
        
        question_label = QLabel("Question:")
        question_label.setFont(QFont("Arial", 10))
        question_label.setStyleSheet("color: #7F8C8D;")
        question_layout.addWidget(question_label)
        
        self.question_text = QLabel("En attente de connexion...")
        self.question_text.setFont(QFont("Arial", 14))
        self.question_text.setWordWrap(True)
        self.question_text.setStyleSheet("color: #2C3E50; padding: 10px;")
        question_layout.addWidget(self.question_text)
        
        layout.addWidget(question_container)
        
        # Zone de transcription
        transcript_label = QLabel("Votre réponse (transcription):")
        transcript_label.setFont(QFont("Arial", 10))
        transcript_label.setStyleSheet("color: #7F8C8D;")
        layout.addWidget(transcript_label)
        
        self.transcript_text = QTextEdit()
        self.transcript_text.setReadOnly(True)
        self.transcript_text.setMaximumHeight(150)
        self.transcript_text.setStyleSheet("""
            QTextEdit {
                background-color: #FFFFFF;
                border: 2px solid #BDC3C7;
                border-radius: 5px;
                padding: 10px;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.transcript_text)
        
        # Boutons de contrôle
        controls_layout = QHBoxLayout()
        
        self.record_button = QPushButton("🎤 Commencer à répondre")
        self.record_button.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.record_button.setMinimumHeight(50)
        self.record_button.setStyleSheet("""
            QPushButton {
                background-color: #27AE60;
                color: white;
                border-radius: 10px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:pressed {
                background-color: #1E8449;
            }
            QPushButton:disabled {
                background-color: #95A5A6;
            }
        """)
        self.record_button.clicked.connect(self._on_record_clicked)
        controls_layout.addWidget(self.record_button)
        
        self.end_button = QPushButton("🛑 Terminer l'entretien")
        self.end_button.setFont(QFont("Arial", 12))
        self.end_button.setMinimumHeight(50)
        self.end_button.setStyleSheet("""
            QPushButton {
                background-color: #E74C3C;
                color: white;
                border-radius: 10px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #C0392B;
            }
        """)
        self.end_button.clicked.connect(self.end_interview.emit)
        controls_layout.addWidget(self.end_button)
        
        layout.addLayout(controls_layout)
        
        # État
        self.is_recording = False
    
    def _on_record_clicked(self):
        """Toggle recording"""
        if not self.is_recording:
            self.start_recording.emit()
            self.is_recording = True
            self.record_button.setText("⏹️ Arrêter l'enregistrement")
            self.record_button.setStyleSheet("""
                QPushButton {
                    background-color: #E74C3C;
                    color: white;
                    border-radius: 10px;
                    padding: 10px;
                }
            """)
        else:
            self.stop_recording.emit()
            self.is_recording = False
            self.record_button.setText("🎤 Commencer à répondre")
            self.record_button.setStyleSheet("""
                QPushButton {
                    background-color: #27AE60;
                    color: white;
                    border-radius: 10px;
                    padding: 10px;
                }
            """)
    
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