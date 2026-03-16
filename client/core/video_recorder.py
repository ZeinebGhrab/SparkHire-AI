"""
Collecteur de frames vidéo — Client PySide6 — SparkHire AI
============================================================

Rôle :
  Capture les frames de la webcam pendant l'enregistrement audio
  et émet chaque frame encodée en JPEG (base64) pour envoi via WebSocket.

Design :
  • Tourne dans le thread Qt principal via QTimer (pas de QThread séparé)
    → évite les problèmes de thread-safety avec OpenCV sur Windows
  • Fréquence cible : 2 fps (largement suffisant pour l'analyse émotions)
    → charge réseau : ~50 Ko/s (JPEG q=70, 640×480)
  • Le serveur collecte les frames et les analyse après answer_complete
"""

import base64
import logging
from typing import Optional

import cv2
import numpy as np
from PySide6.QtCore import QObject, QTimer, Signal

logger = logging.getLogger(__name__)


class VideoFrameCollector(QObject):
    """
    Capture les frames de la webcam à intervalles réguliers.

    Signaux :
      frame_captured(bytes) → frame JPEG encodée, prête pour base64 + WebSocket
      camera_error(str)     → erreur d'ouverture ou de lecture caméra
      camera_ready(bool)    → True si la caméra a été ouverte avec succès
    """

    frame_captured = Signal(bytes)   # JPEG bytes
    camera_error   = Signal(str)
    camera_ready   = Signal(bool)

    def __init__(
        self,
        camera_index: int = 0,
        target_fps: float = 2.0,
        jpeg_quality: int = 70,
        max_width: int = 640,
        parent=None,
    ):
        super().__init__(parent)

        self.camera_index  = camera_index
        self.target_fps    = max(0.5, min(target_fps, 10.0))  # clamp 0.5–10 fps
        self.jpeg_quality  = jpeg_quality
        self.max_width     = max_width

        self._cap: Optional[cv2.VideoCapture] = None
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._capture_frame)
        self.is_capturing = False
        self._frame_count = 0

    # ── Public API ────────────────────────────────────────────────────────────

    def start_capture(self) -> bool:
        """
        Ouvre la caméra et démarre la capture périodique.
        Retourne True si la caméra est disponible.
        """
        if self.is_capturing:
            return True

        self._cap = cv2.VideoCapture(self.camera_index)

        if not self._cap.isOpened():
            msg = f"Caméra index={self.camera_index} non disponible"
            logger.warning(msg)
            self.camera_error.emit(msg)
            self.camera_ready.emit(False)
            self._cap = None
            return False

        # Configuration minimale — laisser OpenCV choisir le reste
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        # Désactiver le buffer OpenCV pour avoir toujours le frame le plus récent
        self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        interval_ms = int(1000 / self.target_fps)
        self._timer.start(interval_ms)
        self.is_capturing = True
        self._frame_count = 0

        logger.info(
            f"Caméra ouverte | index={self.camera_index} | "
            f"fps={self.target_fps} | intervalle={interval_ms}ms"
        )
        self.camera_ready.emit(True)
        return True

    def stop_capture(self):
        """Arrête la capture et libère la caméra."""
        if not self.is_capturing:
            return

        self._timer.stop()
        self.is_capturing = False

        if self._cap:
            self._cap.release()
            self._cap = None

        logger.info(
            f"Caméra fermée | frames capturés : {self._frame_count}"
        )
        self._frame_count = 0

    def is_camera_available(self, index: int = 0) -> bool:
        """Teste rapidement si une caméra est disponible (sans la bloquer)."""
        cap = cv2.VideoCapture(index)
        ok  = cap.isOpened()
        cap.release()
        return ok

    # ── Capture interne ───────────────────────────────────────────────────────

    def _capture_frame(self):
        """Appelé par QTimer — lit un frame et l'émet encodé."""
        if not self._cap or not self.is_capturing:
            return

        ret, frame = self._cap.read()
        if not ret:
            logger.warning("Lecture caméra échouée (frame vide)")
            return

        # Redimensionner si plus large que max_width
        h, w = frame.shape[:2]
        if w > self.max_width:
            scale = self.max_width / w
            frame = cv2.resize(
                frame,
                (int(w * scale), int(h * scale)),
                interpolation=cv2.INTER_AREA,
            )

        # Encoder en JPEG
        encode_params = [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality]
        success, encoded = cv2.imencode(".jpg", frame, encode_params)

        if success:
            self._frame_count += 1
            self.frame_captured.emit(encoded.tobytes())

    # ── Prévisualisation (optionnel, debug) ───────────────────────────────────

    def get_preview_pixmap(self):
        """
        Retourne un QPixmap du frame courant pour afficher
        la prévisualisation dans l'UI (si souhaité).
        Retourne None si la caméra n'est pas active.
        """
        if not self._cap or not self.is_capturing:
            return None

        ret, frame = self._cap.read()
        if not ret:
            return None

        try:
            from PySide6.QtGui import QImage, QPixmap
            rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, c = rgb.shape
            img   = QImage(rgb.data, w, h, c * w, QImage.Format_RGB888)
            return QPixmap.fromImage(img)
        except Exception as e:
            logger.debug(f"get_preview_pixmap: {e}")
            return None

    # ── Nettoyage ─────────────────────────────────────────────────────────────

    def cleanup(self):
        """Libère toutes les ressources — appeler avant fermeture de l'app."""
        self.stop_capture()