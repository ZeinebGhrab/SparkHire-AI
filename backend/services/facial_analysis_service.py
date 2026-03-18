"""
Service d'analyse du langage corporel facial — SparkHire AI  (v4)
==================================================================

Correctifs v4 :
  1. Import mediapipe en PREMIER dans le fichier (avant deepface/tf)
     → sur Windows Python 3.11 + protobuf 4.25.8, l'ordre suffit
  2. Échantillonnage intelligent : max MAX_FRAMES_TO_ANALYZE frames
     → évite timeout sur longues réponses (178 frames × 40ms = 7s)
  3. Détecteur 'mtcnn' en mode dégradé (>opencv Haar cascade)
     → meilleure détection sur visages légèrement tournés
  4. Timeout adaptatif : 2s × min(n_frames, MAX_FRAMES) / 5
  5. Pipeline hybride complet restauré dès que MediaPipe disponible

Installation obligatoire :
  pip install mediapipe==0.10.14
  pip install "protobuf>=4.25.3,<5.0.0"   ← AVANT deepface/tensorflow
  pip install deepface tf-keras
"""

from __future__ import annotations

# ═══════════════════════════════════════════════════════════════════════════
# IMPORT MEDIAPIPE EN PREMIER — critique pour l'ordre de chargement protobuf
# Sur Windows Python 3.11 avec protobuf 4.25.8, cet ordre garantit que
# mediapipe.solutions.face_mesh se charge avant que deepface importe tf_keras.
# ═══════════════════════════════════════════════════════════════════════════
import sys
import types as _types

# Bloquer mediapipe.tasks (importe TF → conflit protobuf)
for _m in [
    "mediapipe.tasks", "mediapipe.tasks.python",
    "mediapipe.tasks.python.audio", "mediapipe.tasks.python.core",
    "mediapipe.tasks.python.vision", "mediapipe.tasks.python.text",
]:
    if _m not in sys.modules:
        sys.modules[_m] = _types.ModuleType(_m)

# Tenter de précharger mediapipe immédiatement
_mp_preloaded = None
try:
    import mediapipe as _mp
    _mp_preloaded = _mp
except Exception:
    pass
# ═══════════════════════════════════════════════════════════════════════════

import logging
import math
import os
from dataclasses import dataclass, field
from statistics import stdev
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)
os.environ.setdefault("GLOG_minloglevel", "3")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")

# ── Constantes ────────────────────────────────────────────────────────────────
_EAR_BLINK_THRESHOLD  = 0.20
_IRIS_CONTACT_X       = 0.35
_IRIS_CONTACT_Y       = 0.28
MAX_FRAMES_TO_ANALYZE = 25   # max frames analysés par DeepFace (perf)

_MODEL_POINTS_3D = np.array([
    [  0.0,    0.0,    0.0  ],
    [  0.0,  -63.6,  -12.5 ],
    [-43.3,   32.7,  -26.0 ],
    [ 43.3,   32.7,  -26.0 ],
    [-28.9,  -28.9,  -24.1 ],
    [ 28.9,  -28.9,  -24.1 ],
], dtype=np.float64)
_MODEL_LM_IDX = [4, 152, 33, 263, 61, 291]


# ═════════════════════════════════════════════════════════════════════════════
#  DATA CLASSES
# ═════════════════════════════════════════════════════════════════════════════

@dataclass
class FrameResult:
    has_face:            bool  = False
    yaw:                 float = 0.0
    pitch:               float = 0.0
    roll:                float = 0.0
    ear_left:            float = 0.0
    ear_right:           float = 0.0
    is_blink:            bool  = False
    iris_offset_x:       float = 0.0
    iris_offset_y:       float = 0.0
    eye_contact:         bool  = False
    mar:                 float = 0.0
    lip_corner_up:       float = 0.0
    brow_raise:          float = 0.0
    brow_frown:          float = 0.0
    emotion_angry:       float = 0.0
    emotion_disgust:     float = 0.0
    emotion_fear:        float = 0.0
    emotion_happy:       float = 0.0
    emotion_sad:         float = 0.0
    emotion_surprise:    float = 0.0
    emotion_neutral:     float = 0.0
    dominant_emotion:    str   = "neutral"
    emotion_source:      str   = "heuristic"
    landmarks_available: bool  = True


