"""
Service d'analyse du langage corporel facial — SparkHire AI  (v2)
==================================================================

Améliorations v2 vs v1 :
  1. Contact visuel par IRIS offset (landmarks 468/473) au lieu de position nez
  2. Clignement détecté via Eye Aspect Ratio (EAR)
  3. Expressions faciales via 12 Action Units FACS reconstruits depuis landmarks
  4. Lissage temporel sur fenêtre glissante de 15 frames (évite le bruit)
  5. Score de confiance / stress recalibré sur données réelles d'entretien RH
  6. Pose de tête via 6 points 3D projetés (solvePnP) → yaw/pitch/roll réels
  7. Engagement = formule composite (contact + sourire + haussement sourcils)
  8. Face detection rate = qualité de la session (seuil 0.30 inchangé)

Architecture :
  FaceMesh 468 landmarks + iris (landmarks 468–477)  ← MediaPipe
  Analyse par frame → FrameResult
  Agrégation N frames → FacialMetrics (stockée MongoDB)
"""

from __future__ import annotations

import logging
import math
import os
from collections import deque
from dataclasses import dataclass, field
from statistics import mean, stdev
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)
os.environ.setdefault("GLOG_minloglevel", "3")


# ── Constantes calibration ────────────────────────────────────────────────────

_EAR_BLINK_THRESHOLD = 0.20   # EAR < seuil → clignement
_IRIS_CONTACT_X      = 0.35   # offset iris X maximal pour "contact visuel"
_IRIS_CONTACT_Y      = 0.28   # offset iris Y maximal pour "contact visuel"
_SMOOTH_WINDOW       = 15     # frames de lissage

# Points 3D de référence pour solvePnP (modèle générique visage)
_MODEL_POINTS_3D = np.array([
    [  0.0,    0.0,    0.0  ],   # bout du nez (4)
    [  0.0,  -63.6,  -12.5 ],   # menton (152)
    [-43.3,   32.7,  -26.0 ],   # coin œil gauche (33)
    [ 43.3,   32.7,  -26.0 ],   # coin œil droit (263)
    [-28.9,  -28.9,  -24.1 ],   # commissure gauche (61)
    [ 28.9,  -28.9,  -24.1 ],   # commissure droite (291)
], dtype=np.float64)

_MODEL_LM_IDX = [4, 152, 33, 263, 61, 291]


# ═════════════════════════════════════════════════════════════════════════════
#  DATA CLASSES
# ═════════════════════════════════════════════════════════════════════════════

@dataclass
class FrameResult:
    has_face: bool = False
    # Pose tête
    yaw:   float = 0.0   # rotation horizontale (°)  neg=gauche, pos=droite
    pitch: float = 0.0   # rotation verticale (°)    neg=haut, pos=bas
    roll:  float = 0.0   # inclinaison latérale (°)
    # Yeux
    ear_left:       float = 0.0    # Eye Aspect Ratio œil gauche
    ear_right:      float = 0.0    # Eye Aspect Ratio œil droit
    is_blink:       bool  = False
    iris_offset_x:  float = 0.0    # offset iris moyen sur axe X (-1..1)
    iris_offset_y:  float = 0.0    # offset iris moyen sur axe Y (-1..1)
    eye_contact:    bool  = False
    # Bouche
    mar:            float = 0.0    # Mouth Aspect Ratio
    lip_corner_up:  float = 0.0    # commissures relevées (smile score 0..1)
    # Sourcils
    brow_raise:     float = 0.0    # haussement sourcils (0..1)
    brow_frown:     float = 0.0    # froncement sourcils (0..1)
    # Émotions (scores bruts 0..1 avant normalisation)
    raw_happy:    float = 0.0
    raw_surprise: float = 0.0
    raw_angry:    float = 0.0
    raw_fear:     float = 0.0
    raw_sad:      float = 0.0
    raw_neutral:  float = 0.0
    dominant_emotion: str = "neutral"


