class T:
    # ── Backgrounds — couches bien définies ───────────────────────
    BG_APP          = "#F5F4EF"   # crème profond — fond de page
    BG_PAGE         = "#EDECEA"   # crème légèrement plus foncé
    BG_CARD         = "#FFFFFF"   # cartes pures
    BG_CARD_ALT     = "#FDFCFB"   # carte secondaire
    BG_HOVER        = "#F8F7F3"
    BG_SELECTED     = "#E8FAF6"
    BG_INPUT        = "#FDFCFB"
    BG_INPUT_FOCUS  = "#FFFFFF"

    # ── Borders ───────────────────────────────────────────────────
    BORDER          = "#E2DFD8"
    BORDER_FOCUS    = "#14B8A6"
    BORDER_HOVER    = "#CCC9C0"
    BORDER_SELECT   = "#0D9488"
    BORDER_STRONG   = "#C5C2B9"

    # ── Teal — palette enrichie ───────────────────────────────────
    TEAL_50         = "#F0FDFA"
    TEAL_100        = "#C8F6EE"
    TEAL_200        = "#94EAD9"
    TEAL_300        = "#5DD8C4"
    TEAL_400        = "#2CC4AE"
    TEAL_500        = "#12A899"   # primary — légèrement plus profond
    TEAL_600        = "#0C8B7D"
    TEAL_700        = "#0A7269"
    TEAL_800        = "#085C54"
    TEAL_900        = "#064840"

    # ── Coral ─────────────────────────────────────────────────────
    CORAL_50        = "#FFF6F3"
    CORAL_100       = "#FFE5DC"
    CORAL_200       = "#FFC8B5"
    CORAL_400       = "#F5714F"
    CORAL_500       = "#E8522E"
    CORAL_600       = "#CC3E1C"
    CORAL_700       = "#A83214"

    # ── Amber ─────────────────────────────────────────────────────
    AMBER_50        = "#FFFBEB"
    AMBER_100       = "#FEF0C0"
    AMBER_200       = "#FDE080"
    AMBER_400       = "#F9B830"
    AMBER_500       = "#F0A014"
    AMBER_600       = "#D4860A"
    AMBER_700       = "#A86406"

    # ── Status ────────────────────────────────────────────────────
    GREEN_50        = "#EFFDF4"
    GREEN_100       = "#D2F8E0"
    GREEN_200       = "#A8EFC0"
    GREEN_500       = "#1DB954"
    GREEN_600       = "#169444"
    GREEN_700       = "#107534"
    RED_50          = "#FFF0F0"
    RED_100         = "#FFD9D9"
    RED_200         = "#FFADAD"
    RED_400         = "#F56565"
    RED_500         = "#E53E3E"
    RED_600         = "#C53030"
    RED_700         = "#9B2C2C"

    # ── Legacy compat (toutes mappées sur Teal) ───────────────────
    INDIGO_50  = "#F0FDFA"; INDIGO_100 = "#C8F6EE"; INDIGO_200 = "#94EAD9"
    INDIGO_400 = "#2CC4AE"; INDIGO_500 = "#12A899"; INDIGO_600 = "#0C8B7D"
    INDIGO_700 = "#0A7269"; INDIGO_800 = "#085C54"; INDIGO_900 = "#064840"
    VIOLET_50  = "#FFF6F3"; VIOLET_100 = "#FFE5DC"
    VIOLET_400 = "#F5714F"; VIOLET_500 = "#E8522E"; VIOLET_600 = "#CC3E1C"
    CYAN_50    = "#F0FDFA"; CYAN_100   = "#C8F6EE"; CYAN_200   = "#94EAD9"
    CYAN_400   = "#2CC4AE"; CYAN_500   = "#12A899"; CYAN_600   = "#0C8B7D"
    CYAN_700   = "#0A7269"
    BLUE_400   = "#2CC4AE"; BLUE_500   = "#12A899"; BLUE_600   = "#0C8B7D"
    ORANGE_500 = "#F97316"; ORANGE_600 = "#EA580C"

    # ── Texte — hiérarchie forte et chaude ────────────────────────
    TEXT_950   = "#17150F"   # quasi-noir chaud — titres H1
    TEXT_900   = "#231F16"
    TEXT_800   = "#36311F"   # corps principal
    TEXT_700   = "#4D4737"
    TEXT_600   = "#67604E"   # secondaire
    TEXT_500   = "#857D6A"   # muted
    TEXT_400   = "#A89E8C"   # placeholder / disabled
    TEXT_300   = "#CEC6B6"
    TEXT_WHITE = "#FFFFFF"
    TEXT_INDIGO = "#0C8B7D"

    # ── Typographie — Sora pour les titres, Inter pour le corps ───
    FONT         = "'Sora', 'Plus Jakarta Sans', 'Segoe UI', system-ui, sans-serif"
    FONT_BODY    = "'Inter', 'Sora', 'Segoe UI', sans-serif"
    FONT_MONO    = "'JetBrains Mono', 'Fira Code', monospace"
    FONT_DISPLAY = "'Sora', 'Plus Jakarta Sans', sans-serif"

    # ── Tailles — échelle augmentée pour plus d'impact ────────────
    FS_2XS  = 9
    FS_XS   = 10
    FS_SM   = 12
    FS_BASE = 13
    FS_MD   = 15
    FS_LG   = 17
    FS_XL   = 21
    FS_2XL  = 26
    FS_3XL  = 32
    FS_4XL  = 42

    # ── Espacement ────────────────────────────────────────────────
    SP_1  = 4;  SP_2  = 8;  SP_3  = 12; SP_4  = 16
    SP_5  = 20; SP_6  = 24; SP_8  = 32; SP_10 = 40; SP_12 = 48

    # ── Radius — généreux et cohérent ─────────────────────────────
    R_SM   = 8
    R_MD   = 12
    R_LG   = 16
    R_XL   = 20
    R_2XL  = 24
    R_3XL  = 28
    R_FULL = 9999

    BG_SIDEBAR = "#0B3530"


