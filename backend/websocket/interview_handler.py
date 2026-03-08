"""
Handler WebSocket - AUDIO PCM PUR EN CHUNKS - MULTILINGUE AR/FR/EN
Pipeline : Voix → Whisper (ASR) → Llama 3 (LLM) → Score / Feedback
"""

import logging, base64, io, wave, struct, asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Optional

from fastapi import WebSocket, WebSocketDisconnect
from backend.config import settings
from backend.interviews.crud import InterviewSessionCRUD, JobPositionCRUD
from backend.interviews.models import Answer
from backend.websocket.connection_manager import manager

logger = logging.getLogger(__name__)

_asr_service    = None
_tts_service    = None
_avatar_service = None

# Thread pools séparés pour ne pas bloquer le TTS avec le LLM
_tts_executor = ThreadPoolExecutor(max_workers=1,  thread_name_prefix="tts-worker")
_llm_executor = ThreadPoolExecutor(max_workers=2,  thread_name_prefix="llm-worker")
_asr_executor = ThreadPoolExecutor(max_workers=2,  thread_name_prefix="asr-worker")

_WS_CLOSE_REASON_MAX_BYTES = 123
AUDIO_CHUNK_SIZE = 64 * 1024
SUPPORTED_LANGUAGES = {"ar", "fr", "en"}

LOCALIZED_TEXTS = {
    "welcome": {
        "ar": "مرحبا بك في المقابلة الصوتية. سأطرح عليك مجموعة من الأسئلة الصوتية فقط. استمع جيداً وأجب بوضوح.",
        "fr": "Bienvenue dans votre entretien vocal. Je vais vous poser des questions uniquement en audio. Écoutez attentivement et répondez clairement.",
        "en": "Welcome to the voice interview. I will ask you questions in audio only. Listen carefully and answer clearly.",
    },
    "completed": {
        "ar": "شكراً لك! انتهت المقابلة. سنتواصل معك قريباً.",
        "fr": "Merci beaucoup ! L'entretien est terminé. Nous vous contacterons prochainement.",
        "en": "Thank you! The interview is complete. We will contact you soon.",
    },
}


def _get_text(key, language):
    return LOCALIZED_TEXTS.get(key, {}).get(language) or LOCALIZED_TEXTS.get(key, {}).get("en", "")


def _truncate_close_reason(reason):
    enc = reason.encode("utf-8")
    if len(enc) <= _WS_CLOSE_REASON_MAX_BYTES:
        return reason
    return enc[:_WS_CLOSE_REASON_MAX_BYTES - 1].decode("utf-8", errors="ignore") + "…"


