"""
Handler WebSocket — AUDIO PCM PUR EN CHUNKS — MULTILINGUE AR/FR/EN
+ ANALYSE LANGAGE CORPOREL FACIAL (MediaPipe v4 + DeepFace CNN)

Pipeline enrichi :
  Voix  → Whisper (ASR) → Llama 3 (LLM) → Score / Feedback
  Vidéo → MediaPipe FaceMesh + DeepFace CNN → FacialMetrics → injectées dans LLM

Correctifs v4 :
  - analyze_frames_batch() avec échantillonnage max 25 frames
  - Timeout adaptatif (5s + 2s par tranche de 5 frames, max 45s)
  - detector_backend='mtcnn' en mode dégradé (>opencv)
  - Import facial_analysis_service en premier dans le module
"""

# ── Import facial en premier pour garantir l'ordre protobuf ──────────────────
# facial_analysis_service injecte le mock mediapipe.tasks en module-level,
# ce qui doit se produire AVANT tout import de deepface/tf_keras.
try:
    from backend.services.facial_analysis_service import get_facial_service as _fac_init
    _fac_init()   # instancier le singleton immédiatement
except Exception:
    pass
# ─────────────────────────────────────────────────────────────────────────────

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
from backend.database import db as mongo_db
from backend.interviews.crud import InterviewSessionCRUD, JobPositionCRUD
from backend.interviews.models import Answer, AnswerEvaluationData, FacialAnalysisData
from backend.websocket.connection_manager import manager

logger = logging.getLogger(__name__)

_asr_service    = None
_tts_service    = None
_avatar_service = None

_tts_executor    = ThreadPoolExecutor(max_workers=1, thread_name_prefix="tts-worker")
_llm_executor    = ThreadPoolExecutor(max_workers=2, thread_name_prefix="llm-worker")
_asr_executor    = ThreadPoolExecutor(max_workers=2, thread_name_prefix="asr-worker")
_facial_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="facial-worker")

_WS_CLOSE_REASON_MAX_BYTES = 123
AUDIO_CHUNK_SIZE            = 64 * 1024
SUPPORTED_LANGUAGES         = {"ar", "fr", "en"}

LOCALIZED_TEXTS = {
    "welcome": {
        "ar": "مرحباً {name}! أهلاً بك في مقابلتك الصوتية لمنصب {position}. سأطرح عليك {total} أسئلة صوتية. استمع جيداً وأجب بوضوح وثقة.",
        "fr": "Bonjour {name} ! Bienvenue dans votre entretien vocal pour le poste de {position}. Je vais vous poser {total} questions en audio. Écoutez attentivement et répondez avec clarté et confiance.",
        "en": "Hello {name}! Welcome to your voice interview for the {position} position. I will ask you {total} questions in audio. Listen carefully and answer with clarity and confidence.",
    },
    "completed": {
        "ar": "شكراً لك {name}! لقد أجبت على جميع الأسئلة بنجاح. انتهت مقابلتك. سنتواصل معك قريباً.",
        "fr": "Merci beaucoup {name} ! Vous avez répondu à toutes les questions avec succès. Votre entretien est terminé. Nous vous contacterons prochainement.",
        "en": "Thank you {name}! You have answered all questions successfully. Your interview is complete. We will contact you soon.",
    },
    "welcome_back": {
        "ar": "مرحباً بعودتك {name}! نستأنف مقابلتك من السؤال {current} من أصل {total}.",
        "fr": "Bon retour {name} ! Nous reprenons votre entretien à la question {current} sur {total}.",
        "en": "Welcome back {name}! We are resuming your interview at question {current} of {total}.",
    },
    "followup_intro": {
        "ar": "شكراً على إجابتك. لدي سؤال إضافي:",
        "fr": "Merci pour votre réponse. J'ai une question complémentaire :",
        "en": "Thank you for your answer. I have a follow-up question:",
    },
    "followup_thanks": {
        "ar": "شكراً على التوضيح. ننتقل إلى السؤال التالي.",
        "fr": "Merci pour votre précision. Passons à la question suivante.",
        "en": "Thank you for the clarification. Let's move to the next question.",
    },
}


