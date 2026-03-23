"""
SparkHire AI ·  Apex Modern
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Glassmorphism premium sur fond mesh pastel.
• Fond   : mesh dégradé radial cyan+teal+coral #EFF9FA
• Cartes : blanc semi-transparent 82%, backdrop-blur
• Accents: cyan #00C8E0 → teal #00A99D | coral #FF6B6B → orange #FF8C42
• Typo   : Inter 900, letter-spacing négatif sur titres
• Radius : 13/16/20/26/30 px — généreux mais pas excessif
• Ombres : colorées teintées, double couche (couleur + neutre)
• Boutons: inset highlight (rgba blanc) pour effet 3D subtil
"""


class T:
    # ── Backgrounds ───────────────────────────────────────────────────────────
    BG_APP          = "#EFF9FA"
    BG_PAGE         = "#EAF7F8"
    BG_CARD         = "#FFFFFF"          # cartes blanches pures
    BG_CARD_GLASS   = "rgba(255,255,255,0.82)"   # glass card
    BG_CARD_ALT     = "#F6FCFD"
    BG_CARD_RAISED  = "#FFFFFF"
    BG_HOVER        = "rgba(0,200,224,0.05)"
    BG_SELECTED     = "rgba(0,200,224,0.09)"
    BG_INPUT        = "rgba(255,255,255,0.80)"
    BG_INPUT_FOCUS  = "#FFFFFF"
    BG_HEADER       = "rgba(255,255,255,0.75)"

    BG_GRADIENT     = (
        "qlineargradient(x1:0,y1:0,x2:1,y2:1,"
        "stop:0 #E6F7FA,stop:0.35 #F4FFFE,"
        "stop:0.65 #EDF9FB,stop:1 #EAF5F2)"
    )

    # ── Borders ───────────────────────────────────────────────────────────────
    BORDER          = "rgba(0,200,224,0.10)"
    BORDER_MID      = "rgba(0,200,224,0.18)"
    BORDER_STRONG   = "rgba(0,200,224,0.35)"
    BORDER_GLASS    = "rgba(255,255,255,0.90)"
    BORDER_FOCUS    = "#00C8E0"
    BORDER_HOVER    = "#1AC8E2"
    BORDER_SELECT   = "#00A99D"

    # ── Cyan ──────────────────────────────────────────────────────────────────
    CYAN_50         = "rgba(0,200,224,0.06)"
    CYAN_100        = "rgba(0,200,224,0.12)"
    CYAN_200        = "rgba(0,200,224,0.22)"
    CYAN_300        = "#7DE8F4"
    CYAN_400        = "#1AC8E2"
    CYAN_500        = "#00C8E0"
    CYAN_600        = "#00A8BE"
    CYAN_700        = "#007A94"

    # ── Teal ──────────────────────────────────────────────────────────────────
    TEAL_400        = "#1ABFB3"
    TEAL_500        = "#00A99D"
    TEAL_600        = "#008A80"
    TEAL_700        = "#006B63"
    TEAL_50         = "rgba(0,169,157,0.06)"
    TEAL_100        = "rgba(0,169,157,0.12)"

    # ── Coral / Orange ────────────────────────────────────────────────────────
    CORAL_50        = "rgba(255,107,107,0.06)"
    CORAL_100       = "rgba(255,107,107,0.14)"
    CORAL_400       = "#FF8E8E"
    CORAL_500       = "#FF6B6B"
    CORAL_600       = "#E85555"
    ORANGE_500      = "#FF8C42"
    ORANGE_600      = "#E5742A"

    # ── Amber ─────────────────────────────────────────────────────────────────
    AMBER_50        = "rgba(255,190,11,0.07)"
    AMBER_100       = "rgba(255,190,11,0.18)"
    AMBER_400       = "#FFCE3D"
    AMBER_500       = "#FFBE0B"
    AMBER_600       = "#CC9500"

    # ── Blue (compat) ─────────────────────────────────────────────────────────
    BLUE_50         = CYAN_50
    BLUE_100        = CYAN_100
    BLUE_500        = "#3B82F6"
    BLUE_600        = "#2563EB"
    BLUE_700        = "#1D4ED8"

    # ── Status ────────────────────────────────────────────────────────────────
    GREEN_50        = "rgba(16,208,120,0.07)"
    GREEN_100       = "rgba(16,208,120,0.15)"
    GREEN_500       = "#10D078"
    GREEN_600       = "#00B864"
    GREEN_700       = "#008A4A"
    RED_50          = "rgba(255,77,106,0.06)"
    RED_100         = "rgba(255,77,106,0.14)"
    RED_500         = "#FF4D6A"
    RED_600         = "#E53352"
    RED_700         = "#C01A3A"

    # ── Text ──────────────────────────────────────────────────────────────────
    TEXT_900        = "#071E22"
    TEXT_800        = "#0A3038"
    TEXT_700        = "#144850"
    TEXT_600        = "#2A6E7A"
    TEXT_400        = "#5A9CA8"
    TEXT_300        = "#A0C8D2"
    TEXT_WHITE      = "#FFFFFF"

    # ── Typography ────────────────────────────────────────────────────────────
    FONT            = "'Inter','Segoe UI Variable','Segoe UI',system-ui,sans-serif"
    FONT_MONO       = "'Cascadia Code','Fira Code','Consolas',monospace"

    FS_XS=10; FS_SM=11; FS_BASE=13; FS_MD=15; FS_LG=18; FS_XL=22; FS_2XL=28; FS_3XL=36

    SP_1=4; SP_2=8; SP_3=12; SP_4=16; SP_5=20; SP_6=24; SP_8=32; SP_10=40; SP_12=48

    R_SM=10; R_MD=14; R_LG=20; R_XL=26; R_2XL=32; R_FULL=9999


