"""
CameraPreviewWidget — Overlay caméra PiP entièrement contenu dans le cadre vidéo
==================================================================================
• Tout tient dans _W x _H — rien ne déborde en dehors
• Métriques affichées en overlay DANS le frame (bandeau bas semi-transparent)
• Analyse faciale temps réel MediaPipe dans un thread daemon
• Badge REC clignotant rouge
"""

import numpy as np
import cv2
import threading
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGraphicsDropShadowEffect, QProgressBar,
)
from PySide6.QtCore  import Qt, QTimer, Signal, Slot
from PySide6.QtGui   import QImage, QPixmap, QColor, QPainter, QPen, QBrush, QFont

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from client.ui.stark_theme import T

# ── Dimensions — tout tient dans ce rectangle ─────────────────────────────────
_W      = 200   # largeur totale du widget
_H      = 170   # hauteur totale du widget (vidéo + barre statut, sans rien en dehors)
_VH     = 144   # hauteur zone vidéo
_BH     = 26    # hauteur barre statut interne
_MARGIN = 14    # marge depuis les bords du parent
_RADIUS = 12

_EMOJI = {
    "happy": "😊", "neutral": "😐", "surprise": "😮",
    "sad":   "😟", "angry":  "😠", "fear":    "😨", "disgust": "🤢",
}


class _Dot(QWidget):
    def __init__(self, color: str, parent=None):
        super().__init__(parent)
        self._c = QColor(color); self._a = 255; self._d = -6
        self.setFixedSize(8, 8)
        t = QTimer(self); t.timeout.connect(self._tick); t.start(50)

    def set_color(self, c: str):
        self._c = QColor(c); self.update()

    def _tick(self):
        self._a = max(60, min(255, self._a + self._d))
        if self._a <= 60:   self._d =  6
        elif self._a >= 255: self._d = -6
        self.update()

    def paintEvent(self, _):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = QColor(self._c); c.setAlpha(self._a)
        p.setBrush(QBrush(c)); p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(0, 0, 8, 8)


