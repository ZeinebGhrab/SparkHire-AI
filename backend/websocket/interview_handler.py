"""
Handler WebSocket pour les entretiens vocaux - MODE VOCAL PUR

CORRECTIFS:
- TTS exécuté dans un thread pool (non-bloquant pour le WebSocket)
- _truncate_close_reason() corrigé (strict 123 bytes UTF-8)
- Instances globales chargées au startup
"""

import logging
import base64
import io
import wave
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

# ============================================================
# INSTANCES GLOBALES DES SERVICES
# ============================================================
_asr_service = None
_tts_service = None
_avatar_service = None

# Thread pool dédié au TTS (lourd, CPU-bound)
_tts_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="tts-worker")

_WS_CLOSE_REASON_MAX_BYTES = 123


def _truncate_close_reason(reason: str) -> str:
    """Tronquer à 123 bytes UTF-8 strict (RFC 6455)."""
    encoded = reason.encode("utf-8")
    if len(encoded) <= _WS_CLOSE_REASON_MAX_BYTES:
        return reason
    # Tronquer proprement sans couper un caractère multi-byte
    truncated = encoded[:_WS_CLOSE_REASON_MAX_BYTES - 1]
    # Décoder en ignorant les bytes invalides à la coupure
    return truncated.decode("utf-8", errors="ignore") + "…"


