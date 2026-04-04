
class T:


    # ── Base Backgrounds — warm ivory palette ─────────────────────
    BG_APP          = "#FAFAF7"   # warm off-white
    BG_PAGE         = "#F4F3EE"   # warm cream
    BG_CARD         = "#FFFFFF"   # pure white cards
    BG_CARD_ALT     = "#FFFFFE"
    BG_HOVER        = "#F7F6F1"   # warm hover
    BG_SELECTED     = "#EBF8F5"   # teal-tinted selection
    BG_INPUT        = "#FFFFFF"
    BG_INPUT_FOCUS  = "#FAFFFE"

    # ── Borders — warm undertone ──────────────────────────────────
    BORDER          = "#E8E6DF"
    BORDER_FOCUS    = "#14B8A6"
    BORDER_HOVER    = "#D6D3C9"
    BORDER_SELECT   = "#0D9488"
    BORDER_STRONG   = "#D6D3C9"

    # ── Teal Primary ──────────────────────────────────────────────
    TEAL_50         = "#F0FDFA"
    TEAL_100        = "#CCFBF1"
    TEAL_200        = "#99F6E4"
    TEAL_300        = "#5EEAD4"
    TEAL_400        = "#2DD4BF"
    TEAL_500        = "#14B8A6"
    TEAL_600        = "#0D9488"
    TEAL_700        = "#0F766E"
    TEAL_800        = "#115E59"
    TEAL_900        = "#134E4A"

    # ── Coral / Warm Accent ───────────────────────────────────────
    CORAL_50        = "#FFF7F5"
    CORAL_100       = "#FFE8E2"
    CORAL_200       = "#FFCFC4"
    CORAL_400       = "#F87B5E"
    CORAL_500       = "#EF5B3A"
    CORAL_600       = "#D94526"
    CORAL_700       = "#B83520"

    # ── Amber / Warm Yellow ───────────────────────────────────────
    AMBER_50        = "#FFFBEB"
    AMBER_100       = "#FEF3C7"
    AMBER_200       = "#FDE68A"
    AMBER_400       = "#FBBF24"
    AMBER_500       = "#F59E0B"
    AMBER_600       = "#D97706"
    AMBER_700       = "#B45309"

    # ── Status ────────────────────────────────────────────────────
    GREEN_50        = "#F0FDF4"
    GREEN_100       = "#DCFCE7"
    GREEN_200       = "#BBF7D0"
    GREEN_500       = "#22C55E"
    GREEN_600       = "#16A34A"
    GREEN_700       = "#15803D"
    RED_50          = "#FFF1F2"
    RED_100         = "#FFE4E6"
    RED_200         = "#FECDD3"
    RED_400         = "#FB7185"
    RED_500         = "#EF4444"
    RED_600         = "#DC2626"
    RED_700         = "#B91C1C"

    # ── Indigo (legacy compat maps to Teal) ──────────────────────
    INDIGO_50       = "#F0FDFA"
    INDIGO_100      = "#CCFBF1"
    INDIGO_200      = "#99F6E4"
    INDIGO_400      = "#2DD4BF"
    INDIGO_500      = "#14B8A6"
    INDIGO_600      = "#0D9488"
    INDIGO_700      = "#0F766E"
    INDIGO_800      = "#115E59"
    INDIGO_900      = "#134E4A"

    # ── Violet (legacy maps to Coral) ─────────────────────────────
    VIOLET_50       = "#FFF7F5"
    VIOLET_100      = "#FFE8E2"
    VIOLET_400      = "#F87B5E"
    VIOLET_500      = "#EF5B3A"
    VIOLET_600      = "#D94526"

    # ── Cyan (legacy maps to Teal) ────────────────────────────────
    CYAN_50         = "#F0FDFA"
    CYAN_100        = "#CCFBF1"
    CYAN_200        = "#99F6E4"
    CYAN_400        = "#2DD4BF"
    CYAN_500        = "#14B8A6"
    CYAN_600        = "#0D9488"
    CYAN_700        = "#0F766E"

    # ── Blue (legacy) ─────────────────────────────────────────────
    BLUE_400        = "#2DD4BF"
    BLUE_500        = "#14B8A6"
    BLUE_600        = "#0D9488"

    # ── Orange (legacy) ───────────────────────────────────────────
    ORANGE_500      = "#F97316"
    ORANGE_600      = "#EA580C"

    # ── Text Hierarchy — warm neutral ─────────────────────────────
    TEXT_950        = "#1A1916"
    TEXT_900        = "#262520"
    TEXT_800        = "#3A3831"
    TEXT_700        = "#504E46"
    TEXT_600        = "#6B6860"
    TEXT_500        = "#8C8A82"
    TEXT_400        = "#ADAAA2"
    TEXT_300        = "#D1CFC7"
    TEXT_WHITE      = "#FFFFFF"
    TEXT_INDIGO     = "#0D9488"

    # ── Typography — warm humanist ────────────────────────────────
    FONT            = "'Plus Jakarta Sans', 'DM Sans', 'Segoe UI', system-ui, sans-serif"
    FONT_BODY       = "'Inter', 'Plus Jakarta Sans', 'Segoe UI', sans-serif"
    FONT_MONO       = "'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace"
    FONT_DISPLAY    = "'Plus Jakarta Sans', 'DM Sans', sans-serif"

    FS_2XS  = 9
    FS_XS   = 10
    FS_SM   = 12
    FS_BASE = 13
    FS_MD   = 15
    FS_LG   = 18
    FS_XL   = 22
    FS_2XL  = 28
    FS_3XL  = 34
    FS_4XL  = 44

    # ── Spacing — 8px grid ────────────────────────────────────────
    SP_1  = 4
    SP_2  = 8
    SP_3  = 12
    SP_4  = 16
    SP_5  = 20
    SP_6  = 24
    SP_8  = 32
    SP_10 = 40
    SP_12 = 48

    # ── Border Radius ─────────────────────────────────────────────
    R_SM   = 8
    R_MD   = 12
    R_LG   = 14
    R_XL   = 18
    R_2XL  = 22
    R_FULL = 9999

    # ── Sidebar ───────────────────────────────────────────────────
    BG_SIDEBAR      = "#0F3D38"


