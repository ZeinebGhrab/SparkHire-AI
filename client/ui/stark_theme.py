"""
Stark Solutions — Design System v2
Premium dark glassmorphism aesthetic with refined typography and depth.
"""


class StarkTheme:
    # ═══════════════════════════════════════════════
    # CORE PALETTE
    # ═══════════════════════════════════════════════
    # Deep navy backgrounds — layered for depth
    BG_VOID        = "#020B18"   # True black base
    BG_DEEP        = "#050F1E"   # Sidebar / panels
    BG_SURFACE     = "#091627"   # Card background
    BG_ELEVATED    = "#0D1E33"   # Hover / elevated card
    BG_BORDER      = "#142843"   # Borders / dividers

    # Primary blue spectrum
    BLUE_ELECTRIC  = "#0EA5E9"   # Primary action / highlight
    BLUE_BRIGHT    = "#38BDF8"   # Hover states
    BLUE_SOFT      = "#7DD3FC"   # Secondary text / icons
    BLUE_DIM       = "#1E4976"   # Disabled / muted
    BLUE_GLOW      = "#0EA5E940" # Glow effects (with alpha)

    # Accent — warm amber (replacing orange for more premium feel)
    AMBER          = "#F59E0B"
    AMBER_BRIGHT   = "#FCD34D"
    AMBER_SOFT     = "#FDE68A"
    AMBER_DIM      = "#78350F"
    AMBER_GLOW     = "#F59E0B30"

    # Status palette
    SUCCESS        = "#10B981"
    SUCCESS_GLOW   = "#10B98130"
    WARNING        = "#F59E0B"
    ERROR          = "#EF4444"
    ERROR_GLOW     = "#EF444430"

    # Text hierarchy
    TEXT_PRIMARY   = "#F0F9FF"   # Headings
    TEXT_SECONDARY = "#94A3B8"   # Body text
    TEXT_MUTED     = "#475569"   # Placeholders
    TEXT_INVERSE   = "#020B18"   # Text on bright backgrounds

    # White for backgrounds
    WHITE          = "#FFFFFF"

    # ═══════════════════════════════════════════════
    # GLASS EFFECT VALUES
    # ═══════════════════════════════════════════════
    GLASS_BG       = "rgba(14, 165, 233, 0.06)"
    GLASS_BORDER   = "rgba(14, 165, 233, 0.15)"
    GLASS_HOVER    = "rgba(14, 165, 233, 0.10)"
    OVERLAY_DARK   = "rgba(2, 11, 24, 0.92)"

    # ═══════════════════════════════════════════════
    # TYPOGRAPHY — distinctive system fonts that render well on Qt
    # ═══════════════════════════════════════════════
    FONT_DISPLAY   = "Segoe UI, 'SF Pro Display', system-ui"
    FONT_BODY      = "Segoe UI, 'SF Pro Text', system-ui"
    FONT_MONO      = "'Cascadia Code', 'Fira Code', Consolas, monospace"

    FS_XS    = "10px"
    FS_SM    = "11px"
    FS_BASE  = "13px"
    FS_MD    = "15px"
    FS_LG    = "18px"
    FS_XL    = "22px"
    FS_2XL   = "28px"
    FS_3XL   = "36px"

    # ═══════════════════════════════════════════════
    # SPACING (integers for Qt, strings for CSS)
    # ═══════════════════════════════════════════════
    SP_XS     = "4px";   SP_XS_INT  = 4
    SP_SM     = "8px";   SP_SM_INT  = 8
    SP_MD     = "14px";  SP_MD_INT  = 14
    SP_LG     = "20px";  SP_LG_INT  = 20
    SP_XL     = "28px";  SP_XL_INT  = 28
    SP_2XL    = "40px";  SP_2XL_INT = 40

    # Legacy aliases (backward compat)
    SPACING_MD     = "14px";  SPACING_MD_INT  = 14
    SPACING_LG     = "20px";  SPACING_LG_INT  = 20
    SPACING_XL     = "28px";  SPACING_XL_INT  = 28
    SPACING_SM_INT = 8
    SPACING_XS_INT = 4

    # ═══════════════════════════════════════════════
    # BORDER RADIUS
    # ═══════════════════════════════════════════════
    R_SM   = "6px"
    R_MD   = "10px"
    R_LG   = "14px"
    R_XL   = "20px"
    R_2XL  = "28px"
    R_FULL = "9999px"

    RADIUS_MEDIUM = "10px"
    RADIUS_LARGE  = "14px"
    RADIUS_SMALL  = "6px"

    # Legacy color aliases
    ORANGE_ACCENT    = AMBER
    ORANGE_LIGHT     = AMBER_BRIGHT
    BLUE_PRIMARY     = BLUE_ELECTRIC
    BLUE_DARK        = "#0D1E33"
    BLUE_LIGHT       = BLUE_BRIGHT
    BLUE_EXTRA_LIGHT = "#1E4976"
    GRAY_DARK        = TEXT_PRIMARY
    GRAY_MEDIUM      = TEXT_SECONDARY
    GRAY_LIGHT       = BG_BORDER
    GRAY_EXTRA_LIGHT = BG_ELEVATED
    FONT_FAMILY_PRIMARY = FONT_BODY
    FONT_FAMILY_MONO    = FONT_MONO

    # ═══════════════════════════════════════════════
    # GRADIENTS
    # ═══════════════════════════════════════════════
    GRADIENT_PRIMARY = (
        "qlineargradient(x1:0, y1:0, x2:1, y2:0, "
        "stop:0 #0369A1, stop:0.5 #0EA5E9, stop:1 #38BDF8)"
    )
    GRADIENT_HEADER = (
        "qlineargradient(x1:0, y1:0, x2:1, y2:0, "
        "stop:0 #020B18, stop:1 #091627)"
    )
    GRADIENT_ACCENT = (
        "qlineargradient(x1:0, y1:0, x2:1, y2:0, "
        "stop:0 #D97706, stop:1 #F59E0B)"
    )
    GRADIENT_BACKGROUND = (
        "qlineargradient(x1:0, y1:0, x2:0, y2:1, "
        "stop:0 #020B18, stop:1 #050F1E)"
    )
    GRADIENT_CARD = (
        "qlineargradient(x1:0, y1:0, x2:0, y2:1, "
        "stop:0 #0D1E33, stop:1 #091627)"
    )

    # ═══════════════════════════════════════════════
    # GLOBAL APP STYLESHEET
    # ═══════════════════════════════════════════════
    @classmethod
    def global_stylesheet(cls) -> str:
        return f"""
        /* ── Reset ── */
        * {{
            outline: none;
        }}

        QMainWindow, QWidget {{
            background: {cls.BG_DEEP};
            color: {cls.TEXT_PRIMARY};
            font-family: {cls.FONT_BODY};
            font-size: {cls.FS_BASE};
        }}

        /* ── Scrollbars ── */
        QScrollBar:vertical {{
            background: {cls.BG_SURFACE};
            width: 6px;
            border-radius: 3px;
            margin: 0;
        }}
        QScrollBar::handle:vertical {{
            background: {cls.BLUE_DIM};
            border-radius: 3px;
            min-height: 30px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {cls.BLUE_ELECTRIC};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
        }}
        QScrollBar:horizontal {{
            background: {cls.BG_SURFACE};
            height: 6px;
            border-radius: 3px;
        }}
        QScrollBar::handle:horizontal {{
            background: {cls.BLUE_DIM};
            border-radius: 3px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background: {cls.BLUE_ELECTRIC};
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0;
        }}

        /* ── StatusBar ── */
        QStatusBar {{
            background: {cls.BG_VOID};
            color: {cls.TEXT_MUTED};
            font-size: {cls.FS_SM};
            font-weight: 500;
            padding: 6px 16px;
            border-top: 1px solid {cls.BG_BORDER};
        }}

        /* ── ToolTip ── */
        QToolTip {{
            background: {cls.BG_ELEVATED};
            color: {cls.TEXT_PRIMARY};
            border: 1px solid {cls.GLASS_BORDER};
            border-radius: {cls.R_SM};
            padding: 6px 10px;
            font-size: {cls.FS_SM};
        }}

        /* ── MessageBox ── */
        QMessageBox {{
            background: {cls.BG_SURFACE};
            color: {cls.TEXT_PRIMARY};
        }}
        QMessageBox QLabel {{
            color: {cls.TEXT_PRIMARY};
            font-size: {cls.FS_MD};
        }}
        QMessageBox QPushButton {{
            background: {cls.GRADIENT_PRIMARY};
            color: {cls.TEXT_PRIMARY};
            border: none;
            border-radius: {cls.R_SM};
            padding: 8px 24px;
            font-weight: 600;
            min-width: 80px;
        }}
        QMessageBox QPushButton:hover {{
            background: {cls.BLUE_BRIGHT};
            color: {cls.TEXT_INVERSE};
        }}
        """

    # ═══════════════════════════════════════════════
    # COMPONENT STYLESHEETS
    # ═══════════════════════════════════════════════

    @classmethod
    def header_style(cls) -> str:
        return f"""
        QFrame {{
            background: {cls.GRADIENT_HEADER};
            border-bottom: 1px solid {cls.BG_BORDER};
        }}
        """

    @classmethod
    def glass_card_style(cls, hover: bool = True) -> str:
        hover_rule = f"""
        QFrame:hover {{
            background: {cls.GLASS_HOVER};
            border: 1px solid rgba(14, 165, 233, 0.25);
        }}
        """ if hover else ""
        return f"""
        QFrame {{
            background: {cls.GLASS_BG};
            border: 1px solid {cls.GLASS_BORDER};
            border-radius: {cls.R_XL};
        }}
        {hover_rule}
        """

    @classmethod
    def solid_card_style(cls) -> str:
        return f"""
        QFrame {{
            background: {cls.GRADIENT_CARD};
            border: 1px solid {cls.BG_BORDER};
            border-radius: {cls.R_XL};
        }}
        """

    @classmethod
    def input_style(cls) -> str:
        return f"""
        QLineEdit {{
            background: {cls.BG_SURFACE};
            border: 1px solid {cls.BG_BORDER};
            border-radius: {cls.R_MD};
            padding: 12px 16px;
            font-size: {cls.FS_MD};
            font-family: {cls.FONT_MONO};
            color: {cls.TEXT_PRIMARY};
            selection-background-color: {cls.BLUE_DIM};
        }}
        QLineEdit:focus {{
            border: 1px solid {cls.BLUE_ELECTRIC};
            background: {cls.BG_ELEVATED};
        }}
        QLineEdit:hover:!focus {{
            border: 1px solid {cls.BLUE_DIM};
        }}
        QLineEdit::placeholder {{
            color: {cls.TEXT_MUTED};
        }}
        """

    @classmethod
    def progress_style(cls) -> str:
        return f"""
        QProgressBar {{
            border: none;
            border-radius: 4px;
            background: {cls.BG_SURFACE};
            height: 6px;
            text-align: center;
            font-size: {cls.FS_XS};
            color: transparent;
        }}
        QProgressBar::chunk {{
            background: {cls.GRADIENT_PRIMARY};
            border-radius: 4px;
        }}
        """

    @classmethod
    def get_button_style(cls, variant: str = "primary") -> str:
        styles = {
            "primary": f"""
                QPushButton {{
                    background: {cls.GRADIENT_PRIMARY};
                    color: {cls.TEXT_PRIMARY};
                    border: none;
                    border-radius: {cls.R_MD};
                    padding: 12px 24px;
                    font-size: {cls.FS_MD};
                    font-weight: 700;
                    letter-spacing: 0.5px;
                }}
                QPushButton:hover {{
                    background: {cls.BLUE_BRIGHT};
                    color: {cls.TEXT_INVERSE};
                }}
                QPushButton:pressed {{
                    background: {cls.BLUE_ELECTRIC};
                    color: {cls.TEXT_INVERSE};
                    padding-top: 13px;
                    padding-bottom: 11px;
                }}
                QPushButton:disabled {{
                    background: {cls.BG_ELEVATED};
                    color: {cls.TEXT_MUTED};
                    border: 1px solid {cls.BG_BORDER};
                }}
            """,
            "accent": f"""
                QPushButton {{
                    background: {cls.GRADIENT_ACCENT};
                    color: {cls.TEXT_INVERSE};
                    border: none;
                    border-radius: {cls.R_MD};
                    padding: 12px 24px;
                    font-size: {cls.FS_MD};
                    font-weight: 700;
                    letter-spacing: 0.5px;
                }}
                QPushButton:hover {{
                    background: {cls.AMBER_BRIGHT};
                    color: {cls.TEXT_INVERSE};
                }}
                QPushButton:pressed {{
                    background: {cls.AMBER};
                    color: {cls.TEXT_INVERSE};
                    padding-top: 13px;
                    padding-bottom: 11px;
                }}
                QPushButton:disabled {{
                    background: {cls.BG_ELEVATED};
                    color: {cls.TEXT_MUTED};
                }}
            """,
            "ghost": f"""
                QPushButton {{
                    background: transparent;
                    color: {cls.TEXT_SECONDARY};
                    border: 1px solid {cls.BG_BORDER};
                    border-radius: {cls.R_MD};
                    padding: 10px 20px;
                    font-size: {cls.FS_BASE};
                    font-weight: 500;
                }}
                QPushButton:hover {{
                    background: {cls.GLASS_BG};
                    border: 1px solid {cls.GLASS_BORDER};
                    color: {cls.TEXT_PRIMARY};
                }}
                QPushButton:pressed {{
                    background: {cls.GLASS_HOVER};
                }}
            """,
            "danger": f"""
                QPushButton {{
                    background: rgba(239, 68, 68, 0.15);
                    color: {cls.ERROR};
                    border: 1px solid rgba(239, 68, 68, 0.3);
                    border-radius: {cls.R_MD};
                    padding: 10px 20px;
                    font-size: {cls.FS_BASE};
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background: {cls.ERROR};
                    color: white;
                    border: 1px solid {cls.ERROR};
                }}
                QPushButton:pressed {{
                    background: #DC2626;
                }}
            """,
            "record": f"""
                QPushButton {{
                    background: {cls.GRADIENT_PRIMARY};
                    color: {cls.TEXT_PRIMARY};
                    border: none;
                    border-radius: {cls.R_MD};
                    padding: 14px 24px;
                    font-size: {cls.FS_MD};
                    font-weight: 700;
                    letter-spacing: 1px;
                }}
                QPushButton:hover {{
                    background: {cls.BLUE_BRIGHT};
                    color: {cls.TEXT_INVERSE};
                }}
                QPushButton:pressed {{
                    padding-top: 15px; padding-bottom: 13px;
                }}
                QPushButton:disabled {{
                    background: {cls.BG_ELEVATED};
                    color: {cls.TEXT_MUTED};
                }}
            """,
        }
        return styles.get(variant, styles["primary"])

    @classmethod
    def get_card_style(cls) -> str:
        return cls.solid_card_style()

    @classmethod
    def get_input_style(cls) -> str:
        return cls.input_style()