class InterviewHandler:

    def __init__(self, session_id: str, websocket: WebSocket, preferred_language: str = ""):
        self.session_id   = session_id
        self.websocket    = websocket
        self.session      = None
        self.position     = None
        self.audio_buffer = bytearray()
        self.is_recording = False
        self.asr_service  = _asr_service
        self.tts_service  = _tts_service
        self.avatar_service = _avatar_service
        self._preferred_language = (
            preferred_language if preferred_language in SUPPORTED_LANGUAGES else ""
        )
        logger.info(
            f"Handler | session={session_id} | "
            f"lang_client={preferred_language!r} | retenu={self._preferred_language or '(session)'}"
        )

    @property
    def lang(self) -> str:
        if self._preferred_language:
            return self._preferred_language
        if self.session:
            return self.session.language or "ar"
        return "ar"

    def _check_connected(self):
        if not manager.is_connected(self.session_id):
            raise WebSocketDisconnect(code=1006, reason="Client déconnecté")

    # ── PCM ──────────────────────────────────────────────────────────────

    @staticmethod
    def _extract_pcm_from_wav(wav_bytes):
        if len(wav_bytes) < 44 or wav_bytes[:4] != b'RIFF':
            return wav_bytes, 22050, 1, 16
        sr, ch, bits = 22050, 1, 16
        offset = 12
        while offset + 8 <= len(wav_bytes):
            cid = wav_bytes[offset:offset + 4]
            csz = struct.unpack_from('<I', wav_bytes, offset + 4)[0]
            ds  = offset + 8
            if cid == b'fmt ' and ds + 16 <= len(wav_bytes):
                ch   = struct.unpack_from('<H', wav_bytes, ds + 2)[0]
                sr   = struct.unpack_from('<I', wav_bytes, ds + 4)[0]
                bits = struct.unpack_from('<H', wav_bytes, ds + 14)[0]
            elif cid == b'data':
                pcm = wav_bytes[ds:]
                logger.info(f"WAV→PCM {len(wav_bytes):,}B→{len(pcm):,}B ({sr}Hz,{ch}ch,{bits}bit)")
                return pcm, sr, ch, bits
            offset = ds + csz + (csz % 2)
        return wav_bytes, sr, ch, bits

    async def _send_audio_chunked(self, audio_bytes, msg_type, extra_data):
        pcm, sr, ch, bits = self._extract_pcm_from_wav(audio_bytes)
        n_chunks = (len(pcm) + AUDIO_CHUNK_SIZE - 1) // AUDIO_CHUNK_SIZE
        meta = {
            **extra_data,
            "audio_mode": "chunked", "audio_format": "pcm_s16le",
            "sample_rate": sr, "channels": ch, "bits_per_sample": bits,
            "total_chunks": n_chunks, "audio_size_bytes": len(pcm),
        }
        await manager.send_json(self.session_id, {"type": msg_type, "data": meta})
        for i in range(n_chunks):
            self._check_connected()
            chunk = pcm[i * AUDIO_CHUNK_SIZE:(i + 1) * AUDIO_CHUNK_SIZE]
            await manager.send_json(self.session_id, {
                "type": "audio_chunk_data",
                "data": {"chunk_index": i, "total": n_chunks,
                         "data": base64.b64encode(chunk).decode()},
            })
            await asyncio.sleep(0)
        await manager.send_json(self.session_id, {
            "type": "audio_chunk_end",
            "data": {"msg_type": msg_type},
        })
        logger.info(f"✅ {n_chunks} chunks PCM pour '{msg_type}' [{self.lang}]")

    # ── TTS ──────────────────────────────────────────────────────────────

    async def _synthesize_bytes(self, text: str) -> Optional[bytes]:
        if not self.tts_service:
            return None
        language = self.lang
        loop = asyncio.get_event_loop()
        def _do():
            try:
                return self.tts_service.synthesize(text, language=language, use_cache=True) or None
            except Exception as e:
                logger.error(f"TTS [{language}]: {e}")
                return None
        result = await loop.run_in_executor(_tts_executor, _do)
        if result:
            logger.info(f"TTS [{language}]: {len(result):,} bytes")
        return result

    # ── Attente fin lecture ───────────────────────────────────────────────

    async def _wait_for_audio_finished(self, timeout=120.0):
        loop = asyncio.get_event_loop()
        deadline = loop.time() + timeout
        while True:
            remaining = deadline - loop.time()
            if remaining <= 0:
                logger.warning("⚠️ Timeout audio_finished")
                return
            try:
                data = await asyncio.wait_for(
                    self.websocket.receive_json(),
                    timeout=min(remaining, 5.0),
                )
                t = data.get("type")
                if t == "audio_finished":
                    return
                elif t == "end_interview":
                    await self._cancel_interview()
                    raise WebSocketDisconnect(code=1000, reason="Terminé")
            except asyncio.TimeoutError:
                self._check_connected()

    # ── Handle principal ─────────────────────────────────────────────────

    async def handle(self):
        try:
            if not await self._load_session():
                return
            logger.info(
                f"🌍 Langue active: {self.lang!r} "
                f"(préférence: {self._preferred_language!r}, session: {self.session.language!r})"
            )
            await asyncio.sleep(0.2)
            self._check_connected()
            await self._send_welcome()
            await self._wait_for_audio_finished(120)
            self._check_connected()
            await self._start_interview()
            await asyncio.sleep(0.3)

            while self.session.status == "in_progress":
                self._check_connected()
                await self._send_current_question()
                await self._wait_for_audio_finished(60)
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
            logger.info(f"Déconnexion code={e.code}: {self.session_id}")
        except Exception as e:
            logger.error(f"Erreur: {e}", exc_info=True)
            if manager.is_connected(self.session_id):
                try:
                    await self._send_error(str(e))
                except Exception:
                    pass
        finally:
            manager.disconnect(self.session_id)

    # ── Session ──────────────────────────────────────────────────────────

    async def _load_session(self) -> bool:
        try:
            session, is_valid, err = InterviewSessionCRUD.validate_session_access(self.session_id)
            if not is_valid:
                await self._send_error(err, "SESSION_INVALID")
                try:
                    await self.websocket.close(code=4003, reason=_truncate_close_reason(err))
                except Exception:
                    pass
                return False
            self.session  = session
            self.position = JobPositionCRUD.get_by_id(self.session.job_position_id)
            logger.info(
                f"Session OK: {self.position.title} | "
                f"{len(self.position.questions)} questions | langue={self.lang!r}"
            )
            return True
        except WebSocketDisconnect:
            raise
        except Exception as e:
            logger.error(f"Load session error: {e}", exc_info=True)
            if manager.is_connected(self.session_id):
                await self._send_error(str(e))
            return False

    # ── Bienvenue ─────────────────────────────────────────────────────────

    async def _send_welcome(self):
        text  = _get_text("welcome", self.lang)
        audio = await self._synthesize_bytes(text)
        extra = {
            "total_questions": len(self.position.questions),
            "position_title": self.position.title,
            "expires_at": self.session.expires_at.isoformat(),
            "vocal_only": True,
            "language": self.lang,
        }
        if audio:
            await self._send_audio_chunked(audio, "welcome", extra)
        else:
            await manager.send_json(self.session_id, {"type": "welcome", "data": extra})

    async def _start_interview(self):
        self.session = InterviewSessionCRUD.update_status(self.session_id, "in_progress")
        logger.info(f"Entretien démarré [{self.lang}]")

    # ── Question ──────────────────────────────────────────────────────────

    async def _send_current_question(self):
        idx = self.session.current_question_index
        if idx >= len(self.position.questions):
            return
        question = self.position.questions[idx]
        text     = question.get_text(self.lang)
        progress = {
            "current":    idx + 1,
            "total":      len(self.position.questions),
            "percentage": int((idx + 1) / len(self.position.questions) * 100),
        }
        logger.info(f"Q{question.order} [{self.lang}]: {text[:80]}")
        await manager.send_json(
            self.session_id,
            {"type": "question_loading", "data": {"progress": progress}},
        )
        audio = await self._synthesize_bytes(text)
        if not audio:
            await self._send_error("Impossible de générer l'audio")
            return
        extra = {
            "order":       question.order,
            "max_duration": question.max_duration_seconds,
            "progress":    progress,
            "vocal_only":  True,
            "language":    self.lang,
        }
        await self._send_audio_chunked(audio, "question", extra)

    # ── Réponse + pipeline ASR → LLM ─────────────────────────────────────

    async def _wait_for_answer(self):
        self.audio_buffer.clear()
        self.is_recording = False
        answer_start_time = None
        self._check_connected()
        try:
            while True:
                data = await self.websocket.receive_json()
                t = data.get("type")
                if t == "audio_chunk":
                    if not self.is_recording:
                        self.is_recording = True
                        answer_start_time = datetime.utcnow()
                    self.audio_buffer.extend(base64.b64decode(data.get("audio_data", "")))
                elif t == "answer_complete":
                    break
                elif t == "end_interview":
                    await self._cancel_interview()
                    raise WebSocketDisconnect(code=1000, reason="Terminé")
        except WebSocketDisconnect:
            raise
        except Exception as e:
            raise WebSocketDisconnect(code=1006, reason=str(e)[:100]) from e
        if self.audio_buffer:
            await self._process_answer(answer_start_time)

    async def _process_answer(self, start_time):
        """
        Pipeline complet :
        1. Sauvegarde audio WAV
        2. Transcription Whisper (ASR)
        3. Évaluation LLM (async en background, non bloquante)
        4. Notification client (answer_saved + evaluation si disponible rapidement)
        """
        idx      = self.session.current_question_index
        question = self.position.questions[idx]
        duration = (datetime.utcnow() - start_time).total_seconds() if start_time else 0.0

        # ── 1. Sauvegarde audio ───────────────────────────────────────────
        audio_path = (
            settings.UPLOAD_DIR / "interviews"
            / f"answer_{self.session_id}_{question.order}.wav"
        )
        audio_path.parent.mkdir(parents=True, exist_ok=True)
        wav = self._buffer_to_wav(bytes(self.audio_buffer))
        audio_path.write_bytes(wav)

        # ── 2. Transcription Whisper ──────────────────────────────────────
        transcript = await self._transcribe_audio(wav)
        logger.info(f"📝 Transcription [{self.lang}] Q{question.order}: '{transcript[:80]}'")

        # ── 3. Sauvegarde réponse en base ─────────────────────────────────
        InterviewSessionCRUD.add_answer(
            self.session_id,
            Answer(
                question_order=question.order,
                question_text=question.get_text(self.lang),
                transcript=transcript,
                audio_file_path=str(audio_path),
                duration_seconds=duration,
            ),
        )

        # ── 4. Notification immédiate au client ───────────────────────────
        if manager.is_connected(self.session_id):
            await manager.send_json(self.session_id, {
                "type": "answer_saved",
                "data": {
                    "duration":       duration,
                    "question_order": question.order,
                    "transcript":     transcript,
                    "saved":          True,
                    "evaluation":     "processing",
                },
            })

        # ── 5. Évaluation LLM (arrière-plan, non bloquante) ───────────────
        asyncio.create_task(
            self._run_llm_evaluation(
                question_text=question.get_text(self.lang),
                transcript=transcript,
                question_order=question.order,
                audio_path=str(audio_path),
            )
        )

    async def _transcribe_audio(self, wav_bytes: bytes) -> str:
        """Transcription Whisper dans un thread séparé."""
        if not self.asr_service:
            logger.warning("ASR non disponible — transcription ignorée")
            return ""
        lang = self.lang
        loop = asyncio.get_event_loop()
        try:
            transcript = await loop.run_in_executor(
                _asr_executor,
                lambda: self.asr_service.transcribe(wav_bytes, language=lang),
            )
            return transcript or ""
        except Exception as e:
            logger.error(f"Erreur ASR : {e}")
            return ""

    async def _run_llm_evaluation(
        self,
        question_text: str,
        transcript: str,
        question_order: int,
        audio_path: str,
    ):
        """
        Évaluation LLM asynchrone déclenchée après chaque réponse.
        Le résultat est envoyé au client WebSocket puis sauvegardé en base.
        """
        try:
            from backend.services.llm_service import get_llm_service
            from backend.evaluation.service import EvaluationService

            llm = get_llm_service()
            if not await llm.is_available():
                logger.warning("Ollama non disponible — évaluation ignorée")
                return

            eval_svc = EvaluationService(llm_service=llm, asr_service=self.asr_service)

            eval_result = await eval_svc.evaluate_single_answer(
                question_text=question_text,
                answer_transcript=transcript,
                question_order=question_order,
                language=self.lang,
                position_title=self.position.title,
                audio_path=audio_path,
            )

            logger.info(
                f"🤖 LLM Q{question_order} [{self.lang}] | "
                f"score={eval_result.score}/10 | verdict={eval_result.verdict}"
            )

            # Persister l'évaluation dans la réponse en base
            self._save_answer_evaluation(question_order, eval_result)

            # Notifier le client si encore connecté
            if manager.is_connected(self.session_id):
                await manager.send_json(self.session_id, {
                    "type": "answer_evaluated",
                    "data": {
                        "question_order": question_order,
                        "score":         eval_result.score,
                        "verdict":       eval_result.verdict,
                        "feedback":      eval_result.feedback,
                        "strengths":     eval_result.strengths,
                        "improvements":  eval_result.improvements,
                    },
                })

        except Exception as e:
            logger.error(f"Évaluation LLM Q{question_order} échouée : {e}", exc_info=True)

    def _save_answer_evaluation(self, question_order: int, eval_result):
        """Met à jour le champ 'evaluation' de la réponse correspondante en base."""
        try:
            from backend.database import db
            db.interview_sessions.update_one(
                {
                    "session_id":             self.session_id,
                    "answers.question_order": question_order,
                },
                {
                    "$set": {
                        "answers.$.evaluation": {
                            "score":        eval_result.score,
                            "verdict":      eval_result.verdict,
                            "feedback":     eval_result.feedback,
                            "strengths":    eval_result.strengths,
                            "improvements": eval_result.improvements,
                            "llm_model":    eval_result.llm_model,
                            "evaluated_at": eval_result.evaluated_at.isoformat(),
                        }
                    }
                },
            )
        except Exception as e:
            logger.error(f"Sauvegarde évaluation Q{question_order} : {e}")

    # ── Fin d'entretien ───────────────────────────────────────────────────

    async def _complete_interview(self):
        self.session = InterviewSessionCRUD.update_status(self.session_id, "completed")
        text  = _get_text("completed", self.lang)
        audio = await self._synthesize_bytes(text)
        extra = {
            "total_questions": len(self.position.questions),
            "total_answers":   len(self.session.answers),
            "position_title":  self.position.title,
        }
        if audio:
            await self._send_audio_chunked(audio, "interview_completed", extra)
        else:
            await manager.send_json(
                self.session_id,
                {"type": "interview_completed", "data": extra},
            )

        # Déclencher l'évaluation globale en arrière-plan
        asyncio.create_task(self._run_global_evaluation())

    async def _run_global_evaluation(self):
        """Génère le rapport global LLM après la fin de l'entretien."""
        try:
            from backend.services.llm_service import get_llm_service
            from backend.evaluation.service import EvaluationService

            llm = get_llm_service()
            if not await llm.is_available():
                return

            svc = EvaluationService(llm_service=llm, asr_service=self.asr_service)
            result = await svc.evaluate_full_session(self.session_id, language=self.lang)

            if result and manager.is_connected(self.session_id):
                await manager.send_json(self.session_id, {
                    "type": "global_evaluation",
                    "data": {
                        "global_score":    result.global_score,
                        "global_verdict":  result.global_verdict,
                        "recommendation":  result.recommendation,
                        "key_strengths":   result.key_strengths,
                        "key_improvements": result.key_improvements,
                        "summary":         result.summary,
                    },
                })
                logger.info(
                    f"📊 Rapport global {self.session_id} | "
                    f"score={result.global_score}/10 | {result.recommendation}"
                )
        except Exception as e:
            logger.error(f"Évaluation globale : {e}", exc_info=True)

    async def _cancel_interview(self):
        self.session = InterviewSessionCRUD.update_status(self.session_id, "cancelled")

    async def _send_error(self, message, error_type="GENERAL_ERROR"):
        if not manager.is_connected(self.session_id):
            return
        try:
            await manager.send_json(
                self.session_id,
                {"type": "error", "data": {"message": message, "error_type": error_type}},
            )
        except WebSocketDisconnect:
            pass

    def _buffer_to_wav(self, audio_data: bytes) -> bytes:
        out = io.BytesIO()
        with wave.open(out, "wb") as wf:
            wf.setnchannels(settings.CHANNELS)
            wf.setsampwidth(2)
            wf.setframerate(settings.SAMPLE_RATE)
            wf.writeframes(audio_data)
        return out.getvalue()


# ─────────────────────────────────────────────────────────────────────
# POINT D'ENTRÉE WEBSOCKET
# ─────────────────────────────────────────────────────────────────────

async def handle_interview_websocket(
    websocket: WebSocket,
    session_id: str,
    lang: str = "",
):
    logger.info(f"WS: {session_id} | lang={lang!r}")
    await manager.connect(session_id, websocket)
    handler = InterviewHandler(session_id, websocket, preferred_language=lang)
    await handler.handle()
    logger.info(f"WS fermé: {session_id}")