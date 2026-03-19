"""
Service d'analyse du langage corporel facial — SparkHire AI  
====================================================================
Installation :
  pip install timm==0.9.2
  pip install hsemotion efficientnet_pytorch
  pip install mediapipe==0.10.14
  pip install "protobuf>=4.25.3,<5.0.0"
"""

from __future__ import annotations

# ═══════════════════════════════════════════════════════════════════════════
# IMPORT MEDIAPIPE EN PREMIER — critique pour l'ordre de chargement protobuf
# ═══════════════════════════════════════════════════════════════════════════
import sys
import types as _types

for _m in [
    "mediapipe.tasks", "mediapipe.tasks.python",
    "mediapipe.tasks.python.audio", "mediapipe.tasks.python.core",
    "mediapipe.tasks.python.vision", "mediapipe.tasks.python.text",
]:
    if _m not in sys.modules:
        sys.modules[_m] = _types.ModuleType(_m)

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
logger.setLevel(logging.DEBUG)
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")

# ── Constantes ────────────────────────────────────────────────────────────────
_EAR_BLINK_THRESHOLD   = 0.22
_IRIS_CONTACT_X        = 0.45
_IRIS_CONTACT_Y        = 0.40
_EYE_CONTACT_MAX_YAW   = 25.0
_EYE_CONTACT_MAX_PITCH = 20.0
MAX_FRAMES_TO_ANALYZE  = 25

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
#  EMOTION BACKENDS
# ═════════════════════════════════════════════════════════════════════════════

class _EmotionBackend:
    name: str = "base"

    def predict(self, face_bgr: np.ndarray) -> dict[str, float] | None:
        raise NotImplementedError

    def predict_batch(self, faces_bgr: list[np.ndarray]) -> list[dict[str, float] | None]:
        return [self.predict(f) for f in faces_bgr]

    @property
    def source_label(self) -> str:
        return self.name


class _HSEmotionBackend(_EmotionBackend):
    """
    HSEmotion EfficientNet entraîné sur AffectNet8 / AFEW.
    ~82% de précision vs ~73% pour DeepFace VGG.

    Prérequis OBLIGATOIRES :
      pip install timm==0.9.2           ← 0.6.13 manque timm.layers
      pip install efficientnet_pytorch  ← requis par enet_b0_8_best_afew
      pip install hsemotion

    Ordre de tentative : enet_b0_8_best_afew → enet_b2_8_best_vgaf
    """
    name = "hsemotion_efficientnet"

    _IDX_MAP = [
        "angry",    # 0
        "disgust",  # 1 contempt → disgust
        "disgust",  # 2
        "fear",     # 3
        "happy",    # 4
        "neutral",  # 5
        "sad",      # 6
        "surprise", # 7
    ]
    _KEYS7 = ["angry", "disgust", "fear", "happy", "neutral", "sad", "surprise"]

    _MODEL_CANDIDATES = [
        "enet_b0_8_best_afew",   # léger, in-the-wild (recommandé)
        "enet_b2_8_best_vgaf",   # plus lourd, AffectNet
    ]

    def __init__(self, device: str = "cpu"):
        import torch
        from hsemotion.facial_emotions import HSEmotionRecognizer

        self._device = "cuda" if (device == "cuda" and torch.cuda.is_available()) else "cpu"
        self._fer = None
        self._model_name = None

        last_err = None
        for model_name in self._MODEL_CANDIDATES:
            try:
                self._fer = HSEmotionRecognizer(model_name=model_name, device=self._device)
                self._model_name = model_name
                logger.info(
                    f"HSEmotion | modèle={model_name} | "
                    f"device={self._device.upper()} | chargé avec succès"
                )
                break
            except Exception as e:
                last_err = e
                logger.warning(f"HSEmotion modèle '{model_name}' échoué : {type(e).__name__}: {e}")
                continue

        if self._fer is None:
            raise ImportError(
                f"Aucun modèle HSEmotion disponible. "
                f"Dernière erreur : {type(last_err).__name__}: {last_err}\n"
                f"Fix : pip install timm==0.9.2 efficientnet_pytorch"
            )

    def predict(self, face_bgr: np.ndarray) -> dict[str, float] | None:
        if face_bgr is None or face_bgr.size == 0:
            return None
        try:
            _, scores = self._fer.predict_emotions(face_bgr, logits=False)
            return self._scores_to_dict(scores)
        except Exception as e:
            logger.debug(f"HSEmotion predict : {e}")
            return None

    def predict_batch(self, faces_bgr: list[np.ndarray]) -> list[dict[str, float] | None]:
        if not faces_bgr:
            return []
        import torch
        results: list[dict[str, float] | None] = [None] * len(faces_bgr)
        with torch.no_grad():
            for i, face in enumerate(faces_bgr):
                if face is None or face.size == 0:
                    continue
                try:
                    _, scores = self._fer.predict_emotions(face, logits=False)
                    results[i] = self._scores_to_dict(scores)
                except Exception as e:
                    logger.debug(f"HSEmotion predict [{i}] : {e}")
                    results[i] = None
        return results

    def _scores_to_dict(self, scores: np.ndarray) -> dict[str, float]:
        merged: dict[str, float] = {k: 0.0 for k in self._KEYS7}
        for i, key in enumerate(self._IDX_MAP):
            merged[key] += float(scores[i])
        total = sum(merged.values()) + 1e-6
        return {k: v / total for k, v in merged.items()}

    @property
    def source_label(self) -> str:
        return f"hsemotion_{self._model_name}_{self._device}"


