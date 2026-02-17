"""
Handler WebSocket pour les entretiens vocaux - MODE VOCAL PUR

CORRECTIFS:
- Instances globales _asr_service/_tts_service/_avatar_service (chargées au startup)
- _check_connected() avant chaque étape majeure
- _truncate_close_reason() : RFC 6455 limite le close frame à 123 octets
  (résout l'erreur "control frame too long")
"""

import logging
import base64
import io
import wave
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
# Initialisées dans main.py au démarrage du serveur.
# ============================================================
_asr_service = None
_tts_service = None
_avatar_service = None

# La spec WebSocket (RFC 6455) limite les control frames à 125 octets,
# dont 2 pour le code de fermeture → max 123 octets pour la raison.
_WS_CLOSE_REASON_MAX_BYTES = 123


def _truncate_close_reason(reason: str) -> str:
    """
    Tronquer la raison de fermeture WebSocket à 123 octets UTF-8.
    Sans cette troncature, websockets lève "control frame too long"
    quand le message d'erreur est long (ex: message de session expirée).
    """
    encoded = reason.encode("utf-8")
    if len(encoded) <= _WS_CLOSE_REASON_MAX_BYTES:
        return reason
    truncated = encoded[:_WS_CLOSE_REASON_MAX_BYTES]
    return truncated.decode("utf-8", errors="ignore") + "…"


