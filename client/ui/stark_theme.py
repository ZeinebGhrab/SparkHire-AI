"""
SparkHire AI — Design System v6  ·  Clean SaaS Edition
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Aesthetic: Stripe / Linear / Notion — refined, light, minimal.
Palette: Pure white surfaces · Soft gray borders · Indigo/violet primary
Rules:
  • Shadows over borders wherever possible
  • 8px grid spacing system
  • 12–16px border-radius on interactive elements
  • Typography: DM Sans display / Inter body
  • Primary: indigo→violet gradient
  • No hard borders — only #E5E7EB separators
"""


class T:
    """Design token namespace — v6 clean SaaS."""

    # ── Base Backgrounds ───────────────────────────────────────────
    BG_APP          = "#F8FAFC"   # off-white, ultra-light blue tint
    BG_PAGE         = "#F1F5F9"   # slate-100
    BG_CARD         = "#FFFFFF"   # pure white cards
    BG_CARD_ALT     = "#FAFAFA"   # barely-there alt
    BG_HOVER        = "#F8FAFC"   # hover state
    BG_SELECTED     = "#EEF2FF"   # indigo-50 selection
    BG_INPUT        = "#FFFFFF"
    BG_INPUT_FOCUS  = "#FAFBFF"
    BG_SIDEBAR      = "#1E1B4B"

    # ── Borders — intentionally very light ────────────────────────
    BORDER          = "#E5E7EB"   # gray-200 — the ONE border color
    BORDER_FOCUS    = "#6366F1"   # indigo-500 focus ring
    BORDER_HOVER    = "#D1D5DB"   # gray-300 hover
    BORDER_SELECT   = "#4F46E5"   # indigo-600 selected
    BORDER_STRONG   = "#D1D5DB"   # gray-300

    # ── Indigo Primary ────────────────────────────────────────────
    INDIGO_50       = "#EEF2FF"
    INDIGO_100      = "#E0E7FF"
    INDIGO_200      = "#C7D2FE"
    INDIGO_300      = "#A5B4FC"
    INDIGO_400      = "#818CF8"
    INDIGO_500      = "#6366F1"
    INDIGO_600      = "#4F46E5"
    INDIGO_700      = "#4338CA"
    INDIGO_800      = "#3730A3"
    INDIGO_900      = "#312E81"

    # ── Violet accent (for gradient pair) ─────────────────────────
    VIOLET_50       = "#F5F3FF"
    VIOLET_100      = "#EDE9FE"
    VIOLET_400      = "#A78BFA"
    VIOLET_500      = "#8B5CF6"
    VIOLET_600      = "#7C3AED"

    # ── Cyan / Teal ───────────────────────────────────────────────
    CYAN_50         = "#ECFEFF"
    CYAN_100        = "#CFFAFE"
    CYAN_200        = "#A5F3FC"
    CYAN_400        = "#22D3EE"
    CYAN_500        = "#06B6D4"
    CYAN_600        = "#0891B2"
    CYAN_700        = "#0E7490"

    # ── Amber ─────────────────────────────────────────────────────
    AMBER_50        = "#FFFBEB"
    AMBER_100       = "#FEF3C7"
    AMBER_200       = "#FDE68A"
    AMBER_400       = "#FBBF24"
    AMBER_500       = "#F59E0B"
    AMBER_600       = "#D97706"
    ORANGE_500      = "#F97316"
    ORANGE_600      = "#EA580C"

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

    # ── Text Hierarchy ────────────────────────────────────────────
    TEXT_950        = "#030712"   # near-black headings
    TEXT_900        = "#111827"   # gray-900 — headings
    TEXT_800        = "#1F2937"   # gray-800 — body
    TEXT_700        = "#374151"   # gray-700
    TEXT_600        = "#4B5563"   # gray-600 — secondary
    TEXT_500        = "#6B7280"   # gray-500 — muted/placeholder
    TEXT_400        = "#9CA3AF"   # gray-400 — disabled
    TEXT_300        = "#D1D5DB"
    TEXT_WHITE      = "#FFFFFF"
    TEXT_INDIGO     = "#4F46E5"

    # ── Typography ────────────────────────────────────────────────
    # DM Sans: geometric but warmer than Inter; excellent at display sizes
    FONT            = "'DM Sans', 'Inter', 'Segoe UI', system-ui, sans-serif"
    FONT_BODY       = "'Inter', 'DM Sans', 'Segoe UI', sans-serif"
    FONT_MONO       = "'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace"
    FONT_DISPLAY    = "'DM Sans', 'Inter', sans-serif"

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

    # ── Border Radius — generous, modern ─────────────────────────
    R_SM   = 8
    R_MD   = 12
    R_LG   = 14
    R_XL   = 16
    R_2XL  = 20
    R_FULL = 9999


