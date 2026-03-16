"""
Moteur TTS avec Edge-TTS (Microsoft) — compatible 7.x
Voix arabes féminines de haute qualité + retry automatique sur 403
"""

import logging
import asyncio
import tempfile
import os
import threading
import time

logger = logging.getLogger(__name__)

_MAX_RETRIES = 3
_RETRY_DELAY = 1.5   # secondes de base (backoff progressif)


class EdgeTTSEngine:
    """
    Moteur TTS utilisant Edge-TTS (Microsoft) avec retry sur erreur 403 / réseau.

    Compatibilité :
      edge-tts >= 7.0  ->  rate/pitch sont des kwargs du constructeur Communicate
      edge-tts  6.x    ->  on retombe sur SSML (code de secours)
    """

    def __init__(self):
        try:
            import edge_tts
            self.edge_tts = edge_tts

            self.voices = {
                "ar": "ar-LB-LaylaNeural",
                "en": "en-US-AriaNeural",
                "fr": "fr-FR-DeniseNeural",
            }
            self.rate  = "+0%"
            self.pitch = "+0Hz"

            logger.info(" Edge-TTS initialise avec voix feminine naturelle")
            logger.info(f"   Voix arabe : {self.voices['ar']}")
            logger.info(f"   Parametres : Rate={self.rate}, Pitch={self.pitch}")

        except ImportError as e:
            logger.error(f" Import Error: {e}")
            raise ImportError("Edge-TTS non installe : pip install edge-tts")

    def synthesize(self, text: str, language: str = "ar") -> bytes:
        """Synthetiser texte en audio - jusqu'a 3 tentatives sur erreur reseau."""
        if not text or not text.strip():
            logger.error(" Texte vide fourni a Edge-TTS")
            return b""

        voice = self.voices.get(language, self.voices["ar"])

        logger.info(" Edge-TTS: Synthese avec voix feminine naturelle")
        logger.info(f"   Texte  : '{text[:100]}...'")
        logger.info(f"   Langue : {language}")
        logger.info(f"   Voix   : {voice}")

        last_error = None

        for attempt in range(1, _MAX_RETRIES + 1):
            result = {"audio": None, "error": None}

            def run_synthesis(r=result):
                try:
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        audio_data = new_loop.run_until_complete(
                            self._synthesize_async(text, voice)
                        )
                        r["audio"] = audio_data
                    finally:
                        new_loop.close()
                except Exception as e:
                    r["error"] = e

            thread = threading.Thread(target=run_synthesis)
            thread.start()
            thread.join(timeout=30)

            if thread.is_alive():
                logger.warning(f"Edge-TTS timeout tentative {attempt}/{_MAX_RETRIES}")
                last_error = TimeoutError("Timeout 30s")
                if attempt < _MAX_RETRIES:
                    time.sleep(_RETRY_DELAY)
                continue

            if result["error"]:
                last_error = result["error"]
                err_str    = str(result["error"])
                recoverable = any(
                    k in err_str
                    for k in ("403", "WebSocket", "Handshake", "ConnectionReset",
                               "aiohttp", "ClientError", "ServerDisconnectedError")
                )
                if recoverable and attempt < _MAX_RETRIES:
                    wait = _RETRY_DELAY * attempt
                    logger.warning(
                        f"Edge-TTS erreur reseau tentative {attempt}/{_MAX_RETRIES} "
                        f"- retry dans {wait:.1f}s : {err_str[:80]}"
                    )
                    time.sleep(wait)
                    continue
                logger.error(f"Edge-TTS erreur non-recuperable : {result['error']}")
                return b""

            audio_data = result["audio"]
            if audio_data and len(audio_data) > 0:
                if attempt > 1:
                    logger.info(f"Edge-TTS OK apres {attempt} tentatives")
                logger.info(f"Audio genere : {len(audio_data)} bytes")
                return audio_data

            logger.warning(f"Edge-TTS audio vide tentative {attempt}/{_MAX_RETRIES}")
            if attempt < _MAX_RETRIES:
                time.sleep(_RETRY_DELAY)

        logger.error(f"Edge-TTS echoue apres {_MAX_RETRIES} tentatives - dernier : {last_error}")
        return b""

    async def _synthesize_async(self, text: str, voice: str) -> bytes:
        """Genere l'audio dans une coroutine asyncio (compatible edge-tts 6.x et 7.x)."""
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
            tmp_path = tmp_file.name

        try:
            # edge-tts 7.x : rate / pitch directement au constructeur
            try:
                communicate = self.edge_tts.Communicate(
                    text,
                    voice,
                    rate=self.rate,
                    pitch=self.pitch,
                )
            except TypeError:
                # Fallback edge-tts 6.x (kwargs non supportes)
                communicate = self.edge_tts.Communicate(text, voice)

            await communicate.save(tmp_path)

            with open(tmp_path, "rb") as f:
                raw = f.read()

            return self._to_wav(raw)

        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

    @staticmethod
    def _to_wav(mp3_data: bytes) -> bytes:
        try:
            from pydub import AudioSegment
            import io
            seg = AudioSegment.from_mp3(io.BytesIO(mp3_data))
            buf = io.BytesIO()
            seg.export(buf, format="wav")
            return buf.getvalue()
        except Exception as e:
            logger.warning(f"Conversion WAV echouee ({e}) - renvoi MP3 brut")
            return mp3_data