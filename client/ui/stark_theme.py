"""
Stark Solutions — Design System v4  ·  Professional Light Theme
Inspiré du design web shadcn/ui · Palette claire moderne · QSS complet
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Règles de design :
  • Fonds solides (pas de semi-transparence sans blur, ça rend mal sous Qt)
  • Ombres via QGraphicsDropShadowEffect uniquement
  • Couleurs fidèles au web : slate-50/white/cyan-500/blue-600/amber-500
  • Borders précis : 1px slate-200 pour les cards, 2px colored pour focus/select
  • Radius : 8 / 12 / 16 / 24 px selon niveau hiérarchique
  • Hover via QSS :hover – pressed via :pressed – disabled via :disabled
"""


class T:
    """Token namespace – toutes les constantes de design."""

    # ── Backgrounds ────────────────────────────────────────────────
    BG_APP         = "#F8FAFC"   # slate-50  – fond fenêtre
    BG_PAGE        = "#F1F5F9"   # slate-100 – zone contenu secondaire
    BG_CARD        = "#FFFFFF"   # blanc pur – cards
    BG_CARD_ALT    = "#F8FAFC"   # slate-50  – card alt / input
    BG_HOVER       = "#F1F5F9"   # slate-100 – survol léger
    BG_SELECTED    = "#EFF6FF"   # blue-50   – card sélectionnée
    BG_INPUT       = "#FFFFFF"
    BG_INPUT_FOCUS = "#FAFEFF"   # fond légèrement teinté cyan au focus
    BG_HEADER      = "#FFFFFF"   # header blanc propre

    # ── Borders ────────────────────────────────────────────────────
    BORDER         = "#E2E8F0"   # slate-200
    BORDER_FOCUS   = "#06B6D4"   # cyan-500
    BORDER_HOVER   = "#CBD5E1"   # slate-300
    BORDER_SELECT  = "#0891B2"   # cyan-600

    # ── Cyan / Blue primary ────────────────────────────────────────
    CYAN_50        = "#ECFEFF"
    CYAN_100       = "#CFFAFE"
    CYAN_200       = "#A5F3FC"
    CYAN_400       = "#22D3EE"
    CYAN_500       = "#06B6D4"
    CYAN_600       = "#0891B2"
    CYAN_700       = "#0E7490"
    BLUE_50        = "#EFF6FF"
    BLUE_100       = "#DBEAFE"
    BLUE_500       = "#3B82F6"
    BLUE_600       = "#2563EB"
    BLUE_700       = "#1D4ED8"

    # ── Amber / Orange accent ──────────────────────────────────────
    AMBER_50       = "#FFFBEB"
    AMBER_100      = "#FEF3C7"
    AMBER_400      = "#FBBF24"
    AMBER_500      = "#F59E0B"
    ORANGE_500     = "#F97316"
    ORANGE_600     = "#EA580C"

    # ── Status ────────────────────────────────────────────────────
    GREEN_50       = "#F0FDF4"
    GREEN_100      = "#DCFCE7"
    GREEN_500      = "#22C55E"
    GREEN_600      = "#16A34A"
    GREEN_700      = "#15803D"
    RED_50         = "#FEF2F2"
    RED_100        = "#FEE2E2"
    RED_500        = "#EF4444"
    RED_600        = "#DC2626"
    RED_700        = "#B91C1C"

    # ── Text hierarchy ─────────────────────────────────────────────
    TEXT_900       = "#0F172A"   # slate-900 – titres principaux
    TEXT_800       = "#1E293B"   # slate-800 – corps principal
    TEXT_600       = "#475569"   # slate-600 – secondaire
    TEXT_400       = "#94A3B8"   # slate-400 – placeholder / muted
    TEXT_300       = "#CBD5E1"   # slate-300 – très atténué
    TEXT_WHITE     = "#FFFFFF"

    # ── Typography ─────────────────────────────────────────────────
    FONT           = "'Segoe UI', 'SF Pro Text', 'Helvetica Neue', sans-serif"
    FONT_MONO      = "'Cascadia Code', 'Fira Code', 'Consolas', monospace"

    FS_XS   = 10
    FS_SM   = 11
    FS_BASE = 13
    FS_MD   = 15
    FS_LG   = 18
    FS_XL   = 22
    FS_2XL  = 28
    FS_3XL  = 34

    # ── Spacing ────────────────────────────────────────────────────
    SP_1  = 4
    SP_2  = 8
    SP_3  = 12
    SP_4  = 16
    SP_5  = 20
    SP_6  = 24
    SP_8  = 32
    SP_10 = 40
    SP_12 = 48

    # ── Radius ────────────────────────────────────────────────────
    R_SM   = 8
    R_MD   = 12
    R_LG   = 16
    R_XL   = 20
    R_2XL  = 24
    R_FULL = 9999


