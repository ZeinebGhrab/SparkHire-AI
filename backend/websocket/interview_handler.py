"""
Handler WebSocket pour les entretiens vocaux - MODE VOCAL PUR
Les questions sont posées uniquement en audio, sans affichage de texte
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
from backend.services import get_asr_service, get_tts_service, get_avatar_service

logger = logging.getLogger(__name__)


class InterviewHandler:
    """Gestionnaire d'entretien vocal avec validation stricte - MODE VOCAL PUR"""
    
    def __init__(self, session_id: str, websocket: WebSocket):
        self.session_id = session_id
        self.websocket = websocket
        self.session = None
        self.position = None
        self.audio_buffer = bytearray()
        self.is_recording = False
        
        # Services
        try:
            self.asr_service = get_asr_service()
            self.tts_service = get_tts_service()
            self.avatar_service = get_avatar_service()
        except Exception as e:
            logger.error(f"Erreur initialisation services: {e}")
            self.asr_service = None
            self.tts_service = None
            self.avatar_service = None
    
    async def handle(self):
        """Gérer le cycle de vie de l'entretien"""
        try:
            # 1. Charger et valider la session
            is_valid = await self._load_session()
            if not is_valid:
                return
            
            # 2. Message de bienvenue
            await self._send_welcome()
            
            # 3. Démarrer l'entretien
            await self._start_interview()
            
            # 4. Boucle de questions/réponses
            while self.session.status == "in_progress":
                # Envoyer la question actuelle (VOCAL uniquement)
                await self._send_current_question()
                
                # Attendre et traiter la réponse
                await self._wait_for_answer()
                
                # Passer à la question suivante
                if self.session.current_question_index + 1 >= len(self.position.questions):
                    # Toutes les questions sont posées
                    await self._complete_interview()
                    break
                else:
                    # Question suivante
                    self.session = InterviewSessionCRUD.increment_question_index(self.session_id)
            
        except WebSocketDisconnect:
            logger.info(f"Client déconnecté: {self.session_id}")
        except Exception as e:
            logger.error(f"Erreur handler: {e}")
            await self._send_error(str(e))
        finally:
            manager.disconnect(self.session_id)
    
    async def _load_session(self) -> bool:
        """Charger et valider la session d'entretien"""
        try:
            session, is_valid, error_message = InterviewSessionCRUD.validate_session_access(self.session_id)
            
            if not is_valid:
                logger.warning(f"Accès refusé à session {self.session_id}: {error_message}")
                await self._send_error(message=error_message, error_type="SESSION_INVALID")
                await self.websocket.close(code=4003, reason=error_message)
                return False
            
            self.session = session
            self.position = JobPositionCRUD.get_by_id(self.session.job_position_id)
            
            logger.info(f"✅ Session chargée: {self.session_id}")
            logger.info(f"   Mode: VOCAL PUR (pas d'affichage texte)")
            logger.info(f"   Poste: {self.position.title}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur chargement session: {e}")
            await self._send_error(f"Erreur lors du chargement de la session: {str(e)}")
            return False
    
    async def _send_welcome(self):
        """Envoyer message de bienvenue VOCAL"""
        welcome_text_ar = "مرحبا بك في المقابلة الصوتية. سأطرح عليك مجموعة من الأسئلة الصوتية فقط. استمع جيداً وأجب بوضوح."
        welcome_text_en = "Welcome to the voice interview. I will ask you questions in audio only. Listen carefully and answer clearly."
        
        welcome_text = welcome_text_ar if self.session.language == "ar" else welcome_text_en
        
        # Générer audio de bienvenue (OBLIGATOIRE)
        audio_url = None
        if self.tts_service:
            try:
                audio_filename = f"welcome_{self.session_id}.wav"
                audio_path = settings.TTS_CACHE_DIR / audio_filename
                
                success = self.tts_service.synthesize_to_file(
                    welcome_text,
                    audio_path,
                    language=self.session.language
                )
                
                if success:
                    audio_url = f"/audio/{audio_filename}"
                    logger.info(f"🔊 Audio bienvenue généré: {audio_filename}")
            except Exception as e:
                logger.error(f"Erreur génération audio bienvenue: {e}")
        
        await manager.send_json(self.session_id, {
            "type": "welcome",
            "data": {
                "audio_url": audio_url,
                "total_questions": len(self.position.questions),
                "position_title": self.position.title,
                "expires_at": self.session.expires_at.isoformat(),
                "vocal_only": True  # Mode vocal pur activé
            }
        })
    
    async def _start_interview(self):
        """Démarrer l'entretien"""
        self.session = InterviewSessionCRUD.update_status(self.session_id, "in_progress")
        logger.info(f"🎬 Entretien VOCAL démarré: {self.session_id}")
    
    async def _send_current_question(self):
        """Envoyer la question actuelle en VOCAL uniquement"""
        question_index = self.session.current_question_index
        
        if question_index >= len(self.position.questions):
            return
        
        question = self.position.questions[question_index]
        
        # Texte de la question (pour génération TTS uniquement)
        question_text = question.question_ar if self.session.language == "ar" else question.question_en
        
        # Progression
        progress = {
            "current": question_index + 1,
            "total": len(self.position.questions),
            "percentage": int((question_index + 1) / len(self.position.questions) * 100)
        }
        
        # Générer audio de la question (OBLIGATOIRE)
        audio_url = None
        if self.tts_service:
            try:
                audio_filename = f"question_{self.session_id}_{question.order}.wav"
                audio_path = settings.TTS_CACHE_DIR / audio_filename
                
                success = self.tts_service.synthesize_to_file(
                    question_text,
                    audio_path,
                    language=self.session.language
                )
                
                if success:
                    audio_url = f"/audio/{audio_filename}"
                    logger.info(f"🔊 Audio question généré: {audio_filename}")
            except Exception as e:
                logger.error(f"❌ Erreur génération audio question: {e}")
        
        if not audio_url:
            logger.error("⚠️ ERREUR CRITIQUE: Impossible de générer l'audio de la question!")
            await self._send_error("Impossible de générer l'audio de la question")
            return
        
        # Envoyer la question SANS TEXTE (vocal uniquement)
        await manager.send_json(self.session_id, {
            "type": "question",
            "data": {
                "order": question.order,
                "max_duration": question.max_duration_seconds,
                "progress": progress,
                "audio_url": audio_url,
                "vocal_only": True  # Flag pour indiquer mode vocal pur
            }
        })
        
        logger.info(f"🎤 Question VOCALE envoyée: {question.order}/{len(self.position.questions)}")
    
    async def _wait_for_answer(self):
        """Attendre et traiter la réponse du candidat"""
        self.audio_buffer.clear()
        self.is_recording = False
        answer_start_time = None
        
        try:
            while True:
                data = await self.websocket.receive_json()
                msg_type = data.get("type")
                
                if msg_type == "audio_chunk":
                    if not self.is_recording:
                        self.is_recording = True
                        answer_start_time = datetime.utcnow()
                        logger.info("🎤 Enregistrement démarré")
                    
                    audio_data = base64.b64decode(data.get("audio_data", ""))
                    self.audio_buffer.extend(audio_data)
                
                elif msg_type == "answer_complete":
                    logger.info("⏹️ Enregistrement terminé")
                    break
                
                elif msg_type == "end_interview":
                    await self._cancel_interview()
                    raise WebSocketDisconnect()
        
        except WebSocketDisconnect:
            raise
        except Exception as e:
            logger.error(f"Erreur réception réponse: {e}")
            raise
        
        if self.audio_buffer:
            await self._process_answer(answer_start_time)
    
    async def _process_answer(self, start_time: Optional[datetime]):
        """Traiter la réponse enregistrée"""
        question_index = self.session.current_question_index
        question = self.position.questions[question_index]
        
        # Calculer durée
        duration = 0.0
        if start_time:
            duration = (datetime.utcnow() - start_time).total_seconds()
        
        # Sauvegarder l'audio
        audio_filename = f"answer_{self.session_id}_{question.order}.wav"
        audio_path = settings.UPLOAD_DIR / "interviews" / audio_filename
        audio_path.parent.mkdir(parents=True, exist_ok=True)
        
        audio_bytes = self._buffer_to_wav(bytes(self.audio_buffer))
        
        with open(audio_path, 'wb') as f:
            f.write(audio_bytes)
        
        logger.info(f"💾 Audio sauvegardé: {audio_path} ({len(audio_bytes)} bytes)")
        
        # Transcrire l'audio
        transcript = ""
        if self.asr_service:
            try:
                transcript = self.asr_service.transcribe(
                    audio_bytes,
                    language=self.session.language
                )
                logger.info(f"📝 Transcription: '{transcript}'")
            except Exception as e:
                logger.error(f"Erreur transcription: {e}")
        
        # Sauvegarder la réponse
        answer = Answer(
            question_order=question.order,
            question_text=question.question_ar if self.session.language == "ar" else question.question_en,
            transcript=transcript,
            audio_file_path=str(audio_path),
            duration_seconds=duration
        )
        
        InterviewSessionCRUD.add_answer(self.session_id, answer)
        
        # Notifier le client (SANS envoyer la transcription au client)
        await manager.send_json(self.session_id, {
            "type": "answer_saved",
            "data": {
                "duration": duration,
                "question_order": question.order,
                "saved": True
            }
        })
    
    def _buffer_to_wav(self, audio_data: bytes) -> bytes:
        """Convertir buffer audio en WAV"""
        output = io.BytesIO()
        
        with wave.open(output, 'wb') as wf:
            wf.setnchannels(settings.CHANNELS)
            wf.setsampwidth(2)
            wf.setframerate(settings.SAMPLE_RATE)
            wf.writeframes(audio_data)
        
        return output.getvalue()
    
    async def _complete_interview(self):
        """Terminer l'entretien"""
        self.session = InterviewSessionCRUD.update_status(self.session_id, "completed")
        
        message_ar = "شكراً لك! انتهت المقابلة. سنتواصل معك قريباً."
        message_en = "Thank you! The interview is complete. We will contact you soon."
        
        message = message_ar if self.session.language == "ar" else message_en
        
        # Générer audio de fin
        audio_url = None
        if self.tts_service:
            try:
                audio_filename = f"complete_{self.session_id}.wav"
                audio_path = settings.TTS_CACHE_DIR / audio_filename
                
                success = self.tts_service.synthesize_to_file(
                    message,
                    audio_path,
                    language=self.session.language
                )
                
                if success:
                    audio_url = f"/audio/{audio_filename}"
            except Exception as e:
                logger.error(f"Erreur génération audio fin: {e}")
        
        await manager.send_json(self.session_id, {
            "type": "interview_completed",
            "data": {
                "audio_url": audio_url,
                "total_questions": len(self.position.questions),
                "total_answers": len(self.session.answers),
                "position_title": self.position.title
            }
        })
        
        logger.info(f"✅ Entretien VOCAL terminé: {self.session_id}")
    
    async def _cancel_interview(self):
        """Annuler l'entretien"""
        self.session = InterviewSessionCRUD.update_status(self.session_id, "cancelled")
        logger.info(f"🚫 Entretien annulé: {self.session_id}")
    
    async def _send_error(self, message: str, error_type: str = "GENERAL_ERROR"):
        """Envoyer une erreur"""
        await manager.send_json(self.session_id, {
            "type": "error",
            "data": {
                "message": message,
                "error_type": error_type
            }
        })


async def handle_interview_websocket(websocket: WebSocket, session_id: str):
    """Point d'entrée pour gérer un WebSocket d'entretien"""
    await manager.connect(session_id, websocket)
    
    handler = InterviewHandler(session_id, websocket)
    await handler.handle()