def _get_text(key: str, language: str, **kwargs) -> str:
    template = LOCALIZED_TEXTS.get(key, {}).get(language) \
               or LOCALIZED_TEXTS.get(key, {}).get("en", "")
    if kwargs:
        try:
            return template.format(**kwargs)
        except KeyError:
            return template
    return template


def _truncate_close_reason(reason: str) -> str:
    enc = reason.encode("utf-8")
    if len(enc) <= _WS_CLOSE_REASON_MAX_BYTES:
        return reason
    return enc[:_WS_CLOSE_REASON_MAX_BYTES - 1].decode("utf-8", errors="ignore") + "…"


class InterviewHandler:

    def __init__(self, session_id: str, websocket: WebSocket, preferred_language: str = ""):
        self.session_id      = session_id
        self.websocket       = websocket
        self.session         = None
        self.position        = None
        self.candidate       = None
        self.audio_buffer    = bytearray()
        self.is_recording    = False
        self.asr_service     = _asr_service
        self.tts_service     = _tts_service
        self.avatar_service  = _avatar_service
        self._preferred_language = (
            preferred_language if preferred_language in SUPPORTED_LANGUAGES else ""
        )
        self._prefetched_audio: Optional[bytes] = None
        self._facial_frames: list[str] = []
        self._facial_enabled: bool = getattr(settings, "FACIAL_ANALYSIS_ENABLED", True)

    @property
    def lang(self) -> str:
        if self._preferred_language:
            return self._preferred_language
        if self.session:
            return self.session.language or "ar"
        return "ar"

    @property
    def candidate_first_name(self) -> str:
        if self.candidate:
            return self.candidate.get("first_name", "").strip() or "Candidat"
        return "Candidat"

    @property
    def candidate_full_name(self) -> str:
        if self.candidate:
            first = self.candidate.get("first_name", "").strip()
            last  = self.candidate.get("last_name",  "").strip()
            return f"{first} {last}".strip() or "Candidat"
        return "Candidat"

    def _check_connected(self):
        if not manager.is_connected(self.session_id):
            raise WebSocketDisconnect(code=1006, reason="Client déconnecté")

    # ── PCM ──────────────────────────────────────────────────────────────────

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
                return wav_bytes[ds:], sr, ch, bits
            offset = ds + csz + (csz % 2)
        return wav_bytes, sr, ch, bits

    async def _send_audio_chunked(self, audio_bytes, msg_type, extra_data):
        pcm, sr, ch, bits = self._extract_pcm_from_wav(audio_bytes)
        n_chunks = (len(pcm) + AUDIO_CHUNK_SIZE - 1) // AUDIO_CHUNK_SIZE
        meta = {
            **extra_data,
            "audio_mode":      "chunked",
            "audio_format":    "pcm_s16le",
            "sample_rate":     sr,
            "channels":        ch,
            "bits_per_sample": bits,
            "total_chunks":    n_chunks,
            "audio_size_bytes": len(pcm),
        }
        await manager.send_json(self.session_id, {"type": msg_type, "data": meta})
        for i in range(n_chunks):
            self._check_connected()
            chunk = pcm[i * AUDIO_CHUNK_SIZE:(i + 1) * AUDIO_CHUNK_SIZE]
            await manager.send_json(self.session_id, {
                "type": "audio_chunk_data",
                "data": {
                    "chunk_index": i,
                    "total":       n_chunks,
                    "data":        base64.b64encode(chunk).decode(),
                },
            })
            await asyncio.sleep(0)
        await manager.send_json(self.session_id, {
            "type": "audio_chunk_end",
            "data": {"msg_type": msg_type},
        })

    # ── TTS ──────────────────────────────────────────────────────────────────

    async def _synthesize_bytes(self, text: str) -> Optional[bytes]:
        if not self.tts_service:
            return None
        language = self.lang
        loop     = asyncio.get_event_loop()

        def _do():
            try:
                return self.tts_service.synthesize(text, language=language, use_cache=True) or None
            except Exception as e:
                logger.error(f"TTS [{language}]: {e}")
                return None

        return await manager.send_heartbeat_during(
            self.session_id,
            loop.run_in_executor(_tts_executor, _do),
            interval=15.0,
        )

    async def _wait_for_audio_finished(self, timeout=120.0):
        loop     = asyncio.get_event_loop()
        deadline = loop.time() + timeout
        while True:
            remaining = deadline - loop.time()
            if remaining <= 0:
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

    # ── Handle principal ─────────────────────────────────────────────────────

    async def handle(self):
        try:
            if not await self._load_session():
                return
            logger.info(f"Langue: {self.lang!r} | Candidat: {self.candidate_full_name}")
            await asyncio.sleep(0.2)
            self._check_connected()

            is_reconnection = (self.session.status == "in_progress")

            if is_reconnection:
                logger.info(
                    f"Reconnexion | Q{self.session.current_question_index + 1}"
                    f"/{len(self.position.questions)} | session={self.session_id}"
                )
                await self._send_welcome_back()
            else:
                await self._send_welcome()
                await self._wait_for_audio_finished(120)
                self._check_connected()
                await self._start_interview()

            await asyncio.sleep(0.1)

            while self.session.status == "in_progress":
                self._check_connected()
                await self._send_current_question()
                await self._wait_for_audio_finished(60)
                self._check_connected()

                next_idx      = self.session.current_question_index + 1
                next_tts_task = None
                if next_idx < len(self.position.questions):
                    next_q    = self.position.questions[next_idx]
                    next_text = next_q.get_text(self.lang)
                    next_tts_task = asyncio.create_task(self._synthesize_bytes(next_text))

                await self._wait_for_answer()

                is_last = (self.session.current_question_index + 1 >= len(self.position.questions))

                if is_last:
                    if next_tts_task and not next_tts_task.done():
                        next_tts_task.cancel()
                    self._check_connected()
                    await self._complete_interview()
                    break
                else:
                    if next_tts_task:
                        try:
                            prefetched = await asyncio.wait_for(next_tts_task, timeout=30.0)
                            self._prefetched_audio = prefetched
                        except Exception as e:
                            logger.warning(f"Prefetch TTS échoué: {e}")
                            self._prefetched_audio = None
                    self.session = InterviewSessionCRUD.increment_question_index(self.session_id)
                    await asyncio.sleep(0.1)

        except WebSocketDisconnect as e:
            logger.info(f"Déconnexion code={e.code}: {self.session_id}")
        except Exception as e:
            logger.error(f"Erreur handler: {e}", exc_info=True)
            if manager.is_connected(self.session_id):
                try:
                    await self._send_error(str(e))
                except Exception:
                    pass
        finally:
            manager.disconnect(self.session_id)

    # ── Session ───────────────────────────────────────────────────────────────

    async def _load_session(self) -> bool:
        try:
            from bson import ObjectId
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
            try:
                self.candidate = mongo_db.candidates.find_one(
                    {"_id": ObjectId(self.session.candidate_id)}
                )
            except Exception as e:
                logger.warning(f"Chargement candidat: {e}")
                self.candidate = None
            return True
        except WebSocketDisconnect:
            raise
        except Exception as e:
            logger.error(f"Load session error: {e}", exc_info=True)
            if manager.is_connected(self.session_id):
                await self._send_error(str(e))
            return False

    async def _send_welcome_back(self):
        idx  = self.session.current_question_index
        text = _get_text(
            "welcome_back", self.lang,
            name=self.candidate_first_name,
            current=idx + 1,
            total=len(self.position.questions),
        )
        audio = await self._synthesize_bytes(text)
        extra = {
            "total_questions":         len(self.position.questions),
            "current_question_index":  idx,
            "position_title":          self.position.title,
            "candidate_name":          self.candidate_full_name,
            "expires_at":              self.session.expires_at.isoformat(),
            "vocal_only":              True,
            "language":                self.lang,
            "is_reconnection":         True,
            "facial_analysis_enabled": self._facial_enabled,
        }
        if audio:
            await self._send_audio_chunked(audio, "welcome_back", extra)
        else:
            await manager.send_json(self.session_id, {"type": "welcome_back", "data": extra})
        await self._wait_for_audio_finished(60)

    async def _send_welcome(self):
        text  = _get_text(
            "welcome", self.lang,
            name=self.candidate_first_name,
            position=self.position.title,
            total=len(self.position.questions),
        )
        audio = await self._synthesize_bytes(text)
        extra = {
            "total_questions":         len(self.position.questions),
            "position_title":          self.position.title,
            "candidate_name":          self.candidate_full_name,
            "expires_at":              self.session.expires_at.isoformat(),
            "vocal_only":              True,
            "language":                self.lang,
            "facial_analysis_enabled": self._facial_enabled,
        }
        if audio:
            await self._send_audio_chunked(audio, "welcome", extra)
        else:
            await manager.send_json(self.session_id, {"type": "welcome", "data": extra})

    async def _start_interview(self):
        self.session = InterviewSessionCRUD.update_status(self.session_id, "in_progress")

    async def _send_current_question(self):
        idx = self.session.current_question_index
        if idx >= len(self.position.questions):
            return
        question = self.position.questions[idx]
        progress = {
            "current":    idx + 1,
            "total":      len(self.position.questions),
            "percentage": int((idx + 1) / len(self.position.questions) * 100),
        }
        await manager.send_json(
            self.session_id,
            {"type": "question_loading", "data": {"progress": progress}},
        )
        audio = self._prefetched_audio
        self._prefetched_audio = None
        if not audio:
            audio = await self._synthesize_bytes(question.get_text(self.lang))
        if not audio:
            await self._send_error("Impossible de générer l'audio")
            return
        await self._send_audio_chunked(audio, "question", {
            "order":        question.order,
            "weight":       question.weight,
            "max_duration": question.max_duration_seconds,
            "progress":     progress,
            "vocal_only":   True,
            "language":     self.lang,
        })

    # ── Réponse + collecte vidéo ──────────────────────────────────────────────

    async def _wait_for_answer(self):
        self.audio_buffer.clear()
        self._facial_frames.clear()
        self.is_recording    = False
        answer_start_time    = None
        self._check_connected()
        try:
            while True:
                data = await self.websocket.receive_json()
                t    = data.get("type")

                if t == "audio_chunk":
                    if not self.is_recording:
                        self.is_recording = True
                        answer_start_time = datetime.utcnow()
                    self.audio_buffer.extend(base64.b64decode(data.get("audio_data", "")))

                elif t == "video_frame":
                    frame_b64 = data.get("data", {}).get("frame", "")
                    if frame_b64 and self._facial_enabled:
                        self._facial_frames.append(frame_b64)

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

    # ── Traitement de la réponse (audio + facial) ─────────────────────────────

    async def _process_answer(self, start_time):
        idx           = self.session.current_question_index
        question      = self.position.questions[idx]
        question_text = question.get_text(self.lang)
        duration      = (datetime.utcnow() - start_time).total_seconds() if start_time else 0.0

        # Sauvegarde audio
        audio_path = (
            settings.UPLOAD_DIR / "interviews"
            / f"answer_{self.session_id}_{question.order}.wav"
        )
        audio_path.parent.mkdir(parents=True, exist_ok=True)
        wav = self._buffer_to_wav(bytes(self.audio_buffer))
        audio_path.write_bytes(wav)

        # Transcription ASR + analyse faciale en parallèle
        frames_snapshot = list(self._facial_frames)

        asr_coro    = self._transcribe_audio(wav)
        facial_coro = self._analyze_facial_frames(frames_snapshot)

        transcript, facial_metrics = await asyncio.gather(asr_coro, facial_coro)

        logger.info(
            f"Transcription [{self.lang}] Q{question.order}: "
            f"'{transcript[:80]}' | "
            f"frames={len(frames_snapshot)} "
            f"facial={'OK' if facial_metrics else 'n/a'}"
        )

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

        try:
            from backend.services.llm_service import get_llm_service
            llm = get_llm_service()
            if not await llm.is_available():
                raise RuntimeError("LLM non disponible")

            # Évaluation LLM enrichie avec données faciales
            if hasattr(llm, "evaluate_with_facial"):
                initial_eval = await llm.evaluate_with_facial(
                    question=question_text,
                    answer=transcript,
                    language=self.lang,
                    position_title=self.position.title,
                    facial_metrics=facial_metrics,
                )
            else:
                initial_eval = await llm.evaluate_with_followup(
                    question=question_text,
                    answer=transcript,
                    language=self.lang,
                    position_title=self.position.title,
                )

            initial_eval["llm_model"] = llm.model
            initial_eval["evaluated"] = True

            needs_followup    = initial_eval.get("needs_followup", False)
            followup_question = initial_eval.get("followup_question", "").strip()

            # Construire FacialAnalysisData pour MongoDB
            facial_data: Optional[FacialAnalysisData] = None
            if facial_metrics and facial_metrics.frames_with_face > 0:
                facial_data = FacialAnalysisData(
                    dominant_emotion    = facial_metrics.dominant_emotion,
                    emotion_scores      = facial_metrics.emotion_scores,
                    eye_contact_ratio   = facial_metrics.eye_contact_ratio,
                    head_stability      = facial_metrics.head_stability,
                    smile_ratio         = facial_metrics.smile_ratio,
                    confidence_score    = facial_metrics.confidence_score,
                    stress_score        = facial_metrics.stress_score,
                    engagement_score    = facial_metrics.engagement_score,
                    frames_analyzed     = facial_metrics.frames_analyzed,
                    frames_with_face    = facial_metrics.frames_with_face,
                    face_detection_rate = facial_metrics.face_detection_rate,
                )

            await self._save_answer_to_db(
                question=question,
                transcript=transcript,
                audio_path=str(audio_path),
                duration=duration,
                eval_result=initial_eval,
                facial_data=facial_data,
            )

            if manager.is_connected(self.session_id):
                await manager.send_json(self.session_id, {
                    "type": "answer_evaluated",
                    "data": {
                        "question_order": question.order,
                        "had_followup":   False,
                        "is_initial":     True,
                    },
                })

            if needs_followup and followup_question and manager.is_connected(self.session_id):
                await self._conduct_followup(
                    question=question,
                    question_text=question_text,
                    initial_transcript=transcript,
                    initial_eval=initial_eval,
                    followup_question=followup_question,
                    audio_path=str(audio_path),
                    duration=duration,
                    llm=llm,
                    facial_data=facial_data,
                )
            return

        except Exception as e:
            logger.error(f"Évaluation LLM Q{question.order} : {e}", exc_info=True)

        InterviewSessionCRUD.add_answer(
            self.session_id,
            Answer(
                question_order=question.order,
                question_text=question_text,
                transcript=transcript,
                audio_file_path=str(audio_path),
                duration_seconds=duration,
                evaluation=None,
            ),
        )

    # ── Analyse faciale asynchrone (v4) ───────────────────────────────────────

    async def _analyze_facial_frames(self, frames_b64: list[str]):
        """
        Analyse les frames JPEG via analyze_frames_batch() avec échantillonnage.
        Timeout adaptatif pour éviter le blocage sur longues réponses.
        """
        if not self._facial_enabled or not frames_b64:
            return None

        # Timeout adaptatif : 5s de base + 2s par tranche de 5 frames
        try:
            from backend.services.facial_analysis_service import MAX_FRAMES_TO_ANALYZE
        except ImportError:
            MAX_FRAMES_TO_ANALYZE = 25

        n_to_analyze = min(len(frames_b64), MAX_FRAMES_TO_ANALYZE)
        timeout_s    = 5.0 + (n_to_analyze / 5) * 2.0
        timeout_s    = min(timeout_s, 45.0)

        loop = asyncio.get_event_loop()
        try:
            return await asyncio.wait_for(
                loop.run_in_executor(
                    _facial_executor,
                    lambda: self._run_facial_sync(frames_b64),
                ),
                timeout=timeout_s,
            )
        except asyncio.TimeoutError:
            logger.warning(
                f"Analyse faciale timeout après {timeout_s:.0f}s "
                f"({len(frames_b64)} frames collectés, "
                f"{n_to_analyze} analysés max)"
            )
            return None
        except Exception as e:
            logger.error(f"Analyse faciale : {e}")
            return None

    @staticmethod
    def _run_facial_sync(frames_b64: list[str]):
        """
        Synchrone — exécuté dans ThreadPoolExecutor.
        Décode les frames JPEG et utilise analyze_frames_batch()
        pour l'échantillonnage + analyse MediaPipe + DeepFace.
        """
        import numpy as np
        import cv2

        try:
            from backend.services.facial_analysis_service import get_facial_service
            svc = get_facial_service()

            if not svc.is_available:
                return None

            # Décoder tous les frames reçus
            frames_bgr = []
            for b64 in frames_b64:
                try:
                    buf   = np.frombuffer(base64.b64decode(b64), np.uint8)
                    frame = cv2.imdecode(buf, cv2.IMREAD_COLOR)
                    if frame is not None:
                        frames_bgr.append(frame)
                except Exception as e:
                    logger.debug(f"Décodage frame: {e}")

            if not frames_bgr:
                return None

            # Analyse avec échantillonnage automatique (max MAX_FRAMES_TO_ANALYZE)
            frame_results = svc.analyze_frames_batch(frames_bgr)
            return svc.compute_metrics(frame_results)

        except Exception as e:
            logger.error(f"_run_facial_sync: {e}")
            return None

    # ── Question de suivi ─────────────────────────────────────────────────────

    async def _conduct_followup(
        self, question, question_text, initial_transcript,
        initial_eval, followup_question, audio_path, duration,
        llm, facial_data=None,
    ):
        if manager.is_connected(self.session_id):
            await manager.send_json(self.session_id, {
                "type": "followup_incoming",
                "data": {
                    "question_order": question.order,
                    "initial_score":  initial_eval.get("score"),
                    "followup_text":  followup_question,
                },
            })

        fq_audio = await self._synthesize_bytes(
            f"{_get_text('followup_intro', self.lang)} {followup_question}"
        )
        if not fq_audio:
            return
        await self._send_audio_chunked(fq_audio, "followup_question", {
            "question_order": question.order,
            "followup_text":  followup_question,
            "vocal_only":     True,
        })
        await self._wait_for_audio_finished(60)

        followup_wav, _ = await self._wait_for_followup_answer(question.order)
        if not followup_wav:
            return

        fq_audio_path = (
            settings.UPLOAD_DIR / "interviews"
            / f"followup_{self.session_id}_{question.order}.wav"
        )
        fq_audio_path.write_bytes(followup_wav)
        followup_transcript = await self._transcribe_audio(followup_wav)

        is_last_question = (
            self.session.current_question_index + 1 >= len(self.position.questions)
        )
        if not is_last_question:
            thanks_audio = await self._synthesize_bytes(_get_text("followup_thanks", self.lang))
            if thanks_audio and manager.is_connected(self.session_id):
                await self._send_audio_chunked(
                    thanks_audio, "followup_thanks", {"question_order": question.order}
                )
                await self._wait_for_audio_finished(30)

        final_eval = await llm.evaluate_final_with_followup(
            question=question_text,
            first_answer=initial_transcript,
            followup_question=followup_question,
            followup_answer=followup_transcript,
            language=self.lang,
            position_title=self.position.title,
        )
        final_eval["llm_model"] = llm.model
        final_eval["evaluated"] = True

        initial_score   = initial_eval.get("score",   0.0)
        initial_verdict = initial_eval.get("verdict", "")
        final_score     = final_eval.get("score",   0.0)
        final_verdict   = final_eval.get("verdict", "")

        final_ev_data = AnswerEvaluationData(
            score=final_score,
            verdict=final_verdict,
            feedback=final_eval.get("feedback", ""),
            strengths=final_eval.get("strengths", []),
            improvements=final_eval.get("improvements", []),
            llm_model=final_eval.get("llm_model", ""),
            evaluated_at=datetime.utcnow(),
            had_followup=True,
            initial_score=initial_score,
            initial_verdict=initial_verdict,
            followup_question=followup_question,
            followup_transcript=followup_transcript,
            facial_analysis=facial_data,
        )

        InterviewSessionCRUD.update_answer(
            session_id=self.session_id,
            question_order=question.order,
            audio_followup_path=str(fq_audio_path),
            evaluation=final_ev_data,
            followup_question=followup_question,
            followup_transcript=followup_transcript,
            initial_score=initial_score,
            initial_verdict=initial_verdict,
        )
        InterviewSessionCRUD.save_answer_evaluation(
            session_id=self.session_id,
            question_order=question.order,
            evaluation=final_ev_data,
        )

        if manager.is_connected(self.session_id):
            await manager.send_json(self.session_id, {
                "type": "answer_followup_completed",
                "data": {
                    "question_order": question.order,
                    "had_followup":   True,
                },
            })

    async def _wait_for_followup_answer(self, question_order: int, timeout: float = 120.0):
        self.audio_buffer.clear()
        self.is_recording = False
        start_time        = None
        deadline          = asyncio.get_event_loop().time() + timeout
        try:
            while True:
                remaining = deadline - asyncio.get_event_loop().time()
                if remaining <= 0:
                    break
                try:
                    data = await asyncio.wait_for(
                        self.websocket.receive_json(),
                        timeout=min(remaining, 5.0),
                    )
                except asyncio.TimeoutError:
                    self._check_connected()
                    continue
                t = data.get("type")
                if t == "audio_chunk":
                    if not self.is_recording:
                        self.is_recording = True
                        start_time        = datetime.utcnow()
                    self.audio_buffer.extend(base64.b64decode(data.get("audio_data", "")))
                elif t == "video_frame":
                    pass   # frames de suivi non analysés
                elif t == "answer_complete":
                    break
                elif t == "end_interview":
                    await self._cancel_interview()
                    raise WebSocketDisconnect(code=1000, reason="Terminé")
        except WebSocketDisconnect:
            raise
        except Exception as e:
            logger.error(f"Erreur attente suivi: {e}")
            return None, 0.0

        if not self.audio_buffer:
            return None, 0.0
        duration = (datetime.utcnow() - start_time).total_seconds() if start_time else 0.0
        wav      = self._buffer_to_wav(bytes(self.audio_buffer))
        self.audio_buffer.clear()
        return wav, duration

    async def _save_answer_to_db(
        self, question, transcript, audio_path, duration,
        eval_result, facial_data: Optional[FacialAnalysisData] = None,
    ):
        ev = AnswerEvaluationData(
            score=eval_result.get("score", 0.0),
            verdict=eval_result.get("verdict", ""),
            feedback=eval_result.get("feedback", ""),
            strengths=eval_result.get("strengths", []),
            improvements=eval_result.get("improvements", []),
            llm_model=eval_result.get("llm_model", ""),
            evaluated_at=datetime.utcnow(),
            weight=question.weight,
            facial_analysis=facial_data,
        )
        InterviewSessionCRUD.add_answer(
            self.session_id,
            Answer(
                question_order=question.order,
                question_text=question.get_text(self.lang),
                transcript=transcript,
                audio_file_path=audio_path,
                duration_seconds=duration,
                evaluation=ev,
            ),
        )
        InterviewSessionCRUD.save_answer_evaluation(
            session_id=self.session_id,
            question_order=question.order,
            evaluation=ev,
        )

    async def _transcribe_audio(self, wav_bytes: bytes) -> str:
        if not self.asr_service:
            return ""
        lang = self.lang
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(
                _asr_executor,
                lambda: self.asr_service.transcribe(wav_bytes, language=lang),
            ) or ""
        except Exception as e:
            logger.error(f"Erreur ASR : {e}")
            return ""

    # ── Fin d'entretien ───────────────────────────────────────────────────────

    async def _complete_interview(self):
        self.session = InterviewSessionCRUD.update_status(self.session_id, "completed")

        text  = _get_text("completed", self.lang, name=self.candidate_first_name)
        audio = await self._synthesize_bytes(text)
        extra = {
            "total_questions": len(self.position.questions),
            "total_answers":   len(self.session.answers),
            "position_title":  self.position.title,
            "candidate_name":  self.candidate_full_name,
        }
        if audio:
            await self._send_audio_chunked(audio, "interview_completed", extra)
        else:
            await manager.send_json(
                self.session_id,
                {"type": "interview_completed", "data": extra},
            )

        asyncio.create_task(self._run_global_evaluation())

    async def _run_global_evaluation(self):
        try:
            from backend.services.llm_service import get_llm_service
            from backend.evaluation.service import EvaluationService
            llm = get_llm_service()
            if not await llm.is_available():
                return
            svc    = EvaluationService(llm_service=llm, asr_service=self.asr_service)
            result = await svc.evaluate_full_session(self.session_id, language=self.lang)
            if result and manager.is_connected(self.session_id):
                await manager.send_json(self.session_id, {
                    "type": "global_evaluation",
                    "data": {
                        "decision":           result.decision,
                        "decision_label":     result.decision_label,
                        "decision_color":     result.decision_color,
                        "candidate_name":     self.candidate_full_name,
                        "position_title":     self.position.title,
                        "total_questions":    result.total_questions,
                        "answered_questions": result.answered_questions,
                    },
                })
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