class StarkTheme:
    """Theme v8 — Professional Premium."""

    # ── Gradients ─────────────────────────────────────────────────
    GRADIENT_PRIMARY = (
        f"qlineargradient(x1:0,y1:0,x2:1,y2:0,"
        f"stop:0 {T.TEAL_500},stop:1 {T.TEAL_600})"
    )
    GRADIENT_PRIMARY_HOVER = (
        f"qlineargradient(x1:0,y1:0,x2:1,y2:0,"
        f"stop:0 {T.TEAL_600},stop:1 {T.TEAL_700})"
    )
    GRADIENT_ACCENT = (
        f"qlineargradient(x1:0,y1:0,x2:1,y2:0,"
        f"stop:0 {T.TEAL_500},stop:1 {T.CORAL_500})"
    )
    GRADIENT_HERO = (
        f"qlineargradient(x1:0,y1:0,x2:1,y2:1,"
        f"stop:0 {T.TEAL_700},stop:0.5 {T.TEAL_500},stop:1 {T.CORAL_500})"
    )
    GRADIENT_CYAN      = GRADIENT_PRIMARY
    GRADIENT_BACKGROUND = f"qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 {T.BG_APP},stop:1 #EEF8F6)"
    GRADIENT_CARD      = T.BG_CARD

    # ── Compat aliases ────────────────────────────────────────────
    BG_VOID = T.BG_APP; BG_DEEP = T.BG_PAGE; BG_SURFACE = T.BG_CARD
    BG_ELEVATED = T.BG_HOVER; BG_BORDER = T.BORDER
    BLUE_ELECTRIC = T.TEAL_500; BLUE_BRIGHT = T.TEAL_400
    BLUE_SOFT = T.TEAL_600; BLUE_DIM = T.TEAL_100
    BLUE_GLOW = "rgba(18,168,153,0.14)"; BLUE_600 = T.TEAL_600
    BLUE_700 = T.TEAL_700; BLUE_PRIMARY = T.TEAL_500
    BLUE_DARK = T.TEAL_700; BLUE_LIGHT = T.TEAL_400
    BLUE_EXTRA_LIGHT = T.TEAL_100; BLUE_50 = T.TEAL_50; BLUE_100 = T.TEAL_100
    CYAN_50 = T.CYAN_50; CYAN_100 = T.CYAN_100
    AMBER = T.AMBER_500; AMBER_BRIGHT = T.AMBER_400
    AMBER_SOFT = T.AMBER_100; AMBER_DIM = T.AMBER_50
    AMBER_GLOW = "rgba(240,160,20,0.10)"
    ORANGE_ACCENT = T.CORAL_500; ORANGE_LIGHT = T.CORAL_400
    ORANGE_500 = T.ORANGE_500; ORANGE_600 = T.ORANGE_600; ORANGE_400 = T.CORAL_400
    SUCCESS = T.GREEN_500; SUCCESS_GLOW = T.GREEN_50
    WARNING = T.AMBER_500; ERROR = T.RED_500; ERROR_GLOW = T.RED_50
    GREEN_50 = T.GREEN_50; GREEN_100 = T.GREEN_100
    GREEN_500 = T.GREEN_500; GREEN_600 = T.GREEN_600; GREEN_700 = T.GREEN_700
    RED_50 = T.RED_50; RED_100 = T.RED_100
    RED_500 = T.RED_500; RED_600 = T.RED_600; RED_700 = T.RED_700
    TEXT_PRIMARY = T.TEXT_800; TEXT_SECONDARY = T.TEXT_600
    TEXT_MUTED = T.TEXT_400; TEXT_INVERSE = T.TEXT_WHITE; WHITE = T.TEXT_WHITE
    GLASS_BG = T.BG_CARD; GLASS_BORDER = T.BORDER
    GLASS_HOVER = T.BG_HOVER; GLASS_STRONG = T.BG_CARD
    OVERLAY_DARK = T.BG_CARD; BORDER_CYAN = T.BORDER_FOCUS; BORDER_WHITE = T.BORDER
    SHADOW_XS  = "0 1px 3px rgba(0,0,0,0.04)"
    SHADOW_SM  = "0 2px 10px rgba(0,0,0,0.06)"
    SHADOW_MD  = "0 4px 20px rgba(0,0,0,0.08)"
    SHADOW_LG  = "0 8px 36px rgba(0,0,0,0.10)"
    SHADOW_XL  = "0 16px 52px rgba(0,0,0,0.12)"
    SHADOW_INDIGO = "0 8px 28px rgba(18,168,153,0.22)"

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
            color: {T.TEXT_400};
            font-size: {T.FS_XS}px;
            font-family: {T.FONT_BODY};
            padding: 0 20px;
            letter-spacing: 0.3px;
        }}
        QScrollBar:vertical {{
            background: transparent;
            width: 5px;
            border-radius: 3px;
            margin: 4px 0;
        }}
        QScrollBar::handle:vertical {{
            background: {T.BORDER};
            border-radius: 3px;
            min-height: 28px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {T.BORDER_HOVER};
        }}
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {{ height: 0; }}
        QToolTip {{
            background: {T.TEXT_900};
            color: {T.TEXT_WHITE};
            border: none;
            border-radius: 8px;
            padding: 7px 12px;
            font-size: {T.FS_SM}px;
            letter-spacing: 0.2px;
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
            border-radius: {T.R_LG}px;
            padding: 15px 20px;
            font-size: {T.FS_MD}px;
            font-family: {T.FONT_MONO};
            color: {T.TEXT_800};
            letter-spacing: 0.5px;
        }}
        QLineEdit:hover {{
            border-color: {T.BORDER_HOVER};
            background: {T.BG_CARD};
        }}
        QLineEdit:focus {{
            border: 2px solid {T.TEAL_500};
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
        _base_primary = f"""
                background: {cls.GRADIENT_PRIMARY};
                color: {T.TEXT_WHITE};
                border: none;
                border-radius: {T.R_LG}px;
                font-size: {T.FS_MD}px;
                font-weight: 700;
                letter-spacing: 0.4px;
                font-family: {T.FONT};
        """
        variants = {
            "primary": f"""
                QPushButton {{ {_base_primary} padding: 14px 34px; }}
                QPushButton:hover {{ background: {cls.GRADIENT_PRIMARY_HOVER}; }}
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
                QPushButton {{ {_base_primary} padding: 15px 34px; }}
                QPushButton:hover {{ background: {cls.GRADIENT_PRIMARY_HOVER}; }}
                QPushButton:pressed {{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 {T.TEAL_700},stop:1 {T.TEAL_800});
                    padding-top: 16px; padding-bottom: 14px;
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
                    padding: 10px 24px;
                    font-size: {T.FS_SM}px;
                    font-weight: 600;
                    font-family: {T.FONT};
                    letter-spacing: 0.2px;
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
                    border: none;
                    border-radius: {T.R_MD}px;
                    padding: 10px 24px;
                    font-size: {T.FS_SM}px;
                    font-weight: 600;
                    font-family: {T.FONT};
                }}
                QPushButton:hover {{
                    background: {T.RED_50};
                    color: {T.RED_600};
                }}
                QPushButton:pressed {{
                    background: {T.RED_100};
                    color: {T.RED_700};
                }}
            """,
            "record": f"""
                QPushButton {{ {_base_primary} padding: 15px 34px; }}
                QPushButton:hover {{ background: {cls.GRADIENT_PRIMARY_HOVER}; }}
                QPushButton:pressed {{ padding-top: 16px; padding-bottom: 14px; }}
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
                border: none;
                border-radius: {T.R_FULL}px;
                padding: 3px 11px;
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