class StarkTheme:
    """Main theme class — all shared aliases and component styles, v6."""

    # ─── Primary Gradients — indigo → violet ──────────────────────
    GRADIENT_PRIMARY = (
        f"qlineargradient(x1:0,y1:0,x2:1,y2:0,"
        f"stop:0 {T.INDIGO_600},stop:1 {T.VIOLET_500})"
    )
    GRADIENT_PRIMARY_HOVER = (
        f"qlineargradient(x1:0,y1:0,x2:1,y2:0,"
        f"stop:0 {T.INDIGO_700},stop:1 {T.VIOLET_600})"
    )
    GRADIENT_CYAN = (
        f"qlineargradient(x1:0,y1:0,x2:1,y2:0,"
        f"stop:0 {T.CYAN_500},stop:1 {T.CYAN_600})"
    )
    GRADIENT_ACCENT = (
        f"qlineargradient(x1:0,y1:0,x2:1,y2:0,"
        f"stop:0 {T.INDIGO_500},stop:1 {T.VIOLET_500})"
    )
    GRADIENT_HERO = (
        f"qlineargradient(x1:0,y1:0,x2:1,y2:1,"
        f"stop:0 {T.INDIGO_600},stop:0.5 {T.VIOLET_500},stop:1 {T.CYAN_500})"
    )
    GRADIENT_BACKGROUND = (
        f"qlineargradient(x1:0,y1:0,x2:1,y2:1,"
        f"stop:0 {T.BG_APP},stop:0.6 {T.BG_CARD},stop:1 #F0F4FF)"
    )
    GRADIENT_CARD = T.BG_CARD

    # ─── Backward Compat Aliases ──────────────────────────────────
    BG_VOID         = T.BG_APP
    BG_DEEP         = T.BG_PAGE
    BG_SURFACE      = T.BG_CARD
    BG_ELEVATED     = T.BG_HOVER
    BG_BORDER       = T.BORDER
    BLUE_ELECTRIC   = T.INDIGO_500
    BLUE_BRIGHT     = T.INDIGO_400
    BLUE_SOFT       = T.INDIGO_600
    BLUE_DIM        = T.INDIGO_100
    BLUE_GLOW       = "rgba(99,102,241,0.12)"
    BLUE_600        = T.INDIGO_600
    BLUE_700        = T.INDIGO_700
    BLUE_PRIMARY    = T.INDIGO_500
    BLUE_DARK       = T.INDIGO_700
    BLUE_LIGHT      = T.CYAN_400
    BLUE_EXTRA_LIGHT = T.CYAN_100
    BLUE_50         = T.INDIGO_50
    BLUE_100        = T.INDIGO_100
    CYAN_50         = T.CYAN_50
    CYAN_100        = T.CYAN_100
    AMBER           = T.AMBER_500
    AMBER_BRIGHT    = T.AMBER_400
    AMBER_SOFT      = T.AMBER_100
    AMBER_DIM       = T.AMBER_50
    AMBER_GLOW      = "rgba(245,158,11,0.10)"
    ORANGE_ACCENT   = T.AMBER_500
    ORANGE_LIGHT    = T.AMBER_400
    ORANGE_500      = T.ORANGE_500
    ORANGE_600      = T.ORANGE_600
    ORANGE_400      = "#FB923C"
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

    # ─── Shared Shadow Presets ────────────────────────────────────
    # Soft, modern — no heavy black shadows
    SHADOW_XS  = "0 1px 2px rgba(0,0,0,0.04)"
    SHADOW_SM  = "0 2px 8px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)"
    SHADOW_MD  = "0 4px 16px rgba(0,0,0,0.08), 0 1px 4px rgba(0,0,0,0.04)"
    SHADOW_LG  = "0 8px 32px rgba(0,0,0,0.10), 0 2px 8px rgba(0,0,0,0.04)"
    SHADOW_XL  = "0 16px 48px rgba(0,0,0,0.12), 0 4px 12px rgba(0,0,0,0.05)"
    SHADOW_INDIGO = "0 8px 24px rgba(99,102,241,0.20), 0 2px 8px rgba(99,102,241,0.10)"

    # ─── Global Stylesheet ────────────────────────────────────────

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

    # ─── Card ─────────────────────────────────────────────────────

    @classmethod
    def card_style(cls, hover: bool = False) -> str:
        """Clean white card — shadow-first, border optional."""
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

    # ─── Input ────────────────────────────────────────────────────

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
            border: 1.5px solid {T.INDIGO_500};
            background: {T.BG_INPUT_FOCUS};
            color: {T.TEXT_900};
        }}
        QLineEdit::placeholder {{
            color: {T.TEXT_400};
        }}
        """

    # ─── Progress Bar ─────────────────────────────────────────────

    @classmethod
    def progress_style(cls) -> str:
        return f"""
        QProgressBar {{
            border: none;
            border-radius: 3px;
            background: {T.INDIGO_100};
            height: 6px;
            text-align: center;
            color: transparent;
        }}
        QProgressBar::chunk {{
            background: {cls.GRADIENT_PRIMARY};
            border-radius: 3px;
        }}
        """

    # ─── Buttons ──────────────────────────────────────────────────

    @classmethod
    def get_button_style(cls, variant: str = "primary") -> str:
        variants = {
            # ── Primary: indigo → violet gradient ────────────────
            "primary": f"""
                QPushButton {{
                    background: {cls.GRADIENT_PRIMARY};
                    color: {T.TEXT_WHITE};
                    border: none;
                    border-radius: {T.R_LG}px;
                    padding: 14px 32px;
                    font-size: {T.FS_MD}px;
                    font-weight: 700;
                    letter-spacing: 0.2px;
                    font-family: {T.FONT};
                }}
                QPushButton:hover {{
                    background: {cls.GRADIENT_PRIMARY_HOVER};
                }}
                QPushButton:pressed {{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 {T.INDIGO_800},stop:1 {T.VIOLET_600});
                    padding-top: 15px; padding-bottom: 13px;
                }}
                QPushButton:disabled {{
                    background: {T.BG_PAGE};
                    color: {T.TEXT_400};
                    border: 1px solid {T.BORDER};
                }}
            """,
            # ── Accent: same gradient, used on session screen ─────
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
                        stop:0 {T.INDIGO_800},stop:1 {T.VIOLET_600});
                }}
                QPushButton:disabled {{
                    background: {T.BG_PAGE};
                    color: {T.TEXT_400};
                    border: 1px solid {T.BORDER};
                }}
            """,
            # ── Ghost / Outline ───────────────────────────────────
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
            # ── Danger ────────────────────────────────────────────
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
            # ── Record ────────────────────────────────────────────
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

    # ─── Badges ───────────────────────────────────────────────────

    @classmethod
    def badge_style(cls, color: str = T.INDIGO_500,
                    bg: str = T.INDIGO_50) -> str:
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

    # ─── Backward compat ─────────────────────────────────────────
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