class InterviewHandler:
    """Gestionnaire d'entretien vocal - MODE VOCAL PUR"""

    def __init__(self, session_id: str, websocket: WebSocket):
        self.session_id = session_id
        self.websocket = websocket
        self.session = None
        self.position = None
        self.audio_buffer = bytearray()
        self.is_recording = False

        # Réutiliser les instances globales pré-chargées au démarrage
        self.asr_service = _asr_service
        self.tts_service = _tts_service
        self.avatar_service = _avatar_service

        if self.tts_service is None:
            logger.warning("TTS non disponible - l'audio des questions sera absent")
        if self.asr_service is None:
            logger.warning("ASR non disponible - pas de transcription")

    # ----------------------------------------------------------
    # UTILITAIRE : vérification de connexion
    # ----------------------------------------------------------

    def _check_connected(self):
        """
        Vérifie que le client est encore dans le manager.
        Lève WebSocketDisconnect si ce n'est plus le cas.
        """
        if not manager.is_connected(self.session_id):
            raise WebSocketDisconnect(code=1006, reason="Client déconnecté")

    # ----------------------------------------------------------
    # POINT D'ENTRÉE PRINCIPAL
    # ----------------------------------------------------------

    async def handle(self):
        """Gérer le cycle de vie complet de l'entretien"""
        try:
            logger.info(f"Démarrage handler pour session: {self.session_id}")

            is_valid = await self._load_session()
            if not is_valid:
                return

            import asyncio

            await asyncio.sleep(0.2)

            self._check_connected()
            logger.info("Envoi message de bienvenue...")
            await self._send_welcome()

            await asyncio.sleep(1.0)

            self._check_connected()
            logger.info("Démarrage de l'entretien...")
            await self._start_interview()

            await asyncio.sleep(0.5)

            logger.info("Entrée dans la boucle questions/réponses")
            while self.session.status == "in_progress":
                self._check_connected()
                await self._send_current_question()

                self._check_connected()
                await self._wait_for_answer()

                if self.session.current_question_index + 1 >= len(self.position.questions):
                    logger.info("Toutes les questions ont été posées")
                    self._check_connected()
                    await self._complete_interview()
                    break
                else:
                    logger.info("Passage à la question suivante...")
                    self.session = InterviewSessionCRUD.increment_question_index(
                        self.session_id
                    )
                    await asyncio.sleep(0.5)

            logger.info(f"Handler terminé avec succès pour: {self.session_id}")

        except WebSocketDisconnect as e:
            logger.info(f"Client déconnecté (code={e.code}): {self.session_id}")
        except Exception as e:
            logger.error(f"Erreur critique dans handler: {e}")
            import traceback
            logger.error(traceback.format_exc())
            if manager.is_connected(self.session_id):
                try:
                    await self._send_error(str(e))
                except Exception:
                    pass
        finally:
            manager.disconnect(self.session_id)
            logger.info(f"Nettoyage terminé pour: {self.session_id}")

    # ----------------------------------------------------------
    # CHARGEMENT DE SESSION
    # ----------------------------------------------------------

    async def _load_session(self) -> bool:
        """Charger et valider la session d'entretien"""
        try:
            logger.info(f"Validation de la session: {self.session_id}")

            session, is_valid, error_message = InterviewSessionCRUD.validate_session_access(
                self.session_id
            )

            if not is_valid:
                logger.warning(
                    f"Accès refusé à session {self.session_id}: {error_message}"
                )
                # Envoyer l'erreur complète en JSON (pas de limite de taille)
                await self._send_error(
                    message=error_message, error_type="SESSION_INVALID"
                )
                # Tronquer la raison à 123 octets pour respecter RFC 6455
                close_reason = _truncate_close_reason(error_message)
                try:
                    await self.websocket.close(code=4003, reason=close_reason)
                except Exception as close_err:
                    logger.warning(f"Erreur fermeture WebSocket: {close_err}")
                return False

            self.session = session
            self.position = JobPositionCRUD.get_by_id(self.session.job_position_id)

            logger.info(f"Session chargée: {self.session_id}")
            logger.info(f"   Poste: {self.position.title}")
            logger.info(f"   Langue: {self.session.language}")
            logger.info(f"   Questions: {len(self.position.questions)}")

            return True

        except WebSocketDisconnect:
            raise
        except Exception as e:
            logger.error(f"Erreur chargement session: {e}")
            import traceback
            logger.error(traceback.format_exc())
            if manager.is_connected(self.session_id):
                try:
                    await self._send_error(
                        f"Erreur lors du chargement de la session: {str(e)}"
                    )
                except Exception:
                    pass
            return False

    # ----------------------------------------------------------
    # BIENVENUE
    # ----------------------------------------------------------

    async def _send_welcome(self):
        """Envoyer message de bienvenue avec audio direct"""
        welcome_text_ar = (
            "مرحبا بك في المقابلة الصوتية. "
            "سأطرح عليك مجموعة من الأسئلة الصوتية فقط. "
            "استمع جيداً وأجب بوضوح."
        )
        welcome_text_en = (
            "Welcome to the voice interview. "
            "I will ask you questions in audio only. "
            "Listen carefully and answer clearly."
        )

        welcome_text = (
            welcome_text_ar if self.session.language == "ar" else welcome_text_en
        )

        logger.info("Génération audio bienvenue...")
        audio_data_b64 = self._synthesize_b64(welcome_text, self.session.language)

        message = {
            "type": "welcome",
            "data": {
                "audio_data": audio_data_b64,
                "total_questions": len(self.position.questions),
                "position_title": self.position.title,
                "expires_at": self.session.expires_at.isoformat(),
                "vocal_only": True,
            },
        }

        await manager.send_json(self.session_id, message)
        logger.info("Message welcome envoyé avec succès")

    # ----------------------------------------------------------
    # DÉMARRAGE
    # ----------------------------------------------------------

    async def _start_interview(self):
        """Passer la session en statut 'in_progress'"""
        self.session = InterviewSessionCRUD.update_status(self.session_id, "in_progress")
        logger.info(f"Entretien VOCAL démarré: {self.session_id}")

    # ----------------------------------------------------------
    # QUESTION
    # ----------------------------------------------------------

    async def _send_current_question(self):
        """Envoyer la question courante avec son audio"""
        question_index = self.session.current_question_index

        if question_index >= len(self.position.questions):
            logger.warning(f"Index de question invalide: {question_index}")
            return

        question = self.position.questions[question_index]
        question_text = (
            question.question_ar
            if self.session.language == "ar"
            else question.question_en
        )

        logger.info(f"📝 Question {question.order}/{len(self.position.questions)}")
        logger.info(f"   Texte: '{question_text}'")
        logger.info(f"   Langue: {self.session.language}")

        progress = {
            "current": question_index + 1,
            "total": len(self.position.questions),
            "percentage": int(
                (question_index + 1) / len(self.position.questions) * 100
            ),
        }

        logger.info("Génération audio question...")
        audio_data_b64 = self._synthesize_b64(question_text, self.session.language)

        if not audio_data_b64:
            logger.error("ERREUR CRITIQUE: Pas d'audio généré pour la question!")
            await self._send_error("Impossible de générer l'audio de la question")
            return

        message = {
            "type": "question",
            "data": {
                "order": question.order,
                "max_duration": question.max_duration_seconds,
                "progress": progress,
                "audio_data": audio_data_b64,
                "vocal_only": True,
            },
        }

        logger.info(f"Envoi question {question.order} avec audio direct")
        await manager.send_json(self.session_id, message)
        logger.info(f"Question {question.order} envoyée avec succès")

    # ----------------------------------------------------------
    # ATTENTE DE RÉPONSE
    # ----------------------------------------------------------

    async def _wait_for_answer(self):
        """Attendre et traiter la réponse du candidat"""
        self.audio_buffer.clear()
        self.is_recording = False
        answer_start_time = None

        self._check_connected()
        logger.info("Attente de la réponse du candidat...")

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
                    logger.info("Demande de fin d'entretien reçue")
                    await self._cancel_interview()
                    raise WebSocketDisconnect(
                        code=1000, reason="Entretien terminé par le candidat"
                    )

        except WebSocketDisconnect:
            raise
        except Exception as e:
            logger.error(f"Erreur réception réponse: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise WebSocketDisconnect(code=1006, reason=str(e)[:100]) from e

        if self.audio_buffer:
            await self._process_answer(answer_start_time)
        else:
            logger.warning("Aucune donnée audio reçue")

    # ----------------------------------------------------------
    # TRAITEMENT DE LA RÉPONSE
    # ----------------------------------------------------------

    async def _process_answer(self, start_time: Optional[datetime]):
        """Transcrire, sauvegarder et notifier pour une réponse enregistrée"""
        question_index = self.session.current_question_index
        question = self.position.questions[question_index]

        logger.info(f"Traitement de la réponse à la question {question.order}")

        duration = 0.0
        if start_time:
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"   Durée: {duration:.2f}s")

        audio_filename = f"answer_{self.session_id}_{question.order}.wav"
        audio_path = settings.UPLOAD_DIR / "interviews" / audio_filename
        audio_path.parent.mkdir(parents=True, exist_ok=True)

        audio_bytes = self._buffer_to_wav(bytes(self.audio_buffer))
        with open(audio_path, "wb") as f:
            f.write(audio_bytes)
        logger.info(f"Audio sauvegardé: {audio_path} ({len(audio_bytes)} bytes)")

        transcript = ""
        if self.asr_service:
            try:
                logger.info("Transcription en cours...")
                transcript = self.asr_service.transcribe(
                    audio_bytes, language=self.session.language
                )
                logger.info(f"Transcription: '{transcript}'")
            except Exception as e:
                logger.error(f"Erreur transcription: {e}")
        else:
            logger.warning("Service ASR non disponible - pas de transcription")

        answer = Answer(
            question_order=question.order,
            question_text=(
                question.question_ar
                if self.session.language == "ar"
                else question.question_en
            ),
            transcript=transcript,
            audio_file_path=str(audio_path),
            duration_seconds=duration,
        )
        InterviewSessionCRUD.add_answer(self.session_id, answer)
        logger.info("Réponse sauvegardée en base de données")

        if manager.is_connected(self.session_id):
            await manager.send_json(
                self.session_id,
                {
                    "type": "answer_saved",
                    "data": {
                        "duration": duration,
                        "question_order": question.order,
                        "saved": True,
                    },
                },
            )
            logger.info("Notification 'answer_saved' envoyée")

    # ----------------------------------------------------------
    # FIN D'ENTRETIEN
    # ----------------------------------------------------------

    async def _complete_interview(self):
        """Terminer l'entretien"""
        self.session = InterviewSessionCRUD.update_status(self.session_id, "completed")

        message_ar = "شكراً لك! انتهت المقابلة. سنتواصل معك قريباً."
        message_en = "Thank you! The interview is complete. We will contact you soon."
        message = message_ar if self.session.language == "ar" else message_en

        logger.info("Génération message de fin...")
        audio_data_b64 = self._synthesize_b64(message, self.session.language)

        await manager.send_json(
            self.session_id,
            {
                "type": "interview_completed",
                "data": {
                    "audio_data": audio_data_b64,
                    "total_questions": len(self.position.questions),
                    "total_answers": len(self.session.answers),
                    "position_title": self.position.title,
                },
            },
        )

        logger.info(f"Entretien VOCAL terminé: {self.session_id}")
        logger.info(f"   Questions posées: {len(self.position.questions)}")
        logger.info(f"   Réponses reçues: {len(self.session.answers)}")

    async def _cancel_interview(self):
        """Annuler l'entretien"""
        self.session = InterviewSessionCRUD.update_status(self.session_id, "cancelled")
        logger.info(f"Entretien annulé: {self.session_id}")

    # ----------------------------------------------------------
    # ENVOI D'ERREUR
    # ----------------------------------------------------------

    async def _send_error(self, message: str, error_type: str = "GENERAL_ERROR"):
        """Envoyer une erreur au client (uniquement s'il est encore connecté)"""
        if not manager.is_connected(self.session_id):
            logger.debug(f"Erreur non envoyée (client déconnecté): {error_type}")
            return

        logger.error(f"Envoi erreur au client: {error_type} - {message}")
        try:
            await manager.send_json(
                self.session_id,
                {
                    "type": "error",
                    "data": {"message": message, "error_type": error_type},
                },
            )
        except WebSocketDisconnect:
            pass

    # ----------------------------------------------------------
    # UTILITAIRES AUDIO
    # ----------------------------------------------------------

    def _synthesize_b64(self, text: str, language: str) -> Optional[str]:
        """Synthétiser du texte en audio et retourner le résultat en base64."""
        if not self.tts_service:
            logger.error("Service TTS non disponible")
            return None

        try:
            audio_data = self.tts_service.synthesize(
                text, language=language, use_cache=True
            )

            if audio_data and len(audio_data) > 0:
                b64 = base64.b64encode(audio_data).decode("utf-8")
                logger.info(
                    f"Audio synthétisé: {len(audio_data)} bytes → {len(b64)} chars base64"
                )
                return b64
            else:
                logger.error("Synthèse TTS: audio vide retourné")
                return None

        except Exception as e:
            logger.error(f"Erreur synthèse TTS: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def _buffer_to_wav(self, audio_data: bytes) -> bytes:
        """Convertir un buffer PCM brut en fichier WAV"""
        output = io.BytesIO()
        with wave.open(output, "wb") as wf:
            wf.setnchannels(settings.CHANNELS)
            wf.setsampwidth(2)
            wf.setframerate(settings.SAMPLE_RATE)
            wf.writeframes(audio_data)
        return output.getvalue()


# ============================================================
# POINT D'ENTRÉE WEBSOCKET
# ============================================================

async def handle_interview_websocket(websocket: WebSocket, session_id: str):
    """Point d'entrée pour gérer un WebSocket d'entretien"""
    logger.info(f"Nouvelle connexion WebSocket pour: {session_id}")
    await manager.connect(session_id, websocket)
    handler = InterviewHandler(session_id, websocket)
    await handler.handle()
    logger.info(f"Connexion WebSocket terminée: {session_id}")