@dataclass
class FacialMetrics:
    dominant_emotion:            str   = "neutral"
    emotion_scores:              dict  = field(default_factory=dict)
    eye_contact_ratio:           float = 0.0
    head_stability:              float = 1.0
    smile_ratio:                 float = 0.0
    blink_rate:                  float = 0.0
    confidence_score:            float = 5.0
    stress_score:                float = 5.0
    engagement_score:            float = 5.0
    frames_analyzed:             int   = 0
    frames_with_face:            int   = 0
    face_detection_rate:         float = 0.0
    avg_yaw:                     float = 0.0
    avg_pitch:                   float = 0.0
    emotion_source:              str   = "heuristic"
    behavioral_metrics_reliable: bool  = True

    def to_dict(self) -> dict:
        return {
            "dominant_emotion":            self.dominant_emotion,
            "emotion_scores":              self.emotion_scores,
            "eye_contact_ratio":           round(self.eye_contact_ratio,  3),
            "head_stability":              round(self.head_stability,     3),
            "smile_ratio":                 round(self.smile_ratio,        3),
            "blink_rate":                  round(self.blink_rate,         1),
            "confidence_score":            round(self.confidence_score,   1),
            "stress_score":                round(self.stress_score,       1),
            "engagement_score":            round(self.engagement_score,   1),
            "frames_analyzed":             self.frames_analyzed,
            "frames_with_face":            self.frames_with_face,
            "face_detection_rate":         round(self.face_detection_rate, 2),
            "avg_yaw":                     round(self.avg_yaw,   1),
            "avg_pitch":                   round(self.avg_pitch, 1),
            "emotion_source":              self.emotion_source,
            "behavioral_metrics_reliable": self.behavioral_metrics_reliable,
        }


# ═════════════════════════════════════════════════════════════════════════════
#  SERVICE
# ═════════════════════════════════════════════════════════════════════════════

