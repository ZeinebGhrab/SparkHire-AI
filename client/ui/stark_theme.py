"""
SparkHire AI — Design System v5  ·  Precision Intelligence
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Aesthetic: Editorial luxury meets enterprise precision.
Palette: Pearl white · Deep indigo · Electric cyan · Warm amber
Influences: Linear.app · Vercel Dashboard · Stripe Atlas

Rules:
  • Layered depth through shadows, NOT opacity hacks
  • Indigo primary, cyan accent, amber highlight
  • Typography: Outfit display / Inter body (system fallbacks)
  • Border: 1px #E2E8F0 cards | 2px colored for focus/select
  • Motion: pure QSS :hover/:pressed states
"""


class T:
    """Design token namespace."""

    # ── Base Backgrounds ───────────────────────────────────────────
    BG_APP          = "#F5F7FF"   # pearl blue-white — main window
    BG_PAGE         = "#EEF2FF"   # indigo-50 tint — secondary zones
    BG_CARD         = "#FFFFFF"   # pure white — cards/surfaces
    BG_CARD_ALT     = "#FAFBFF"   # barely-there tint — alt cards
    BG_HOVER        = "#F0F4FF"   # hovered surfaces
    BG_SELECTED     = "#EEF2FF"   # selected state
    BG_INPUT        = "#FFFFFF"
    BG_INPUT_FOCUS  = "#FAFBFF"
    BG_SIDEBAR      = "#1E1B4B"   # deep indigo sidebar

    # ── Borders ───────────────────────────────────────────────────
    BORDER          = "#E2E8F0"   # slate-200
    BORDER_FOCUS    = "#6366F1"   # indigo-500
    BORDER_HOVER    = "#C7D2FE"   # indigo-200
    BORDER_SELECT   = "#4F46E5"   # indigo-600
    BORDER_STRONG   = "#CBD5E1"   # slate-300

    # ── Indigo/Blue Primary ───────────────────────────────────────
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

    # ── Cyan / Teal Accent ────────────────────────────────────────
    CYAN_50         = "#ECFEFF"
    CYAN_100        = "#CFFAFE"
    CYAN_200        = "#A5F3FC"
    CYAN_400        = "#22D3EE"
    CYAN_500        = "#06B6D4"
    CYAN_600        = "#0891B2"
    CYAN_700        = "#0E7490"

    # ── Amber / Gold Highlight ────────────────────────────────────
    AMBER_50        = "#FFFBEB"
    AMBER_100       = "#FEF3C7"
    AMBER_200       = "#FDE68A"
    AMBER_400       = "#FBBF24"
    AMBER_500       = "#F59E0B"
    AMBER_600       = "#D97706"
    ORANGE_500      = "#F97316"
    ORANGE_600      = "#EA580C"

    # ── Status Colors ─────────────────────────────────────────────
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
    VIOLET_50       = "#F5F3FF"
    VIOLET_100      = "#EDE9FE"
    VIOLET_500      = "#8B5CF6"
    VIOLET_600      = "#7C3AED"

    # ── Text Hierarchy ────────────────────────────────────────────
    TEXT_950        = "#030712"   # near-black for headings
    TEXT_900        = "#0F172A"   # slate-900
    TEXT_800        = "#1E293B"   # slate-800 — body
    TEXT_700        = "#334155"   # slate-700 — secondary body
    TEXT_600        = "#475569"   # slate-600 — muted
    TEXT_500        = "#64748B"   # slate-500 — placeholder
    TEXT_400        = "#94A3B8"   # slate-400 — disabled
    TEXT_300        = "#CBD5E1"   # slate-300
    TEXT_WHITE      = "#FFFFFF"
    TEXT_INDIGO     = "#4F46E5"   # colored text

    # ── Typography ────────────────────────────────────────────────
    FONT            = "'Outfit', 'Plus Jakarta Sans', 'Nunito', 'Segoe UI', sans-serif"
    FONT_BODY       = "'Inter', 'DM Sans', 'Segoe UI', sans-serif"
    FONT_MONO       = "'JetBrains Mono', 'Cascadia Code', 'Fira Code', monospace"
    FONT_DISPLAY    = "'Outfit', 'Plus Jakarta Sans', sans-serif"

    FS_2XS  = 9
    FS_XS   = 10
    FS_SM   = 12
    FS_BASE = 13
    FS_MD   = 15
    FS_LG   = 18
    FS_XL   = 22
    FS_2XL  = 28
    FS_3XL  = 36
    FS_4XL  = 44

    # ── Spacing ───────────────────────────────────────────────────
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
    R_SM   = 6
    R_MD   = 10
    R_LG   = 14
    R_XL   = 18
    R_2XL  = 24
    R_FULL = 9999