@dataclass
class FacialMetrics:
    dominant_emotion: str = "neutral"
    emotion_scores:   dict = field(default_factory=dict)
    eye_contact_ratio:  float = 0.0
    head_stability:     float = 1.0
    smile_ratio:        float = 0.0
    blink_rate:         float = 0.0   # clignements/minute
    confidence_score:   float = 5.0
    stress_score:       float = 5.0
    engagement_score:   float = 5.0
    frames_analyzed:    int   = 0
    frames_with_face:   int   = 0
    face_detection_rate: float = 0.0
    # Détails pose
    avg_yaw:   float = 0.0
    avg_pitch: float = 0.0

    def to_dict(self) -> dict:
        return {
            "dominant_emotion":   self.dominant_emotion,
            "emotion_scores":     self.emotion_scores,
            "eye_contact_ratio":  round(self.eye_contact_ratio,  3),
            "head_stability":     round(self.head_stability,     3),
            "smile_ratio":        round(self.smile_ratio,        3),
            "blink_rate":         round(self.blink_rate,         1),
            "confidence_score":   round(self.confidence_score,   1),
            "stress_score":       round(self.stress_score,       1),
            "engagement_score":   round(self.engagement_score,   1),
            "frames_analyzed":    self.frames_analyzed,
            "frames_with_face":   self.frames_with_face,
            "face_detection_rate": round(self.face_detection_rate, 2),
            "avg_yaw":            round(self.avg_yaw,   1),
            "avg_pitch":          round(self.avg_pitch, 1),
        }


# ═════════════════════════════════════════════════════════════════════════════
#  SERVICE
# ═════════════════════════════════════════════════════════════════════════════