class StarkTheme:
    """Main theme class — v7 Warm Premium Light."""

    GRADIENT_PRIMARY = (
        f"qlineargradient(x1:0,y1:0,x2:1,y2:0,"
        f"stop:0 {T.TEAL_500},stop:1 {T.TEAL_600})"
    )
    GRADIENT_PRIMARY_HOVER = (
        f"qlineargradient(x1:0,y1:0,x2:1,y2:0,"
        f"stop:0 {T.TEAL_600},stop:1 {T.TEAL_700})"
    )
    GRADIENT_CYAN = (
        f"qlineargradient(x1:0,y1:0,x2:1,y2:0,"
        f"stop:0 {T.TEAL_400},stop:1 {T.TEAL_500})"
    )
    GRADIENT_ACCENT = (
        f"qlineargradient(x1:0,y1:0,x2:1,y2:0,"
        f"stop:0 {T.TEAL_500},stop:1 {T.CORAL_500})"
    )
    GRADIENT_HERO = (
        f"qlineargradient(x1:0,y1:0,x2:1,y2:1,"
        f"stop:0 {T.TEAL_600},stop:0.5 {T.TEAL_500},stop:1 {T.CORAL_500})"
    )
    GRADIENT_BACKGROUND = (
        f"qlineargradient(x1:0,y1:0,x2:1,y2:1,"
        f"stop:0 {T.BG_APP},stop:0.6 {T.BG_CARD},stop:1 #F0FAF8)"
    )
    GRADIENT_CARD = T.BG_CARD

    # Backward compat aliases
    BG_VOID         = T.BG_APP
    BG_DEEP         = T.BG_PAGE
    BG_SURFACE      = T.BG_CARD
    BG_ELEVATED     = T.BG_HOVER
    BG_BORDER       = T.BORDER
    BLUE_ELECTRIC   = T.TEAL_500
    BLUE_BRIGHT     = T.TEAL_400
    BLUE_SOFT       = T.TEAL_600
    BLUE_DIM        = T.TEAL_100
    BLUE_GLOW       = "rgba(20,184,166,0.12)"
    BLUE_600        = T.TEAL_600
    BLUE_700        = T.TEAL_700
    BLUE_PRIMARY    = T.TEAL_500
    BLUE_DARK       = T.TEAL_700
    BLUE_LIGHT      = T.TEAL_400
    BLUE_EXTRA_LIGHT = T.TEAL_100
    BLUE_50         = T.TEAL_50
    BLUE_100        = T.TEAL_100
    CYAN_50         = T.CYAN_50
    CYAN_100        = T.CYAN_100
    AMBER           = T.AMBER_500
    AMBER_BRIGHT    = T.AMBER_400
    AMBER_SOFT      = T.AMBER_100
    AMBER_DIM       = T.AMBER_50
    AMBER_GLOW      = "rgba(245,158,11,0.10)"
    ORANGE_ACCENT   = T.CORAL_500
    ORANGE_LIGHT    = T.CORAL_400
    ORANGE_500      = T.ORANGE_500
    ORANGE_600      = T.ORANGE_600
    ORANGE_400      = T.CORAL_400
    SUCCESS         = T.GREEN_500
    SUCCESS_GLOW    = T.GREEN_50
    WARNING         = T.AMBER_500
    ERROR           = T.RED_500
    ERROR_GLOW      = T.RED_50
    GREEN_50        = T.GREEN_50
    GREEN_100       = T.GREEN_100
    GREEN_500       = T.GREEN_500
    GREEN_600       = T.GREEN_600
    GREEN_700       = T.GREEN_700
    RED_50          = T.RED_50
    RED_100         = T.RED_100
    RED_500         = T.RED_500
    RED_600         = T.RED_600
    RED_700         = T.RED_700
    TEXT_PRIMARY    = T.TEXT_800
    TEXT_SECONDARY  = T.TEXT_600
    TEXT_MUTED      = T.TEXT_400
    TEXT_INVERSE    = T.TEXT_WHITE
    WHITE           = T.TEXT_WHITE
    GLASS_BG        = T.BG_CARD
    GLASS_BORDER    = T.BORDER
    GLASS_HOVER     = T.BG_HOVER
    GLASS_STRONG    = T.BG_CARD
    OVERLAY_DARK    = T.BG_CARD
    BORDER_CYAN     = T.BORDER_FOCUS
    BORDER_WHITE    = T.BORDER

    SHADOW_XS  = "0 1px 2px rgba(0,0,0,0.03)"
    SHADOW_SM  = "0 2px 8px rgba(0,0,0,0.05), 0 1px 2px rgba(0,0,0,0.03)"
    SHADOW_MD  = "0 4px 16px rgba(0,0,0,0.07), 0 1px 4px rgba(0,0,0,0.03)"
    SHADOW_LG  = "0 8px 32px rgba(0,0,0,0.09), 0 2px 8px rgba(0,0,0,0.03)"
    SHADOW_XL  = "0 16px 48px rgba(0,0,0,0.11), 0 4px 12px rgba(0,0,0,0.04)"
    SHADOW_INDIGO = "0 8px 24px rgba(20,184,166,0.18), 0 2px 8px rgba(20,184,166,0.08)"

    @classmethod
    def global_stylesheet(cls) -> str:
        return f"""
        * {{
            font-family: {T.FONT};
            outline: none;
        }}
        QMainWindow {{
            background: {T.BG_APP};
        }}
        QStatusBar {{
            background: {T.BG_CARD};
            border-top: 1px solid {T.BORDER};
            color: {T.TEXT_500};
            font-size: {T.FS_XS}px;
            font-family: {T.FONT};
            padding: 0 16px;
        }}
        QScrollBar:vertical {{
            background: {T.BG_APP};
            width: 6px;
            border-radius: 3px;
        }}
        QScrollBar::handle:vertical {{
            background: {T.BORDER};
            border-radius: 3px;
            min-height: 24px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {T.BORDER_HOVER};
        }}
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {{
            height: 0;
        }}
        QToolTip {{
            background: {T.TEXT_900};
            color: {T.TEXT_WHITE};
            border: none;
            border-radius: 6px;
            padding: 6px 10px;
            font-size: {T.FS_SM}px;
        }}
        """

    @classmethod
    def card_style(cls, hover: bool = False) -> str:
        hover_css = f"""
            QFrame:hover {{
                background: {T.BG_CARD};
                border-color: {T.BORDER_HOVER};
            }}
        """ if hover else ""
        return f"""
        QFrame {{
            background: {T.BG_CARD};
            border: 1px solid {T.BORDER};
            border-radius: {T.R_XL}px;
        }}
        {hover_css}
        """

    @classmethod
    def input_style(cls) -> str:
        return f"""
        QLineEdit {{
            background: {T.BG_INPUT};
            border: 1.5px solid {T.BORDER};
            border-radius: {T.R_MD}px;
            padding: 14px 18px;
            font-size: {T.FS_MD}px;
            font-family: {T.FONT_MONO};
            color: {T.TEXT_800};
            letter-spacing: 0.4px;
        }}
        QLineEdit:hover {{
            border-color: {T.BORDER_HOVER};
            background: {T.BG_CARD};
        }}
        QLineEdit:focus {{
            border: 1.5px solid {T.TEAL_500};
            background: {T.BG_INPUT_FOCUS};
            color: {T.TEXT_900};
        }}
        QLineEdit::placeholder {{
            color: {T.TEXT_400};
        }}
        """

    @classmethod
    def progress_style(cls) -> str:
        return f"""
        QProgressBar {{
            border: none;
            border-radius: 3px;
            background: {T.TEAL_100};
            height: 5px;
            text-align: center;
            color: transparent;
        }}
        QProgressBar::chunk {{
            background: {cls.GRADIENT_PRIMARY};
            border-radius: 3px;
        }}
        """

    @classmethod
    def get_button_style(cls, variant: str = "primary") -> str:
        variants = {
            "primary": f"""
                QPushButton {{
                    background: {cls.GRADIENT_PRIMARY};
                    color: {T.TEXT_WHITE};
                    border: none;
                    border-radius: {T.R_LG}px;
                    padding: 14px 32px;
                    font-size: {T.FS_MD}px;
                    font-weight: 700;
                    letter-spacing: 0.3px;
                    font-family: {T.FONT};
                }}
                QPushButton:hover {{
                    background: {cls.GRADIENT_PRIMARY_HOVER};
                }}
                QPushButton:pressed {{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 {T.TEAL_700},stop:1 {T.TEAL_800});
                    padding-top: 15px; padding-bottom: 13px;
                }}
                QPushButton:disabled {{
                    background: {T.BG_PAGE};
                    color: {T.TEXT_400};
                    border: 1px solid {T.BORDER};
                }}
            """,
            "accent": f"""
                QPushButton {{
                    background: {cls.GRADIENT_PRIMARY};
                    color: {T.TEXT_WHITE};
                    border: none;
                    border-radius: {T.R_LG}px;
                    padding: 15px 32px;
                    font-size: {T.FS_MD}px;
                    font-weight: 700;
                    letter-spacing: 0.2px;
                    font-family: {T.FONT};
                }}
                QPushButton:hover {{
                    background: {cls.GRADIENT_PRIMARY_HOVER};
                }}
                QPushButton:pressed {{
                    padding-top: 16px; padding-bottom: 14px;
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 {T.TEAL_700},stop:1 {T.TEAL_800});
                }}
                QPushButton:disabled {{
                    background: {T.BG_PAGE};
                    color: {T.TEXT_400};
                    border: 1px solid {T.BORDER};
                }}
            """,
            "ghost": f"""
                QPushButton {{
                    background: transparent;
                    color: {T.TEXT_600};
                    border: 1px solid {T.BORDER};
                    border-radius: {T.R_MD}px;
                    padding: 10px 22px;
                    font-size: {T.FS_SM}px;
                    font-weight: 600;
                    font-family: {T.FONT};
                }}
                QPushButton:hover {{
                    background: {T.BG_HOVER};
                    border-color: {T.BORDER_HOVER};
                    color: {T.TEXT_800};
                }}
                QPushButton:pressed {{
                    background: {T.BG_PAGE};
                    color: {T.TEXT_900};
                }}
            """,
            "danger": f"""
                QPushButton {{
                    background: transparent;
                    color: {T.RED_500};
                    border: 1px solid {T.RED_200};
                    border-radius: {T.R_MD}px;
                    padding: 10px 22px;
                    font-size: {T.FS_SM}px;
                    font-weight: 600;
                    font-family: {T.FONT};
                }}
                QPushButton:hover {{
                    background: {T.RED_500};
                    color: {T.TEXT_WHITE};
                    border-color: {T.RED_500};
                }}
                QPushButton:pressed {{
                    background: {T.RED_600};
                    border-color: {T.RED_600};
                    padding-top: 11px; padding-bottom: 9px;
                }}
            """,
            "record": f"""
                QPushButton {{
                    background: {cls.GRADIENT_PRIMARY};
                    color: {T.TEXT_WHITE};
                    border: none;
                    border-radius: {T.R_LG}px;
                    padding: 15px 32px;
                    font-size: {T.FS_MD}px;
                    font-weight: 700;
                    letter-spacing: 0.2px;
                    font-family: {T.FONT};
                }}
                QPushButton:hover {{
                    background: {cls.GRADIENT_PRIMARY_HOVER};
                }}
                QPushButton:pressed {{
                    padding-top: 16px; padding-bottom: 14px;
                }}
                QPushButton:disabled {{
                    background: {T.BG_PAGE};
                    color: {T.TEXT_400};
                    border: 1px solid {T.BORDER};
                }}
            """,
        }
        return variants.get(variant, variants["primary"])

    @classmethod
    def badge_style(cls, color: str = T.TEAL_500, bg: str = T.TEAL_50) -> str:
        return f"""
            QLabel {{
                background: {bg};
                color: {color};
                border: 1px solid {color}30;
                border-radius: {T.R_FULL}px;
                padding: 3px 10px;
                font-size: {T.FS_XS}px;
                font-weight: 700;
                letter-spacing: 0.6px;
            }}
        """

    @classmethod
    def section_title_style(cls) -> str:
        return f"""
            QLabel {{
                color: {T.TEXT_400};
                font-size: {T.FS_XS}px;
                font-weight: 700;
                letter-spacing: 1.5px;
                background: transparent;
            }}
        """

    @classmethod
    def glass_card_style(cls, hover: bool = True) -> str:
        return cls.card_style()

    @classmethod
    def solid_card_style(cls) -> str:
        return cls.card_style()

    @classmethod
    def get_card_style(cls) -> str:
        return cls.card_style()

    @classmethod
    def get_input_style(cls) -> str:
        return cls.input_style()