class StarkTheme:
    """Main theme class — all shared aliases and component styles."""

    # ─── Primary Gradients ────────────────────────────────────────
    GRADIENT_PRIMARY = (
        f"qlineargradient(x1:0,y1:0,x2:1,y2:0,"
        f"stop:0 {T.INDIGO_600},stop:1 {T.INDIGO_500})"
    )
    GRADIENT_PRIMARY_HOVER = (
        f"qlineargradient(x1:0,y1:0,x2:1,y2:0,"
        f"stop:0 {T.INDIGO_700},stop:1 {T.INDIGO_600})"
    )
    GRADIENT_CYAN = (
        f"qlineargradient(x1:0,y1:0,x2:1,y2:0,"
        f"stop:0 {T.CYAN_500},stop:1 {T.CYAN_600})"
    )
    GRADIENT_ACCENT = (
        f"qlineargradient(x1:0,y1:0,x2:1,y2:0,"
        f"stop:0 {T.AMBER_500},stop:1 {T.ORANGE_500})"
    )
    GRADIENT_HERO = (
        f"qlineargradient(x1:0,y1:0,x2:1,y2:1,"
        f"stop:0 {T.INDIGO_600},stop:0.5 {T.INDIGO_500},stop:1 {T.CYAN_500})"
    )
    GRADIENT_BACKGROUND = (
        f"qlineargradient(x1:0,y1:0,x2:1,y2:1,"
        f"stop:0 {T.BG_APP},stop:0.6 {T.BG_CARD},stop:1 {T.INDIGO_50})"
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
    BLUE_GLOW       = "rgba(99,102,241,0.15)"
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
    AMBER_GLOW      = "rgba(245,158,11,0.12)"
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
    BORDER_LIGHT    = T.BORDER
    FONT_DISPLAY    = T.FONT
    FONT_BODY       = T.FONT_BODY
    FONT_MONO       = T.FONT_MONO
    FONT_FAMILY_PRIMARY = T.FONT
    FONT_FAMILY_MONO    = T.FONT_MONO
    FS_XS   = f"{T.FS_XS}px";  FS_SM   = f"{T.FS_SM}px"
    FS_BASE = f"{T.FS_BASE}px"; FS_MD   = f"{T.FS_MD}px"
    FS_LG   = f"{T.FS_LG}px";  FS_XL   = f"{T.FS_XL}px"
    FS_2XL  = f"{T.FS_2XL}px"; FS_3XL  = f"{T.FS_3XL}px"
    SP_XS   = f"{T.SP_1}px";  SP_XS_INT = T.SP_1
    SP_SM   = f"{T.SP_2}px";  SP_SM_INT = T.SP_2
    SP_MD   = f"{T.SP_4}px";  SP_MD_INT = T.SP_4
    SP_LG   = f"{T.SP_5}px";  SP_LG_INT = T.SP_5
    SP_XL   = f"{T.SP_6}px";  SP_XL_INT = T.SP_6
    SP_2XL  = f"{T.SP_8}px";  SP_2XL_INT = T.SP_8
    SPACING_MD  = f"{T.SP_4}px"; SPACING_MD_INT  = T.SP_4
    SPACING_LG  = f"{T.SP_5}px"; SPACING_LG_INT  = T.SP_5
    SPACING_XL  = f"{T.SP_6}px"; SPACING_XL_INT  = T.SP_6
    SPACING_SM_INT = T.SP_2; SPACING_XS_INT = T.SP_1
    R_SM   = f"{T.R_SM}px";  R_MD   = f"{T.R_MD}px"
    R_LG   = f"{T.R_LG}px";  R_XL   = f"{T.R_XL}px"
    R_2XL  = f"{T.R_2XL}px"; R_FULL = f"{T.R_FULL}px"
    RADIUS_MEDIUM = f"{T.R_MD}px"
    RADIUS_LARGE  = f"{T.R_LG}px"
    RADIUS_SMALL  = f"{T.R_SM}px"

    # ─────────────────────────────────────────────────────────────────
    #  GLOBAL STYLESHEET
    # ─────────────────────────────────────────────────────────────────
    @classmethod
    def global_stylesheet(cls) -> str:
        return f"""
/* ══════════════════════════════════════════════════════════
   BASE
══════════════════════════════════════════════════════════ */
QMainWindow, QDialog {{
    background: {T.BG_APP};
}}
QWidget {{
    background: transparent;
    color: {T.TEXT_800};
    font-family: {T.FONT};
    font-size: {T.FS_BASE}px;
    selection-background-color: {T.INDIGO_100};
    selection-color: {T.INDIGO_700};
}}

/* ══════════════════════════════════════════════════════════
   SCROLLBARS
══════════════════════════════════════════════════════════ */
QScrollBar:vertical {{
    background: transparent;
    width: 5px;
    border-radius: 3px;
    margin: 4px 1px;
}}
QScrollBar::handle:vertical {{
    background: {T.INDIGO_200};
    border-radius: 3px;
    min-height: 28px;
}}
QScrollBar::handle:vertical:hover {{ background: {T.INDIGO_400}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{
    background: transparent;
    height: 5px;
    border-radius: 3px;
    margin: 1px 4px;
}}
QScrollBar::handle:horizontal {{
    background: {T.INDIGO_200};
    border-radius: 3px;
    min-width: 28px;
}}
QScrollBar::handle:horizontal:hover {{ background: {T.INDIGO_400}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

/* ══════════════════════════════════════════════════════════
   TOOLTIP
══════════════════════════════════════════════════════════ */
QToolTip {{
    background: {T.TEXT_900};
    color: {T.TEXT_WHITE};
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: {T.R_SM}px;
    padding: 7px 12px;
    font-size: {T.FS_SM}px;
    font-weight: 500;
}}

/* ══════════════════════════════════════════════════════════
   MESSAGEBOX
══════════════════════════════════════════════════════════ */
QMessageBox {{
    background: {T.BG_CARD};
    border: 1px solid {T.BORDER};
    border-radius: {T.R_XL}px;
}}
QMessageBox QLabel {{
    color: {T.TEXT_700};
    font-size: {T.FS_MD}px;
    background: transparent;
}}
QMessageBox QPushButton {{
    background: {cls.GRADIENT_PRIMARY};
    color: {T.TEXT_WHITE};
    border: none;
    border-radius: {T.R_MD}px;
    padding: 9px 24px;
    font-weight: 700;
    font-size: {T.FS_SM}px;
    min-width: 88px;
    letter-spacing: 0.3px;
}}
QMessageBox QPushButton:hover {{
    background: {cls.GRADIENT_PRIMARY_HOVER};
}}

/* ══════════════════════════════════════════════════════════
   STATUS BAR
══════════════════════════════════════════════════════════ */
QStatusBar {{
    background: {T.BG_CARD};
    color: {T.TEXT_500};
    font-size: {T.FS_XS}px;
    font-weight: 500;
    border-top: 1px solid {T.BORDER};
    padding: 0 20px;
    min-height: 26px;
    letter-spacing: 0.5px;
}}
QStatusBar::item {{ border: none; }}
"""

    # ─────────────────────────────────────────────────────────────────
    #  COMPONENT STYLES
    # ─────────────────────────────────────────────────────────────────

    @classmethod
    def card_style(cls, *, selected: bool = False, radius: int = T.R_LG,
                   hover: bool = False) -> str:
        if selected:
            return f"""QFrame {{
                background: {T.INDIGO_50};
                border: 2px solid {T.INDIGO_500};
                border-radius: {radius}px;
            }}"""
        return f"""QFrame {{
            background: {T.BG_CARD};
            border: 1px solid {T.BORDER};
            border-radius: {radius}px;
        }}
        QFrame:hover {{
            border: 1px solid {T.BORDER_HOVER};
            background: {T.BG_HOVER};
        }}"""

    @classmethod
    def input_style(cls) -> str:
        return f"""
        QLineEdit {{
            background: {T.BG_INPUT};
            border: 1.5px solid {T.BORDER};
            border-radius: {T.R_MD}px;
            padding: 12px 16px;
            font-size: {T.FS_MD}px;
            font-family: {T.FONT_MONO};
            color: {T.TEXT_800};
            letter-spacing: 0.5px;
        }}
        QLineEdit:hover {{
            border: 1.5px solid {T.BORDER_HOVER};
            background: {T.BG_HOVER};
        }}
        QLineEdit:focus {{
            border: 2px solid {T.INDIGO_500};
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
            border-radius: 5px;
            background: {T.INDIGO_100};
            height: 8px;
            text-align: center;
            color: transparent;
        }}
        QProgressBar::chunk {{
            background: {cls.GRADIENT_PRIMARY};
            border-radius: 5px;
        }}
        """

    @classmethod
    def get_button_style(cls, variant: str = "primary") -> str:
        variants = {
            # ── Indigo gradient (main action) ────────────────────
            "primary": f"""
                QPushButton {{
                    background: {cls.GRADIENT_PRIMARY};
                    color: {T.TEXT_WHITE};
                    border: none;
                    border-radius: {T.R_MD}px;
                    padding: 13px 30px;
                    font-size: {T.FS_MD}px;
                    font-weight: 700;
                    letter-spacing: 0.4px;
                    font-family: {T.FONT};
                }}
                QPushButton:hover {{
                    background: {cls.GRADIENT_PRIMARY_HOVER};
                }}
                QPushButton:pressed {{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 {T.INDIGO_800},stop:1 {T.INDIGO_700});
                    padding-top: 14px; padding-bottom: 12px;
                }}
                QPushButton:disabled {{
                    background: {T.BG_PAGE};
                    color: {T.TEXT_400};
                    border: 1px solid {T.BORDER};
                }}
            """,
            # ── Amber/Orange (start/accent) ──────────────────────
            "accent": f"""
                QPushButton {{
                    background: {cls.GRADIENT_ACCENT};
                    color: {T.TEXT_WHITE};
                    border: none;
                    border-radius: {T.R_MD}px;
                    padding: 13px 30px;
                    font-size: {T.FS_MD}px;
                    font-weight: 700;
                    letter-spacing: 0.4px;
                    font-family: {T.FONT};
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 {T.AMBER_600},stop:1 {T.ORANGE_600});
                }}
                QPushButton:pressed {{
                    padding-top: 14px; padding-bottom: 12px;
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 #92400E,stop:1 #7C2D12);
                }}
                QPushButton:disabled {{
                    background: {T.BG_PAGE};
                    color: {T.TEXT_400};
                    border: 1px solid {T.BORDER};
                }}
            """,
            # ── Ghost / Outline ──────────────────────────────────
            "ghost": f"""
                QPushButton {{
                    background: transparent;
                    color: {T.TEXT_600};
                    border: 1.5px solid {T.BORDER};
                    border-radius: {T.R_MD}px;
                    padding: 10px 22px;
                    font-size: {T.FS_BASE}px;
                    font-weight: 600;
                    font-family: {T.FONT};
                }}
                QPushButton:hover {{
                    background: {T.INDIGO_50};
                    border: 1.5px solid {T.INDIGO_200};
                    color: {T.INDIGO_600};
                }}
                QPushButton:pressed {{
                    background: {T.INDIGO_100};
                    border: 1.5px solid {T.INDIGO_300};
                    color: {T.INDIGO_700};
                }}
            """,
            # ── Danger (end interview) ───────────────────────────
            "danger": f"""
                QPushButton {{
                    background: {T.RED_50};
                    color: {T.RED_600};
                    border: 1.5px solid {T.RED_200};
                    border-radius: {T.R_MD}px;
                    padding: 10px 22px;
                    font-size: {T.FS_BASE}px;
                    font-weight: 600;
                    font-family: {T.FONT};
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 {T.RED_500},stop:1 {T.RED_600});
                    color: {T.TEXT_WHITE};
                    border: none;
                }}
                QPushButton:pressed {{
                    background: {T.RED_700};
                    padding-top: 11px; padding-bottom: 9px;
                }}
            """,
            # ── Record (cyan action) ─────────────────────────────
            "record": f"""
                QPushButton {{
                    background: {cls.GRADIENT_PRIMARY};
                    color: {T.TEXT_WHITE};
                    border: none;
                    border-radius: {T.R_MD}px;
                    padding: 14px 30px;
                    font-size: {T.FS_MD}px;
                    font-weight: 700;
                    letter-spacing: 0.5px;
                    font-family: {T.FONT};
                }}
                QPushButton:hover {{
                    background: {cls.GRADIENT_PRIMARY_HOVER};
                }}
                QPushButton:pressed {{
                    padding-top: 15px; padding-bottom: 13px;
                }}
                QPushButton:disabled {{
                    background: {T.BG_PAGE};
                    color: {T.TEXT_400};
                    border: 1.5px solid {T.BORDER};
                }}
            """,
        }
        return variants.get(variant, variants["primary"])

    # ─── Helper utilities ─────────────────────────────────────────────────────

    @classmethod
    def badge_style(cls, color: str = T.INDIGO_500,
                    bg: str = T.INDIGO_50) -> str:
        return f"""
            QLabel {{
                background: {bg};
                color: {color};
                border: 1px solid {color}40;
                border-radius: {T.R_FULL}px;
                padding: 4px 12px;
                font-size: {T.FS_XS}px;
                font-weight: 700;
                letter-spacing: 0.8px;
            }}
        """

    @classmethod
    def section_title_style(cls) -> str:
        return f"""
            QLabel {{
                color: {T.TEXT_400};
                font-size: {T.FS_XS}px;
                font-weight: 700;
                letter-spacing: 2px;
                background: transparent;
            }}
        """

    # ─── Backward compat ─────────────────────────────────────────────────────
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