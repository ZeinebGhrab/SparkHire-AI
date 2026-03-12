"""
Service LLM - Évaluation des réponses via Ollama + Llama 3
Pipeline: Transcription → LLM → Score / Feedback multilingue
+ Génération de questions de suivi si la réponse est floue
"""

import json
import logging
import re
import httpx
from typing import Optional

logger = logging.getLogger(__name__)

# ── Prompts multilingues — Évaluation standard ────────────────────────────────

_SYSTEM_PROMPT = {
    "ar": """أنت خبير تقييم مقابلات توظيف. مهمتك تقييم إجابة مرشح على سؤال مقابلة.
أعد JSON فقط بالشكل التالي بدون أي نص إضافي:
{
  "score": <رقم من 0 إلى 10>,
  "verdict": "<ممتاز|جيد جداً|جيد|مقبول|ضعيف>",
  "strengths": ["<نقطة قوة 1>", "<نقطة قوة 2>"],
  "improvements": ["<نقطة تحسين 1>", "<نقطة تحسين 2>"],
  "feedback": "<ملاحظة مفصلة بثلاثة أسطر كحد أقصى>"
}""",

    "fr": """Tu es un expert en évaluation d'entretiens de recrutement. Évalue la réponse du candidat.
Retourne UNIQUEMENT un JSON sans texte supplémentaire :
{
  "score": <nombre de 0 à 10>,
  "verdict": "<Excellent|Très bien|Bien|Acceptable|Insuffisant>",
  "strengths": ["<point fort 1>", "<point fort 2>"],
  "improvements": ["<axe d'amélioration 1>", "<axe d'amélioration 2>"],
  "feedback": "<commentaire détaillé en 3 lignes max>"
}""",

    "en": """You are a recruitment interview evaluation expert. Evaluate the candidate's answer.
Return ONLY a JSON object with no extra text:
{
  "score": <number from 0 to 10>,
  "verdict": "<Excellent|Very Good|Good|Acceptable|Poor>",
  "strengths": ["<strength 1>", "<strength 2>"],
  "improvements": ["<improvement area 1>", "<improvement area 2>"],
  "feedback": "<detailed comment in max 3 lines>"
}""",
}

# ── Prompts — Évaluation AVEC question de suivi ───────────────────────────────

_SYSTEM_PROMPT_FOLLOWUP = {
    "ar": """أنت خبير تقييم مقابلات توظيف. مهمتك تقييم إجابة مرشح وتحديد ما إذا كانت تحتاج إلى توضيح.

قواعد الاستفسار:
- اطرح سؤال متابعة إذا كانت الإجابة غامضة أو غير كافية أو تحتاج مثالاً ملموساً (score < 7)
- لا تطرح سؤال متابعة إذا كانت الإجابة واضحة وكاملة (score >= 7) أو إذا كانت الإجابة فارغة
- السؤال يجب أن يكون قصيراً (جملة واحدة) ومباشراً ومرتبطاً بالإجابة المقدمة

أعد JSON فقط بهذا الشكل بدون أي نص إضافي:
{
  "score": <رقم من 0 إلى 10>,
  "verdict": "<ممتاز|جيد جداً|جيد|مقبول|ضعيف>",
  "strengths": ["<نقطة قوة>"],
  "improvements": ["<نقطة تحسين>"],
  "feedback": "<ملاحظة مفصلة>",
  "needs_followup": <true|false>,
  "followup_question": "<سؤال متابعة واحد أو سلسلة فارغة إذا لم يلزم>"
}""",

    "fr": """Tu es un expert en évaluation d'entretiens de recrutement. Évalue la réponse ET détermine si une question de suivi est nécessaire.

Règles pour le suivi :
- Pose une question de suivi si la réponse est vague, incomplète ou manque d'exemples concrets (score < 7)
- Ne pose PAS de question de suivi si la réponse est claire et complète (score >= 7) ou si la réponse est vide
- La question doit être courte (une phrase), directe, et liée spécifiquement à la réponse fournie

Retourne UNIQUEMENT ce JSON sans texte supplémentaire :
{
  "score": <nombre de 0 à 10>,
  "verdict": "<Excellent|Très bien|Bien|Acceptable|Insuffisant>",
  "strengths": ["<point fort>"],
  "improvements": ["<axe d'amélioration>"],
  "feedback": "<commentaire détaillé>",
  "needs_followup": <true|false>,
  "followup_question": "<une question de suivi ou chaîne vide si non nécessaire>"
}""",

    "en": """You are a recruitment interview evaluation expert. Evaluate the answer AND determine if a follow-up question is needed.

Follow-up rules:
- Ask a follow-up if the answer is vague, incomplete, or lacks concrete examples (score < 7)
- Do NOT ask a follow-up if the answer is clear and complete (score >= 7) or if the answer is empty
- The question must be short (one sentence), direct, and specifically tied to the given answer

Return ONLY this JSON with no extra text:
{
  "score": <number from 0 to 10>,
  "verdict": "<Excellent|Very Good|Good|Acceptable|Poor>",
  "strengths": ["<strength>"],
  "improvements": ["<improvement area>"],
  "feedback": "<detailed comment>",
  "needs_followup": <true|false>,
  "followup_question": "<one follow-up question or empty string if not needed>"
}""",
}