class InterviewHandler:
    """Gestionnaire d'entretien vocal"""

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

        if self.tts_service is None:
            logger.warning("TTS non disponible")
        if self.asr_service is None:
            logger.warning("ASR non disponible")

    # ----------------------------------------------------------
    # UTILITAIRE : vérification connexion
    # ----------------------------------------------------------

    def _check_connected(self):
        if not manager.is_connected(self.session_id):
            raise WebSocketDisconnect(code=1006, reason="Client déconnecté")

    # ----------------------------------------------------------
    # TTS ASYNCHRONE (non-bloquant)
    # ----------------------------------------------------------

    async def _synthesize_async(self, text: str, language: str) -> Optional[str]:
        """
        Synthétise l'audio dans le thread pool TTS.
        Retourne le base64 de l'audio, ou None si échec.
        Le WebSocket reste réactif pendant la synthèse.
        """
        if not self.tts_service:
            logger.error("Service TTS non disponible")
            return None

        loop = asyncio.get_event_loop()

        def _do_synthesize():
            try:
                audio_data = self.tts_service.synthesize(
                    text, language=language, use_cache=True
                )
                if audio_data and len(audio_data) > 0:
                    return base64.b64encode(audio_data).decode("utf-8")
                logger.error("TTS: audio vide retourné")
                return None
            except Exception as e:
                logger.error(f"Erreur synthèse TTS: {e}")
                return None

        try:
            result = await loop.run_in_executor(_tts_executor, _do_synthesize)
            if result:
                logger.info(f"Audio synthétisé: {len(result)} chars base64")
            return result
        except Exception as e:
            logger.error(f"Erreur run_in_executor TTS: {e}")
            return None

    # ----------------------------------------------------------
    # POINT D'ENTRÉE PRINCIPAL
    # ----------------------------------------------------------

    async def handle(self):
        try:
            logger.info(f"Démarrage handler: {self.session_id}")

            is_valid = await self._load_session()
            if not is_valid:
                return

            await asyncio.sleep(0.2)
            self._check_connected()
            await self._send_welcome()

            await asyncio.sleep(1.0)
            self._check_connected()
            await self._start_interview()

            await asyncio.sleep(0.5)

            while self.session.status == "in_progress":
                self._check_connected()
                await self._send_current_question()

                self._check_connected()
                await self._wait_for_answer()

                if self.session.current_question_index + 1 >= len(self.position.questions):
                    self._check_connected()
                    await self._complete_interview()
                    break
                else:
                    self.session = InterviewSessionCRUD.increment_question_index(
                        self.session_id
                    )
                    await asyncio.sleep(0.5)

            logger.info(f"Handler terminé: {self.session_id}")

        except WebSocketDisconnect as e:
            logger.info(f"Client déconnecté (code={e.code}): {self.session_id}")
        except Exception as e:
            logger.error(f"Erreur critique: {e}")
            import traceback
            logger.error(traceback.format_exc())
            if manager.is_connected(self.session_id):
                try:
                    await self._send_error(str(e))
                except Exception:
                    pass
        finally:
            manager.disconnect(self.session_id)

    # ----------------------------------------------------------
    # CHARGEMENT DE SESSION
    # ----------------------------------------------------------

    async def _load_session(self) -> bool:
        try:
            session, is_valid, error_message = InterviewSessionCRUD.validate_session_access(
                self.session_id
            )

            if not is_valid:
                logger.warning(f"Accès refusé: {error_message}")
                # Envoyer l'erreur complète via JSON (pas de limite)
                await self._send_error(
                    message=error_message, error_type="SESSION_INVALID"
                )
                # Fermer avec raison tronquée (max 123 bytes)
                close_reason = _truncate_close_reason(error_message)
                logger.info(f"Close reason ({len(close_reason.encode())} bytes): {close_reason}")
                try:
                    await self.websocket.close(code=4003, reason=close_reason)
                except Exception as close_err:
                    logger.warning(f"Erreur fermeture: {close_err}")
                return False

            self.session = session
            self.position = JobPositionCRUD.get_by_id(self.session.job_position_id)

            logger.info(f"Session OK: {self.session_id} | {self.position.title} | {len(self.position.questions)} questions")
            return True

        except WebSocketDisconnect:
            raise
        except Exception as e:
            logger.error(f"Erreur chargement session: {e}")
            if manager.is_connected(self.session_id):
                try:
                    await self._send_error(f"Erreur session: {str(e)}")
                except Exception:
                    pass
            return False

    # ----------------------------------------------------------
    # BIENVENUE
    # ----------------------------------------------------------

    async def _send_welcome(self):
        welcome_texts = {
            "ar": "مرحبا بك في المقابلة الصوتية. سأطرح عليك مجموعة من الأسئلة الصوتية فقط. استمع جيداً وأجب بوضوح.",
            "en": "Welcome to the voice interview. I will ask you questions in audio only. Listen carefully and answer clearly."
        }
        welcome_text = welcome_texts.get(self.session.language, welcome_texts["ar"])

        logger.info("Génération audio bienvenue (async)...")
        audio_data_b64 = await self._synthesize_async(welcome_text, self.session.language)

        await manager.send_json(self.session_id, {
            "type": "welcome",
            "data": {
                "audio_data": audio_data_b64,
                "total_questions": len(self.position.questions),
                "position_title": self.position.title,
                "expires_at": self.session.expires_at.isoformat(),
                "vocal_only": True,
            },
        })
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
        question_index = self.session.current_question_index

        if question_index >= len(self.position.questions):
            logger.warning(f"Index invalide: {question_index}")
            return

        question = self.position.questions[question_index]
        question_text = (
            question.question_ar
            if self.session.language == "ar"
            else question.question_en
        )

        logger.info(f"Question {question.order}/{len(self.position.questions)}: '{question_text}'")

        progress = {
            "current": question_index + 1,
            "total": len(self.position.questions),
            "percentage": int((question_index + 1) / len(self.position.questions) * 100),
        }

        # Envoyer d'abord un message "question_loading" pour informer le client
        await manager.send_json(self.session_id, {
            "type": "question_loading",
            "data": {"progress": progress}
        })

        logger.info("Génération audio question (async)...")
        audio_data_b64 = await self._synthesize_async(question_text, self.session.language)

        if not audio_data_b64:
            await self._send_error("Impossible de générer l'audio")
            return

        await manager.send_json(self.session_id, {
            "type": "question",
            "data": {
                "order": question.order,
                "max_duration": question.max_duration_seconds,
                "progress": progress,
                "audio_data": audio_data_b64,
                "vocal_only": True,
            },
        })
        logger.info(f"Question {question.order} envoyée")

    # ----------------------------------------------------------
    # ATTENTE DE RÉPONSE
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
                        logger.info("Enregistrement démarré")
                    audio_data = base64.b64decode(data.get("audio_data", ""))
                    self.audio_buffer.extend(audio_data)

                elif msg_type == "answer_complete":
                    logger.info(f"Enregistrement terminé: {len(self.audio_buffer)} bytes")
                    break

                elif msg_type == "end_interview":
                    await self._cancel_interview()
                    raise WebSocketDisconnect(code=1000, reason="Termine par candidat")

        except WebSocketDisconnect:
            raise
        except Exception as e:
            logger.error(f"Erreur réception: {e}")
            raise WebSocketDisconnect(code=1006, reason=str(e)[:100]) from e

        if self.audio_buffer:
            await self._process_answer(answer_start_time)

    # ----------------------------------------------------------
    # TRAITEMENT RÉPONSE
    # ----------------------------------------------------------

    async def _process_answer(self, start_time: Optional[datetime]):
        question_index = self.session.current_question_index
        question = self.position.questions[question_index]

        duration = 0.0
        if start_time:
            duration = (datetime.utcnow() - start_time).total_seconds()

        audio_filename = f"answer_{self.session_id}_{question.order}.wav"
        audio_path = settings.UPLOAD_DIR / "interviews" / audio_filename
        audio_path.parent.mkdir(parents=True, exist_ok=True)

        audio_bytes = self._buffer_to_wav(bytes(self.audio_buffer))
        with open(audio_path, "wb") as f:
            f.write(audio_bytes)

        # ASR dans thread pool (non-bloquant)
        transcript = ""
        if self.asr_service:
            try:
                loop = asyncio.get_event_loop()
                asr_svc = self.asr_service
                lang = self.session.language
                audio_b = audio_bytes
                transcript = await loop.run_in_executor(
                    None,
                    lambda: asr_svc.transcribe(audio_b, language=lang)
                )
                logger.info(f"Transcription: '{transcript}'")
            except Exception as e:
                logger.error(f"Erreur ASR: {e}")

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
                "data": {
                    "duration": duration,
                    "question_order": question.order,
                    "saved": True,
                },
            })

    # ----------------------------------------------------------
    # FIN D'ENTRETIEN
    # ----------------------------------------------------------

    async def _complete_interview(self):
        self.session = InterviewSessionCRUD.update_status(self.session_id, "completed")

        end_texts = {
            "ar": "شكراً لك! انتهت المقابلة. سنتواصل معك قريباً.",
            "en": "Thank you! The interview is complete. We will contact you soon."
        }
        message = end_texts.get(self.session.language, end_texts["ar"])

        audio_data_b64 = await self._synthesize_async(message, self.session.language)

        await manager.send_json(self.session_id, {
            "type": "interview_completed",
            "data": {
                "audio_data": audio_data_b64,
                "total_questions": len(self.position.questions),
                "total_answers": len(self.session.answers),
                "position_title": self.position.title,
            },
        })
        logger.info(f"Entretien terminé: {self.session_id}")

    async def _cancel_interview(self):
        self.session = InterviewSessionCRUD.update_status(self.session_id, "cancelled")
        logger.info(f"Entretien annulé: {self.session_id}")

    # ----------------------------------------------------------
    # ERREUR
    # ----------------------------------------------------------

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

    # ----------------------------------------------------------
    # UTILITAIRES AUDIO
    # ----------------------------------------------------------

    def _buffer_to_wav(self, audio_data: bytes) -> bytes:
        output = io.BytesIO()
        with wave.open(output, "wb") as wf:
            wf.setnchannels(settings.CHANNELS)
            wf.setsampwidth(2)
            wf.setframerate(settings.SAMPLE_RATE)
            wf.writeframes(audio_data)
        return output.getvalue()


# ============================================================
# POINT D'ENTRÉE
# ============================================================

async def handle_interview_websocket(websocket: WebSocket, session_id: str):
    logger.info(f"Nouvelle connexion WebSocket: {session_id}")
    await manager.connect(session_id, websocket)
    handler = InterviewHandler(session_id, websocket)
    await handler.handle()
    logger.info(f"Connexion terminée: {session_id}")