"""
Handler WebSocket - AUDIO PCM PUR EN CHUNKS
Fix qualité audio: extrait le PCM brut du WAV avant d'envoyer les chunks.
Le client reçoit du PCM s16le 16kHz mono, jouable directement par QAudioSink.
"""

import logging
import base64
import io
import wave
import struct
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Optional

from fastapi import WebSocket, WebSocketDisconnect
from backend.config import settings
from backend.interviews.crud import InterviewSessionCRUD, JobPositionCRUD
from backend.interviews.models import Answer
from backend.websocket.connection_manager import manager

logger = logging.getLogger(__name__)

_asr_service = None
_tts_service = None
_avatar_service = None

_tts_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="tts-worker")

_WS_CLOSE_REASON_MAX_BYTES = 123
AUDIO_CHUNK_SIZE = 64 * 1024  # 64 KB de PCM par chunk


def _truncate_close_reason(reason: str) -> str:
    encoded = reason.encode("utf-8")
    if len(encoded) <= _WS_CLOSE_REASON_MAX_BYTES:
        return reason
    truncated = encoded[:_WS_CLOSE_REASON_MAX_BYTES - 1]
    return truncated.decode("utf-8", errors="ignore") + "…"


class InterviewHandler:

    def __init__(self, session_id: str, websocket: WebSocket):
        self.session_id = session_id
        self.websocket = websocket
        self.session = None
        self.position = None
        self.audio_buffer = bytearray()
        self.is_recording = False
        self.asr_service = _asr_service
        self.tts_service = _tts_service
        self.avatar_service = _avatar_service

    def _check_connected(self):
        if not manager.is_connected(self.session_id):
            raise WebSocketDisconnect(code=1006, reason="Client déconnecté")

    # ----------------------------------------------------------
    # EXTRACTION PCM + ENVOI CHUNKS
    # ----------------------------------------------------------

    @staticmethod
    def _extract_pcm_from_wav(wav_bytes: bytes) -> tuple:
        """
        Extrait les samples PCM + métadonnées de format depuis un fichier WAV.
        Parcourt le RIFF chunk tree correctement.
        Retourne: (pcm_bytes, sample_rate, channels, bits_per_sample)
        """
        import struct

        if len(wav_bytes) < 44 or wav_bytes[:4] != b'RIFF':
            # Pas un WAV → supposer PCM 22050Hz mono 16bit (défaut Coqui)
            return wav_bytes, 22050, 1, 16

        # Parcourir les chunks RIFF proprement
        sample_rate, channels, bits = 22050, 1, 16
        offset = 12  # après 'RIFF' + size + 'WAVE'

        while offset + 8 <= len(wav_bytes):
            chunk_id   = wav_bytes[offset:offset + 4]
            chunk_size = struct.unpack_from('<I', wav_bytes, offset + 4)[0]
            data_start = offset + 8

            if chunk_id == b'fmt ':
                # fmt chunk: audio_format(2) channels(2) sample_rate(4)
                #            byte_rate(4) block_align(2) bits_per_sample(2)
                if data_start + 16 <= len(wav_bytes):
                    channels    = struct.unpack_from('<H', wav_bytes, data_start + 2)[0]
                    sample_rate = struct.unpack_from('<I', wav_bytes, data_start + 4)[0]
                    bits        = struct.unpack_from('<H', wav_bytes, data_start + 14)[0]

            elif chunk_id == b'data':
                pcm_bytes = wav_bytes[data_start:]
                logger.info(
                    f"WAV → PCM: {len(wav_bytes):,}B → {len(pcm_bytes):,}B "
                    f"({sample_rate}Hz, {channels}ch, {bits}bit)"
                )
                return pcm_bytes, sample_rate, channels, bits

            # Avancer au chunk suivant (padding à 2 bytes)
            offset = data_start + chunk_size
            if chunk_size % 2 != 0:
                offset += 1

        logger.warning("Chunk 'data' introuvable dans le WAV")
        return wav_bytes, sample_rate, channels, bits

    async def _send_audio_chunked(self, audio_bytes: bytes, msg_type: str, extra_data: dict):
        """
        Extrait le PCM pur du WAV avec le vrai sample_rate,
        puis envoie les métadonnées + chunks au client.
        """
        pcm_bytes, sample_rate, channels, bits = self._extract_pcm_from_wav(audio_bytes)

        total_bytes = len(pcm_bytes)
        total_chunks = (total_bytes + AUDIO_CHUNK_SIZE - 1) // AUDIO_CHUNK_SIZE

        logger.info(
            f"Audio {msg_type}: {len(audio_bytes):,}B WAV → {total_bytes:,}B PCM "
            f"({sample_rate}Hz) → {total_chunks} chunks"
        )

        # Message principal : métadonnées EXACTES pour que le client configure QAudioSink
        msg_data = dict(extra_data)
        msg_data.update({
            "audio_mode":       "chunked",
            "audio_format":     "pcm_s16le",
            "sample_rate":      sample_rate,   # ← vrai sample rate du TTS (22050Hz)
            "channels":         channels,
            "bits_per_sample":  bits,
            "total_chunks":     total_chunks,
            "audio_size_bytes": total_bytes,
        })

        await manager.send_json(self.session_id, {
            "type": msg_type,
            "data": msg_data
        })

        # Envoyer les chunks PCM
        for i in range(total_chunks):
            self._check_connected()
            chunk = pcm_bytes[i * AUDIO_CHUNK_SIZE:(i + 1) * AUDIO_CHUNK_SIZE]
            await manager.send_json(self.session_id, {
                "type": "audio_chunk_data",
                "data": {
                    "chunk_index": i,
                    "total":       total_chunks,
                    "data":        base64.b64encode(chunk).decode("utf-8")
                }
            })
            # Yield pour ne pas bloquer la boucle asyncio
            await asyncio.sleep(0)

        # Signal de fin
        await manager.send_json(self.session_id, {
            "type": "audio_chunk_end",
            "data": {"msg_type": msg_type}
        })

        logger.info(f"✅ {total_chunks} chunks PCM envoyés pour '{msg_type}'")

    # ----------------------------------------------------------
    # TTS ASYNCHRONE (thread pool)
    # ----------------------------------------------------------

    async def _synthesize_bytes(self, text: str, language: str) -> Optional[bytes]:
        if not self.tts_service:
            return None

        loop = asyncio.get_event_loop()

        def _do():
            try:
                data = self.tts_service.synthesize(text, language=language, use_cache=True)
                return data if data else None
            except Exception as e:
                logger.error(f"TTS error: {e}")
                return None

        result = await loop.run_in_executor(_tts_executor, _do)
        if result:
            logger.info(f"TTS: {len(result):,} bytes générés")
        return result

    # ----------------------------------------------------------
    # ATTENTE FIN LECTURE AUDIO CLIENT
    # ----------------------------------------------------------

    async def _wait_for_audio_finished(self, timeout: float = 120.0):
        """
        Bloque jusqu'à recevoir {"type":"audio_finished"} du client.
        Le client l'envoie quand QAudioSink passe en IdleState (lecture terminée).
        Indispensable pour ne pas envoyer la prochaine question pendant que
        la précédente joue encore — ce qui couperait l'audio en cours.
        """
        logger.info(f"⏳ Attente audio_finished (max {int(timeout)}s)...")
        loop = asyncio.get_event_loop()
        deadline = loop.time() + timeout
        while True:
            remaining = deadline - loop.time()
            if remaining <= 0:
                logger.warning("⚠️ Timeout audio_finished — on continue sans attendre")
                return
            try:
                data = await asyncio.wait_for(
                    self.websocket.receive_json(),
                    timeout=min(remaining, 5.0)
                )
                msg_type = data.get("type")
                if msg_type == "audio_finished":
                    logger.info("✅ Client prêt (audio terminé)")
                    return
                elif msg_type == "end_interview":
                    await self._cancel_interview()
                    raise WebSocketDisconnect(code=1000, reason="Terminé par l'utilisateur")
                else:
                    logger.debug(f"Message ignoré pendant attente audio: {msg_type}")
            except asyncio.TimeoutError:
                self._check_connected()

    # ----------------------------------------------------------
    # HANDLE PRINCIPAL
    # ----------------------------------------------------------

    async def handle(self):
        try:
            logger.info(f"Handler démarré: {self.session_id}")

            if not await self._load_session():
                return

            await asyncio.sleep(0.2)
            self._check_connected()
            await self._send_welcome()

            # Attendre que le client finisse de jouer le message de bienvenue
            await self._wait_for_audio_finished(timeout=120.0)

            self._check_connected()
            await self._start_interview()
            await asyncio.sleep(0.3)

            while self.session.status == "in_progress":
                self._check_connected()
                await self._send_current_question()

                # Attendre que le client finisse de jouer la question
                await self._wait_for_audio_finished(timeout=60.0)

                self._check_connected()
                await self._wait_for_answer()

                if self.session.current_question_index + 1 >= len(self.position.questions):
                    self._check_connected()
                    await self._complete_interview()
                    break
                else:
                    self.session = InterviewSessionCRUD.increment_question_index(self.session_id)
                    await asyncio.sleep(0.3)

        except WebSocketDisconnect as e:
            logger.info(f"Déconnexion (code={e.code}): {self.session_id}")
        except Exception as e:
            logger.error(f"Erreur: {e}", exc_info=True)
            if manager.is_connected(self.session_id):
                try:
                    await self._send_error(str(e))
                except Exception:
                    pass
        finally:
            manager.disconnect(self.session_id)

    # ----------------------------------------------------------
    # SESSION
    # ----------------------------------------------------------

    async def _load_session(self) -> bool:
        try:
            session, is_valid, error_message = InterviewSessionCRUD.validate_session_access(
                self.session_id
            )
            if not is_valid:
                logger.warning(f"Session invalide: {error_message}")
                await self._send_error(error_message, "SESSION_INVALID")
                close_reason = _truncate_close_reason(error_message)
                try:
                    await self.websocket.close(code=4003, reason=close_reason)
                except Exception as e:
                    logger.warning(f"Fermeture WS: {e}")
                return False

            self.session = session
            self.position = JobPositionCRUD.get_by_id(self.session.job_position_id)
            logger.info(f"Session OK: {self.position.title} | {len(self.position.questions)} questions")
            return True

        except WebSocketDisconnect:
            raise
        except Exception as e:
            logger.error(f"Load session error: {e}", exc_info=True)
            if manager.is_connected(self.session_id):
                await self._send_error(str(e))
            return False

    # ----------------------------------------------------------
    # BIENVENUE
    # ----------------------------------------------------------

    async def _send_welcome(self):
        texts = {
            "ar": "مرحبا بك في المقابلة الصوتية. سأطرح عليك مجموعة من الأسئلة الصوتية فقط. استمع جيداً وأجب بوضوح.",
            "en": "Welcome to the voice interview. I will ask you questions in audio only. Listen carefully and answer clearly."
        }
        text = texts.get(self.session.language, texts["ar"])

        logger.info("Synthèse audio bienvenue...")
        audio_bytes = await self._synthesize_bytes(text, self.session.language)

        extra = {
            "total_questions": len(self.position.questions),
            "position_title":  self.position.title,
            "expires_at":      self.session.expires_at.isoformat(),
            "vocal_only":      True,
        }

        if audio_bytes:
            await self._send_audio_chunked(audio_bytes, "welcome", extra)
        else:
            await manager.send_json(self.session_id, {"type": "welcome", "data": extra})

        logger.info("Welcome envoyé")

    # ----------------------------------------------------------
    # DÉMARRAGE
    # ----------------------------------------------------------

    async def _start_interview(self):
        self.session = InterviewSessionCRUD.update_status(self.session_id, "in_progress")
        logger.info(f"Entretien démarré: {self.session_id}")

    # ----------------------------------------------------------
    # QUESTION
    # ----------------------------------------------------------

    async def _send_current_question(self):
        idx = self.session.current_question_index
        if idx >= len(self.position.questions):
            return

        question = self.position.questions[idx]
        text = question.question_ar if self.session.language == "ar" else question.question_en

        progress = {
            "current":    idx + 1,
            "total":      len(self.position.questions),
            "percentage": int((idx + 1) / len(self.position.questions) * 100),
        }

        logger.info(f"Question {question.order}/{len(self.position.questions)}: '{text}'")

        # Prévenir le client que l'audio est en cours de génération
        await manager.send_json(self.session_id, {
            "type": "question_loading",
            "data": {"progress": progress}
        })

        audio_bytes = await self._synthesize_bytes(text, self.session.language)

        if not audio_bytes:
            await self._send_error("Impossible de générer l'audio")
            return

        extra = {
            "order":        question.order,
            "max_duration": question.max_duration_seconds,
            "progress":     progress,
            "vocal_only":   True,
        }

        await self._send_audio_chunked(audio_bytes, "question", extra)
        logger.info(f"Question {question.order} envoyée")

    # ----------------------------------------------------------
    # ATTENTE RÉPONSE
    # ----------------------------------------------------------

    async def _wait_for_answer(self):
        self.audio_buffer.clear()
        self.is_recording = False
        answer_start_time = None

        self._check_connected()

        try:
            while True:
                data = await self.websocket.receive_json()
                msg_type = data.get("type")

                if msg_type == "audio_chunk":
                    if not self.is_recording:
                        self.is_recording = True
                        answer_start_time = datetime.utcnow()
                    audio_data = base64.b64decode(data.get("audio_data", ""))
                    self.audio_buffer.extend(audio_data)

                elif msg_type == "answer_complete":
                    logger.info(f"Réponse: {len(self.audio_buffer):,} bytes")
                    break

                elif msg_type == "end_interview":
                    await self._cancel_interview()
                    raise WebSocketDisconnect(code=1000, reason="Termine")

        except WebSocketDisconnect:
            raise
        except Exception as e:
            raise WebSocketDisconnect(code=1006, reason=str(e)[:100]) from e

        if self.audio_buffer:
            await self._process_answer(answer_start_time)

    # ----------------------------------------------------------
    # TRAITEMENT RÉPONSE
    # ----------------------------------------------------------

    async def _process_answer(self, start_time: Optional[datetime]):
        idx = self.session.current_question_index
        question = self.position.questions[idx]
        duration = (datetime.utcnow() - start_time).total_seconds() if start_time else 0.0

        audio_path = (
            settings.UPLOAD_DIR / "interviews"
            / f"answer_{self.session_id}_{question.order}.wav"
        )
        audio_path.parent.mkdir(parents=True, exist_ok=True)

        audio_bytes = self._buffer_to_wav(bytes(self.audio_buffer))
        audio_path.write_bytes(audio_bytes)

        transcript = ""
        if self.asr_service:
            try:
                loop = asyncio.get_event_loop()
                svc, lang, ab = self.asr_service, self.session.language, audio_bytes
                transcript = await loop.run_in_executor(
                    None, lambda: svc.transcribe(ab, language=lang)
                )
                logger.info(f"Transcription: '{transcript}'")
            except Exception as e:
                logger.error(f"ASR error: {e}")

        answer = Answer(
            question_order=question.order,
            question_text=(
                question.question_ar if self.session.language == "ar" else question.question_en
            ),
            transcript=transcript,
            audio_file_path=str(audio_path),
            duration_seconds=duration,
        )
        InterviewSessionCRUD.add_answer(self.session_id, answer)

        if manager.is_connected(self.session_id):
            await manager.send_json(self.session_id, {
                "type": "answer_saved",
                "data": {"duration": duration, "question_order": question.order, "saved": True},
            })

    # ----------------------------------------------------------
    # FIN
    # ----------------------------------------------------------

    async def _complete_interview(self):
        self.session = InterviewSessionCRUD.update_status(self.session_id, "completed")

        texts = {
            "ar": "شكراً لك! انتهت المقابلة. سنتواصل معك قريباً.",
            "en": "Thank you! The interview is complete. We will contact you soon."
        }
        text = texts.get(self.session.language, texts["ar"])

        audio_bytes = await self._synthesize_bytes(text, self.session.language)

        extra = {
            "total_questions": len(self.position.questions),
            "total_answers":   len(self.session.answers),
            "position_title":  self.position.title,
        }

        if audio_bytes:
            await self._send_audio_chunked(audio_bytes, "interview_completed", extra)
        else:
            await manager.send_json(self.session_id, {
                "type": "interview_completed", "data": extra
            })

    async def _cancel_interview(self):
        self.session = InterviewSessionCRUD.update_status(self.session_id, "cancelled")

    async def _send_error(self, message: str, error_type: str = "GENERAL_ERROR"):
        if not manager.is_connected(self.session_id):
            return
        try:
            await manager.send_json(self.session_id, {
                "type": "error",
                "data": {"message": message, "error_type": error_type},
            })
        except WebSocketDisconnect:
            pass

    def _buffer_to_wav(self, audio_data: bytes) -> bytes:
        output = io.BytesIO()
        with wave.open(output, "wb") as wf:
            wf.setnchannels(settings.CHANNELS)
            wf.setsampwidth(2)
            wf.setframerate(settings.SAMPLE_RATE)
            wf.writeframes(audio_data)
        return output.getvalue()


async def handle_interview_websocket(websocket: WebSocket, session_id: str):
    logger.info(f"Connexion WebSocket: {session_id}")
    await manager.connect(session_id, websocket)
    handler = InterviewHandler(session_id, websocket)
    await handler.handle()
    logger.info(f"Connexion fermée: {session_id}")