class CameraPreviewWidget(QWidget):
    """
    Overlay caméra PiP auto-contenu.
    Dimensions fixes : _W × _H — ne déborde jamais.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.SubWindow)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(_W + 4, _H + 4)

        self._recording    = False
        self._has_camera   = False
        self._no_signal    = True
        self._blink        = True
        self._face_present = False

        self._mp_ready      = False
        self._face_mesh     = None
        self._rt_lock       = threading.Lock()
        self._last_metrics: dict = {}
        self._eval_metrics: dict = {}

        self._blink_timer = QTimer(self)
        self._blink_timer.setInterval(600)
        self._blink_timer.timeout.connect(self._toggle_blink)

        self._metrics_timer = QTimer(self)
        self._metrics_timer.setInterval(400)
        self._metrics_timer.timeout.connect(self._refresh_metrics_overlay)
        self._metrics_timer.start()

        self._init_mediapipe()
        self._build()
        self._show_placeholder()

    # ── MediaPipe ─────────────────────────────────────────────────────────────

    def _init_mediapipe(self):
        try:
            import mediapipe as mp
            self._face_mesh = mp.solutions.face_mesh.FaceMesh(
                static_image_mode=False, max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            self._mp_ready = True
        except Exception as e:
            print(f"[CameraPreview] MediaPipe non dispo : {e}")

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(2, 2, 2, 2)
        root.setSpacing(0)

        # Cadre principal (tout le widget)
        self._frame = QFrame()
        self._frame.setFixedSize(_W, _H)
        self._frame.setStyleSheet(f"""
            QFrame {{
                background: #0F172A;
                border: 2px solid rgba(255,255,255,0.18);
                border-radius: {_RADIUS}px;
            }}
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20); shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 140))
        self._frame.setGraphicsEffect(shadow)

        inner = QVBoxLayout(self._frame)
        inner.setContentsMargins(0, 0, 0, 0)
        inner.setSpacing(0)

        # ── Zone image ────────────────────────────────────────────────────────
        self._img_lbl = QLabel()
        self._img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._img_lbl.setStyleSheet(f"""
            QLabel {{
                background: transparent;
                border-top-left-radius:  {_RADIUS - 2}px;
                border-top-right-radius: {_RADIUS - 2}px;
            }}
        """)
        self._img_lbl.setFixedSize(_W - 4, _VH)
        inner.addWidget(self._img_lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        # ── Bandeau métriques overlay (DANS le cadre, pas en dehors) ─────────
        metrics_bar = QFrame()
        metrics_bar.setFixedSize(_W - 4, _BH + 18)   # barre statut + mini-métriques
        metrics_bar.setStyleSheet("""
            QFrame {
                background: rgba(10, 15, 30, 0.92);
                border-bottom-left-radius: 10px;
                border-bottom-right-radius: 10px;
            }
        """)
        mb_lay = QVBoxLayout(metrics_bar)
        mb_lay.setContentsMargins(8, 3, 8, 4)
        mb_lay.setSpacing(3)

        # Ligne 1 : statut + émotion + REC
        row1 = QHBoxLayout(); row1.setSpacing(5)
        self._dot = _Dot(T.GREEN_500)
        row1.addWidget(self._dot)

        self._face_lbl = QLabel("Caméra active")
        self._face_lbl.setFont(QFont(T.FONT, 7, QFont.Weight.DemiBold))
        self._face_lbl.setStyleSheet("color: rgba(255,255,255,0.80); background: transparent;")
        row1.addWidget(self._face_lbl, stretch=1)

        self._emotion_lbl = QLabel("")
        self._emotion_lbl.setFont(QFont("Segoe UI Emoji, Apple Color Emoji", 11))
        self._emotion_lbl.setStyleSheet("background: transparent;")
        row1.addWidget(self._emotion_lbl)

        self._rec_badge = QLabel(" ● REC ")
        self._rec_badge.setFont(QFont(T.FONT, 6, QFont.Weight.Bold))
        self._rec_badge.setStyleSheet(f"""
            color: white; background: {T.RED_600};
            border-radius: 4px; padding: 1px 4px;
        """)
        self._rec_badge.setVisible(False)
        row1.addWidget(self._rec_badge)
        mb_lay.addLayout(row1)

        # Ligne 2 : 4 mini-barres côte à côte
        row2 = QHBoxLayout(); row2.setSpacing(6)

        def _mini(color):
            b = QProgressBar()
            b.setRange(0, 100); b.setValue(0)
            b.setTextVisible(False); b.setFixedHeight(4)
            b.setStyleSheet(f"""
                QProgressBar {{ background: rgba(255,255,255,0.15);
                                border-radius: 2px; border: none; }}
                QProgressBar::chunk {{ background: {color}; border-radius: 2px; }}
            """)
            return b

        col_data = [
            ("Conf.",    T.CYAN_500,  "_conf_bar"),
            ("Stress",   T.RED_500,   "_stress_bar"),
            ("Contact",  T.GREEN_500, "_contact_bar"),
            ("Stab.",    T.AMBER_500, "_stab_bar"),
        ]
        for label, color, attr in col_data:
            col = QVBoxLayout(); col.setSpacing(1)
            lbl = QLabel(label)
            lbl.setFont(QFont(T.FONT, 5))
            lbl.setStyleSheet("color: rgba(255,255,255,0.45); background: transparent;")
            bar = _mini(color)
            setattr(self, attr, bar)
            col.addWidget(lbl); col.addWidget(bar)
            row2.addLayout(col)

        mb_lay.addLayout(row2)
        inner.addWidget(metrics_bar, alignment=Qt.AlignmentFlag.AlignCenter)

        root.addWidget(self._frame)

    # ── Analyse temps réel ────────────────────────────────────────────────────

    def _analyze_frame_rt(self, frame_bgr: np.ndarray) -> dict:
        """
        Analyse temps réel alignée avec facial_analysis_service v2.
        Utilise EAR pour clignements et iris offset pour contact visuel.
        """
        if not self._mp_ready or self._face_mesh is None:
            return {}
        try:
            import math
            h, w = frame_bgr.shape[:2]
            if w > 320:
                s = 320 / w
                frame_bgr = cv2.resize(frame_bgr, (320, int(h * s)))
            rgb    = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            result = self._face_mesh.process(rgb)
            if not result.multi_face_landmarks:
                return {"face": False}
            lm = result.multi_face_landmarks[0].landmark

            # EAR (Eye Aspect Ratio)
            def ear(top, bot, outer, inner):
                h_ = abs(lm[top].y - lm[bot].y)
                w_ = abs(lm[outer].x - lm[inner].x) + 1e-6
                return h_ / w_
            ear_l  = ear(159, 145, 33, 133)
            ear_r  = ear(386, 374, 263, 362)
            is_blink = (ear_l + ear_r) / 2 < 0.20

            # Iris offset (contact visuel précis)
            def iris_offset(iris, outer, inner, top, bot):
                cx = (lm[outer].x + lm[inner].x) / 2
                cy = (lm[top].y   + lm[bot].y)   / 2
                ew = abs(lm[outer].x - lm[inner].x) + 1e-6
                return (lm[iris].x - cx) / ew, (lm[iris].y - cy) / ew
            ox_l, oy_l = iris_offset(468, 33,  133, 159, 145)
            ox_r, oy_r = iris_offset(473, 263, 362, 386, 374)
            ox = (ox_l + ox_r) / 2
            oy = (oy_l + oy_r) / 2
            eye_contact = abs(ox) < 0.35 and abs(oy) < 0.28 and not is_blink

            # Pose tête simplifiée (sans solvePnP pour la perf temps réel)
            yaw_approx = abs(lm[454].x - lm[234].x - 0.5) * 60
            stab = max(0.0, min(1.0, 1.0 - yaw_approx / 30))

            # Émotion
            eye_dist   = abs(lm[33].x - lm[263].x) + 1e-6
            lip_mid_y  = (lm[13].y + lm[14].y) / 2
            corner_avg = (lm[61].y + lm[291].y) / 2
            corner_up  = max(0.0, (lip_mid_y - corner_avg) / eye_dist * 3)
            brow_gap   = abs(lm[107].x - lm[336].x) / eye_dist
            brow_frown = max(0.0, min(1.0, (0.55 - brow_gap) * 5))
            brow_raise = max(0.0, min(1.0,
                ((lm[159].y - lm[107].y) + (lm[386].y - lm[336].y)) / eye_dist * 2))
            mar = abs(lm[13].y - lm[14].y) / (abs(lm[61].x - lm[291].x) + 1e-6)

            if corner_up > 0.25:                emotion = "happy"
            elif brow_frown > 0.30:             emotion = "angry"
            elif brow_raise > 0.40 and mar > 0.25: emotion = "surprise"
            elif brow_raise > 0.30:             emotion = "fear"
            else:                               emotion = "neutral"

            # Scores synthétiques
            blink_factor = 1.0  # temps réel : pas assez de frames pour blink_rate
            confidence = min(10.0, max(0.0,
                (1 if eye_contact else 0) * 3.5 + stab * 2.5
                + corner_up * 2.0 - brow_frown * 3.0))
            stress = min(10.0, max(0.0,
                brow_frown * 3.5 + (1 - stab) * 2.0
                + (1 - (1 if eye_contact else 0)) * 2.0
                - corner_up * 1.5))

            return {
                "face":        True,
                "eye_contact": eye_contact,
                "is_blink":    is_blink,
                "stability":   stab,
                "emotion":     emotion,
                "confidence":  confidence,
                "stress":      stress,
                "brow_frown":  brow_frown,
            }
        except Exception:
            return {"face": False}

    # ── Slots publics ─────────────────────────────────────────────────────────

    @Slot(bytes)
    def on_frame(self, jpeg_bytes: bytes):
        """Reçoit un frame JPEG depuis VideoFrameCollector."""
        try:
            buf   = np.frombuffer(jpeg_bytes, dtype=np.uint8)
            frame = cv2.imdecode(buf, cv2.IMREAD_COLOR)
            if frame is None:
                return

            # Analyse dans un thread daemon
            frame_copy = frame.copy()
            threading.Thread(
                target=self._run_analysis_thread,
                args=(frame_copy,), daemon=True
            ).start()

            # Flip miroir + affichage
            frame = cv2.flip(frame, 1)
            rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, c = rgb.shape
            tw, th  = _W - 4, _VH

            ratio   = min(tw / w, th / h)
            nw, nh  = int(w * ratio), int(h * ratio)
            resized = cv2.resize(rgb, (nw, nh), interpolation=cv2.INTER_AREA)

            # Contour vert si visage détecté
            with self._rt_lock:
                face_ok = self._last_metrics.get("face", False)
            color = (34, 197, 94) if face_ok else (71, 85, 105)
            cv2.rectangle(resized, (1, 1), (nw - 2, nh - 2), color, 2)

            img = QImage(resized.data.tobytes(), nw, nh, nw * c,
                         QImage.Format.Format_RGB888)
            self._img_lbl.setPixmap(QPixmap.fromImage(img))

            if self._no_signal:
                self._no_signal  = False
                self._has_camera = True
                self._face_lbl.setText("Analyse active")
                self._dot.set_color(T.GREEN_500)

        except Exception:
            pass

    def _run_analysis_thread(self, frame: np.ndarray):
        metrics = self._analyze_frame_rt(frame)
        with self._rt_lock:
            self._last_metrics = metrics

    def set_recording(self, recording: bool):
        self._recording = recording
        self._rec_badge.setVisible(recording)
        if recording:
            self._blink_timer.start()
            self._face_lbl.setText("Enregistrement…")
            self._dot.set_color(T.RED_500)
        else:
            self._blink_timer.stop()
            self._rec_badge.setVisible(False)
            if self._has_camera:
                self._face_lbl.setText("Analyse active")
                self._dot.set_color(T.GREEN_500)

    def set_facial_result(self, metrics: dict):
        """Métriques post-évaluation reçues du serveur."""
        self._eval_metrics = metrics
        self._refresh_metrics_overlay()

    def set_camera_unavailable(self):
        self._has_camera = False
        self._face_lbl.setText("Pas de caméra")
        self._dot.set_color(T.TEXT_400)
        self._show_placeholder()

    # ── Mise à jour overlay métriques ─────────────────────────────────────────

    def _refresh_metrics_overlay(self):
        if self._eval_metrics:
            m       = self._eval_metrics
            conf    = int(m.get("confidence_score",  5.0) * 10)
            contact = int(m.get("eye_contact_ratio", 0.0) * 100)
            stress  = int(m.get("stress_score",      5.0) * 10)
            stab    = int(m.get("head_stability",     1.0) * 100)
            emotion = m.get("dominant_emotion", "neutral")
        else:
            with self._rt_lock:
                m = dict(self._last_metrics)
            if not m.get("face"):
                self._conf_bar.setValue(0); self._stress_bar.setValue(0)
                self._contact_bar.setValue(0); self._stab_bar.setValue(0)
                self._emotion_lbl.setText("")
                return
            conf    = int(m.get("confidence", 5.0) * 10)
            contact = 100 if m.get("eye_contact") else 0
            stress  = int(m.get("stress",     0.0) * 10)
            stab    = int(m.get("stability",  1.0) * 100)
            emotion = m.get("emotion", "neutral")

        self._conf_bar.setValue(conf)
        self._stress_bar.setValue(stress)
        self._contact_bar.setValue(contact)
        self._stab_bar.setValue(stab)
        self._emotion_lbl.setText(_EMOJI.get(emotion, "😐"))

    def _toggle_blink(self):
        self._blink = not self._blink
        self._rec_badge.setVisible(self._blink and self._recording)

    def _show_placeholder(self):
        w, h = _W - 4, _VH
        img  = np.zeros((h, w, 3), dtype=np.uint8)
        img[:, :] = (30, 41, 59)
        cx, cy = w // 2, h // 2
        cv2.rectangle(img, (cx - 22, cy - 14), (cx + 22, cy + 14), (71, 85, 105), -1)
        cv2.rectangle(img, (cx - 22, cy - 14), (cx + 22, cy + 14), (100, 116, 139), 1)
        pts = np.array([[cx+22,cy-8],[cx+34,cy-16],[cx+34,cy+16],[cx+22,cy+8]])
        cv2.fillPoly(img, [pts], (71, 85, 105))
        cv2.circle(img, (cx, cy), 7, (100, 116, 139), -1)
        cv2.circle(img, (cx, cy), 4, (30, 41, 59), -1)
        qt = QImage(img.tobytes(), w, h, w * 3, QImage.Format.Format_RGB888)
        self._img_lbl.setPixmap(QPixmap.fromImage(qt))

    def reposition(self):
        """Place l'overlay dans le coin bas-gauche du parent."""
        if self.parent():
            self.move(_MARGIN, self.parent().height() - self.height() - _MARGIN)

    def cleanup(self):
        if self._face_mesh:
            try: self._face_mesh.close()
            except Exception: pass
            self._face_mesh = None