# ── Backward-compat alias ─────────────────────────────────────────────────────
class StarkTheme:
    """Alias public — remplace l'ancienne classe sombre."""

    # Surfaces
    BG_VOID        = T.BG_APP
    BG_DEEP        = T.BG_PAGE
    BG_SURFACE     = T.BG_CARD
    BG_ELEVATED    = T.BG_HOVER
    BG_BORDER      = T.BORDER

    # Primary
    BLUE_ELECTRIC  = T.CYAN_500
    BLUE_BRIGHT    = T.CYAN_400
    BLUE_SOFT      = T.CYAN_600
    BLUE_DIM       = T.CYAN_100
    BLUE_GLOW      = "rgba(6,182,212,0.15)"
    BLUE_600       = T.BLUE_600
    BLUE_700       = T.BLUE_700
    CYAN_50        = T.CYAN_50
    CYAN_100       = T.CYAN_100
    BLUE_50        = T.BLUE_50
    BLUE_100       = T.BLUE_100

    # Accent
    AMBER          = T.AMBER_500
    AMBER_BRIGHT   = T.AMBER_400
    AMBER_SOFT     = T.AMBER_100
    AMBER_DIM      = T.AMBER_50
    AMBER_GLOW     = "rgba(245,158,11,0.12)"
    ORANGE_500     = T.ORANGE_500
    ORANGE_600     = T.ORANGE_600
    ORANGE_400     = "#FB923C"

    # Status
    SUCCESS        = T.GREEN_500
    SUCCESS_GLOW   = T.GREEN_50
    WARNING        = T.AMBER_500
    ERROR          = T.RED_500
    ERROR_GLOW     = T.RED_50
    GREEN_50       = T.GREEN_50
    GREEN_500      = T.GREEN_500
    GREEN_600      = T.GREEN_600
    GREEN_700      = T.GREEN_700
    RED_50         = T.RED_50
    RED_500        = T.RED_500
    RED_600        = T.RED_600
    RED_700        = T.RED_700

    # Text
    TEXT_PRIMARY   = T.TEXT_800
    TEXT_SECONDARY = T.TEXT_600
    TEXT_MUTED     = T.TEXT_400
    TEXT_INVERSE   = T.TEXT_WHITE
    WHITE          = T.TEXT_WHITE

    # Glass (solide sous Qt, pas de backdrop-filter)
    GLASS_BG       = T.BG_CARD
    GLASS_BORDER   = T.BORDER
    GLASS_HOVER    = T.BG_HOVER
    GLASS_STRONG   = T.BG_CARD
    OVERLAY_DARK   = T.BG_CARD
    BORDER_CYAN    = T.BORDER_FOCUS
    BORDER_WHITE   = T.BORDER
    BORDER_LIGHT   = T.BORDER

    # Fonts
    FONT_DISPLAY   = T.FONT
    FONT_BODY      = T.FONT
    FONT_MONO      = T.FONT_MONO
    FONT_FAMILY_PRIMARY = T.FONT
    FONT_FAMILY_MONO    = T.FONT_MONO

    # Font sizes (px strings)
    FS_XS   = f"{T.FS_XS}px"
    FS_SM   = f"{T.FS_SM}px"
    FS_BASE = f"{T.FS_BASE}px"
    FS_MD   = f"{T.FS_MD}px"
    FS_LG   = f"{T.FS_LG}px"
    FS_XL   = f"{T.FS_XL}px"
    FS_2XL  = f"{T.FS_2XL}px"
    FS_3XL  = f"{T.FS_3XL}px"

    # Spacing (px strings)
    SP_XS = f"{T.SP_1}px"; SP_XS_INT = T.SP_1
    SP_SM = f"{T.SP_2}px"; SP_SM_INT = T.SP_2
    SP_MD = f"{T.SP_4}px"; SP_MD_INT = T.SP_4
    SP_LG = f"{T.SP_5}px"; SP_LG_INT = T.SP_5
    SP_XL = f"{T.SP_6}px"; SP_XL_INT = T.SP_6
    SP_2XL = f"{T.SP_8}px"; SP_2XL_INT = T.SP_8

    SPACING_MD  = f"{T.SP_4}px"; SPACING_MD_INT  = T.SP_4
    SPACING_LG  = f"{T.SP_5}px"; SPACING_LG_INT  = T.SP_5
    SPACING_XL  = f"{T.SP_6}px"; SPACING_XL_INT  = T.SP_6
    SPACING_SM_INT = T.SP_2
    SPACING_XS_INT = T.SP_1

    # Radius
    R_SM   = f"{T.R_SM}px"
    R_MD   = f"{T.R_MD}px"
    R_LG   = f"{T.R_LG}px"
    R_XL   = f"{T.R_XL}px"
    R_2XL  = f"{T.R_2XL}px"
    R_FULL = f"{T.R_FULL}px"
    RADIUS_MEDIUM = f"{T.R_MD}px"
    RADIUS_LARGE  = f"{T.R_LG}px"
    RADIUS_SMALL  = f"{T.R_SM}px"

    # Gradients (Qt linear)
    GRADIENT_PRIMARY = (
        f"qlineargradient(x1:0,y1:0,x2:1,y2:0,"
        f"stop:0 {T.CYAN_500},stop:1 {T.BLUE_600})"
    )
    GRADIENT_HEADER = f"#FFFFFF"
    GRADIENT_ACCENT = (
        f"qlineargradient(x1:0,y1:0,x2:1,y2:0,"
        f"stop:0 {T.AMBER_500},stop:1 {T.ORANGE_500})"
    )
    GRADIENT_BACKGROUND = (
        f"qlineargradient(x1:0,y1:0,x2:1,y2:1,"
        f"stop:0 {T.BG_APP},stop:0.6 {T.BG_CARD},stop:1 {T.CYAN_50})"
    )
    GRADIENT_CARD = T.BG_CARD

    # Legacy aliases
    ORANGE_ACCENT    = T.AMBER_500
    ORANGE_LIGHT     = T.AMBER_400
    BLUE_PRIMARY     = T.CYAN_500
    BLUE_DARK        = T.BLUE_700
    BLUE_LIGHT       = T.CYAN_400
    BLUE_EXTRA_LIGHT = T.CYAN_100
    GRAY_DARK        = T.TEXT_800
    GRAY_MEDIUM      = T.TEXT_600
    GRAY_LIGHT       = T.BORDER
    GRAY_EXTRA_LIGHT = T.BG_HOVER

    # ─────────────────────────────────────────────────────────────────────────
    #  GLOBAL STYLESHEET
    # ─────────────────────────────────────────────────────────────────────────
    @classmethod
    def global_stylesheet(cls) -> str:
        return f"""
/* ═══════════════════════════════════════════════════════════════
   BASE — fenêtre et widgets génériques
═══════════════════════════════════════════════════════════════ */
QMainWindow, QDialog {{
    background: {T.BG_APP};
}}
QWidget {{
    background: transparent;
    color: {T.TEXT_800};
    font-family: {T.FONT};
    font-size: {T.FS_BASE}px;
    selection-background-color: {T.CYAN_100};
    selection-color: {T.TEXT_800};
}}

/* ═══════════════════════════════════════════════════════════════
   SCROLLBARS  (fines, discrètes)
═══════════════════════════════════════════════════════════════ */
QScrollBar:vertical {{
    background: {T.BG_PAGE};
    width: 6px; border-radius: 3px; margin: 2px;
}}
QScrollBar::handle:vertical {{
    background: {T.BORDER_HOVER};
    border-radius: 3px; min-height: 32px;
}}
QScrollBar::handle:vertical:hover {{ background: {T.CYAN_500}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{
    background: {T.BG_PAGE};
    height: 6px; border-radius: 3px; margin: 2px;
}}
QScrollBar::handle:horizontal {{
    background: {T.BORDER_HOVER};
    border-radius: 3px; min-width: 32px;
}}
QScrollBar::handle:horizontal:hover {{ background: {T.CYAN_500}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

/* ═══════════════════════════════════════════════════════════════
   TOOLTIP
═══════════════════════════════════════════════════════════════ */
QToolTip {{
    background: {T.TEXT_900};
    color: {T.TEXT_WHITE};
    border: none;
    border-radius: {T.R_SM}px;
    padding: 6px 10px;
    font-size: {T.FS_SM}px;
}}

/* ═══════════════════════════════════════════════════════════════
   MESSAGEBOX
═══════════════════════════════════════════════════════════════ */
QMessageBox {{
    background: {T.BG_CARD};
}}
QMessageBox QLabel {{
    color: {T.TEXT_800};
    font-size: {T.FS_MD}px;
    background: transparent;
}}
QMessageBox QPushButton {{
    background: {cls.GRADIENT_PRIMARY};
    color: {T.TEXT_WHITE};
    border: none;
    border-radius: {T.R_MD}px;
    padding: 8px 20px;
    font-weight: 600;
    min-width: 80px;
}}
QMessageBox QPushButton:hover {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 {T.CYAN_400},stop:1 {T.BLUE_500});
}}

/* ═══════════════════════════════════════════════════════════════
   STATUS BAR
═══════════════════════════════════════════════════════════════ */
QStatusBar {{
    background: {T.BG_CARD};
    color: {T.TEXT_600};
    font-size: {T.FS_SM}px;
    font-weight: 500;
    border-top: 1px solid {T.BORDER};
    padding: 0 16px;
    min-height: 28px;
}}
QStatusBar::item {{ border: none; }}
"""

    # ─────────────────────────────────────────────────────────────────────────
    #  COMPOSANTS
    # ─────────────────────────────────────────────────────────────────────────

    @classmethod
    def card_style(cls, *, selected: bool = False, radius: int = T.R_LG) -> str:
        border = f"2px solid {T.BORDER_SELECT}" if selected else f"1px solid {T.BORDER}"
        bg     = T.BG_SELECTED if selected else T.BG_CARD
        return f"""
            QFrame {{
                background: {bg};
                border: {border};
                border-radius: {radius}px;
            }}
        """

    @classmethod
    def input_style(cls) -> str:
        return f"""
        QLineEdit {{
            background: {T.BG_INPUT};
            border: 1px solid {T.BORDER};
            border-radius: {T.R_MD}px;
            padding: 11px 14px;
            font-size: {T.FS_MD}px;
            font-family: {T.FONT_MONO};
            color: {T.TEXT_800};
        }}
        QLineEdit:hover {{
            border: 1px solid {T.BORDER_HOVER};
        }}
        QLineEdit:focus {{
            border: 2px solid {T.BORDER_FOCUS};
            background: {T.BG_INPUT_FOCUS};
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
            background: {T.BG_PAGE};
            height: 8px;
            text-align: center;
            color: transparent;
        }}
        QProgressBar::chunk {{
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 {T.CYAN_500},stop:1 {T.BLUE_600});
            border-radius: 5px;
        }}
        """

    @classmethod
    def get_button_style(cls, variant: str = "primary") -> str:
        variants = {
            # ── Cyan→Blue (action principale) ──────────────────────
            "primary": f"""
                QPushButton {{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 {T.CYAN_500},stop:1 {T.BLUE_600});
                    color: {T.TEXT_WHITE};
                    border: none;
                    border-radius: {T.R_MD}px;
                    padding: 12px 28px;
                    font-size: {T.FS_MD}px;
                    font-weight: 700;
                    letter-spacing: 0.3px;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 {T.CYAN_400},stop:1 {T.BLUE_500});
                }}
                QPushButton:pressed {{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 {T.CYAN_600},stop:1 {T.BLUE_700});
                    padding-top: 13px; padding-bottom: 11px;
                }}
                QPushButton:disabled {{
                    background: {T.BG_PAGE};
                    color: {T.TEXT_400};
                    border: 1px solid {T.BORDER};
                }}
            """,
            # ── Amber→Orange (accent / start) ───────────────────────
            "accent": f"""
                QPushButton {{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 {T.AMBER_500},stop:1 {T.ORANGE_500});
                    color: {T.TEXT_WHITE};
                    border: none;
                    border-radius: {T.R_MD}px;
                    padding: 12px 28px;
                    font-size: {T.FS_MD}px;
                    font-weight: 700;
                    letter-spacing: 0.3px;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 {T.AMBER_400},stop:1 #FB923C);
                }}
                QPushButton:pressed {{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 #D97706,stop:1 {T.ORANGE_600});
                    padding-top: 13px; padding-bottom: 11px;
                }}
                QPushButton:disabled {{
                    background: {T.BG_PAGE};
                    color: {T.TEXT_400};
                    border: 1px solid {T.BORDER};
                }}
            """,
            # ── Outline (secondaire / retour) ────────────────────────
            "ghost": f"""
                QPushButton {{
                    background: {T.BG_CARD};
                    color: {T.TEXT_600};
                    border: 1px solid {T.BORDER};
                    border-radius: {T.R_MD}px;
                    padding: 10px 22px;
                    font-size: {T.FS_BASE}px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background: {T.BG_HOVER};
                    border: 1px solid {T.BORDER_HOVER};
                    color: {T.TEXT_800};
                }}
                QPushButton:pressed {{
                    background: {T.CYAN_50};
                    border: 1px solid {T.CYAN_200};
                    color: {T.CYAN_700};
                }}
            """,
            # ── Danger / Terminer ────────────────────────────────────
            "danger": f"""
                QPushButton {{
                    background: {T.RED_50};
                    color: {T.RED_600};
                    border: 1px solid #FECACA;
                    border-radius: {T.R_MD}px;
                    padding: 10px 22px;
                    font-size: {T.FS_BASE}px;
                    font-weight: 600;
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
            # ── Record (identique primary + état stop) ───────────────
            "record": f"""
                QPushButton {{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 {T.CYAN_500},stop:1 {T.BLUE_600});
                    color: {T.TEXT_WHITE};
                    border: none;
                    border-radius: {T.R_MD}px;
                    padding: 13px 28px;
                    font-size: {T.FS_MD}px;
                    font-weight: 700;
                    letter-spacing: 0.5px;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 {T.CYAN_400},stop:1 {T.BLUE_500});
                }}
                QPushButton:pressed {{
                    padding-top: 14px; padding-bottom: 12px;
                }}
                QPushButton:disabled {{
                    background: {T.BG_PAGE};
                    color: {T.TEXT_400};
                    border: 1px solid {T.BORDER};
                }}
            """,
        }
        return variants.get(variant, variants["primary"])

    # ─── Helpers pour widgets personnalisés ───────────────────────────────────

    @classmethod
    def badge_style(cls, color: str = T.CYAN_500, bg: str = T.CYAN_50) -> str:
        """Petit badge pill (ex: statut, langue)."""
        return f"""
            QLabel {{
                background: {bg};
                color: {color};
                border: 1px solid {color}40;
                border-radius: {T.R_FULL}px;
                padding: 4px 12px;
                font-size: {T.FS_SM}px;
                font-weight: 700;
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