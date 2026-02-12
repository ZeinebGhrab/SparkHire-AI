"""
Icônes SVG Professionnelles - Stark Solutions
Palette de couleurs officielle basée sur stark-solutions.online
"""

from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtCore import QByteArray, QSize
import sys
from pathlib import Path

# Import du thème
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from .stark_theme import StarkTheme


class StarkIcons:
    """Gestionnaire d'icônes SVG avec la palette officielle Stark"""
    
    @staticmethod
    def _create_icon_from_svg(svg_data: str, size: QSize = QSize(32, 32)) -> QIcon:
        """Créer une QIcon à partir de données SVG"""
        renderer = QSvgRenderer(QByteArray(svg_data.encode()))
        pixmap = QPixmap(size)
        pixmap.fill(0)  # Transparent
        
        from PySide6.QtGui import QPainter
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        
        return QIcon(pixmap)
    
    @classmethod
    def microphone(cls, color=None) -> QIcon:
        """Icône microphone"""
        if color is None:
            color = StarkTheme.WHITE
        svg = f'''
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"></path>
            <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
            <line x1="12" x2="12" y1="19" y2="22"></line>
        </svg>
        '''
        return cls._create_icon_from_svg(svg)
    
    @classmethod
    def stop_circle(cls, color=None) -> QIcon:
        """Icône stop"""
        if color is None:
            color = StarkTheme.WHITE
        svg = f'''
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"></circle>
            <rect width="6" height="6" x="9" y="9"></rect>
        </svg>
        '''
        return cls._create_icon_from_svg(svg)
    
    @classmethod
    def power(cls, color=None) -> QIcon:
        """Icône power/terminer"""
        if color is None:
            color = StarkTheme.WHITE
        svg = f'''
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2v10"></path>
            <path d="M18.4 6.6a9 9 0 1 1-12.77.04"></path>
        </svg>
        '''
        return cls._create_icon_from_svg(svg)
    
    @classmethod
    def help_circle(cls, color=None) -> QIcon:
        """Icône question/aide"""
        if color is None:
            color = StarkTheme.ORANGE_ACCENT
        svg = f'''
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"></circle>
            <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path>
            <path d="M12 17h.01"></path>
        </svg>
        '''
        return cls._create_icon_from_svg(svg)
    
    @classmethod
    def file_text(cls, color=None) -> QIcon:
        """Icône document/transcription"""
        if color is None:
            color = StarkTheme.BLUE_PRIMARY
        svg = f'''
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"></path>
            <polyline points="14 2 14 8 20 8"></polyline>
            <line x1="16" x2="8" y1="13" y2="13"></line>
            <line x1="16" x2="8" y1="17" y2="17"></line>
            <line x1="10" x2="8" y1="9" y2="9"></line>
        </svg>
        '''
        return cls._create_icon_from_svg(svg)
    
    @classmethod
    def activity(cls, color=None) -> QIcon:
        """Icône activité/monitoring"""
        if color is None:
            color = StarkTheme.BLUE_LIGHT
        svg = f'''
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M22 12h-4l-3 9L9 3l-3 9H2"></path>
        </svg>
        '''
        return cls._create_icon_from_svg(svg)
    
    @classmethod
    def user_check(cls, color=None) -> QIcon:
        """Icône utilisateur vérifié/RH"""
        if color is None:
            color = StarkTheme.BLUE_PRIMARY
        svg = f'''
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path>
            <circle cx="9" cy="7" r="4"></circle>
            <polyline points="16 11 18 13 22 9"></polyline>
        </svg>
        '''
        return cls._create_icon_from_svg(svg)
    
    @classmethod
    def headphones(cls, color=None) -> QIcon:
        """Icône écoute"""
        if color is None:
            color = StarkTheme.ORANGE_ACCENT
        svg = f'''
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 14h3a2 2 0 0 1 2 2v3a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-7a9 9 0 0 1 18 0v7a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3"></path>
        </svg>
        '''
        return cls._create_icon_from_svg(svg)
    
    @classmethod
    def message_circle(cls, color=None) -> QIcon:
        """Icône message/speaking"""
        if color is None:
            color = StarkTheme.BLUE_LIGHT
        svg = f'''
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="m3 21 1.9-5.7a8.5 8.5 0 1 1 3.8 3.8z"></path>
        </svg>
        '''
        return cls._create_icon_from_svg(svg)
    
    @classmethod
    def shield_check(cls, color=None) -> QIcon:
        """Icône sécurité"""
        if color is None:
            color = StarkTheme.SUCCESS
        svg = f'''
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10"></path>
            <path d="m9 12 2 2 4-4"></path>
        </svg>
        '''
        return cls._create_icon_from_svg(svg)
    
    @classmethod
    def zap(cls, color=None) -> QIcon:
        """Icône énergie/action"""
        if color is None:
            color = StarkTheme.ORANGE_ACCENT
        svg = f'''
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
        </svg>
        '''
        return cls._create_icon_from_svg(svg)
    
    @classmethod
    def logo_stark(cls) -> QIcon:
        """Logo Stark Solutions"""
        svg = f'''
        <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48">
            <circle cx="24" cy="24" r="22" fill="{StarkTheme.BLUE_PRIMARY}"/>
            <text x="24" y="32" font-family="Arial" font-size="24" font-weight="bold" fill="{StarkTheme.WHITE}" text-anchor="middle">S</text>
        </svg>
        '''
        return cls._create_icon_from_svg(svg, QSize(48, 48))