# ── Prompts — Évaluation FINALE (avec réponse de suivi) ──────────────────────

_SYSTEM_PROMPT_FINAL = {
    "ar": """أنت خبير تقييم مقابلات توظيف. لديك السؤال الأصلي، الإجابة الأولى، وإجابة التوضيح.
قيّم الإجابة الكاملة مع الأخذ بعين الاعتبار كلتا الإجابتين.
أعد JSON فقط:
{
  "score": <رقم من 0 إلى 10>,
  "verdict": "<ممتاز|جيد جداً|جيد|مقبول|ضعيف>",
  "strengths": ["<نقطة قوة>"],
  "improvements": ["<نقطة تحسين>"],
  "feedback": "<تقييم شامل يأخذ بعين الاعتبار كلتا الإجابتين>"
}""",

    "fr": """Tu es un expert en évaluation d'entretiens. Tu as la question originale, la première réponse et la réponse de clarification.
Évalue l'ensemble en prenant en compte les deux réponses.
Retourne UNIQUEMENT ce JSON :
{
  "score": <nombre de 0 à 10>,
  "verdict": "<Excellent|Très bien|Bien|Acceptable|Insuffisant>",
  "strengths": ["<point fort>"],
  "improvements": ["<axe d'amélioration>"],
  "feedback": "<évaluation globale tenant compte des deux réponses>"
}""",

    "en": """You are a recruitment interview expert. You have the original question, first answer, and clarification answer.
Evaluate the complete response taking both answers into account.
Return ONLY this JSON:
{
  "score": <number from 0 to 10>,
  "verdict": "<Excellent|Very Good|Good|Acceptable|Poor>",
  "strengths": ["<strength>"],
  "improvements": ["<improvement area>"],
  "feedback": "<comprehensive evaluation considering both answers>"
}""",
}

_USER_PROMPT = {
    "ar": "السؤال: {question}\n\nإجابة المرشح: {answer}\n\nقيّم هذه الإجابة:",
    "fr": "Question : {question}\n\nRéponse du candidat : {answer}\n\nÉvalue cette réponse :",
    "en": "Question: {question}\n\nCandidate's answer: {answer}\n\nEvaluate this answer:",
}

_USER_PROMPT_FINAL = {
    "ar": "السؤال: {question}\n\nالإجابة الأولى: {answer}\n\nسؤال التوضيح: {followup_q}\n\nإجابة التوضيح: {followup_a}\n\nقيّم الإجابة الكاملة:",
    "fr": "Question : {question}\n\nPremière réponse : {answer}\n\nQuestion de suivi : {followup_q}\n\nRéponse de suivi : {followup_a}\n\nÉvalue la réponse complète :",
    "en": "Question: {question}\n\nFirst answer: {answer}\n\nFollow-up question: {followup_q}\n\nFollow-up answer: {followup_a}\n\nEvaluate the complete answer:",
}

_EMPTY_ANSWER_RESULT = {
    "ar": {
        "score": 0,
        "verdict": "ضعيف",
        "strengths": [],
        "improvements": ["لم يتم تقديم أي إجابة"],
        "feedback": "لم يقدم المرشح أي إجابة على هذا السؤال.",
    },
    "fr": {
        "score": 0,
        "verdict": "Insuffisant",
        "strengths": [],
        "improvements": ["Aucune réponse fournie"],
        "feedback": "Le candidat n'a fourni aucune réponse à cette question.",
    },
    "en": {
        "score": 0,
        "verdict": "Poor",
        "strengths": [],
        "improvements": ["No answer provided"],
        "feedback": "The candidate did not provide any answer to this question.",
    },
}


