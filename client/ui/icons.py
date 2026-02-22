"""
Icônes SVG Premium - Stark Solutions
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Bibliothèque : Lucide Icons  https://lucide.dev/
Technique     : textPath SVG — texte épousant les contours
Rendu         : PySide6 QSvgRenderer
"""

from PySide6.QtGui  import QIcon, QPixmap, QPainter
from PySide6.QtSvg  import QSvgRenderer
from PySide6.QtCore import QByteArray, QSize, Qt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from .stark_theme import StarkTheme


# ─────────────────────────────────────────────────────────────────────────────
#  MOTEUR DE RENDU
# ─────────────────────────────────────────────────────────────────────────────

class StarkIcons:
    """
    Icônes SVG Lucide + Logos Stark avec texte sur contour (SVG textPath).
    """

    @staticmethod
    def _render(svg: str, size: QSize = QSize(32, 32)) -> QIcon:
        renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
        pix      = QPixmap(size)
        pix.fill(Qt.GlobalColor.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        renderer.render(p)
        p.end()
        return QIcon(pix)

    # ─────────────────────────────────────────────────────────────
    #  LOGOS — texte épousant le contour (textPath)
    # ─────────────────────────────────────────────────────────────

    @classmethod
    def logo_stark(cls, size: QSize = QSize(64, 64)) -> QIcon:
        """
        Badge hexagonal premium.
        • Texte "STARK SOLUTIONS" suit l'arc supérieur de l'hexagone.
        • Lettre « S » centrale en serif italique.
        • Point-étoile accent orange.
        """
        svg = """<svg xmlns="http://www.w3.org/2000/svg"
                      xmlns:xlink="http://www.w3.org/1999/xlink"
                      width="128" height="128" viewBox="0 0 128 128">
          <defs>
            <!-- Dégradés -->
            <linearGradient id="gBg" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%"   stop-color="#00254D"/>
              <stop offset="50%"  stop-color="#003E7E"/>
              <stop offset="100%" stop-color="#0055A8"/>
            </linearGradient>
            <linearGradient id="gAcc" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%"   stop-color="#FF5500"/>
              <stop offset="100%" stop-color="#FF8C61"/>
            </linearGradient>
            <linearGradient id="gS" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%"   stop-color="#FFFFFF"/>
              <stop offset="60%"  stop-color="#CCE5FF"/>
              <stop offset="100%" stop-color="#FF6B35"/>
            </linearGradient>
            <filter id="fGlow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur in="SourceGraphic" stdDeviation="2.5" result="blur"/>
              <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
            </filter>
            <filter id="fShadow" x="-15%" y="-15%" width="130%" height="130%">
              <feDropShadow dx="0" dy="3" stdDeviation="4" flood-color="#001A3A" flood-opacity="0.6"/>
            </filter>

            <!-- Chemin arc supérieur de l'hexagone (pour textPath) -->
            <!-- Hexagone centré en (64,64) rayon 56 — on trace l'arc du haut -->
            <path id="arcTop"
              d="M 20,37  A 52,52 0 0,1 108,37"/>

            <!-- Chemin arc inférieur (pour label bas) -->
            <path id="arcBot"
              d="M 22,93  A 52,52 0 0,0 106,93"/>
          </defs>

          <!-- ── Ombre portée globale ── -->
          <g filter="url(#fShadow)">

            <!-- Hexagone principal -->
            <polygon
              points="64,8 116,37 116,91 64,120 12,91 12,37"
              fill="url(#gBg)"/>

            <!-- Anneau intérieur fin -->
            <polygon
              points="64,15 110,40.5 110,87.5 64,113 18,87.5 18,40.5"
              fill="none" stroke="rgba(255,255,255,0.12)" stroke-width="1.5"/>

            <!-- Bande décorative diagonale -->
            <polygon
              points="64,8 116,37 116,55 64,26"
              fill="rgba(255,255,255,0.04)"/>

            <!-- Lettre S centrale -->
            <text x="64" y="86"
              font-family="Georgia,'Times New Roman',serif"
              font-size="68" font-weight="bold" font-style="italic"
              fill="url(#gS)"
              text-anchor="middle"
              filter="url(#fGlow)">S</text>

            <!-- Point-étoile accent -->
            <circle cx="98" cy="30" r="7" fill="url(#gAcc)"/>
            <circle cx="98" cy="30" r="3.5" fill="white" opacity="0.75"/>

            <!-- Trait horizontal décoratif bas -->
            <line x1="38" y1="105" x2="90" y2="105"
              stroke="rgba(255,107,53,0.55)" stroke-width="1.5" stroke-linecap="round"/>
          </g>

          <!-- ── Texte supérieur suivant l'arc ── -->
          <text font-family="'Segoe UI','Helvetica Neue',sans-serif"
                font-size="10.5" font-weight="700" letter-spacing="2.8"
                fill="rgba(255,255,255,0.85)">
            <textPath xlink:href="#arcTop" startOffset="50%" text-anchor="middle">
              STARK SOLUTIONS
            </textPath>
          </text>

          <!-- ── Texte inférieur suivant l'arc ── -->
          <text font-family="'Segoe UI','Helvetica Neue',sans-serif"
                font-size="8.5" font-weight="400" letter-spacing="3"
                fill="rgba(255,140,97,0.90)">
            <textPath xlink:href="#arcBot" startOffset="50%" text-anchor="middle">
              RECRUITMENT · AI
            </textPath>
          </text>
        </svg>"""
        return cls._render(svg, size)

    # ──────────────────────────────────────────────────────────────────────

    @classmethod
    def logo_stark_compact(cls, size: QSize = QSize(40, 40)) -> QIcon:
        """
        Badge circulaire compact — icône dans barre de titre.
        Texte « STARK AI » sur l'arc supérieur du cercle.
        """
        svg = """<svg xmlns="http://www.w3.org/2000/svg"
                      xmlns:xlink="http://www.w3.org/1999/xlink"
                      width="80" height="80" viewBox="0 0 80 80">
          <defs>
            <linearGradient id="cBg" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%"   stop-color="#00254D"/>
              <stop offset="100%" stop-color="#0066CC"/>
            </linearGradient>
            <linearGradient id="cAcc" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%"   stop-color="#FF5500"/>
              <stop offset="100%" stop-color="#FF8C61"/>
            </linearGradient>
            <filter id="cGlow">
              <feGaussianBlur in="SourceGraphic" stdDeviation="1.5" result="b"/>
              <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
            </filter>
            <!-- Arc supérieur du cercle r=33 centré (40,40) -->
            <path id="cArcTop" d="M 11,40 A 29,29 0 0,1 69,40"/>
            <!-- Arc inférieur -->
            <path id="cArcBot" d="M 13,44 A 29,29 0 0,0 67,44"/>
          </defs>

          <!-- Cercle de fond avec double bord -->
          <circle cx="40" cy="40" r="38" fill="url(#cBg)"/>
          <circle cx="40" cy="40" r="35" fill="none"
            stroke="rgba(255,255,255,0.14)" stroke-width="1.2"/>
          <circle cx="40" cy="40" r="30" fill="none"
            stroke="rgba(255,107,53,0.3)" stroke-width="0.8"/>

          <!-- Lettre S -->
          <text x="40" y="53"
            font-family="Georgia,serif" font-size="40"
            font-weight="bold" font-style="italic"
            fill="white" text-anchor="middle"
            filter="url(#cGlow)">S</text>

          <!-- Texte sur arc supérieur -->
          <text font-family="'Segoe UI',sans-serif"
                font-size="7.5" font-weight="700" letter-spacing="2.5"
                fill="rgba(255,255,255,0.9)">
            <textPath xlink:href="#cArcTop" startOffset="50%" text-anchor="middle">
              STARK  AI
            </textPath>
          </text>

          <!-- Tirets décoratifs bas -->
          <text font-family="'Segoe UI',sans-serif"
                font-size="6" font-weight="400" letter-spacing="3"
                fill="rgba(255,140,97,0.8)">
            <textPath xlink:href="#cArcBot" startOffset="50%" text-anchor="middle">
              ·  ·  ·
            </textPath>
          </text>

          <!-- Point accent -->
          <circle cx="62" cy="20" r="4.5" fill="url(#cAcc)"/>
          <circle cx="62" cy="20" r="2"   fill="white" opacity="0.7"/>
        </svg>"""
        return cls._render(svg, size)

    # ──────────────────────────────────────────────────────────────────────

    @classmethod
    def logo_stark_banner(cls, size: QSize = QSize(260, 72)) -> QIcon:
        """
        Logo bannière horizontal — header principal.
        • Badge hexagonal à gauche.
        • Texte « STARK » en gras + tagline.
        • Ligne accentuée orange sous le titre.
        • Mini texte « RECRUITMENT AI » épousant une légère courbe.
        """
        svg = """<svg xmlns="http://www.w3.org/2000/svg"
                      xmlns:xlink="http://www.w3.org/1999/xlink"
                      width="260" height="72" viewBox="0 0 260 72">
          <defs>
            <linearGradient id="bBg" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%"   stop-color="#00254D"/>
              <stop offset="100%" stop-color="#0066CC"/>
            </linearGradient>
            <linearGradient id="bAcc" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%"   stop-color="#FF5500"/>
              <stop offset="100%" stop-color="#FF8C61"/>
            </linearGradient>
            <linearGradient id="bTitle" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%"   stop-color="#FFFFFF"/>
              <stop offset="100%" stop-color="#CCE5FF"/>
            </linearGradient>
            <filter id="bGlow">
              <feGaussianBlur in="SourceGraphic" stdDeviation="1.8" result="b"/>
              <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
            </filter>

            <!-- Hexagone r=28 centré (36,36) — arc du haut -->
            <path id="bArcTop" d="M 12,28 A 27,27 0 0,1 60,28"/>
            <!-- Arc du bas -->
            <path id="bArcBot" d="M 13,47 A 27,27 0 0,0 59,47"/>

            <!-- Courbe légère pour le tagline texte à droite -->
            <path id="bCurve"
              d="M 80,56 Q 170,50 250,57"/>
          </defs>

          <!-- ══ BADGE HEXAGONAL ══ -->
          <g>
            <polygon points="36,4 62,19 62,49 36,64 10,49 10,19"
              fill="url(#bBg)"/>
            <polygon points="36,9 58,21.5 58,46.5 36,59 14,46.5 14,21.5"
              fill="none" stroke="rgba(255,255,255,0.12)" stroke-width="1"/>

            <!-- S central -->
            <text x="36" y="49"
              font-family="Georgia,'Times New Roman',serif"
              font-size="38" font-weight="bold" font-style="italic"
              fill="white" text-anchor="middle"
              filter="url(#bGlow)">S</text>

            <!-- Point accent -->
            <circle cx="57" cy="16" r="4.5" fill="url(#bAcc)"/>
            <circle cx="57" cy="16" r="2"   fill="white" opacity="0.75"/>

            <!-- Texte sur arc supérieur du badge -->
            <text font-family="'Segoe UI',sans-serif"
                  font-size="6" font-weight="700" letter-spacing="1.8"
                  fill="rgba(255,255,255,0.8)">
              <textPath xlink:href="#bArcTop" startOffset="50%" text-anchor="middle">
                STARK · AI
              </textPath>
            </text>

            <!-- Texte sur arc inférieur du badge -->
            <text font-family="'Segoe UI',sans-serif"
                  font-size="5.5" font-weight="400" letter-spacing="1.5"
                  fill="rgba(255,140,97,0.85)">
              <textPath xlink:href="#bArcBot" startOffset="50%" text-anchor="middle">
                ─ ─ ─
              </textPath>
            </text>
          </g>

          <!-- ══ TITRE STARK ══ -->
          <text x="77" y="37"
            font-family="'Segoe UI','Helvetica Neue',sans-serif"
            font-size="30" font-weight="900"
            fill="url(#bTitle)"
            letter-spacing="5">STARK</text>

          <!-- Ligne accent orange sous STARK -->
          <rect x="78" y="42" width="108" height="2.5" rx="1.25"
            fill="url(#bAcc)"/>

          <!-- ══ TAGLINE sur courbe légère ══ -->
          <text font-family="'Segoe UI',sans-serif"
                font-size="8.5" font-weight="500" letter-spacing="3.5"
                fill="rgba(255,255,255,0.55)">
            <textPath xlink:href="#bCurve" startOffset="0%">
              RECRUITMENT  ·  INTELLIGENCE  ARTIFICIELLE
            </textPath>
          </text>
        </svg>"""
        return cls._render(svg, size)

    # ──────────────────────────────────────────────────────────────────────

    @classmethod
    def logo_stark_badge(cls, size: QSize = QSize(96, 96)) -> QIcon:
        """
        Badge circulaire premium — style timbre/sceau officiel.
        Texte « STARK RECRUITMENT AI » suit tout le périmètre du cercle.
        Étoile centrale à 6 branches.
        """
        svg = """<svg xmlns="http://www.w3.org/2000/svg"
                      xmlns:xlink="http://www.w3.org/1999/xlink"
                      width="192" height="192" viewBox="0 0 192 192">
          <defs>
            <linearGradient id="bbBg" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%"   stop-color="#001A3A"/>
              <stop offset="50%"  stop-color="#003E7E"/>
              <stop offset="100%" stop-color="#0055A8"/>
            </linearGradient>
            <linearGradient id="bbAcc" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%"   stop-color="#FF4500"/>
              <stop offset="100%" stop-color="#FF8C61"/>
            </linearGradient>
            <linearGradient id="bbS" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%"   stop-color="#FFFFFF"/>
              <stop offset="100%" stop-color="#AAD4FF"/>
            </linearGradient>
            <filter id="bbGlow">
              <feGaussianBlur in="SourceGraphic" stdDeviation="3" result="b"/>
              <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
            </filter>
            <filter id="bbShadow">
              <feDropShadow dx="0" dy="4" stdDeviation="6"
                flood-color="#001020" flood-opacity="0.7"/>
            </filter>

            <!-- Cercle complet pour textPath (sens horaire, arc supérieur) -->
            <!-- Rayon 80 centré (96,96) — arc du dessus -->
            <path id="bbCircTop"
              d="M 16,96 A 80,80 0 0,1 176,96"/>
            <!-- Arc du bas (sens anti-horaire pour lire normalement) -->
            <path id="bbCircBot"
              d="M 22,108 A 76,76 0 0,0 170,108"/>
          </defs>

          <!-- Fond principal -->
          <circle cx="96" cy="96" r="92" fill="url(#bbBg)" filter="url(#bbShadow)"/>

          <!-- Cercle de bord doré -->
          <circle cx="96" cy="96" r="90"
            fill="none" stroke="url(#bbAcc)" stroke-width="2.5"/>

          <!-- Double cercle intérieur décoratif -->
          <circle cx="96" cy="96" r="78"
            fill="none" stroke="rgba(255,255,255,0.15)" stroke-width="1"/>
          <circle cx="96" cy="96" r="68"
            fill="none" stroke="rgba(255,107,53,0.25)" stroke-width="0.8"
            stroke-dasharray="4,3"/>

          <!-- Étoile à 6 branches (hexagramme) centrale -->
          <g transform="translate(96,96)" filter="url(#bbGlow)">
            <polygon points="0,-28 8,-8 28,-8 13,5 20,25 0,14 -20,25 -13,5 -28,-8 -8,-8"
              fill="rgba(255,107,53,0.18)" stroke="rgba(255,107,53,0.4)" stroke-width="1"/>
          </g>

          <!-- Lettre S monumentale -->
          <text x="96" y="120"
            font-family="Georgia,'Times New Roman',serif"
            font-size="90" font-weight="bold" font-style="italic"
            fill="url(#bbS)" text-anchor="middle"
            filter="url(#bbGlow)">S</text>

          <!-- Points cardinaux décoratifs -->
          <circle cx="96" cy="10"  r="3.5" fill="url(#bbAcc)"/>
          <circle cx="96" cy="182" r="3.5" fill="url(#bbAcc)"/>
          <circle cx="10"  cy="96" r="3.5" fill="url(#bbAcc)"/>
          <circle cx="182" cy="96" r="3.5" fill="url(#bbAcc)"/>

          <!-- ══ TEXTE ARC SUPÉRIEUR ══ -->
          <text font-family="'Segoe UI','Helvetica Neue',sans-serif"
                font-size="14" font-weight="700" letter-spacing="4"
                fill="rgba(255,255,255,0.92)">
            <textPath xlink:href="#bbCircTop" startOffset="50%" text-anchor="middle">
              ★  STARK  SOLUTIONS  ★
            </textPath>
          </text>

          <!-- ══ TEXTE ARC INFÉRIEUR ══ -->
          <text font-family="'Segoe UI','Helvetica Neue',sans-serif"
                font-size="11.5" font-weight="500" letter-spacing="3.5"
                fill="rgba(255,140,97,0.9)">
            <textPath xlink:href="#bbCircBot" startOffset="50%" text-anchor="middle">
              RECRUITMENT  ·  AI  ·  2026
            </textPath>
          </text>
        </svg>"""
        return cls._render(svg, size)

    # ─────────────────────────────────────────────────────────────
    #  ICÔNES LUCIDE  (stroke SVG purs, sans remplissage parasite)
    # ─────────────────────────────────────────────────────────────

    @classmethod
    def _lucide(cls, paths: str, color: str,
                w: int = 24, h: int = 24,
                size: QSize = QSize(32, 32),
                extra: str = "") -> QIcon:
        """Helper générique Lucide — stroke uniquement."""
        svg = f"""<svg xmlns="http://www.w3.org/2000/svg"
            width="{w}" height="{h}" viewBox="0 0 {w} {h}"
            fill="none" stroke="{color}" stroke-width="2"
            stroke-linecap="round" stroke-linejoin="round">
          {extra}{paths}
        </svg>"""
        return cls._render(svg, size)

    # — Audio —

    @classmethod
    def microphone(cls, color: str | None = None, size: QSize = QSize(32, 32)) -> QIcon:
        """Lucide · Mic"""
        c = color or StarkTheme.WHITE
        return cls._lucide("""
          <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/>
          <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
          <line x1="12" y1="19" x2="12" y2="22"/>
          <line x1="8"  y1="22" x2="16" y2="22"/>""", c, size=size)

    @classmethod
    def microphone_off(cls, color: str | None = None, size: QSize = QSize(32, 32)) -> QIcon:
        """Lucide · MicOff"""
        c = color or StarkTheme.ERROR
        return cls._lucide("""
          <line x1="2" y1="2" x2="22" y2="22"/>
          <path d="M18.89 13.23A7.12 7.12 0 0 0 19 12v-2"/>
          <path d="M5 10v2a7 7 0 0 0 12 5"/>
          <path d="M15 9.34V5a3 3 0 0 0-5.68-1.33"/>
          <path d="M9 9v3a3 3 0 0 0 5.12 2.12"/>
          <line x1="12" y1="19" x2="12" y2="22"/>
          <line x1="8"  y1="22" x2="16" y2="22"/>""", c, size=size)

    @classmethod
    def headphones(cls, color: str | None = None, size: QSize = QSize(32, 32)) -> QIcon:
        """Lucide · Headphones"""
        c = color or StarkTheme.ORANGE_ACCENT
        return cls._lucide("""
          <path d="M3 14h3a2 2 0 0 1 2 2v3a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-7
                   a9 9 0 0 1 18 0v7a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3
                   a2 2 0 0 1 2-2h3"/>""", c, size=size)

    @classmethod
    def volume_2(cls, color: str | None = None, size: QSize = QSize(32, 32)) -> QIcon:
        """Lucide · Volume2"""
        c = color or StarkTheme.BLUE_LIGHT
        return cls._lucide("""
          <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
          <path d="M15.54 8.46a5 5 0 0 1 0 7.07"/>
          <path d="M19.07 4.93a10 10 0 0 1 0 14.14"/>""", c, size=size)

    @classmethod
    def radio(cls, color: str | None = None, size: QSize = QSize(32, 32)) -> QIcon:
        """Lucide · Radio"""
        c = color or StarkTheme.ERROR
        return cls._lucide("""
          <path d="M4.9 19.1C1 15.2 1 8.8 4.9 4.9"/>
          <path d="M7.8 16.2c-2.3-2.3-2.3-6.1 0-8.4"/>
          <circle cx="12" cy="12" r="2"/>
          <path d="M16.2 7.8c2.3 2.3 2.3 6.1 0 8.4"/>
          <path d="M19.1 4.9C23 8.8 23 15.1 19.1 19"/>""", c, size=size)

    @classmethod
    def message_circle(cls, color: str | None = None, size: QSize = QSize(32, 32)) -> QIcon:
        """Lucide · MessageCircle"""
        c = color or StarkTheme.BLUE_LIGHT
        return cls._lucide("""
          <path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"/>""", c, size=size)

    # — Stop / Contrôle —

    @classmethod
    def stop_circle(cls, color: str | None = None, size: QSize = QSize(32, 32)) -> QIcon:
        """Lucide · StopCircle"""
        c = color or StarkTheme.WHITE
        return cls._lucide("""
          <circle cx="12" cy="12" r="10"/>
          <rect x="9" y="9" width="6" height="6" rx="1"
                fill="{c}" stroke="{c}"/>""".replace("{c}", c), c, size=size)

    @classmethod
    def power(cls, color: str | None = None, size: QSize = QSize(32, 32)) -> QIcon:
        """Lucide · Power"""
        c = color or StarkTheme.WHITE
        return cls._lucide("""
          <path d="M12 2v10"/>
          <path d="M18.4 6.6a9 9 0 1 1-12.77.04"/>""", c, size=size)

    @classmethod
    def log_out(cls, color: str | None = None, size: QSize = QSize(32, 32)) -> QIcon:
        """Lucide · LogOut"""
        c = color or StarkTheme.WHITE
        return cls._lucide("""
          <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
          <polyline points="16 17 21 12 16 7"/>
          <line x1="21" y1="12" x2="9" y2="12"/>""", c, size=size)

    # — Statuts —

    @classmethod
    def activity(cls, color: str | None = None, size: QSize = QSize(32, 32)) -> QIcon:
        """Lucide · Activity"""
        c = color or StarkTheme.BLUE_LIGHT
        return cls._lucide("""
          <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>""", c, size=size)

    @classmethod
    def circle_check(cls, color: str | None = None, size: QSize = QSize(32, 32)) -> QIcon:
        """Lucide · CircleCheck"""
        c = color or StarkTheme.SUCCESS
        return cls._lucide("""
          <circle cx="12" cy="12" r="10"/>
          <path d="m9 12 2 2 4-4"/>""", c, size=size)

    @classmethod
    def circle_alert(cls, color: str | None = None, size: QSize = QSize(32, 32)) -> QIcon:
        """Lucide · CircleAlert"""
        c = color or StarkTheme.WARNING
        return cls._lucide("""
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="8"  x2="12" y2="12"/>
          <line x1="12" y1="16" x2="12.01" y2="16"/>""", c, size=size)

    @classmethod
    def wifi(cls, color: str | None = None, size: QSize = QSize(32, 32)) -> QIcon:
        """Lucide · Wifi"""
        c = color or StarkTheme.SUCCESS
        return cls._lucide("""
          <path d="M5 12.55a11 11 0 0 1 14.08 0"/>
          <path d="M1.42 9a16 16 0 0 1 21.16 0"/>
          <path d="M8.53 16.11a6 6 0 0 1 6.95 0"/>
          <line x1="12" y1="20" x2="12.01" y2="20"/>""", c, size=size)

    @classmethod
    def wifi_off(cls, color: str | None = None, size: QSize = QSize(32, 32)) -> QIcon:
        """Lucide · WifiOff"""
        c = color or StarkTheme.ERROR
        return cls._lucide("""
          <line x1="2" y1="2" x2="22" y2="22"/>
          <path d="M8.5 16.5a5 5 0 0 1 7 0"/>
          <path d="M2 8.82a15 15 0 0 1 4.17-2.65"/>
          <path d="M10.66 5c4.01-.36 8.14.9 11.34 3.76"/>
          <path d="M16.85 11.25a10 10 0 0 1 2.22 1.68"/>
          <path d="M5 12.55a10 10 0 0 1 5.17-2.39"/>
          <line x1="12" y1="20" x2="12.01" y2="20"/>""", c, size=size)

    # — Navigation —

    @classmethod
    def arrow_left(cls, color: str | None = None, size: QSize = QSize(32, 32)) -> QIcon:
        """Lucide · ArrowLeft"""
        c = color or StarkTheme.GRAY_MEDIUM
        return cls._lucide("""
          <path d="m12 19-7-7 7-7"/>
          <path d="M19 12H5"/>""", c, size=size)

    @classmethod
    def chevron_right(cls, color: str | None = None, size: QSize = QSize(32, 32)) -> QIcon:
        """Lucide · ChevronRight"""
        c = color or StarkTheme.WHITE
        return cls._lucide("""
          <path d="m9 18 6-6-6-6"/>""", c, size=size)

    @classmethod
    def check(cls, color: str | None = None, size: QSize = QSize(32, 32)) -> QIcon:
        """Lucide · Check"""
        c = color or StarkTheme.SUCCESS
        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24"
            viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="3"
            stroke-linecap="round" stroke-linejoin="round">
          <path d="M20 6 9 17l-5-5"/>
        </svg>"""
        return cls._render(svg, size)

    @classmethod
    def x_circle(cls, color: str | None = None, size: QSize = QSize(32, 32)) -> QIcon:
        """Lucide · XCircle"""
        c = color or StarkTheme.ERROR
        return cls._lucide("""
          <circle cx="12" cy="12" r="10"/>
          <path d="m15 9-6 6"/>
          <path d="m9 9 6 6"/>""", c, size=size)

    # — RH & Recrutement —

    @classmethod
    def user_check(cls, color: str | None = None, size: QSize = QSize(32, 32)) -> QIcon:
        """Lucide · UserCheck"""
        c = color or StarkTheme.BLUE_PRIMARY
        return cls._lucide("""
          <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>
          <circle cx="9" cy="7" r="4"/>
          <polyline points="16 11 18 13 22 9"/>""", c, size=size)

    @classmethod
    def user_circle(cls, color: str | None = None, size: QSize = QSize(32, 32)) -> QIcon:
        """Lucide · CircleUser"""
        c = color or StarkTheme.BLUE_LIGHT
        return cls._lucide("""
          <circle cx="12" cy="12" r="10"/>
          <circle cx="12" cy="10" r="3"/>
          <path d="M7 20.662V19a2 2 0 0 1 2-2h6a2 2 0 0 1 2 2v1.662"/>""", c, size=size)

    @classmethod
    def briefcase(cls, color: str | None = None, size: QSize = QSize(32, 32)) -> QIcon:
        """Lucide · Briefcase"""
        c = color or StarkTheme.ORANGE_ACCENT
        return cls._lucide("""
          <rect x="2" y="7" width="20" height="14" rx="2"/>
          <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>""", c, size=size)

    @classmethod
    def file_text(cls, color: str | None = None, size: QSize = QSize(32, 32)) -> QIcon:
        """Lucide · FileText"""
        c = color or StarkTheme.BLUE_PRIMARY
        return cls._lucide("""
          <path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/>
          <path d="M14 2v4a2 2 0 0 0 2 2h4"/>
          <line x1="16" y1="13" x2="8" y2="13"/>
          <line x1="16" y1="17" x2="8" y2="17"/>
          <line x1="10" y1="9"  x2="8" y2="9"/>""", c, size=size)

    @classmethod
    def clipboard_list(cls, color: str | None = None, size: QSize = QSize(32, 32)) -> QIcon:
        """Lucide · ClipboardList"""
        c = color or StarkTheme.BLUE_PRIMARY
        return cls._lucide("""
          <rect x="8" y="2" width="8" height="4" rx="1"/>
          <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/>
          <line x1="9"  y1="12" x2="15" y2="12"/>
          <line x1="9"  y1="16" x2="15" y2="16"/>
          <line x1="9"  y1="8"  x2="9.01" y2="8"/>""", c, size=size)

    # — Sécurité —

    @classmethod
    def shield_check(cls, color: str | None = None, size: QSize = QSize(32, 32)) -> QIcon:
        """Lucide · ShieldCheck"""
        c = color or StarkTheme.SUCCESS
        return cls._lucide("""
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10"/>
          <path d="m9 12 2 2 4-4"/>""", c, size=size)

    @classmethod
    def lock(cls, color: str | None = None, size: QSize = QSize(32, 32)) -> QIcon:
        """Lucide · Lock"""
        c = color or StarkTheme.BLUE_PRIMARY
        return cls._lucide("""
          <rect x="3" y="11" width="18" height="11" rx="2"/>
          <path d="M7 11V7a5 5 0 0 1 10 0v4"/>""", c, size=size)

    @classmethod
    def key_round(cls, color: str | None = None, size: QSize = QSize(32, 32)) -> QIcon:
        """Lucide · KeyRound"""
        c = color or StarkTheme.ORANGE_ACCENT
        return cls._lucide("""
          <circle cx="7.5" cy="15.5" r="5.5"/>
          <path d="m21 2-9.6 9.6"/>
          <path d="m15.5 7.5 3 3L22 7l-3-3"/>""", c, size=size)

    @classmethod
    def zap(cls, color: str | None = None, size: QSize = QSize(32, 32)) -> QIcon:
        """Lucide · Zap"""
        c = color or StarkTheme.ORANGE_ACCENT
        return cls._lucide("""
          <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>""", c, size=size)

    @classmethod
    def help_circle(cls, color: str | None = None, size: QSize = QSize(32, 32)) -> QIcon:
        """Lucide · HelpCircle"""
        c = color or StarkTheme.ORANGE_ACCENT
        return cls._lucide("""
          <circle cx="12" cy="12" r="10"/>
          <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
          <line x1="12" y1="17" x2="12.01" y2="17"/>""", c, size=size)

    @classmethod
    def settings(cls, color: str | None = None, size: QSize = QSize(32, 32)) -> QIcon:
        """Lucide · Settings"""
        c = color or StarkTheme.GRAY_MEDIUM
        return cls._lucide("""
          <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25
                   a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38
                   a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51
                   a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38
                   a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25
                   a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18
                   a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08
                   a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08
                   a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09
                   a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08
                   a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/>
          <circle cx="12" cy="12" r="3"/>""", c, size=size)

    @classmethod
    def square(cls, color: str | None = None, size: QSize = QSize(32, 32)) -> QIcon:
        """Lucide · Square (filled)"""
        c = color or StarkTheme.WHITE
        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24"
            viewBox="0 0 24 24" fill="{c}" stroke="{c}" stroke-width="2"
            stroke-linecap="round" stroke-linejoin="round">
          <rect x="3" y="3" width="18" height="18" rx="2"/>
        </svg>"""
        return cls._render(svg, size)