class _DeepFaceBackend(_EmotionBackend):
    name = "deepface_vgg"

    def __init__(self):
        from deepface import DeepFace
        self._df = DeepFace
        logger.info("DeepFace VGG disponible (fallback — précision≈73%)")

    def warmup(self) -> bool:
        try:
            dummy = np.full((48, 48, 3), 128, dtype=np.uint8)
            self._df.analyze(
                dummy, actions=["emotion"],
                detector_backend="skip",
                enforce_detection=False, silent=True,
            )
            logger.info("DeepFace CNN | poids chargés (warm-up)")
            return True
        except Exception as e:
            logger.warning(f"DeepFace warm-up : {e}")
            return False

    def predict(self, face_bgr: np.ndarray) -> dict[str, float] | None:
        if face_bgr is None or face_bgr.size == 0:
            return None
        try:
            res   = self._df.analyze(
                face_bgr, actions=["emotion"],
                detector_backend="skip",
                enforce_detection=False, silent=True,
            )
            raw   = res[0]["emotion"]
            total = sum(raw.values()) + 1e-6
            return {k.lower(): v / total for k, v in raw.items()}
        except Exception as e:
            logger.debug(f"DeepFace predict : {e}")
            return None

    @property
    def source_label(self) -> str:
        return "deepface_vgg"


class _FACSBackend(_EmotionBackend):
    name = "facs_heuristic"

    def predict(self, face_bgr: np.ndarray) -> dict[str, float] | None:
        return None

    @property
    def source_label(self) -> str:
        return "heuristic"


# ═════════════════════════════════════════════════════════════════════════════
#  SERVICE PRINCIPAL
# ═════════════════════════════════════════════════════════════════════════════

