"""
Service LLM - Évaluation des réponses via Ollama + Llama 3
Pipeline: Transcription → LLM → Score / Feedback multilingue
"""

import json
import logging
import re
import httpx
from typing import Optional

logger = logging.getLogger(__name__)

# ── Prompts multilingues ───────────────────────────────────────────────────

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

_USER_PROMPT = {
    "ar": "السؤال: {question}\n\nإجابة المرشح: {answer}\n\nقيّم هذه الإجابة:",
    "fr": "Question : {question}\n\nRéponse du candidat : {answer}\n\nÉvalue cette réponse :",
    "en": "Question: {question}\n\nCandidate's answer: {answer}\n\nEvaluate this answer:",
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
        Évalue la réponse d'un candidat et retourne un dict structuré.

        Returns:
            {
                score: float (0–10),
                verdict: str,
                strengths: list[str],
                improvements: list[str],
                feedback: str,
                llm_model: str,
                evaluated: bool,
            }
        """
        lang = language if language in ("ar", "fr", "en") else "fr"

        # Réponse vide → score 0 immédiat
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

        raw = await self._call_ollama(system, user)
        parsed = self._parse_json(raw, lang)
        parsed["llm_model"] = self.model
        parsed["evaluated"] = True

        logger.info(
            f"Évaluation LLM [{lang}] | score={parsed['score']}/10 "
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

        Returns:
            {
                global_score: float,
                global_verdict: str,
                recommendation: str,
                key_strengths: list,
                key_improvements: list,
                summary: str,
            }
        """
        lang = language if language in ("ar", "fr", "en") else "fr"

        if not answers_eval:
            return self._empty_summary(lang)

        scores = [a.get("score", 0) for a in answers_eval]
        avg = round(sum(scores) / len(scores), 2)

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

        raw = await self._call_ollama("", prompts[lang])
        result = self._parse_json(raw, lang)
        result.setdefault("global_score", avg)
        result.setdefault("global_verdict", self._score_to_verdict(avg, lang))
        result.setdefault("recommendation", "")
        result.setdefault("key_strengths", [])
        result.setdefault("key_improvements", [])
        result.setdefault("summary", "")
        return result

    # ── HTTP Ollama ───────────────────────────────────────────────────────────

    async def _call_ollama(self, system: str, user: str) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": user})

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "top_p": 0.9,
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
                data = resp.json()
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
        # Extraire le bloc JSON (résistant aux balises markdown)
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

    def _normalize(self, obj: dict, lang: str) -> dict:
        """Normalise et valide les champs de l'évaluation."""
        try:
            score = float(obj.get("score", 5))
            score = max(0.0, min(10.0, score))
        except (TypeError, ValueError):
            score = 5.0

        return {
            "score": round(score, 1),
            "verdict": str(obj.get("verdict", self._score_to_verdict(score, lang))),
            "strengths": list(obj.get("strengths", [])),
            "improvements": list(obj.get("improvements", [])),
            "feedback": str(obj.get("feedback", "")),
        }

    def _fallback_result(self, lang: str) -> dict:
        """Résultat par défaut en cas d'erreur LLM."""
        msgs = {
            "fr": "Évaluation non disponible (erreur LLM).",
            "en": "Evaluation unavailable (LLM error).",
            "ar": "التقييم غير متاح (خطأ في النموذج).",
        }
        return {
            "score": 5.0,
            "verdict": self._score_to_verdict(5.0, lang),
            "strengths": [],
            "improvements": [],
            "feedback": msgs.get(lang, msgs["fr"]),
        }

    def _empty_summary(self, lang: str) -> dict:
        msgs = {
            "fr": "Aucune réponse à évaluer.",
            "en": "No answers to evaluate.",
            "ar": "لا توجد إجابات للتقييم.",
        }
        return {
            "global_score": 0.0,
            "global_verdict": self._score_to_verdict(0.0, lang),
            "recommendation": "",
            "key_strengths": [],
            "key_improvements": [],
            "summary": msgs.get(lang, msgs["fr"]),
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
            base_url=getattr(settings, "OLLAMA_URL", "http://localhost:11434"),
            model=getattr(settings, "OLLAMA_MODEL", "llama3"),
            timeout=getattr(settings, "OLLAMA_TIMEOUT", 60.0),
        )
    return _llm_instance