class OllamaLLMService:
    """
    Service d'évaluation LLM via Ollama (Llama 3 local).
    Compatible avec tout modèle disponible dans Ollama.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3",
        timeout: float = 60.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        logger.info(f"LLM Service initialisé | modèle={model} | url={base_url}")

    # ── Santé ─────────────────────────────────────────────────────────────────

    async def is_available(self) -> bool:
        """Vérifie qu'Ollama est en ligne."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(f"{self.base_url}/api/tags")
                return r.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama non disponible : {e}")
            return False

    # ── Évaluation principale ─────────────────────────────────────────────────

    async def evaluate_answer(
        self,
        question: str,
        answer: str,
        language: str = "fr",
        position_title: str = "",
    ) -> dict:
        """
        Évalue la réponse d'un candidat (sans question de suivi).
        Returns:
            { score, verdict, strengths, improvements, feedback, llm_model, evaluated }
        """
        lang = language if language in ("ar", "fr", "en") else "fr"

        if not answer or len(answer.strip()) < 5:
            result = dict(_EMPTY_ANSWER_RESULT[lang])
            result["llm_model"] = self.model
            result["evaluated"] = True
            return result

        system = _SYSTEM_PROMPT[lang]
        user   = _USER_PROMPT[lang].format(question=question, answer=answer)

        if position_title:
            suffix = {
                "ar": f"\n\nالمنصب: {position_title}",
                "fr": f"\n\nPoste : {position_title}",
                "en": f"\n\nPosition: {position_title}",
            }
            user += suffix[lang]

        raw    = await self._call_ollama(system, user)
        parsed = self._parse_json(raw, lang)
        parsed["llm_model"] = self.model
        parsed["evaluated"] = True

        logger.info(
            f"Évaluation LLM [{lang}] | score={parsed['score']}/10 "
            f"| verdict={parsed['verdict']}"
        )
        return parsed

    # ── Évaluation avec détection de suivi ────────────────────────────────────

    async def evaluate_with_followup(
        self,
        question: str,
        answer: str,
        language: str = "fr",
        position_title: str = "",
    ) -> dict:
        """
        Évalue la réponse ET détermine si une question de suivi est nécessaire.

        Returns:
            {
                score, verdict, strengths, improvements, feedback,
                llm_model, evaluated,
                needs_followup: bool,
                followup_question: str  (vide si pas de suivi nécessaire)
            }
        """
        lang = language if language in ("ar", "fr", "en") else "fr"

        # Réponse vide → pas de suivi
        if not answer or len(answer.strip()) < 5:
            result = dict(_EMPTY_ANSWER_RESULT[lang])
            result.update({
                "llm_model":       self.model,
                "evaluated":       True,
                "needs_followup":  False,
                "followup_question": "",
            })
            return result

        system = _SYSTEM_PROMPT_FOLLOWUP[lang]
        user   = _USER_PROMPT[lang].format(question=question, answer=answer)

        if position_title:
            suffix = {
                "ar": f"\n\nالمنصب: {position_title}",
                "fr": f"\n\nPoste : {position_title}",
                "en": f"\n\nPosition: {position_title}",
            }
            user += suffix[lang]

        raw    = await self._call_ollama(system, user)
        parsed = self._parse_followup_json(raw, lang)
        parsed["llm_model"] = self.model
        parsed["evaluated"] = True

        logger.info(
            f"Évaluation+Suivi LLM [{lang}] | score={parsed['score']}/10 "
            f"| needs_followup={parsed['needs_followup']} "
            f"| followup_q='{parsed.get('followup_question', '')[:60]}'"
        )
        return parsed

    # ── Évaluation finale (après réponse de suivi) ────────────────────────────

    async def evaluate_final_with_followup(
        self,
        question: str,
        first_answer: str,
        followup_question: str,
        followup_answer: str,
        language: str = "fr",
        position_title: str = "",
    ) -> dict:
        """
        Évalue la réponse complète (première réponse + réponse de suivi).

        Returns:
            { score, verdict, strengths, improvements, feedback, llm_model, evaluated }
        """
        lang = language if language in ("ar", "fr", "en") else "fr"

        # Si la réponse de suivi est vide, évaluation standard
        if not followup_answer or len(followup_answer.strip()) < 5:
            return await self.evaluate_answer(question, first_answer, language, position_title)

        system = _SYSTEM_PROMPT_FINAL[lang]
        user   = _USER_PROMPT_FINAL[lang].format(
            question=question,
            answer=first_answer,
            followup_q=followup_question,
            followup_a=followup_answer,
        )

        if position_title:
            suffix = {
                "ar": f"\n\nالمنصب: {position_title}",
                "fr": f"\n\nPoste : {position_title}",
                "en": f"\n\nPosition: {position_title}",
            }
            user += suffix[lang]

        raw    = await self._call_ollama(system, user)
        parsed = self._parse_json(raw, lang)
        parsed["llm_model"] = self.model
        parsed["evaluated"] = True

        logger.info(
            f"Évaluation Finale LLM [{lang}] | score={parsed['score']}/10 "
            f"| verdict={parsed['verdict']}"
        )
        return parsed

    # ── Résumé global ─────────────────────────────────────────────────────────

    async def generate_global_summary(
        self,
        answers_eval: list[dict],
        position_title: str,
        candidate_name: str,
        language: str = "fr",
    ) -> dict:
        """
        Génère un résumé global de l'entretien depuis les évaluations individuelles.
        """
        lang = language if language in ("ar", "fr", "en") else "fr"

        if not answers_eval:
            return self._empty_summary(lang)

        scores  = [a.get("score", 0) for a in answers_eval]
        avg     = round(sum(scores) / len(scores), 2)

        summaries_prompt = "\n".join(
            f"Q{i+1}: score={a.get('score', 0)}/10 | {a.get('feedback', '')}"
            for i, a in enumerate(answers_eval)
        )

        prompts = {
            "fr": (
                f"Tu évalues l'entretien de {candidate_name} pour le poste {position_title}.\n"
                f"Score moyen : {avg}/10\n"
                f"Détail par question :\n{summaries_prompt}\n\n"
                "Génère un résumé global en JSON :\n"
                '{"global_score":<0-10>,"global_verdict":"<str>","recommendation":"<Embaucher|À considérer|Refuser>",'
                '"key_strengths":["<str>"],"key_improvements":["<str>"],"summary":"<3 phrases>"}'
            ),
            "en": (
                f"You are evaluating the interview of {candidate_name} for position {position_title}.\n"
                f"Average score: {avg}/10\n"
                f"Per-question detail:\n{summaries_prompt}\n\n"
                "Generate a global summary as JSON:\n"
                '{"global_score":<0-10>,"global_verdict":"<str>","recommendation":"<Hire|Consider|Reject>",'
                '"key_strengths":["<str>"],"key_improvements":["<str>"],"summary":"<3 sentences>"}'
            ),
            "ar": (
                f"أنت تقيّم مقابلة {candidate_name} لمنصب {position_title}.\n"
                f"المتوسط : {avg}/10\n"
                f"التفاصيل :\n{summaries_prompt}\n\n"
                "أنشئ ملخصاً عاماً بصيغة JSON :\n"
                '{"global_score":<0-10>,"global_verdict":"<str>","recommendation":"<توظيف|للنظر|رفض>",'
                '"key_strengths":["<str>"],"key_improvements":["<str>"],"summary":"<3 جمل>"}'
            ),
        }

        raw    = await self._call_ollama("", prompts[lang])
        result = self._parse_json(raw, lang)
        result.setdefault("global_score",      avg)
        result.setdefault("global_verdict",    self._score_to_verdict(avg, lang))
        result.setdefault("recommendation",    "")
        result.setdefault("key_strengths",     [])
        result.setdefault("key_improvements",  [])
        result.setdefault("summary",           "")
        return result

    # ── HTTP Ollama ───────────────────────────────────────────────────────────

    async def _call_ollama(self, system: str, user: str) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": user})

        payload = {
            "model":   self.model,
            "messages": messages,
            "stream":  False,
            "options": {
                "temperature": 0.3,
                "top_p":       0.9,
                "num_predict": 512,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                )
                resp.raise_for_status()
                data    = resp.json()
                content = data.get("message", {}).get("content", "")
                logger.debug(f"Ollama raw: {content[:200]}")
                return content

        except httpx.TimeoutException:
            logger.error("Timeout Ollama")
            return ""
        except Exception as e:
            logger.error(f"Erreur Ollama : {e}")
            return ""

    # ── Parsing ───────────────────────────────────────────────────────────────

    def _parse_json(self, raw: str, lang: str) -> dict:
        """Extrait et valide le JSON retourné par le LLM."""
        for pattern in (
            r"```json\s*([\s\S]+?)\s*```",
            r"```\s*([\s\S]+?)\s*```",
            r"(\{[\s\S]+\})",
        ):
            m = re.search(pattern, raw)
            if m:
                try:
                    obj = json.loads(m.group(1))
                    return self._normalize(obj, lang)
                except json.JSONDecodeError:
                    continue

        logger.warning(f"Impossible de parser la réponse LLM : {raw[:300]}")
        return self._fallback_result(lang)

    def _parse_followup_json(self, raw: str, lang: str) -> dict:
        """Extrait et valide le JSON avec champs de suivi."""
        for pattern in (
            r"```json\s*([\s\S]+?)\s*```",
            r"```\s*([\s\S]+?)\s*```",
            r"(\{[\s\S]+\})",
        ):
            m = re.search(pattern, raw)
            if m:
                try:
                    obj = json.loads(m.group(1))
                    base = self._normalize(obj, lang)
                    base["needs_followup"]   = bool(obj.get("needs_followup", False))
                    base["followup_question"] = str(obj.get("followup_question", "")).strip()
                    # Sécurité : si score >= 7, forcer needs_followup = False
                    if base["score"] >= 7:
                        base["needs_followup"]    = False
                        base["followup_question"] = ""
                    return base
                except json.JSONDecodeError:
                    continue

        logger.warning(f"Impossible de parser la réponse LLM (followup) : {raw[:300]}")
        result = self._fallback_result(lang)
        result["needs_followup"]    = False
        result["followup_question"] = ""
        return result

    def _normalize(self, obj: dict, lang: str) -> dict:
        """Normalise et valide les champs de l'évaluation."""
        try:
            score = float(obj.get("score", 5))
            score = max(0.0, min(10.0, score))
        except (TypeError, ValueError):
            score = 5.0

        return {
            "score":        round(score, 1),
            "verdict":      str(obj.get("verdict", self._score_to_verdict(score, lang))),
            "strengths":    list(obj.get("strengths", [])),
            "improvements": list(obj.get("improvements", [])),
            "feedback":     str(obj.get("feedback", "")),
        }

    def _fallback_result(self, lang: str) -> dict:
        """Résultat par défaut en cas d'erreur LLM."""
        msgs = {
            "fr": "Évaluation non disponible (erreur LLM).",
            "en": "Evaluation unavailable (LLM error).",
            "ar": "التقييم غير متاح (خطأ في النموذج).",
        }
        return {
            "score":        5.0,
            "verdict":      self._score_to_verdict(5.0, lang),
            "strengths":    [],
            "improvements": [],
            "feedback":     msgs.get(lang, msgs["fr"]),
        }

    def _empty_summary(self, lang: str) -> dict:
        msgs = {
            "fr": "Aucune réponse à évaluer.",
            "en": "No answers to evaluate.",
            "ar": "لا توجد إجابات للتقييم.",
        }
        return {
            "global_score":     0.0,
            "global_verdict":   self._score_to_verdict(0.0, lang),
            "recommendation":   "",
            "key_strengths":    [],
            "key_improvements": [],
            "summary":          msgs.get(lang, msgs["fr"]),
        }

    @staticmethod
    def _score_to_verdict(score: float, lang: str) -> str:
        verdicts = {
            "fr": ["Insuffisant", "Insuffisant", "Insuffisant", "Acceptable",
                   "Acceptable", "Bien", "Bien", "Très bien", "Très bien",
                   "Excellent", "Excellent"],
            "en": ["Poor", "Poor", "Poor", "Acceptable", "Acceptable",
                   "Good", "Good", "Very Good", "Very Good", "Excellent", "Excellent"],
            "ar": ["ضعيف", "ضعيف", "ضعيف", "مقبول", "مقبول",
                   "جيد", "جيد", "جيد جداً", "جيد جداً", "ممتاز", "ممتاز"],
        }
        idx = min(10, max(0, round(score)))
        return verdicts.get(lang, verdicts["fr"])[idx]


# ── Singleton ──────────────────────────────────────────────────────────────

_llm_instance: Optional[OllamaLLMService] = None


def get_llm_service() -> OllamaLLMService:
    global _llm_instance
    if _llm_instance is None:
        from backend.config import settings
        _llm_instance = OllamaLLMService(
            base_url=getattr(settings, "OLLAMA_URL",    "http://localhost:11434"),
            model=getattr(settings, "OLLAMA_MODEL",     "llama3"),
            timeout=getattr(settings, "OLLAMA_TIMEOUT", 60.0),
        )
    return _llm_instance