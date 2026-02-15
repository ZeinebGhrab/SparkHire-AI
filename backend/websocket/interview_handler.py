"""
Handler WebSocket pour les entretiens vocaux - MODE VOCAL PUR
Audio streamé directement en base64 (pas d'URLs)
VERSION COMPLÈTE ET CORRIGÉE
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
            logger.info(f"✅ Services initialisés pour session {session_id}")
        except Exception as e:
            logger.error(f"❌ Erreur initialisation services: {e}")
            self.asr_service = None
            self.tts_service = None
            self.avatar_service = None
    
    async def handle(self):
        """Gérer le cycle de vie de l'entretien"""
        try:
            logger.info(f"🎬 Démarrage handler pour session: {self.session_id}")
            
            # 1. Charger et valider la session
            is_valid = await self._load_session()
            if not is_valid:
                logger.warning(f"❌ Session invalide: {self.session_id}")
                return
            
            # ✅ Petit délai pour s'assurer que le WebSocket est prêt
            import asyncio
            await asyncio.sleep(0.2)
            
            # 2. Message de bienvenue
            logger.info("📢 Envoi message de bienvenue...")
            await self._send_welcome()
            
            # ✅ Attendre un peu avant de commencer
            await asyncio.sleep(1.0)
            
            # 3. Démarrer l'entretien
            logger.info("🚀 Démarrage de l'entretien...")
            await self._start_interview()
            
            # ✅ Attendre avant d'envoyer la première question
            await asyncio.sleep(0.5)
            
            # 4. Boucle de questions/réponses
            logger.info("🔄 Entrée dans la boucle questions/réponses")
            while self.session.status == "in_progress":
                # Envoyer la question actuelle (VOCAL uniquement)
                await self._send_current_question()
                
                # Attendre et traiter la réponse
                await self._wait_for_answer()
                
                # Passer à la question suivante
                if self.session.current_question_index + 1 >= len(self.position.questions):
                    logger.info("✅ Toutes les questions ont été posées")
                    await self._complete_interview()
                    break
                else:
                    logger.info(f"➡️ Passage à la question suivante...")
                    self.session = InterviewSessionCRUD.increment_question_index(self.session_id)
                    await asyncio.sleep(0.5)  # ✅ Pause entre questions
            
            logger.info(f"✅ Handler terminé avec succès pour: {self.session_id}")
            
        except WebSocketDisconnect:
            logger.info(f"🔌 Client déconnecté: {self.session_id}")
        except Exception as e:
            logger.error(f"❌ Erreur critique dans handler: {e}")
            import traceback
            logger.error(traceback.format_exc())
            await self._send_error(str(e))
        finally:
            manager.disconnect(self.session_id)
            logger.info(f"🔚 Nettoyage terminé pour: {self.session_id}")
    
    async def _load_session(self) -> bool:
        """Charger et valider la session d'entretien"""
        try:
            logger.info(f"🔍 Validation de la session: {self.session_id}")
            
            session, is_valid, error_message = InterviewSessionCRUD.validate_session_access(self.session_id)
            
            if not is_valid:
                logger.warning(f"❌ Accès refusé à session {self.session_id}: {error_message}")
                await self._send_error(message=error_message, error_type="SESSION_INVALID")
                await self.websocket.close(code=4003, reason=error_message)
                return False
            
            self.session = session
            self.position = JobPositionCRUD.get_by_id(self.session.job_position_id)
            
            logger.info(f"✅ Session chargée: {self.session_id}")
            logger.info(f"   Mode: VOCAL PUR (audio direct)")
            logger.info(f"   Poste: {self.position.title}")
            logger.info(f"   Langue: {self.session.language}")
            logger.info(f"   Questions: {len(self.position.questions)}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur chargement session: {e}")
            import traceback
            logger.error(traceback.format_exc())
            await self._send_error(f"Erreur lors du chargement de la session: {str(e)}")
            return False
    
    async def _send_welcome(self):
        """Envoyer message de bienvenue VOCAL avec audio direct"""
        welcome_text_ar = "مرحبا بك في المقابلة الصوتية. سأطرح عليك مجموعة من الأسئلة الصوتية فقط. استمع جيداً وأجب بوضوح."
        welcome_text_en = "Welcome to the voice interview. I will ask you questions in audio only. Listen carefully and answer clearly."
        
        welcome_text = welcome_text_ar if self.session.language == "ar" else welcome_text_en
        
        logger.info(f"🎤 Génération audio bienvenue...")
        logger.info(f"   Texte: '{welcome_text[:50]}...'")
        logger.info(f"   Langue: {self.session.language}")
        
        # ✅ Générer l'audio et l'envoyer directement en base64
        audio_data_b64 = None
        if self.tts_service:
            try:
                audio_data = self.tts_service.synthesize(
                    welcome_text,
                    language=self.session.language,
                    use_cache=True
                )
                
                if audio_data and len(audio_data) > 0:
                    audio_data_b64 = base64.b64encode(audio_data).decode('utf-8')
                    logger.info(f"✅ Audio bienvenue généré: {len(audio_data)} bytes")
                    logger.info(f"   Base64: {len(audio_data_b64)} caractères")
                else:
                    logger.error(f"❌ Audio vide ou invalide")
                    
            except Exception as e:
                logger.error(f"❌ Erreur génération audio bienvenue: {e}")
                import traceback
                logger.error(traceback.format_exc())
        else:
            logger.error(f"❌ Service TTS non disponible")
        
        message = {
            "type": "welcome",
            "data": {
                "audio_data": audio_data_b64,  # ✅ Audio direct en base64
                "total_questions": len(self.position.questions),
                "position_title": self.position.title,
                "expires_at": self.session.expires_at.isoformat(),
                "vocal_only": True
            }
        }
        
        logger.info(f"📤 Envoi message welcome (audio_data présent: {audio_data_b64 is not None})")
        await manager.send_json(self.session_id, message)
        logger.info(f"✅ Message welcome envoyé avec succès")
    
    async def _start_interview(self):
        """Démarrer l'entretien"""
        self.session = InterviewSessionCRUD.update_status(self.session_id, "in_progress")
        logger.info(f"🎬 Entretien VOCAL démarré: {self.session_id}")
    
    async def _send_current_question(self):
        """Envoyer la question actuelle en VOCAL uniquement avec audio direct"""
        question_index = self.session.current_question_index
        
        if question_index >= len(self.position.questions):
            logger.warning(f"⚠️ Index de question invalide: {question_index}")
            return
        
        question = self.position.questions[question_index]
        
        # ✅ CRITIQUE: Extraire le TEXTE complet, pas le numéro
        question_text = question.question_ar if self.session.language == "ar" else question.question_en
        
        logger.info(f"📝 Question {question.order}/{len(self.position.questions)}")
        logger.info(f"   Texte: '{question_text}'")
        logger.info(f"   Langue: {self.session.language}")
        
        # Progression
        progress = {
            "current": question_index + 1,
            "total": len(self.position.questions),
            "percentage": int((question_index + 1) / len(self.position.questions) * 100)
        }
        
        # ✅ Générer l'audio directement
        audio_data_b64 = None
        if self.tts_service:
            try:
                logger.info(f"🔊 Génération audio question...")
                
                audio_data = self.tts_service.synthesize(
                    question_text,  # ✅ Texte complet, PAS question.order
                    language=self.session.language,
                    use_cache=True
                )
                
                if audio_data and len(audio_data) > 0:
                    audio_data_b64 = base64.b64encode(audio_data).decode('utf-8')
                    logger.info(f"✅ Audio question généré: {len(audio_data)} bytes")
                    logger.info(f"   Base64: {len(audio_data_b64)} caractères")
                else:
                    logger.error(f"❌ Audio vide ou invalide")
                    
            except Exception as e:
                logger.error(f"❌ Erreur génération audio question: {e}")
                import traceback
                logger.error(traceback.format_exc())
        else:
            logger.error(f"❌ Service TTS non disponible")
        
        if not audio_data_b64:
            logger.error("⚠️ ERREUR CRITIQUE: Pas d'audio généré pour la question!")
            await self._send_error("Impossible de générer l'audio de la question")
            return
        
        message = {
            "type": "question",
            "data": {
                "order": question.order,
                "max_duration": question.max_duration_seconds,
                "progress": progress,
                "audio_data": audio_data_b64,  # ✅ Audio direct en base64
                "vocal_only": True
            }
        }
        
        logger.info(f"📤 Envoi question {question.order} avec audio direct")
        await manager.send_json(self.session_id, message)
        logger.info(f"✅ Question {question.order} envoyée avec succès")
    
    async def _wait_for_answer(self):
        """Attendre et traiter la réponse du candidat"""
        self.audio_buffer.clear()
        self.is_recording = False
        answer_start_time = None
        
        logger.info("⏳ Attente de la réponse du candidat...")
        
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
                    logger.info(f"⏹️ Enregistrement terminé: {len(self.audio_buffer)} bytes")
                    break
                
                elif msg_type == "end_interview":
                    logger.info("🛑 Demande de fin d'entretien reçue")
                    await self._cancel_interview()
                    raise WebSocketDisconnect()
        
        except WebSocketDisconnect:
            raise
        except Exception as e:
            logger.error(f"❌ Erreur réception réponse: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
        
        if self.audio_buffer:
            await self._process_answer(answer_start_time)
        else:
            logger.warning("⚠️ Aucune donnée audio reçue")
    
    async def _process_answer(self, start_time: Optional[datetime]):
        """Traiter la réponse enregistrée"""
        question_index = self.session.current_question_index
        question = self.position.questions[question_index]
        
        logger.info(f"⚙️ Traitement de la réponse à la question {question.order}")
        
        # Calculer durée
        duration = 0.0
        if start_time:
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"   Durée: {duration:.2f}s")
        
        # Sauvegarder l'audio
        audio_filename = f"answer_{self.session_id}_{question.order}.wav"
        audio_path = settings.UPLOAD_DIR / "interviews" / audio_filename
        audio_path.parent.mkdir(parents=True, exist_ok=True)
        
        audio_bytes = self._buffer_to_wav(bytes(self.audio_buffer))
        
        with open(audio_path, 'wb') as f:
            f.write(audio_bytes)
        
        logger.info(f"💾 Audio sauvegardé: {audio_path}")
        logger.info(f"   Taille: {len(audio_bytes)} bytes")
        
        # Transcrire l'audio
        transcript = ""
        if self.asr_service:
            try:
                logger.info("🔤 Transcription en cours...")
                transcript = self.asr_service.transcribe(
                    audio_bytes,
                    language=self.session.language
                )
                logger.info(f"📝 Transcription: '{transcript}'")
            except Exception as e:
                logger.error(f"❌ Erreur transcription: {e}")
                import traceback
                logger.error(traceback.format_exc())
        else:
            logger.warning("⚠️ Service ASR non disponible")
        
        # Sauvegarder la réponse
        answer = Answer(
            question_order=question.order,
            question_text=question.question_ar if self.session.language == "ar" else question.question_en,
            transcript=transcript,
            audio_file_path=str(audio_path),
            duration_seconds=duration
        )
        
        InterviewSessionCRUD.add_answer(self.session_id, answer)
        logger.info(f"✅ Réponse sauvegardée en base de données")
        
        # Notifier le client
        await manager.send_json(self.session_id, {
            "type": "answer_saved",
            "data": {
                "duration": duration,
                "question_order": question.order,
                "saved": True
            }
        })
        logger.info(f"📤 Notification 'answer_saved' envoyée")
    
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
        
        logger.info(f"🎉 Génération message de fin...")
        logger.info(f"   Texte: '{message}'")
        
        # ✅ Générer l'audio directement
        audio_data_b64 = None
        if self.tts_service:
            try:
                audio_data = self.tts_service.synthesize(
                    message,
                    language=self.session.language
                )
                
                if audio_data and len(audio_data) > 0:
                    audio_data_b64 = base64.b64encode(audio_data).decode('utf-8')
                    logger.info(f"✅ Audio fin généré: {len(audio_data)} bytes")
            except Exception as e:
                logger.error(f"❌ Erreur génération audio fin: {e}")
                import traceback
                logger.error(traceback.format_exc())
        
        await manager.send_json(self.session_id, {
            "type": "interview_completed",
            "data": {
                "audio_data": audio_data_b64,  # ✅ Audio direct
                "total_questions": len(self.position.questions),
                "total_answers": len(self.session.answers),
                "position_title": self.position.title
            }
        })
        
        logger.info(f"✅ Entretien VOCAL terminé: {self.session_id}")
        logger.info(f"   Questions posées: {len(self.position.questions)}")
        logger.info(f"   Réponses reçues: {len(self.session.answers)}")
    
    async def _cancel_interview(self):
        """Annuler l'entretien"""
        self.session = InterviewSessionCRUD.update_status(self.session_id, "cancelled")
        logger.info(f"🚫 Entretien annulé: {self.session_id}")
    
    async def _send_error(self, message: str, error_type: str = "GENERAL_ERROR"):
        """Envoyer une erreur"""
        logger.error(f"🚨 Envoi erreur au client: {error_type} - {message}")
        
        await manager.send_json(self.session_id, {
            "type": "error",
            "data": {
                "message": message,
                "error_type": error_type
            }
        })


async def handle_interview_websocket(websocket: WebSocket, session_id: str):
    """
    Point d'entrée pour gérer un WebSocket d'entretien
    
    Args:
        websocket: Connexion WebSocket
        session_id: Identifiant de session (ex: session_xxxxx)
    """
    logger.info(f"🔌 Nouvelle connexion WebSocket pour: {session_id}")
    
    await manager.connect(session_id, websocket)
    
    handler = InterviewHandler(session_id, websocket)
    await handler.handle()
    
    logger.info(f"🔚 Connexion WebSocket terminée: {session_id}")