class FacialAnalysisService:

    def __init__(self, device: str = "cpu"):
        self.device       = "cpu"
        self._mp_ready    = False
        self._face_mesh   = None
        self._df_ready    = False
        self._df_analyzer = None

        self._init_mediapipe()
        self._init_deepface()

    # ── Initialisations ───────────────────────────────────────────────────────

    def _init_mediapipe(self):
        try:
            # Utiliser le module préchargé si disponible
            mp = _mp_preloaded
            if mp is None:
                import mediapipe as mp

            self._face_mesh = mp.solutions.face_mesh.FaceMesh(
                static_image_mode=False,
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            self._mp_ready = True
            logger.info(
                "✅ MediaPipe FaceMesh v4 | 478 landmarks + iris | "
                "EAR + solvePnP + iris gaze | CPU"
            )
        except ImportError:
            logger.warning(
                "mediapipe non installé\n"
                "  pip install mediapipe==0.10.14\n"
                "  pip install \"protobuf>=4.25.3,<5.0.0\""
            )
        except Exception as e:
            logger.error(
                f"MediaPipe init échoué : {e}\n"
                "  Vérifier : pip install \"protobuf>=4.25.3,<5.0.0\""
            )

    def _init_deepface(self):
        try:
            from deepface import DeepFace
            self._df_analyzer = DeepFace
            self._df_ready    = True
            logger.info(
                "DeepFace disponible | appeler warmup_deepface() au démarrage"
            )
        except ImportError:
            logger.warning(
                "DeepFace non installé → fallback heuristiques FACS\n"
                "  pip install deepface tf-keras"
            )
        except Exception as e:
            logger.error(f"DeepFace init : {e}")

    def warmup_deepface(self) -> bool:
        """
        Précharge les poids DeepFace en mémoire.
        Appeler dans lifespan() de main.py pour éviter le timeout Q1.
        """
        if not self._df_ready or self._df_analyzer is None:
            return False
        try:
            dummy = np.full((48, 48, 3), 128, dtype=np.uint8)
            self._df_analyzer.analyze(
                dummy, actions=["emotion"],
                detector_backend="skip",
                enforce_detection=False, silent=True,
            )
            logger.info("✅ DeepFace CNN Emotion | VGG ~73% AffectNet | poids chargés")
            return True
        except Exception as e:
            logger.warning(f"DeepFace warm-up : poids chargés au 1er appel ({e})")
            return False

    @property
    def is_available(self) -> bool:
        return self._mp_ready or self._df_ready

    @property
    def status(self) -> dict:
        return {
            "mediapipe":       self._mp_ready,
            "deepface":        self._df_ready,
            "device":          self.device,
            "emotion_backend": "deepface_cnn" if self._df_ready else "facs_heuristic",
            "full_pipeline":   self._mp_ready and self._df_ready,
        }

    # ── Helpers landmarks ─────────────────────────────────────────────────────

    @staticmethod
    def _ear(lm, top, bot, outer, inner) -> float:
        return abs(lm[top].y - lm[bot].y) / (abs(lm[outer].x - lm[inner].x) + 1e-6)

    @staticmethod
    def _iris_offset(lm, iris, outer, inner, top, bot):
        cx = (lm[outer].x + lm[inner].x) / 2
        cy = (lm[top].y   + lm[bot].y)   / 2
        w  = abs(lm[outer].x - lm[inner].x) + 1e-6
        return (lm[iris].x - cx) / w, (lm[iris].y - cy) / w

    @staticmethod
    def _dist(lm, a, b) -> float:
        return math.sqrt((lm[a].x-lm[b].x)**2 + (lm[a].y-lm[b].y)**2)

    @staticmethod
    def _head_pose(lm, img_w, img_h):
        try:
            import cv2
            img_pts = np.array(
                [[lm[i].x*img_w, lm[i].y*img_h] for i in _MODEL_LM_IDX],
                dtype=np.float64,
            )
            focal   = float(img_w)
            cam_mat = np.array(
                [[focal,0,img_w/2],[0,focal,img_h/2],[0,0,1]], dtype=np.float64
            )
            ok, rvec, tvec = cv2.solvePnP(
                _MODEL_POINTS_3D, img_pts, cam_mat, np.zeros((4,1)),
                flags=cv2.SOLVEPNP_ITERATIVE,
            )
            if not ok:
                return 0.0, 0.0, 0.0
            rmat, _ = cv2.Rodrigues(rvec)
            _, _, _, _, _, _, euler = cv2.decomposeProjectionMatrix(
                np.hstack((rmat, tvec))
            )
            return float(euler[1,0]), float(euler[0,0]), float(euler[2,0])
        except Exception:
            return 0.0, 0.0, 0.0

    # ── Émotions FACS (fallback) ──────────────────────────────────────────────

    @staticmethod
    def _emotions_facs(lm) -> dict[str, float]:
        eye_dist   = abs(lm[33].x - lm[263].x) + 1e-6
        lip_mid_y  = (lm[13].y + lm[14].y) / 2
        corner_avg = (lm[61].y + lm[291].y) / 2
        corner_up  = max(0.0, (lip_mid_y - corner_avg) / eye_dist * 3.0)
        brow_gap   = abs(lm[107].x - lm[336].x) / eye_dist
        brow_frown = max(0.0, min(1.0, (0.55 - brow_gap) * 5.0))
        brow_h_l   = max(0.0, lm[159].y - lm[107].y) / eye_dist
        brow_h_r   = max(0.0, lm[386].y - lm[336].y) / eye_dist
        brow_raise = min(1.0, (brow_h_l + brow_h_r) / 2 * 4.0)
        mar        = abs(lm[13].y-lm[14].y)/(abs(lm[61].x-lm[291].x)+1e-6)
        lip_tight  = max(0.0, 0.15 - mar) * 6.0
        corner_dn  = max(0.0, corner_avg - lip_mid_y) / eye_dist * 3.0
        raw = {
            "happy":    min(1.0, corner_up  * 1.5),
            "surprise": min(1.0, brow_raise * 0.6 + min(mar*4, 0.4)),
            "angry":    min(1.0, brow_frown * 0.7 + lip_tight * 0.3),
            "fear":     min(1.0, brow_raise * 0.4 + brow_frown*0.3 + min(mar*3,0.3)),
            "sad":      min(1.0, corner_dn  * 0.7 + brow_raise*0.3),
            "disgust":  min(1.0, brow_frown * 0.5 + lip_tight * 0.5),
        }
        raw["neutral"] = max(0.0, 1.0 - sum(raw.values()) * 0.6)
        t = sum(raw.values()) + 1e-6
        return {k: v/t for k, v in raw.items()}

    # ── Émotions DeepFace CNN ─────────────────────────────────────────────────

    def _emotions_deepface(self, face_roi: np.ndarray) -> dict[str, float] | None:
        if not self._df_ready or self._df_analyzer is None:
            return None
        try:
            res   = self._df_analyzer.analyze(
                face_roi, actions=["emotion"],
                detector_backend="skip",
                enforce_detection=False, silent=True,
            )
            raw   = res[0]["emotion"]
            total = sum(raw.values()) + 1e-6
            return {k.lower(): v/total for k,v in raw.items()}
        except Exception as e:
            logger.debug(f"DeepFace analyze : {e}")
            return None

    @staticmethod
    def _face_roi(frame_bgr, lm, img_w, img_h, pad=0.30):
        xs = [lm[i].x for i in range(468)]
        ys = [lm[i].y for i in range(468)]
        pw, ph = (max(xs)-min(xs))*pad, (max(ys)-min(ys))*pad
        x1 = max(0,     int((min(xs)-pw)*img_w))
        y1 = max(0,     int((min(ys)-ph)*img_h))
        x2 = min(img_w, int((max(xs)+pw)*img_w))
        y2 = min(img_h, int((max(ys)+ph)*img_h))
        return frame_bgr if (x2<=x1 or y2<=y1) else frame_bgr[y1:y2, x1:x2]

    # ── Mode dégradé DeepFace-only ────────────────────────────────────────────

    def _analyze_frame_deepface_only(self, frame_bgr: np.ndarray) -> FrameResult:
        """
        Mode dégradé sans MediaPipe.
        Utilise 'mtcnn' (meilleur que 'opencv' Haar cascade pour les visages
        légèrement tournés ou dans des conditions d'éclairage variées).
        Métriques comportementales (EAR/gaze/pose) non disponibles.
        """
        result = FrameResult(landmarks_available=False)
        if not self._df_ready or self._df_analyzer is None:
            return result
        try:
            res = self._df_analyzer.analyze(
                frame_bgr,
                actions=["emotion"],
                detector_backend="mtcnn",  # meilleur que opencv
                enforce_detection=False,
                silent=True,
            )
            if not res:
                return result
            if res[0].get("face_confidence", 0) < 0.5:
                return result

            result.has_face = True
            raw   = res[0]["emotion"]
            total = sum(raw.values()) + 1e-6
            emo   = {k.lower(): v/total for k,v in raw.items()}

            result.emotion_angry    = emo.get("angry",    0.0)
            result.emotion_disgust  = emo.get("disgust",  0.0)
            result.emotion_fear     = emo.get("fear",     0.0)
            result.emotion_happy    = emo.get("happy",    0.0)
            result.emotion_sad      = emo.get("sad",      0.0)
            result.emotion_surprise = emo.get("surprise", 0.0)
            result.emotion_neutral  = emo.get("neutral",  0.0)
            result.dominant_emotion = max(emo, key=emo.get)
            result.emotion_source   = "deepface_only"
            # Métriques comportementales neutres (non disponibles sans landmarks)
            result.eye_contact    = False
            result.is_blink       = False
            result.head_stability = 0.5

        except Exception as e:
            logger.debug(f"DeepFace-only : {e}")
        return result

    # ── Échantillonnage intelligent ───────────────────────────────────────────

    @staticmethod
    def _sample_frames(frames: list, max_n: int) -> list:
        """
        Sélectionne max_n frames répartis uniformément sur toute la séquence.
        Garantit une représentation équitable début/milieu/fin de réponse.
        """
        if len(frames) <= max_n:
            return frames
        step    = len(frames) / max_n
        indices = [int(i * step) for i in range(max_n)]
        return [frames[i] for i in indices]

    # ── Analyse principale ────────────────────────────────────────────────────

    def analyze_frame(self, frame_bgr: np.ndarray) -> FrameResult:
        """Analyse un seul frame (appelé depuis run_facial_sync)."""
        import cv2

        if frame_bgr is None or frame_bgr.size == 0:
            return FrameResult()

        if not self._mp_ready:
            return self._analyze_frame_deepface_only(frame_bgr)

        result = FrameResult()
        h, w   = frame_bgr.shape[:2]
        if w > 640:
            s         = 640 / w
            frame_bgr = cv2.resize(frame_bgr, (int(w*s), int(h*s)))
            h, w      = frame_bgr.shape[:2]

        try:
            rgb    = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            mp_res = self._face_mesh.process(rgb)
            if not mp_res.multi_face_landmarks:
                return result

            result.has_face          = True
            result.landmarks_available = True
            lm = mp_res.multi_face_landmarks[0].landmark

            # 1. Pose solvePnP
            result.yaw, result.pitch, result.roll = self._head_pose(lm, w, h)

            # 2. EAR + clignement
            result.ear_left  = self._ear(lm, 159, 145,  33, 133)
            result.ear_right = self._ear(lm, 386, 374, 263, 362)
            result.is_blink  = (result.ear_left + result.ear_right) / 2 < _EAR_BLINK_THRESHOLD

            # 3. Contact visuel iris
            ox_l, oy_l = self._iris_offset(lm, 468,  33, 133, 159, 145)
            ox_r, oy_r = self._iris_offset(lm, 473, 263, 362, 386, 374)
            result.iris_offset_x = (ox_l + ox_r) / 2
            result.iris_offset_y = (oy_l + oy_r) / 2
            result.eye_contact   = (
                abs(result.iris_offset_x) < _IRIS_CONTACT_X
                and abs(result.iris_offset_y) < _IRIS_CONTACT_Y
                and not result.is_blink
                and abs(result.yaw)   < 20
                and abs(result.pitch) < 15
            )

            # 4. Bouche
            eye_dist          = self._dist(lm, 33, 263) + 1e-6
            result.mar        = abs(lm[13].y-lm[14].y) / (self._dist(lm,61,291)+1e-6)
            lip_mid_y         = (lm[13].y + lm[14].y) / 2
            corner_avg        = (lm[61].y + lm[291].y) / 2
            result.lip_corner_up = max(0.0, (lip_mid_y - corner_avg) / eye_dist * 3.0)

            # 5. Sourcils
            brow_gap          = abs(lm[107].x - lm[336].x) / eye_dist
            result.brow_frown = max(0.0, min(1.0, (0.55 - brow_gap) * 5.0))
            brow_h_l          = max(0.0, lm[159].y - lm[107].y) / eye_dist
            brow_h_r          = max(0.0, lm[386].y - lm[336].y) / eye_dist
            result.brow_raise = min(1.0, (brow_h_l + brow_h_r) / 2 * 4.0)

            # 6. Émotions DeepFace CNN sur crop visage
            emo_scores = None
            if self._df_ready and not result.is_blink:
                roi        = self._face_roi(frame_bgr, lm, w, h)
                emo_scores = self._emotions_deepface(roi)

            if emo_scores is not None:
                result.emotion_source = "deepface"
            else:
                emo_scores            = self._emotions_facs(lm)
                result.emotion_source = "heuristic"

            result.emotion_angry    = emo_scores.get("angry",    0.0)
            result.emotion_disgust  = emo_scores.get("disgust",  0.0)
            result.emotion_fear     = emo_scores.get("fear",     0.0)
            result.emotion_happy    = emo_scores.get("happy",    0.0)
            result.emotion_sad      = emo_scores.get("sad",      0.0)
            result.emotion_surprise = emo_scores.get("surprise", 0.0)
            result.emotion_neutral  = emo_scores.get("neutral",  0.0)
            result.dominant_emotion = max(emo_scores, key=emo_scores.get)

        except Exception as e:
            logger.debug(f"analyze_frame : {e}")

        return result

    # ── Analyse d'une liste de frames avec échantillonnage ────────────────────

    def analyze_frames_batch(
        self,
        frames_bgr: list[np.ndarray],
    ) -> list[FrameResult]:
        """
        Analyse une liste de frames avec échantillonnage intelligent.
        Limite à MAX_FRAMES_TO_ANALYZE frames pour la performance.

        C'est ici que le sous-ensemble est sélectionné — puis chaque frame
        est analysé individuellement (MediaPipe n'a pas d'API batch).
        """
        total = len(frames_bgr)
        if total == 0:
            return []

        sampled = self._sample_frames(frames_bgr, MAX_FRAMES_TO_ANALYZE)
        logger.info(
            f"Analyse faciale | total={total} frames | "
            f"analysés={len(sampled)} (échantillonnage 1/{max(1, total//len(sampled))})"
        )

        results = []
        for frame in sampled:
            results.append(self.analyze_frame(frame))

        return results

    # ── Agrégation ────────────────────────────────────────────────────────────

    def compute_metrics(self, frame_results: list[FrameResult]) -> FacialMetrics:
        total = len(frame_results)
        if total == 0:
            return FacialMetrics()

        valid = [f for f in frame_results if f.has_face]
        n     = len(valid)

        metrics = FacialMetrics(
            frames_analyzed=total,
            frames_with_face=n,
            face_detection_rate=round(n/total, 2) if total > 0 else 0.0,
        )

        if n == 0:
            logger.info("Aucun visage détecté dans les frames")
            return metrics

        def _avg(vals): return float(np.mean(vals)) if vals else 0.0

        lm_frames = sum(1 for f in valid if f.landmarks_available)
        df_frames = sum(1 for f in valid if "deepface" in f.emotion_source)
        metrics.behavioral_metrics_reliable = lm_frames > n * 0.5
        metrics.emotion_source = "deepface" if df_frames > n * 0.5 else "heuristic"

        if metrics.behavioral_metrics_reliable:
            lm_v = [f for f in valid if f.landmarks_available]
            m    = len(lm_v)

            metrics.eye_contact_ratio = round(
                sum(1 for f in lm_v if f.eye_contact) / m, 3
            )
            yaw_v   = [y for y in yaw_v   if abs(y)   < 60]   # exclure les valeurs aberrantes solvePnP
            pitch_v = [p for p in pitch_v if abs(p)   < 45]
            yaw_std = stdev(yaw_v)   if len(yaw_v)   > 1 else 0.0
            pit_std = stdev(pitch_v) if len(pitch_v) > 1 else 0.0
            metrics.avg_yaw        = round(_avg(yaw_v),   1)
            metrics.avg_pitch      = round(_avg(pitch_v), 1)
            metrics.head_stability = round(max(0.0, 1.0 - (yaw_std + pit_std) / 60.0), 3)
            metrics.smile_ratio    = round(
                sum(1 for f in lm_v if f.lip_corner_up > 0.25) / m, 3
            )
            blink_n         = sum(1 for f in lm_v if f.is_blink)
            dur_min         = max(0.01, m / (2.0 * 60))
            metrics.blink_rate = round(blink_n / dur_min, 1)
        else:
            logger.warning(
                "Mode dégradé : MediaPipe indisponible — "
                "métriques comportementales non fiables "
                "(eye_contact/blink/stability)"
            )
            metrics.eye_contact_ratio = 0.5
            metrics.head_stability    = 0.5
            metrics.smile_ratio       = 0.0
            metrics.blink_rate        = 0.0

        # Émotions
        emo_avgs = {
            k: _avg([getattr(f, f"emotion_{k}") for f in valid])
            for k in ("angry","disgust","fear","happy","sad","surprise","neutral")
        }
        t = sum(emo_avgs.values()) + 1e-6
        metrics.emotion_scores   = {k: round(v/t*100,1) for k,v in emo_avgs.items()}
        metrics.dominant_emotion = max(metrics.emotion_scores, key=metrics.emotion_scores.get)

        # Scores synthétiques
        if metrics.behavioral_metrics_reliable:
            blink_stress = min(1.0, max(0.0,
                (metrics.blink_rate-20)/20 if metrics.blink_rate > 20 else 0.0))
            metrics.confidence_score = round(max(0.0, min(10.0,
                metrics.eye_contact_ratio * 3.5
                + metrics.head_stability  * 2.5
                + metrics.smile_ratio     * 2.0
                + (1 - blink_stress)      * 1.0
                - emo_avgs["angry"]       * 3.0
                - emo_avgs["fear"]        * 2.0
                - abs(metrics.avg_yaw/30) * 0.5
            )), 1)
            brow_frown_avg = _avg([f.brow_frown for f in valid if f.landmarks_available])
            blink_anomaly  = min(1.0, abs(metrics.blink_rate - 17) / 17)
            metrics.stress_score = round(max(0.0, min(10.0,
                brow_frown_avg                    * 3.5
                + (1-metrics.eye_contact_ratio)   * 2.0
                + (1-metrics.head_stability)      * 2.0
                + blink_anomaly                   * 1.0
                + emo_avgs["fear"]                * 3.0
                + emo_avgs["angry"]               * 2.0
                - emo_avgs["happy"]               * 1.5
            )), 1)
            brow_raise_avg = _avg([f.brow_raise for f in valid if f.landmarks_available])
            expressiveness = 1.0 - emo_avgs.get("neutral", 1.0)
            metrics.engagement_score = round(max(0.0, min(10.0,
                metrics.eye_contact_ratio * 3.5
                + expressiveness          * 2.0
                + metrics.smile_ratio     * 2.0
                + metrics.head_stability  * 1.5
                + brow_raise_avg          * 1.0
            )), 1)
        else:
            # Scores basés uniquement sur les émotions DeepFace
            expressiveness = 1.0 - emo_avgs.get("neutral", 1.0)
            metrics.confidence_score = round(max(0.0, min(10.0,
                5.0 + emo_avgs["happy"]*3.0 - emo_avgs["angry"]*3.0
                - emo_avgs["fear"]*2.0 + expressiveness*1.0
            )), 1)
            metrics.stress_score = round(max(0.0, min(10.0,
                3.0 + emo_avgs["fear"]*4.0 + emo_avgs["angry"]*3.0
                - emo_avgs["happy"]*2.0
            )), 1)
            metrics.engagement_score = round(max(0.0, min(10.0,
                5.0 + expressiveness*3.0 + emo_avgs["happy"]*2.0
                - emo_avgs["neutral"]*1.5
            )), 1)

        mode = "full" if metrics.behavioral_metrics_reliable else "DÉGRADÉ-emotions-only"
        logger.info(
            f"FacialMetrics v4 [{metrics.emotion_source}] [{mode}] | "
            f"frames={n}/{total} | "
            f"émotion={metrics.dominant_emotion} | "
            f"contact={'{}%'.format(int(metrics.eye_contact_ratio*100)) if metrics.behavioral_metrics_reliable else 'N/A'} | "
            f"confiance={metrics.confidence_score}/10 | "
            f"stress={metrics.stress_score}/10 | "
            f"engagement={metrics.engagement_score}/10 | "
            f"clign={'{}bpm'.format(metrics.blink_rate) if metrics.behavioral_metrics_reliable else 'N/A'} | "
            f"stab={metrics.head_stability if metrics.behavioral_metrics_reliable else 'N/A'}"
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