class FacialAnalysisService:

    def __init__(self, device: str = "cpu"):
        self.device       = device
        self._mp_ready    = False
        self._face_mesh   = None

        self._emotion_backend: _EmotionBackend = _FACSBackend()
        self._df_backend: Optional[_DeepFaceBackend] = None

        self._init_mediapipe()
        self._init_emotion_backend(device)

    # ── Initialisations ───────────────────────────────────────────────────────

    def _init_mediapipe(self):
        try:
            mp = _mp_preloaded or __import__("mediapipe")
            self._face_mesh = mp.solutions.face_mesh.FaceMesh(
                static_image_mode=False,
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            self._mp_ready = True
            logger.info(
                "MediaPipe FaceMesh v5 | 478 landmarks + iris | "
                "EAR + solvePnP + iris gaze | CPU"
            )
        except ImportError:
            logger.warning("mediapipe non installé → pip install mediapipe==0.10.14")
        except Exception as e:
            logger.error(f"MediaPipe init : {e}")

    def _init_emotion_backend(self, device: str):
        # Priorité 1 : HSEmotion (requiert timm==0.6.13)
        try:
            self._emotion_backend = _HSEmotionBackend(device=device)
            return
        except ImportError as e:
            logger.warning(
                f"HSEmotion ImportError : {e}\n"
                f"  Fix : pip install timm==0.9.2 efficientnet_pytorch hsemotion\n"
                f"  Fallback : DeepFace VGG (~73%)"
            )
        except Exception as e:
            logger.warning(f"HSEmotion init échoué ({type(e).__name__}: {e}) → fallback DeepFace")

        # Priorité 2 : DeepFace
        try:
            backend = _DeepFaceBackend()
            self._df_backend      = backend
            self._emotion_backend = backend
            return
        except ImportError:
            logger.warning(
                "DeepFace non installé → pip install deepface tf-keras\n"
                "  Fallback : FACS heuristiques"
            )
        except Exception as e:
            logger.warning(f"DeepFace init échoué ({e}) → FACS heuristiques")

        # Priorité 3 : FACS (déjà défaut)
        logger.warning("Mode minimal : émotions FACS heuristiques uniquement")

    def warmup_deepface(self) -> bool:
        if isinstance(self._emotion_backend, _HSEmotionBackend):
            try:
                dummy = np.full((64, 64, 3), 128, dtype=np.uint8)
                self._emotion_backend.predict(dummy)
                logger.info(
                    f"HSEmotion warm-up OK | "
                    f"device={self._emotion_backend._device.upper()}"
                )
                return True
            except Exception as e:
                logger.warning(f"HSEmotion warm-up : {e}")
                return False

        if self._df_backend:
            return self._df_backend.warmup()

        return False

    @property
    def is_available(self) -> bool:
        return self._mp_ready or not isinstance(self._emotion_backend, _FACSBackend)

    @property
    def status(self) -> dict:
        is_hsemotion = isinstance(self._emotion_backend, _HSEmotionBackend)
        is_deepface  = isinstance(self._emotion_backend, _DeepFaceBackend)
        return {
            "mediapipe":       self._mp_ready,
            "deepface":        is_deepface,
            "hsemotion":       is_hsemotion,
            "device":          self.device,
            "emotion_backend": self._emotion_backend.source_label,
            "full_pipeline":   self._mp_ready and not isinstance(self._emotion_backend, _FACSBackend),
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
        return math.sqrt((lm[a].x - lm[b].x) ** 2 + (lm[a].y - lm[b].y) ** 2)

    @staticmethod
    def _head_pose(lm, img_w, img_h):
        """
        Calcule les angles de pose de tête (yaw, pitch, roll) via solvePnP.
        """
        try:
            import cv2
            img_pts = np.array(
                [[lm[i].x * img_w, lm[i].y * img_h] for i in _MODEL_LM_IDX],
                dtype=np.float64,
            )
            focal   = float(img_w)
            cam_mat = np.array(
                [[focal, 0, img_w / 2], [0, focal, img_h / 2], [0, 0, 1]],
                dtype=np.float64,
            )
            ok, rvec, tvec = cv2.solvePnP(
                _MODEL_POINTS_3D, img_pts, cam_mat, np.zeros((4, 1)),
                flags=cv2.SOLVEPNP_ITERATIVE,
            )
            if not ok:
                return 0.0, 0.0, 0.0

            rmat, _ = cv2.Rodrigues(rvec)
            _, _, _, _, _, _, euler = cv2.decomposeProjectionMatrix(
                np.hstack((rmat, tvec))
            )

            yaw   = float(euler[1, 0])
            pitch = float(euler[0, 0])
            roll  = float(euler[2, 0])

            # ── Normalisation angles ───────────────────────────────
            # decomposeProjectionMatrix peut retourner pitch ≈ ±165–180° pour
            # un visage de face (valeur attendue ≈ 0°).
            # On ramène yaw et pitch dans [-90, +90].
            if pitch > 90:
                pitch -= 180
            elif pitch < -90:
                pitch += 180

            if yaw > 90:
                yaw -= 180
            elif yaw < -90:
                yaw += 180
            # ──────────────────────────────────────────────────────────────────

            return yaw, pitch, roll

        except Exception:
            return 0.0, 0.0, 0.0

    # ── Émotions FACS (fallback landmark) ────────────────────────────────────

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
        mar        = abs(lm[13].y - lm[14].y) / (abs(lm[61].x - lm[291].x) + 1e-6)
        lip_tight  = max(0.0, 0.15 - mar) * 6.0
        corner_dn  = max(0.0, corner_avg - lip_mid_y) / eye_dist * 3.0
        raw = {
            "happy":    min(1.0, corner_up  * 1.5),
            "surprise": min(1.0, brow_raise * 0.6 + min(mar * 4, 0.4)),
            "angry":    min(1.0, brow_frown * 0.7 + lip_tight * 0.3),
            "fear":     min(1.0, brow_raise * 0.4 + brow_frown * 0.3 + min(mar * 3, 0.3)),
            "sad":      min(1.0, corner_dn  * 0.7 + brow_raise * 0.3),
            "disgust":  min(1.0, brow_frown * 0.5 + lip_tight * 0.5),
        }
        raw["neutral"] = max(0.0, 1.0 - sum(raw.values()) * 0.6)
        t = sum(raw.values()) + 1e-6
        return {k: v / t for k, v in raw.items()}

    # ── Crop visage depuis landmarks ──────────────────────────────────────────

    @staticmethod
    def _face_roi(frame_bgr, lm, img_w, img_h, pad=0.30):
        xs = [lm[i].x for i in range(468)]
        ys = [lm[i].y for i in range(468)]
        pw, ph = (max(xs) - min(xs)) * pad, (max(ys) - min(ys)) * pad
        x1 = max(0,     int((min(xs) - pw) * img_w))
        y1 = max(0,     int((min(ys) - ph) * img_h))
        x2 = min(img_w, int((max(xs) + pw) * img_w))
        y2 = min(img_h, int((max(ys) + ph) * img_h))
        return frame_bgr if (x2 <= x1 or y2 <= y1) else frame_bgr[y1:y2, x1:x2]

    # ── Échantillonnage ───────────────────────────────────────────────────────

    @staticmethod
    def _sample_frames(frames: list, max_n: int) -> list:
        if len(frames) <= max_n:
            return frames
        step    = len(frames) / max_n
        indices = [int(i * step) for i in range(max_n)]
        return [frames[i] for i in indices]

    # ── Mode dégradé (sans MediaPipe) ────────────────────────────────────────

    def _analyze_frame_no_landmarks(self, frame_bgr: np.ndarray) -> FrameResult:
        result = FrameResult(landmarks_available=False)
        import cv2
        gray        = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        cascade     = cv2.CascadeClassifier(cascade_path)
        faces       = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80))
        if len(faces) == 0:
            return result
        x, y, w, h = max(faces, key=lambda r: r[2] * r[3])
        face_roi    = frame_bgr[y:y + h, x:x + w]
        emo_scores  = self._emotion_backend.predict(face_roi)
        if emo_scores is None:
            return result
        result.has_face         = True
        result.emotion_angry    = emo_scores.get("angry",    0.0)
        result.emotion_disgust  = emo_scores.get("disgust",  0.0)
        result.emotion_fear     = emo_scores.get("fear",     0.0)
        result.emotion_happy    = emo_scores.get("happy",    0.0)
        result.emotion_sad      = emo_scores.get("sad",      0.0)
        result.emotion_surprise = emo_scores.get("surprise", 0.0)
        result.emotion_neutral  = emo_scores.get("neutral",  0.0)
        result.dominant_emotion = max(emo_scores, key=emo_scores.get)
        result.emotion_source   = self._emotion_backend.source_label
        return result

    # ── Analyse frame principal ───────────────────────────────────────────────

    def analyze_frame(self, frame_bgr: np.ndarray) -> FrameResult:
        import cv2

        if frame_bgr is None or frame_bgr.size == 0:
            return FrameResult()

        if not self._mp_ready:
            return self._analyze_frame_no_landmarks(frame_bgr)

        result = FrameResult()
        h, w   = frame_bgr.shape[:2]
        if w > 640:
            s         = 640 / w
            frame_bgr = cv2.resize(frame_bgr, (int(w * s), int(h * s)))
            h, w      = frame_bgr.shape[:2]

        try:
            rgb    = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            mp_res = self._face_mesh.process(rgb)
            if not mp_res.multi_face_landmarks:
                return result

            result.has_face            = True
            result.landmarks_available = True
            lm = mp_res.multi_face_landmarks[0].landmark

            # 1. Pose solvePnP (angles normalisés v5.1)
            result.yaw, result.pitch, result.roll = self._head_pose(lm, w, h)

            # 2. EAR + clignement
            result.ear_left  = self._ear(lm, 159, 145,  33, 133)
            result.ear_right = self._ear(lm, 386, 374, 263, 362)
            result.is_blink  = (result.ear_left + result.ear_right) / 2 < _EAR_BLINK_THRESHOLD

            # 3. Iris offset (métriques fines)
            ox_l, oy_l = self._iris_offset(lm, 468,  33, 133, 159, 145)
            ox_r, oy_r = self._iris_offset(lm, 473, 263, 362, 386, 374)
            result.iris_offset_x = (ox_l + ox_r) / 2
            result.iris_offset_y = (oy_l + oy_r) / 2

            # 4. Contact visuel basé sur yaw/pitch normalisés
            result.eye_contact = (
                not result.is_blink
                and abs(result.yaw)   < _EYE_CONTACT_MAX_YAW
                and abs(result.pitch) < _EYE_CONTACT_MAX_PITCH
                and abs(result.iris_offset_x) < _IRIS_CONTACT_X
            )

            logger.debug(
                f"[eye_debug] yaw={result.yaw:+.1f}° pitch={result.pitch:+.1f}° "
                f"iris_x={result.iris_offset_x:+.3f} iris_y={result.iris_offset_y:+.3f} "
                f"blink={result.is_blink} → contact={result.eye_contact}"
            )

            # 5. Bouche
            eye_dist             = self._dist(lm, 33, 263) + 1e-6
            result.mar           = abs(lm[13].y - lm[14].y) / (self._dist(lm, 61, 291) + 1e-6)
            lip_mid_y            = (lm[13].y + lm[14].y) / 2
            corner_avg           = (lm[61].y + lm[291].y) / 2
            result.lip_corner_up = max(0.0, (lip_mid_y - corner_avg) / eye_dist * 3.0)

            # 6. Sourcils
            brow_gap          = abs(lm[107].x - lm[336].x) / eye_dist
            result.brow_frown = max(0.0, min(1.0, (0.55 - brow_gap) * 5.0))
            brow_h_l          = max(0.0, lm[159].y - lm[107].y) / eye_dist
            brow_h_r          = max(0.0, lm[386].y - lm[336].y) / eye_dist
            result.brow_raise = min(1.0, (brow_h_l + brow_h_r) / 2 * 4.0)

            # 7. Cache crop pour batch inference émotions
            result._face_roi_cache = (
                self._face_roi(frame_bgr, lm, w, h) if not result.is_blink else None
            )

        except Exception as e:
            logger.debug(f"analyze_frame : {e}")

        return result

    # ── Analyse batch ─────────────────────────────────────────────────────────

    def analyze_frames_batch(self, frames_bgr: list[np.ndarray]) -> list[FrameResult]:
        """
        Pipeline optimisé :
          1. Échantillonnage max MAX_FRAMES_TO_ANALYZE frames
          2. MediaPipe sur chaque frame (CPU — séquentiel)
          3. Extraction crops visages depuis landmarks
          4. Batch inference PyTorch sur tous les crops (GPU)
          5. Injection des scores d'émotions dans les FrameResult
        """
        total = len(frames_bgr)
        if total == 0:
            return []

        sampled = self._sample_frames(frames_bgr, MAX_FRAMES_TO_ANALYZE)
        logger.info(
            f"Analyse faciale | total={total} frames | "
            f"analysés={len(sampled)} "
            f"(échantillonnage 1/{max(1, total // len(sampled))})"
        )

        # Étape 1 : MediaPipe (comportemental)
        frame_results: list[FrameResult] = []
        for frame in sampled:
            frame_results.append(self.analyze_frame(frame))

        # Étape 2 : Batch inference émotions
        if not isinstance(self._emotion_backend, _FACSBackend):
            valid_pairs: list[tuple[int, np.ndarray]] = []
            for i, fr in enumerate(frame_results):
                roi = getattr(fr, "_face_roi_cache", None)
                if fr.has_face and roi is not None and roi.size > 0:
                    valid_pairs.append((i, roi))
                if hasattr(fr, "_face_roi_cache"):
                    del fr._face_roi_cache

            if valid_pairs:
                indices, crops = zip(*valid_pairs)
                emo_results = self._emotion_backend.predict_batch(list(crops))

                for j, (orig_idx, _) in enumerate(valid_pairs):
                    emo = emo_results[j]
                    if emo is None:
                        # Fallback FACS si le backend a échoué pour ce frame
                        if frame_results[orig_idx].landmarks_available and self._mp_ready:
                            try:
                                import cv2
                                rgb    = cv2.cvtColor(sampled[orig_idx], cv2.COLOR_BGR2RGB)
                                mp_res = self._face_mesh.process(rgb)
                                if mp_res and mp_res.multi_face_landmarks:
                                    lm  = mp_res.multi_face_landmarks[0].landmark
                                    emo = self._emotions_facs(lm)
                            except Exception as _e:
                                logger.debug(f"FACS fallback frame {orig_idx} : {_e}")
                        if emo is None:
                            continue

                    fr = frame_results[orig_idx]
                    fr.emotion_angry    = emo.get("angry",    0.0)
                    fr.emotion_disgust  = emo.get("disgust",  0.0)
                    fr.emotion_fear     = emo.get("fear",     0.0)
                    fr.emotion_happy    = emo.get("happy",    0.0)
                    fr.emotion_sad      = emo.get("sad",      0.0)
                    fr.emotion_surprise = emo.get("surprise", 0.0)
                    fr.emotion_neutral  = emo.get("neutral",  0.0)
                    fr.dominant_emotion = max(emo, key=emo.get)
                    fr.emotion_source   = self._emotion_backend.source_label
        else:
            # FACS depuis landmarks
            for i, fr in enumerate(frame_results):
                if hasattr(fr, "_face_roi_cache"):
                    del fr._face_roi_cache
                if fr.has_face and fr.landmarks_available:
                    import cv2
                    rgb    = cv2.cvtColor(sampled[i], cv2.COLOR_BGR2RGB)
                    mp_res = self._face_mesh.process(rgb) if self._mp_ready else None
                    if mp_res and mp_res.multi_face_landmarks:
                        lm  = mp_res.multi_face_landmarks[0].landmark
                        emo = self._emotions_facs(lm)
                        fr.emotion_angry    = emo.get("angry",    0.0)
                        fr.emotion_disgust  = emo.get("disgust",  0.0)
                        fr.emotion_fear     = emo.get("fear",     0.0)
                        fr.emotion_happy    = emo.get("happy",    0.0)
                        fr.emotion_sad      = emo.get("sad",      0.0)
                        fr.emotion_surprise = emo.get("surprise", 0.0)
                        fr.emotion_neutral  = emo.get("neutral",  0.0)
                        fr.dominant_emotion = max(emo, key=emo.get)
                        fr.emotion_source   = "heuristic"

        return frame_results

    # ── Agrégation métriques ──────────────────────────────────────────────────

    def compute_metrics(self, frame_results: list[FrameResult]) -> FacialMetrics:
        total = len(frame_results)
        if total == 0:
            return FacialMetrics()

        valid = [f for f in frame_results if f.has_face]
        n     = len(valid)

        metrics = FacialMetrics(
            frames_analyzed=total,
            frames_with_face=n,
            face_detection_rate=round(n / total, 2) if total > 0 else 0.0,
        )

        if n == 0:
            return metrics

        def _avg(vals):
            return float(np.mean(vals)) if vals else 0.0

        lm_frames = sum(1 for f in valid if f.landmarks_available)
        df_frames = sum(
            1 for f in valid
            if f.emotion_source not in ("heuristic", "facs_heuristic")
        )
        metrics.behavioral_metrics_reliable = lm_frames > n * 0.5
        metrics.emotion_source = (
            self._emotion_backend.source_label
            if df_frames > n * 0.5 else "heuristic"
        )

        if metrics.behavioral_metrics_reliable:
            lm_v = [f for f in valid if f.landmarks_available]
            m    = len(lm_v)

            metrics.eye_contact_ratio = round(
                sum(1 for f in lm_v if f.eye_contact) / m, 3
            )
            yaw_v   = [f.yaw   for f in lm_v if abs(f.yaw)   < 60]
            pitch_v = [f.pitch for f in lm_v if abs(f.pitch) < 45]
            yaw_std = stdev(yaw_v)   if len(yaw_v)   > 1 else 0.0
            pit_std = stdev(pitch_v) if len(pitch_v) > 1 else 0.0
            metrics.avg_yaw        = round(_avg(yaw_v),   1)
            metrics.avg_pitch      = round(_avg(pitch_v), 1)
            metrics.head_stability = round(max(0.0, 1.0 - (yaw_std + pit_std) / 60.0), 3)
            metrics.smile_ratio    = round(
                sum(1 for f in lm_v if f.lip_corner_up > 0.25) / m, 3
            )
            blink_n        = sum(1 for f in lm_v if f.is_blink)
            # Durée estimée : ~10 fps après échantillonnage (MAX_FRAMES_TO_ANALYZE=25)
            # Clamp min à 0.1 min pour éviter taux aberrants sur courtes séquences
            dur_min        = max(0.1, m / (10.0 * 60))
            raw_blink_rate = blink_n / dur_min
            # Sous 5 frames : taux non fiable → 0.0
            metrics.blink_rate = round(raw_blink_rate, 1) if m >= 5 else 0.0
        else:
            metrics.eye_contact_ratio = 0.5
            metrics.head_stability    = 0.5
            metrics.smile_ratio       = 0.0
            metrics.blink_rate        = 0.0

        # Émotions
        emo_avgs = {
            k: _avg([getattr(f, f"emotion_{k}") for f in valid])
            for k in ("angry", "disgust", "fear", "happy", "sad", "surprise", "neutral")
        }
        t = sum(emo_avgs.values()) + 1e-6
        metrics.emotion_scores   = {k: round(v / t * 100, 1) for k, v in emo_avgs.items()}
        metrics.dominant_emotion = max(metrics.emotion_scores, key=metrics.emotion_scores.get)

        # Scores synthétiques (formules)
        #
        #   - confidence : équilibre regard / stabilité / émotions positives vs négatives
        #   - stress     : intègre sad + surprise en plus de fear/angry
        #   - engagement : pénalise sad + neutral fortement
        if metrics.behavioral_metrics_reliable:
            # Score émotionnel positif (0→1) : happy + surprise légère
            emo_positive = min(1.0, emo_avgs["happy"] * 1.2 + emo_avgs["surprise"] * 0.3)
            # Score émotionnel négatif (0→1) : angry + fear + sad + disgust
            emo_negative = min(1.0,
                emo_avgs["angry"]   * 1.0
                + emo_avgs["fear"]  * 1.0
                + emo_avgs["sad"]   * 0.8
                + emo_avgs["disgust"] * 0.5
            )
            # Pénalité neutral : neutral élevé = manque d'engagement/expressivité
            neutral_penalty = emo_avgs["neutral"] * 0.3

            metrics.confidence_score = round(max(0.0, min(10.0,
                metrics.eye_contact_ratio * 2.5   # réduit de 4.0 → 2.5
                + metrics.head_stability  * 2.0   # réduit de 3.0 → 2.0
                + emo_positive            * 2.0   # nouveau : émotions positives
                + metrics.smile_ratio     * 1.0
                + 2.5                             # base offset
                - emo_negative            * 2.5   # augmenté : émotions négatives pénalisent plus
                - neutral_penalty                 # nouveau : neutral pénalise légèrement
                - abs(metrics.avg_yaw / 45) * 0.5
            )), 1)

            brow_frown_avg = _avg([f.brow_frown for f in valid if f.landmarks_available])
            metrics.stress_score = round(max(0.0, min(10.0,
                brow_frown_avg                    * 3.5
                + (1 - metrics.head_stability)    * 2.0
                + (1 - metrics.eye_contact_ratio) * 1.0
                + emo_avgs["fear"]                * 1.5
                + emo_avgs["angry"]               * 1.0
                + emo_avgs["sad"]                 * 1.0   # sad → stress
                + emo_avgs["surprise"]            * 0.5   # surprise → stress léger
                - emo_avgs["happy"]               * 1.5
            )), 1)

            brow_raise_avg = _avg([f.brow_raise for f in valid if f.landmarks_available])
            expressiveness = 1.0 - emo_avgs.get("neutral", 1.0)
            metrics.engagement_score = round(max(0.0, min(10.0,
                metrics.eye_contact_ratio * 3.0   # réduit légèrement
                + expressiveness          * 2.0
                + metrics.smile_ratio     * 1.5
                + metrics.head_stability  * 1.5
                + brow_raise_avg          * 0.5
                + emo_avgs["happy"]       * 1.0   # happy booste engagement
                - emo_avgs["sad"]         * 1.5   # sad pénalise engagement
                - emo_avgs["disgust"]     * 1.0   # disgust pénalise engagement
            )), 1)
        else:
            expressiveness = 1.0 - emo_avgs.get("neutral", 1.0)
            metrics.confidence_score = round(max(0.0, min(10.0,
                5.0 + emo_avgs["happy"] * 3.0 - emo_avgs["angry"] * 3.0
                - emo_avgs["fear"] * 2.0 + expressiveness * 1.0
            )), 1)
            metrics.stress_score = round(max(0.0, min(10.0,
                3.0 + emo_avgs["fear"] * 4.0 + emo_avgs["angry"] * 3.0
                - emo_avgs["happy"] * 2.0
            )), 1)
            metrics.engagement_score = round(max(0.0, min(10.0,
                5.0 + expressiveness * 3.0 + emo_avgs["happy"] * 2.0
                - emo_avgs["neutral"] * 1.5
            )), 1)

        mode = "full" if metrics.behavioral_metrics_reliable else "DÉGRADÉ-emotions-only"
        logger.info(
            f"FacialMetrics v5 [{metrics.emotion_source}] [{mode}] | "
            f"frames={n}/{total} | "
            f"émotion={metrics.dominant_emotion} | "
            f"contact={'{}%'.format(int(metrics.eye_contact_ratio * 100)) if metrics.behavioral_metrics_reliable else 'N/A'} | "
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