class StarkTheme:
    """Alias rétrocompatible."""
    BG_VOID=T.BG_APP; BG_DEEP=T.BG_PAGE; BG_SURFACE=T.BG_CARD; BG_ELEVATED=T.BG_HOVER; BG_BORDER=T.BORDER
    BLUE_ELECTRIC=T.CYAN_500; BLUE_BRIGHT=T.CYAN_400; BLUE_SOFT=T.CYAN_600; BLUE_DIM=T.CYAN_100
    BLUE_GLOW="rgba(0,200,224,0.15)"; BLUE_600=T.BLUE_600; BLUE_700=T.BLUE_700
    CYAN_50=T.CYAN_50; CYAN_100=T.CYAN_100; BLUE_50=T.CYAN_50; BLUE_100=T.CYAN_100
    BLUE_PRIMARY=T.CYAN_500; BLUE_LIGHT=T.CYAN_400
    AMBER=T.AMBER_500; AMBER_BRIGHT=T.AMBER_400; AMBER_SOFT=T.AMBER_100; AMBER_DIM=T.AMBER_50
    AMBER_GLOW="rgba(255,190,11,0.12)"; ORANGE_500=T.ORANGE_500; ORANGE_600=T.ORANGE_600
    ORANGE_400="#FF9D5C"; ORANGE_ACCENT=T.ORANGE_500
    SUCCESS=T.GREEN_500; SUCCESS_GLOW=T.GREEN_50; WARNING=T.AMBER_500; ERROR=T.RED_500; ERROR_GLOW=T.RED_50
    GREEN_50=T.GREEN_50; GREEN_100=T.GREEN_100; GREEN_500=T.GREEN_500; GREEN_600=T.GREEN_600; GREEN_700=T.GREEN_700
    RED_50=T.RED_50; RED_100=T.RED_100; RED_500=T.RED_500; RED_600=T.RED_600; RED_700=T.RED_700
    TEXT_PRIMARY=T.TEXT_700; TEXT_SECONDARY=T.TEXT_600; TEXT_MUTED=T.TEXT_400
    TEXT_INVERSE=T.TEXT_WHITE; WHITE=T.TEXT_WHITE; GRAY_MEDIUM=T.TEXT_600
    GLASS_BG=T.BG_CARD; GLASS_BORDER=T.BORDER; GLASS_HOVER=T.BG_HOVER; GLASS_STRONG=T.BG_CARD
    OVERLAY_DARK="rgba(0,0,0,0.15)"; BORDER_CYAN=T.BORDER_FOCUS; BORDER_WHITE="#FFFFFF"; BORDER_LIGHT=T.BORDER
    FONT_DISPLAY=T.FONT; FONT_BODY=T.FONT; FONT_MONO=T.FONT_MONO
    FONT_FAMILY_PRIMARY=T.FONT; FONT_FAMILY_MONO=T.FONT_MONO

    FS_XS=f"{T.FS_XS}px"; FS_SM=f"{T.FS_SM}px"; FS_BASE=f"{T.FS_BASE}px"; FS_MD=f"{T.FS_MD}px"
    FS_LG=f"{T.FS_LG}px"; FS_XL=f"{T.FS_XL}px"; FS_2XL=f"{T.FS_2XL}px"; FS_3XL=f"{T.FS_3XL}px"
    SP_XS=f"{T.SP_1}px"; SP_XS_INT=T.SP_1; SP_SM=f"{T.SP_2}px"; SP_SM_INT=T.SP_2
    SP_MD=f"{T.SP_4}px"; SP_MD_INT=T.SP_4; SP_LG=f"{T.SP_5}px"; SP_LG_INT=T.SP_5
    SP_XL=f"{T.SP_6}px"; SP_XL_INT=T.SP_6; SP_2XL=f"{T.SP_8}px"; SP_2XL_INT=T.SP_8
    SPACING_MD=f"{T.SP_4}px"; SPACING_MD_INT=T.SP_4; SPACING_LG=f"{T.SP_5}px"
    SPACING_LG_INT=T.SP_5; SPACING_XL=f"{T.SP_6}px"; SPACING_XL_INT=T.SP_6
    SPACING_SM_INT=T.SP_2; SPACING_XS_INT=T.SP_1
    R_SM=f"{T.R_SM}px"; R_MD=f"{T.R_MD}px"; R_LG=f"{T.R_LG}px"
    R_XL=f"{T.R_XL}px"; R_2XL=f"{T.R_2XL}px"; R_FULL=f"{T.R_FULL}px"
    RADIUS_MEDIUM=f"{T.R_MD}px"; RADIUS_LARGE=f"{T.R_LG}px"; RADIUS_SMALL=f"{T.R_SM}px"
    GRADIENT_PRIMARY=f"qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {T.CYAN_500},stop:1 {T.TEAL_500})"
    GRADIENT_HEADER=T.BG_HEADER
    GRADIENT_ACCENT=f"qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {T.CORAL_500},stop:1 {T.ORANGE_500})"
    GRADIENT_BACKGROUND=T.BG_GRADIENT

    @classmethod
    def global_stylesheet(cls) -> str:
        return f"""
        QMainWindow, QWidget {{
            background: transparent;
            color: {T.TEXT_700};
            font-family: {T.FONT};
            font-size: {T.FS_BASE}px;
        }}
        QScrollArea {{ background: transparent; border: none; }}
        QScrollBar:vertical {{
            background: transparent; width: 4px; border-radius: 2px; border: none;
        }}
        QScrollBar::handle:vertical {{
            background: {T.CYAN_300}; border-radius: 2px; min-height: 20px;
        }}
        QScrollBar::handle:vertical:hover {{ background: {T.CYAN_500}; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        QToolTip {{
            background: {T.BG_CARD}; color: {T.TEXT_700};
            border: 1px solid {T.BORDER_MID}; border-radius: {T.R_SM}px;
            padding: 6px 10px; font-size: {T.FS_SM}px;
        }}
        QStatusBar {{
            background: rgba(255,255,255,0.65); color: {T.TEXT_300};
            border-top: 1px solid {T.BORDER}; font-size: {T.FS_SM}px; padding: 0 12px;
        }}
        """

    @classmethod
    def card_style(cls, selected=False, radius=None) -> str:
        r = radius if radius else T.R_LG
        if selected:
            return f"""QFrame {{
                background: {T.BG_SELECTED};
                border: 1.5px solid {T.CYAN_500};
                border-radius: {r}px;
            }}"""
        return f"""QFrame {{
            background: {T.BG_CARD};
            border: 1px solid {T.BORDER_GLASS};
            border-radius: {r}px;
        }}"""

    @classmethod
    def input_style(cls) -> str:
        return f"""
        QLineEdit {{
            background: {T.BG_INPUT};
            border: 1.5px solid {T.BORDER_MID};
            border-radius: {T.R_MD}px;
            padding: 14px 20px;
            font-size: {T.FS_MD}px;
            font-family: {T.FONT_MONO};
            color: {T.TEXT_800};
        }}
        QLineEdit:hover {{ border: 1.5px solid {T.BORDER_STRONG}; }}
        QLineEdit:focus {{
            border: 2px solid {T.CYAN_500};
            background: {T.BG_INPUT_FOCUS};
        }}
        QLineEdit::placeholder {{ color: {T.TEXT_300}; }}
        """

    @classmethod
    def progress_style(cls) -> str:
        return f"""
        QProgressBar {{
            border: none; border-radius: 5px;
            background: {T.CYAN_50}; height: 8px; color: transparent;
        }}
        QProgressBar::chunk {{
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 {T.CYAN_500},stop:1 {T.TEAL_400});
            border-radius: 5px;
        }}
        """

    @classmethod
    def get_button_style(cls, variant: str = "primary") -> str:
        V = {
            "primary": f"""
                QPushButton {{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {T.CYAN_500},stop:1 {T.TEAL_500});
                    color: #fff; border: none; border-radius: {T.R_MD}px;
                    padding: 14px 36px; font-size: {T.FS_MD}px; font-weight: 700; letter-spacing: 0.2px;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {T.CYAN_400},stop:1 {T.TEAL_400});
                }}
                QPushButton:pressed {{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {T.CYAN_600},stop:1 {T.TEAL_600});
                    padding-top: 15px; padding-bottom: 13px;
                }}
                QPushButton:disabled {{
                    background: {T.CYAN_100}; color: {T.CYAN_300}; border: none;
                }}
            """,
            "accent": f"""
                QPushButton {{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {T.CORAL_500},stop:1 {T.ORANGE_500});
                    color: #fff; border: none; border-radius: {T.R_MD}px;
                    padding: 14px 36px; font-size: {T.FS_MD}px; font-weight: 700;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {T.CORAL_400},stop:1 {T.ORANGE_500});
                }}
                QPushButton:pressed {{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {T.CORAL_600},stop:1 {T.ORANGE_600});
                    padding-top: 15px; padding-bottom: 13px;
                }}
                QPushButton:disabled {{
                    background: {T.CORAL_100}; color: {T.CORAL_400}; border: none;
                }}
            """,
            "ghost": f"""
                QPushButton {{
                    background: transparent; color: {T.TEXT_400};
                    border: 1px solid {T.BORDER_MID}; border-radius: {T.R_MD}px;
                    padding: 12px 28px; font-size: {T.FS_BASE}px; font-weight: 600;
                }}
                QPushButton:hover {{
                    background: {T.BG_HOVER}; border-color: {T.BORDER_STRONG}; color: {T.CYAN_500};
                }}
                QPushButton:pressed {{
                    background: {T.BG_SELECTED}; border-color: {T.CYAN_500};
                }}
            """,
            "danger": f"""
                QPushButton {{
                    background: transparent; color: {T.RED_500};
                    border: 1px solid {T.RED_100}; border-radius: {T.R_MD}px;
                    padding: 12px 28px; font-size: {T.FS_BASE}px; font-weight: 600;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {T.RED_500},stop:1 {T.RED_600});
                    color: #fff; border: none;
                }}
                QPushButton:pressed {{ background: {T.RED_700}; color: #fff; border: none; }}
            """,
            "record": f"""
                QPushButton {{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {T.CYAN_500},stop:1 {T.TEAL_500});
                    color: #fff; border: none; border-radius: {T.R_MD}px;
                    padding: 14px 36px; font-size: {T.FS_MD}px; font-weight: 700; letter-spacing: 0.3px;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {T.CYAN_400},stop:1 {T.TEAL_400});
                }}
                QPushButton:pressed {{ padding-top: 15px; padding-bottom: 13px; }}
                QPushButton:disabled {{
                    background: {T.CYAN_100}; color: {T.CYAN_300}; border: none;
                }}
            """,
        }
        return V.get(variant, V["primary"])

    @classmethod
    def badge_style(cls, color=None, bg=None) -> str:
        c = color or T.CYAN_600; bg = bg or T.CYAN_50
        return f"""QLabel {{
            background: {bg}; color: {c}; border: 1px solid {T.BORDER_MID};
            border-radius: {T.R_FULL}px; padding: 4px 14px;
            font-size: {T.FS_SM}px; font-weight: 700;
        }}"""

    @classmethod
    def section_title_style(cls) -> str:
        return f"""QLabel {{
            color: {T.CYAN_400}; font-size: {T.FS_XS}px;
            font-weight: 800; letter-spacing: 3px; background: transparent;
        }}"""

    @classmethod
    def glass_card_style(cls, hover=True) -> str: return cls.card_style()
    @classmethod
    def solid_card_style(cls) -> str: return cls.card_style()
    @classmethod
    def get_card_style(cls) -> str: return cls.card_style()
    @classmethod
    def get_input_style(cls) -> str: return cls.input_style()