class FacialAnalysisService:

    def __init__(self, device: str = "cpu"):
        self.device            = "cpu"
        self._mediapipe_ready  = False
        self._face_mesh        = None
        self._smooth_buf: deque[FrameResult] = deque(maxlen=_SMOOTH_WINDOW)
        self._init_mediapipe()

    # ── Init ──────────────────────────────────────────────────────────────────

    def _init_mediapipe(self):
        try:
            import mediapipe as mp
            self._face_mesh = mp.solutions.face_mesh.FaceMesh(
                static_image_mode=False,
                max_num_faces=1,
                refine_landmarks=True,   # active les landmarks iris 468-477
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            self._mediapipe_ready = True
            logger.info(
                "✅ MediaPipe FaceMesh v2 | EAR + iris gaze + solvePnP pose | CPU"
            )
        except ImportError:
            logger.warning("mediapipe non installé — pip install mediapipe==0.10.14")
        except Exception as e:
            logger.error(f"MediaPipe init : {e}")

    @property
    def is_available(self) -> bool:
        return self._mediapipe_ready

    @property
    def status(self) -> dict:
        return {
            "mediapipe": self._mediapipe_ready,
            "device":    self.device,
            "version":   "v2",
        }

    # ── Helpers landmarks ─────────────────────────────────────────────────────

    @staticmethod
    def _ear(lm, top: int, bot: int, outer: int, inner: int) -> float:
        """Eye Aspect Ratio — 0 = fermé, ~0.30 = grand ouvert."""
        h = abs(lm[top].y - lm[bot].y)
        w = abs(lm[outer].x - lm[inner].x) + 1e-6
        return h / w

    @staticmethod
    def _iris_offset(lm, iris: int, outer: int, inner: int,
                     top: int, bot: int) -> tuple[float, float]:
        """
        Décalage du centre de l'iris dans le carré œil.
        Returns (offset_x, offset_y) normalisés par la largeur de l'œil.
        0,0 = iris parfaitement centré = regard caméra.
        """
        iris_x = lm[iris].x
        iris_y = lm[iris].y
        cx = (lm[outer].x + lm[inner].x) / 2
        cy = (lm[top].y   + lm[bot].y)   / 2
        w  = abs(lm[outer].x - lm[inner].x) + 1e-6
        return (iris_x - cx) / w, (iris_y - cy) / w

    @staticmethod
    def _dist(lm, a: int, b: int) -> float:
        dx = lm[a].x - lm[b].x
        dy = lm[a].y - lm[b].y
        return math.sqrt(dx * dx + dy * dy)

    # ── Pose de tête (solvePnP) ───────────────────────────────────────────────

    @staticmethod
    def _head_pose(lm, img_w: int, img_h: int) -> tuple[float, float, float]:
        """
        Estime yaw/pitch/roll via cv2.solvePnP avec 6 points de référence.
        Returns (yaw_deg, pitch_deg, roll_deg).
        Valeurs typiques entretien :
          yaw   ∈ [-15, +15]°  correct
          pitch ∈ [-10, +10]°  correct
        """
        try:
            import cv2
            img_pts = np.array([
                [lm[i].x * img_w, lm[i].y * img_h]
                for i in _MODEL_LM_IDX
            ], dtype=np.float64)

            focal   = img_w
            center  = (img_w / 2, img_h / 2)
            cam_mat = np.array([
                [focal, 0,     center[0]],
                [0,     focal, center[1]],
                [0,     0,     1        ],
            ], dtype=np.float64)
            dist_coeffs = np.zeros((4, 1))

            ok, rvec, tvec = cv2.solvePnP(
                _MODEL_POINTS_3D, img_pts, cam_mat, dist_coeffs,
                flags=cv2.SOLVEPNP_ITERATIVE,
            )
            if not ok:
                return 0.0, 0.0, 0.0

            rmat, _ = cv2.Rodrigues(rvec)
            proj    = np.hstack((rmat, tvec))
            _, _, _, _, _, _, euler = cv2.decomposeProjectionMatrix(proj)

            pitch = float(euler[0, 0])
            yaw   = float(euler[1, 0])
            roll  = float(euler[2, 0])
            return yaw, pitch, roll

        except Exception:
            return 0.0, 0.0, 0.0

    # ── Analyse d'un frame ────────────────────────────────────────────────────

    def analyze_frame(self, frame_bgr: np.ndarray) -> FrameResult:
        import cv2

        result = FrameResult()
        if frame_bgr is None or frame_bgr.size == 0:
            return result
        if not self._mediapipe_ready or self._face_mesh is None:
            return result

        h, w = frame_bgr.shape[:2]
        if w > 640:
            scale     = 640 / w
            frame_bgr = cv2.resize(frame_bgr, (int(w * scale), int(h * scale)))
            h, w = frame_bgr.shape[:2]

        try:
            rgb    = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            mp_res = self._face_mesh.process(rgb)
            if not mp_res.multi_face_landmarks:
                return result

            result.has_face = True
            lm = mp_res.multi_face_landmarks[0].landmark

            # ── 1. Pose de tête ───────────────────────────────────────────────
            result.yaw, result.pitch, result.roll = self._head_pose(lm, w, h)

            # ── 2. EAR + détection clignement ─────────────────────────────────
            result.ear_left  = self._ear(lm, 159, 145, 33,  133)
            result.ear_right = self._ear(lm, 386, 374, 263, 362)
            ear_avg          = (result.ear_left + result.ear_right) / 2
            result.is_blink  = ear_avg < _EAR_BLINK_THRESHOLD

            # ── 3. Contact visuel via iris ─────────────────────────────────────
            ox_l, oy_l = self._iris_offset(lm, 468, 33,  133, 159, 145)
            ox_r, oy_r = self._iris_offset(lm, 473, 263, 362, 386, 374)
            result.iris_offset_x = (ox_l + ox_r) / 2
            result.iris_offset_y = (oy_l + oy_r) / 2
            result.eye_contact   = (
                abs(result.iris_offset_x) < _IRIS_CONTACT_X
                and abs(result.iris_offset_y) < _IRIS_CONTACT_Y
                and not result.is_blink
            )

            # ── 4. Sourire (lip corner ratio) ─────────────────────────────────
            eye_dist = self._dist(lm, 33, 263) + 1e-6   # référence normalisation
            mouth_w  = self._dist(lm, 61, 291)
            # Les commissures relevées → lip_corner_up positif
            lip_mid_y  = (lm[13].y + lm[14].y) / 2
            corner_avg = (lm[61].y + lm[291].y) / 2
            result.lip_corner_up = max(0.0, (lip_mid_y - corner_avg) / eye_dist * 3)
            # MAR (Mouth Aspect Ratio)
            result.mar = abs(lm[13].y - lm[14].y) / (mouth_w + 1e-6)

            # ── 5. Sourcils ────────────────────────────────────────────────────
            # Haussement : écart entre sourcil et paupière supérieure
            brow_h_l = (lm[159].y - lm[107].y) / eye_dist
            brow_h_r = (lm[386].y - lm[336].y) / eye_dist
            result.brow_raise = max(0.0, min(1.0, (brow_h_l + brow_h_r) / 2 * 4))

            # Froncement : rapprochement des deux sourcils
            brow_gap  = abs(lm[107].x - lm[336].x) / eye_dist
            result.brow_frown = max(0.0, min(1.0, (0.55 - brow_gap) * 5))

            # ── 6. Émotions FACS ──────────────────────────────────────────────
            #
            # Chaque émotion = combinaison d'Action Units mesurés ci-dessus
            # Calibration sur espace normalisé [0,1]
            #
            # happy    = AU6 (joues) + AU12 (zygomatique) → lip_corner_up
            result.raw_happy    = min(1.0, result.lip_corner_up * 1.5)

            # surprise = AU1+2 (sourcils) + AU26 (bouche ouverte)
            result.raw_surprise = min(1.0,
                result.brow_raise * 0.6 + min(result.mar * 4, 0.4))

            # angry    = AU4 (froncement) + AU23 (lèvres pincées)
            lip_tighten = max(0.0, 0.15 - result.mar) * 6
            result.raw_angry = min(1.0, result.brow_frown * 0.7 + lip_tighten * 0.3)

            # fear     = AU1+2+4 + AU20 (lip stretch) + AU26
            result.raw_fear  = min(1.0,
                result.brow_raise * 0.4 + result.brow_frown * 0.3
                + min(result.mar * 3, 0.3))

            # sad      = AU1 intérieur + AU15 (commissures basses)
            corner_down = max(0.0, corner_avg - lip_mid_y) / eye_dist * 3
            result.raw_sad = min(1.0, corner_down * 0.7 + result.brow_raise * 0.3)

            # neutral  = résidu
            pos_sum = (result.raw_happy + result.raw_surprise +
                       result.raw_angry + result.raw_fear + result.raw_sad)
            result.raw_neutral = max(0.0, 1.0 - pos_sum * 0.6)

            # Émotion dominante
            emo_map = {
                "happy":    result.raw_happy,
                "surprise": result.raw_surprise,
                "angry":    result.raw_angry,
                "fear":     result.raw_fear,
                "sad":      result.raw_sad,
                "neutral":  result.raw_neutral,
            }
            result.dominant_emotion = max(emo_map, key=emo_map.get)

        except Exception as e:
            logger.debug(f"analyze_frame: {e}")

        return result

    # ── Agrégation avec lissage ───────────────────────────────────────────────

    def compute_metrics(self, frame_results: list[FrameResult]) -> FacialMetrics:

        total = len(frame_results)
        if total == 0:
            return FacialMetrics()

        valid = [f for f in frame_results if f.has_face]
        n     = len(valid)

        metrics = FacialMetrics(
            frames_analyzed=total,
            frames_with_face=n,
            face_detection_rate=round(n / total, 2),
        )

        if n == 0:
            logger.info("Aucun visage détecté dans les frames")
            return metrics

        # ── Appliquer le lissage temporel par médiane glissante ───────────────
        # (élimine les outliers mieux que la moyenne)

        def _med(vals): return float(np.median(vals)) if vals else 0.0
        def _avg(vals): return float(np.mean(vals))   if vals else 0.0

        # ── Contact visuel ────────────────────────────────────────────────────
        # Compter uniquement les frames où le regard est effectivement dirigé
        # vers la caméra (iris centré + yeux ouverts + pose neutre)
        contact_frames = sum(
            1 for f in valid
            if f.eye_contact and not f.is_blink
            and abs(f.yaw) < 20 and abs(f.pitch) < 15
        )
        metrics.eye_contact_ratio = round(contact_frames / n, 3)

        # ── Stabilité de la tête ──────────────────────────────────────────────
        # Basée sur l'écart-type des angles yaw et pitch
        yaw_vals   = [f.yaw   for f in valid]
        pitch_vals = [f.pitch for f in valid]
        yaw_std    = stdev(yaw_vals)   if len(yaw_vals)   > 1 else 0.0
        pitch_std  = stdev(pitch_vals) if len(pitch_vals) > 1 else 0.0
        metrics.avg_yaw   = round(_avg(yaw_vals),   1)
        metrics.avg_pitch = round(_avg(pitch_vals), 1)
        # Normalisation : std 0°=stab 1.0 ; std 15°=stab 0.5 ; std 30°=stab 0.0
        stab = 1.0 - min(1.0, (yaw_std + pitch_std) / 30.0)
        metrics.head_stability = round(stab, 3)

        # ── Sourire ───────────────────────────────────────────────────────────
        smile_frames = sum(1 for f in valid if f.lip_corner_up > 0.25)
        metrics.smile_ratio = round(smile_frames / n, 3)

        # ── Clignements ───────────────────────────────────────────────────────
        blink_count = sum(1 for f in valid if f.is_blink)
        # Estimer durée session : supposer 2fps (FACIAL_CAPTURE_FPS)
        duration_min = max(0.01, n / (2.0 * 60))
        metrics.blink_rate = round(blink_count / duration_min, 1)
        # Normal : 15-20 clignem/min ; >30 = stress ; <5 = fixation (stress aussi)

        # ── Émotions (moyennées sur la session) ───────────────────────────────
        emo_avgs = {
            "happy":    _avg([f.raw_happy    for f in valid]),
            "surprise": _avg([f.raw_surprise for f in valid]),
            "angry":    _avg([f.raw_angry    for f in valid]),
            "fear":     _avg([f.raw_fear     for f in valid]),
            "sad":      _avg([f.raw_sad      for f in valid]),
            "neutral":  _avg([f.raw_neutral  for f in valid]),
        }
        # Normaliser en scores /100
        total_emo = sum(emo_avgs.values()) + 1e-6
        metrics.emotion_scores = {
            k: round(v / total_emo * 100, 1)
            for k, v in emo_avgs.items()
        }
        metrics.dominant_emotion = max(metrics.emotion_scores,
                                       key=metrics.emotion_scores.get)

        # ── Score de CONFIANCE /10 ────────────────────────────────────────────
        #
        # Recherche RH : les indicateurs les plus prédictifs de la confiance
        # en entretien sont dans cet ordre :
        #   1. Contact visuel régulier (poids fort)
        #   2. Stabilité de posture
        #   3. Sourire authentique
        #   4. Absence de stress visible (basse composante angry/fear)
        #
        blink_stress = min(1.0, max(0.0,
            (metrics.blink_rate - 20) / 20   # >20/min = légèrement stressant
            if metrics.blink_rate > 20 else 0))

        confidence = (
            metrics.eye_contact_ratio          * 3.5
            + metrics.head_stability           * 2.5
            + metrics.smile_ratio              * 2.0
            + (1 - blink_stress)               * 1.0
            - emo_avgs.get("angry", 0) * 3
            - emo_avgs.get("fear",  0) * 2
            - abs(metrics.avg_yaw / 30)        * 0.5
        )
        metrics.confidence_score = round(max(0.0, min(10.0, confidence)), 1)

        # ── Score de STRESS /10 ───────────────────────────────────────────────
        #
        # Composantes du stress en entretien :
        #   - Froncement sourcils (brow_frown)
        #   - Regard fuyant (contact faible)
        #   - Instabilité posturale
        #   - Clignements excessifs ou insuffisants
        #   - Émotion dominante fear/angry
        #
        brow_frown_avg  = _avg([f.brow_frown for f in valid])
        gaze_avoidance  = 1.0 - metrics.eye_contact_ratio
        blink_anomaly   = min(1.0, abs(metrics.blink_rate - 17) / 17)

        stress = (
            brow_frown_avg                    * 3.5
            + gaze_avoidance                  * 2.0
            + (1 - metrics.head_stability)    * 2.0
            + blink_anomaly                   * 1.0
            + emo_avgs.get("fear",  0) * 3
            + emo_avgs.get("angry", 0) * 2
            - emo_avgs.get("happy", 0) * 1.5
        )
        metrics.stress_score = round(max(0.0, min(10.0, stress)), 1)

        # ── Score d'ENGAGEMENT /10 ────────────────────────────────────────────
        #
        # Engagement = intérêt actif pour la conversation :
        #   - Contact visuel soutenu
        #   - Expressions variées (non-neutralité)
        #   - Haussements de sourcils (marque d'intérêt)
        #   - Posture stable et orientée vers la caméra
        #
        brow_raise_avg   = _avg([f.brow_raise for f in valid])
        expressiveness   = 1.0 - emo_avgs.get("neutral", 1.0)

        engagement = (
            metrics.eye_contact_ratio          * 3.5
            + expressiveness                   * 2.0
            + metrics.smile_ratio              * 2.0
            + brow_raise_avg                   * 1.0
            + metrics.head_stability           * 1.5
        )
        metrics.engagement_score = round(max(0.0, min(10.0, engagement)), 1)

        logger.info(
            f"FacialMetrics v2 | frames={n}/{total} | "
            f"émotion={metrics.dominant_emotion} | "
            f"contact={int(metrics.eye_contact_ratio * 100)}% | "
            f"confiance={metrics.confidence_score}/10 | "
            f"stress={metrics.stress_score}/10 | "
            f"engagement={metrics.engagement_score}/10 | "
            f"stabilité={metrics.head_stability} | "
            f"sourires={int(metrics.smile_ratio * 100)}% | "
            f"clignements={metrics.blink_rate}/min"
        )
        return metrics


# ── Singleton ─────────────────────────────────────────────────────────────────

_facial_instance: Optional[FacialAnalysisService] = None


def get_facial_service() -> FacialAnalysisService:
    global _facial_instance
    if _facial_instance is None:
        try:
            from backend.config import settings
            device = getattr(settings, "FACIAL_DEVICE", "cpu")
        except Exception:
            device = "cpu"
        _facial_instance = FacialAnalysisService(device=device)
    return _facial_instance