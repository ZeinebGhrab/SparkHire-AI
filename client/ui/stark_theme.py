"""
Palette de Couleurs Officielle Stark Solutions
Basée sur https://stark-solutions.online/
"""

class StarkTheme:
    """
    Thème visuel officiel de Stark Solutions
    Utilisé dans toute l'application pour assurer la cohérence visuelle
    """
    
    # ========== COULEURS PRINCIPALES ==========
    BLUE_PRIMARY = "#0066CC"        # Bleu corporate principal
    BLUE_DARK = "#003E7E"           # Bleu foncé (headers, nav)
    BLUE_LIGHT = "#4DA6FF"          # Bleu clair (hover, accents)
    BLUE_EXTRA_LIGHT = "#CCE5FF"    # Bleu très clair (backgrounds)
    
    # ========== COULEURS SECONDAIRES ==========
    ORANGE_ACCENT = "#FF6B35"       # Orange (CTA, important)
    ORANGE_LIGHT = "#FF8C61"        # Orange clair (hover)
    
    # ========== NUANCES DE GRIS ==========
    GRAY_DARK = "#2C3E50"           # Gris foncé (textes)
    GRAY_MEDIUM = "#7F8C8D"         # Gris moyen
    GRAY_LIGHT = "#BDC3C7"          # Gris clair
    GRAY_EXTRA_LIGHT = "#ECF0F1"    # Gris très clair (backgrounds)
    
    # ========== COULEURS DE BASE ==========
    WHITE = "#FFFFFF"
    BLACK = "#000000"
    
    # ========== COULEURS DE STATUT ==========
    SUCCESS = "#27AE60"             # Vert (succès)
    WARNING = "#F39C12"             # Jaune/Orange (attention)
    ERROR = "#E74C3C"               # Rouge (erreur)
    INFO = "#3498DB"                # Bleu info
    
    # ========== TRANSPARENCES ==========
    OVERLAY_DARK = "rgba(0, 62, 126, 0.9)"
    OVERLAY_LIGHT = "rgba(255, 255, 255, 0.95)"
    GLASS_EFFECT = "rgba(255, 255, 255, 0.1)"
    
    # ========== DÉGRADÉS ==========
    GRADIENT_PRIMARY = f"""
        qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {BLUE_DARK},
            stop:0.5 {BLUE_PRIMARY},
            stop:1 {BLUE_LIGHT})
    """
    
    GRADIENT_HEADER = f"""
        qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {BLUE_DARK},
            stop:1 {BLUE_PRIMARY})
    """
    
    GRADIENT_ACCENT = f"""
        qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {ORANGE_ACCENT},
            stop:1 {ORANGE_LIGHT})
    """
    
    GRADIENT_BACKGROUND = f"""
        qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {GRAY_EXTRA_LIGHT},
            stop:1 {WHITE})
    """
    
    # ========== OMBRES ==========
    SHADOW_SMALL = "0 2px 4px rgba(0, 0, 0, 0.1)"
    SHADOW_MEDIUM = "0 4px 8px rgba(0, 0, 0, 0.15)"
    SHADOW_LARGE = "0 8px 16px rgba(0, 0, 0, 0.2)"
    SHADOW_GLOW = f"0 0 20px {BLUE_PRIMARY}"
    
    # ========== TYPOGRAPHIE ==========
    FONT_FAMILY_PRIMARY = "Segoe UI, Arial, sans-serif"
    FONT_FAMILY_SECONDARY = "Roboto, Helvetica, sans-serif"
    FONT_FAMILY_MONO = "Consolas, Monaco, monospace"
    
    # ========== TAILLES DE POLICE ==========
    FONT_SIZE_SMALL = "11px"
    FONT_SIZE_NORMAL = "13px"
    FONT_SIZE_MEDIUM = "15px"
    FONT_SIZE_LARGE = "18px"
    FONT_SIZE_XLARGE = "24px"
    FONT_SIZE_TITLE = "32px"
    
    # ========== ESPACEMENTS (INT pour setSpacing, STR pour CSS) ==========
    # Valeurs entières pour Qt
    SPACING_XS_INT = 4
    SPACING_SM_INT = 8
    SPACING_MD_INT = 16
    SPACING_LG_INT = 24
    SPACING_XL_INT = 32
    
    # Valeurs string pour CSS
    SPACING_XS = "4px"
    SPACING_SM = "8px"
    SPACING_MD = "16px"
    SPACING_LG = "24px"
    SPACING_XL = "32px"
    
    # ========== BORDER RADIUS ==========
    RADIUS_SMALL = "4px"
    RADIUS_MEDIUM = "8px"
    RADIUS_LARGE = "12px"
    RADIUS_XLARGE = "16px"
    RADIUS_ROUND = "50%"
    
    @classmethod
    def get_button_style(cls, variant="primary"):
        """Retourne le style d'un bouton selon le variant"""
        styles = {
            "primary": f"""
                QPushButton {{
                    background: {cls.GRADIENT_PRIMARY};
                    color: {cls.WHITE};
                    border: none;
                    border-radius: {cls.RADIUS_MEDIUM};
                    padding: 12px 24px;
                    font-size: {cls.FONT_SIZE_MEDIUM};
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background: {cls.BLUE_LIGHT};
                }}
                QPushButton:pressed {{
                    background: {cls.BLUE_DARK};
                }}
                QPushButton:disabled {{
                    background: {cls.GRAY_LIGHT};
                    color: {cls.GRAY_MEDIUM};
                }}
            """,
            "accent": f"""
                QPushButton {{
                    background: {cls.GRADIENT_ACCENT};
                    color: {cls.WHITE};
                    border: none;
                    border-radius: {cls.RADIUS_MEDIUM};
                    padding: 12px 24px;
                    font-size: {cls.FONT_SIZE_MEDIUM};
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background: {cls.ORANGE_LIGHT};
                }}
                QPushButton:pressed {{
                    background: {cls.ORANGE_ACCENT};
                }}
            """,
            "secondary": f"""
                QPushButton {{
                    background: {cls.WHITE};
                    color: {cls.BLUE_PRIMARY};
                    border: 2px solid {cls.BLUE_PRIMARY};
                    border-radius: {cls.RADIUS_MEDIUM};
                    padding: 12px 24px;
                    font-size: {cls.FONT_SIZE_MEDIUM};
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background: {cls.BLUE_EXTRA_LIGHT};
                }}
                QPushButton:pressed {{
                    background: {cls.BLUE_PRIMARY};
                    color: {cls.WHITE};
                }}
            """
        }
        return styles.get(variant, styles["primary"])
    
    @classmethod
    def get_card_style(cls):
        """Style pour les cartes/panels"""
        return f"""
            QFrame {{
                background: {cls.WHITE};
                border: 1px solid {cls.GRAY_LIGHT};
                border-radius: {cls.RADIUS_LARGE};
                padding: {cls.SPACING_LG};
            }}
        """
    
    @classmethod
    def get_input_style(cls):
        """Style pour les champs de saisie"""
        return f"""
            QLineEdit, QTextEdit {{
                background: {cls.WHITE};
                border: 2px solid {cls.GRAY_LIGHT};
                border-radius: {cls.RADIUS_MEDIUM};
                padding: {cls.SPACING_MD};
                font-size: {cls.FONT_SIZE_NORMAL};
                color: {cls.GRAY_DARK};
            }}
            QLineEdit:focus, QTextEdit:focus {{
                border: 2px solid {cls.BLUE_PRIMARY};
            }}
        """