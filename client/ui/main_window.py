"""
Fenêtre Principale - Design Professionnel Stark Solutions
Utilise la charte graphique officielle de stark-solutions.online
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QMessageBox, QLabel, QLineEdit, QPushButton, QFrame, 
    QGraphicsDropShadowEffect, QStatusBar
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QColor
import base64
import sys
from pathlib import Path

# Imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from .stark_theme import StarkTheme
from .icons import StarkIcons


class MainWindow(QMainWindow):
    """
    Fenêtre Principale - Design Professionnel Stark Solutions
    Interface moderne basée sur la charte graphique stark-solutions.online
    """
    
    def __init__(self):
        super().__init__()
        
        self.websocket_client = None
        self.audio_recorder = None  # À initialiser séparément
        self.session_id = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Initialiser l'interface avec le design Stark"""
        self.setWindowTitle("Stark Recruitment AI - Entretien Vocal Intelligent")
        self.showMaximized()
        
        # Style global
        self.setStyleSheet(f"""
            QMainWindow {{
                background: {StarkTheme.GRADIENT_BACKGROUND};
            }}
        """)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # ========== EN-TÊTE ==========
        header = self._create_header()
        main_layout.addWidget(header)
        
        # ========== ZONE DE CONNEXION ==========
        self.connection_widget = self._create_connection_widget()
        main_layout.addWidget(self.connection_widget)
        
        # ========== ZONE D'ENTRETIEN (cachée au début) ==========
        self.interview_container = QWidget()
        self.interview_container.setVisible(False)
        # ... à compléter avec le layout d'interview
        
        main_layout.addWidget(self.interview_container)
        
        # ========== BARRE DE STATUT ==========
        self._setup_statusbar()
    
    def _create_header(self) -> QWidget:
        """Créer l'en-tête avec logo et titre"""
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background: {StarkTheme.GRADIENT_HEADER};
                border-bottom: 3px solid {StarkTheme.ORANGE_ACCENT};
            }}
        """)
        header.setFixedHeight(80)
        
        # Ombre
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(StarkTheme.BLUE_DARK))
        shadow.setOffset(0, 3)
        header.setGraphicsEffect(shadow)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(40, 15, 40, 15)
        
        # Logo + Titre
        title_container = QWidget()
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(15)
        
        # Logo
        logo_label = QLabel()
        logo_label.setPixmap(StarkIcons.logo_stark().pixmap(QSize(50, 50)))
        title_layout.addWidget(logo_label)
        
        # Texte
        text_widget = QWidget()
        text_layout = QVBoxLayout(text_widget)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)
        
        main_title = QLabel("STARK RECRUITMENT AI")
        main_title.setFont(QFont(StarkTheme.FONT_FAMILY_PRIMARY, 20, QFont.Weight.ExtraBold))
        main_title.setStyleSheet(f"""
            color: {StarkTheme.WHITE};
            letter-spacing: 2px;
        """)
        text_layout.addWidget(main_title)
        
        subtitle = QLabel("Système d'Entretien Vocal Intelligent")
        subtitle.setFont(QFont(StarkTheme.FONT_FAMILY_PRIMARY, 10))
        subtitle.setStyleSheet(f"color: {StarkTheme.BLUE_EXTRA_LIGHT};")
        text_layout.addWidget(subtitle)
        
        title_layout.addWidget(text_widget)
        layout.addWidget(title_container)
        
        layout.addStretch()
        
        # Indicateur de statut
        self.status_container = self._create_status_indicator()
        layout.addWidget(self.status_container)
        
        return header
    
    def _create_status_indicator(self) -> QWidget:
        """Créer l'indicateur de statut"""
        container = QFrame()
        container.setStyleSheet(f"""
            QFrame {{
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: {StarkTheme.RADIUS_MEDIUM};
                padding: 8px 15px;
            }}
        """)
        
        layout = QHBoxLayout(container)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(10)
        
        # Icône
        self.status_icon_label = QLabel()
        self.status_icon_label.setPixmap(StarkIcons.activity().pixmap(QSize(24, 24)))
        layout.addWidget(self.status_icon_label)
        
        # Texte
        status_text_container = QWidget()
        status_text_layout = QVBoxLayout(status_text_container)
        status_text_layout.setContentsMargins(0, 0, 0, 0)
        status_text_layout.setSpacing(0)
        
        self.status_label = QLabel("DÉCONNECTÉ")
        self.status_label.setFont(QFont(StarkTheme.FONT_FAMILY_PRIMARY, 11, QFont.Weight.Bold))
        self.status_label.setStyleSheet(f"color: {StarkTheme.WHITE}; letter-spacing: 1px;")
        status_text_layout.addWidget(self.status_label)
        
        self.status_detail = QLabel("En attente de connexion")
        self.status_detail.setFont(QFont(StarkTheme.FONT_FAMILY_PRIMARY, 8))
        self.status_detail.setStyleSheet(f"color: {StarkTheme.BLUE_EXTRA_LIGHT};")
        status_text_layout.addWidget(self.status_detail)
        
        layout.addWidget(status_text_container)
        
        return container
    
    def _create_connection_widget(self) -> QWidget:
        """Créer le widget de connexion"""
        widget = QFrame()
        widget.setStyleSheet("QFrame { background: transparent; }")
        
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(30)
        
        # Carte de connexion
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {StarkTheme.WHITE};
                border: 2px solid {StarkTheme.BLUE_EXTRA_LIGHT};
                border-radius: {StarkTheme.RADIUS_XLARGE};
            }}
        """)
        card.setFixedSize(550, 450)
        
        # Ombre
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(StarkTheme.BLUE_PRIMARY))
        shadow.setOffset(0, 8)
        card.setGraphicsEffect(shadow)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(50, 50, 50, 50)
        card_layout.setSpacing(25)
        
        # Icône
        icon_container = QFrame()
        icon_container.setStyleSheet(f"""
            QFrame {{
                background: {StarkTheme.BLUE_EXTRA_LIGHT};
                border-radius: 40px;
            }}
        """)
        icon_container.setFixedSize(80, 80)
        
        icon_layout = QVBoxLayout(icon_container)
        icon_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        shield_icon = QLabel()
        shield_icon.setPixmap(StarkIcons.shield_check().pixmap(QSize(50, 50)))
        icon_layout.addWidget(shield_icon)
        
        card_layout.addWidget(icon_container, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Titre
        title = QLabel("CONNEXION SÉCURISÉE")
        title.setFont(QFont(StarkTheme.FONT_FAMILY_PRIMARY, 20, QFont.Weight.ExtraBold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"""
            color: {StarkTheme.BLUE_PRIMARY};
            letter-spacing: 2px;
        """)
        card_layout.addWidget(title)
        
        # Sous-titre
        subtitle = QLabel("Entrez votre identifiant de session")
        subtitle.setFont(QFont(StarkTheme.FONT_FAMILY_PRIMARY, 11))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(f"color: {StarkTheme.GRAY_MEDIUM};")
        card_layout.addWidget(subtitle)
        
        # Champ de saisie
        self.session_input = QLineEdit()
        self.session_input.setPlaceholderText("session_xxxxxxxxxxxxx")
        self.session_input.setFont(QFont(StarkTheme.FONT_FAMILY_MONO, 12, QFont.Weight.Bold))
        self.session_input.setMinimumHeight(50)
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
                border: 2px solid {StarkTheme.BLUE_PRIMARY};
                background: {StarkTheme.WHITE};
            }}
        """)
        card_layout.addWidget(self.session_input)
        
        # Bouton de connexion
        self.connect_btn = QPushButton("DÉMARRER L'ENTRETIEN")
        self.connect_btn.setFont(QFont(StarkTheme.FONT_FAMILY_PRIMARY, 13, QFont.Weight.Bold))
        self.connect_btn.setMinimumHeight(55)
        self.connect_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.connect_btn.setStyleSheet(StarkTheme.get_button_style("primary"))
        self.connect_btn.clicked.connect(self._connect_to_interview)
        
        # Ombre du bouton
        btn_shadow = QGraphicsDropShadowEffect()
        btn_shadow.setBlurRadius(15)
        btn_shadow.setColor(QColor(StarkTheme.BLUE_PRIMARY))
        btn_shadow.setOffset(0, 4)
        self.connect_btn.setGraphicsEffect(btn_shadow)
        
        card_layout.addWidget(self.connect_btn)
        
        layout.addWidget(card)
        
        return widget
    
    def _setup_statusbar(self):
        """Configurer la barre de statut"""
        status_bar = self.statusBar()
        status_bar.setStyleSheet(f"""
            QStatusBar {{
                background: {StarkTheme.WHITE};
                color: {StarkTheme.GRAY_DARK};
                font-size: 11px;
                font-weight: bold;
                padding: 8px;
                border-top: 1px solid {StarkTheme.GRAY_LIGHT};
            }}
        """)
        status_bar.showMessage("🔒 Système Sécurisé Stark Solutions - Prêt à Démarrer")
    
    def _connect_to_interview(self):
        """Connecter à l'entretien"""
        session_id = self.session_input.text().strip()
        
        if not session_id:
            self._show_error_dialog("Erreur de Connexion", 
                                   "Veuillez entrer un identifiant de session valide")
            return
        
        # TODO: Implémenter la connexion WebSocket
        self.status_label.setText("CONNECTÉ")
        self.status_label.setStyleSheet(f"color: {StarkTheme.SUCCESS}; letter-spacing: 1px;")
        self.status_detail.setText("Session active")
        self.statusBar().showMessage("✅ Connexion Sécurisée Établie")
        
        # Basculer vers l'interface d'entretien
        self.connection_widget.setVisible(False)
        self.interview_container.setVisible(True)
    
    def _show_error_dialog(self, title: str, message: str):
        """Afficher un dialogue d'erreur"""
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStyleSheet(f"""
            QMessageBox {{
                background: {StarkTheme.WHITE};
            }}
            QMessageBox QLabel {{
                color: {StarkTheme.ERROR};
                font-size: 13px;
            }}
            QPushButton {{
                background: {StarkTheme.ERROR};
                color: {StarkTheme.WHITE};
                border-radius: {StarkTheme.RADIUS_MEDIUM};
                padding: 10px 25px;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background: #C0392B;
            }}
        """)
        msg_box.exec()