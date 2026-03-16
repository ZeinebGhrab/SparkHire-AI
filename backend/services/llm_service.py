"""
Service LLM — Évaluation des réponses via Ollama + Llama 3
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
    "ar": """أنت محكّم صارم لمقابلات التوظيف. قيّم إجابة المرشح بموضوعية وصرامة.

معايير التقييم الصارمة:
- 9-10 : إجابة استثنائية، دقيقة، مع أمثلة ملموسة وعمق تقني نادر
- 7-8  : إجابة جيدة وواضحة، لكن تفتقر لبعض التفاصيل أو الأمثلة
- 5-6  : إجابة سطحية أو مبهمة، تفتقر للدقة التقنية
- 3-4  : إجابة ضعيفة، أخطاء واضحة أو فهم جزئي للموضوع
- 0-2  : إجابة خاطئة، فارغة أو خارج الموضوع تماماً

تحذير: لا تتساهل في التقييم. الإجابة العامة أو المكررة لا تستحق أكثر من 5/10.
أعد JSON فقط بالشكل التالي بدون أي نص إضافي:
{
  "score": <رقم من 0 إلى 10>,
  "verdict": "<ممتاز|جيد جداً|جيد|مقبول|ضعيف>",
  "strengths": ["<نقطة قوة 1>", "<نقطة قوة 2>"],
  "improvements": ["<نقطة تحسين 1>", "<نقطة تحسين 2>"],
  "feedback": "<ملاحظة مفصلة بثلاثة أسطر كحد أقصى>"
}""",

    "fr": """Tu es un évaluateur sévère et rigoureux d'entretiens de recrutement. Tu notes avec exigence.

Barème strict :
- 9-10 : Réponse exceptionnelle, précise, structurée, avec exemples concrets et maîtrise technique rare
- 7-8  : Bonne réponse, claire, mais manque de profondeur ou d'exemples spécifiques
- 5-6  : Réponse superficielle ou vague, imprécisions techniques notables
- 3-4  : Réponse faible, erreurs ou compréhension partielle du sujet
- 0-2  : Réponse incorrecte, hors sujet ou absence de réponse

Avertissement : Ne sois PAS complaisant. Une réponse générique ou floue ne dépasse pas 5/10.
Retourne UNIQUEMENT un JSON sans texte supplémentaire :
{
  "score": <nombre de 0 à 10>,
  "verdict": "<Excellent|Très bien|Bien|Acceptable|Insuffisant>",
  "strengths": ["<point fort 1>", "<point fort 2>"],
  "improvements": ["<axe d'amélioration 1>", "<axe d'amélioration 2>"],
  "feedback": "<commentaire détaillé en 3 lignes max>"
}""",

    "en": """You are a strict and demanding recruitment interview evaluator. You grade with rigor.

Strict grading scale:
- 9-10: Exceptional answer, precise, structured, with concrete examples and rare technical mastery
- 7-8 : Good answer, clear, but lacking depth or specific examples
- 5-6 : Superficial or vague answer, notable technical inaccuracies
- 3-4 : Weak answer, errors or partial understanding of the topic
- 0-2 : Incorrect, off-topic, or empty answer

Warning: Do NOT be lenient. A generic or vague answer scores no more than 5/10.
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
    "ar": """أنت محكّم صارم لمقابلات التوظيف. قيّم الإجابة بصرامة وحدد إن كانت تحتاج توضيحاً.

معايير التقييم الصارمة:
- 9-10 : إجابة استثنائية، دقيقة، مع أمثلة ملموسة وعمق تقني نادر
- 7-8  : إجابة جيدة وواضحة، لكن تفتقر لبعض التفاصيل أو الأمثلة
- 5-6  : إجابة سطحية أو مبهمة، تفتقر للدقة التقنية
- 3-4  : إجابة ضعيفة، أخطاء واضحة أو فهم جزئي
- 0-2  : إجابة خاطئة أو فارغة

قواعد الاستفسار:
- اطرح سؤال متابعة إذا كانت الإجابة غامضة أو غير كافية (score < 8)
- لا تطرح سؤال متابعة إذا كانت الإجابة ممتازة (score >= 8) أو إذا كانت فارغة
- السؤال يجب أن يكون قصيراً (جملة واحدة) ومباشراً ومرتبطاً بالإجابة

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

    "fr": """Tu es un évaluateur sévère d'entretiens de recrutement. Tu notes avec exigence ET tu détermines si une question de suivi est nécessaire.

Barème strict :
- 9-10 : Réponse exceptionnelle, précise, avec exemples concrets et maîtrise technique rare
- 7-8  : Bonne réponse mais manque de profondeur ou d'exemples spécifiques
- 5-6  : Réponse superficielle ou vague, imprécisions notables
- 3-4  : Réponse faible, erreurs ou compréhension partielle
- 0-2  : Réponse incorrecte, hors sujet ou absente

Règles pour le suivi :
- Pose une question de suivi si la réponse est vague, incomplète ou manque d'exemples (score < 8)
- Ne pose PAS de question de suivi si la réponse est excellente (score >= 8) ou si elle est vide
- La question doit être courte (une phrase), directe, et liée spécifiquement à la réponse

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

    "en": """You are a strict recruitment interview evaluator. You grade with rigor AND determine if a follow-up is needed.

Strict grading scale:
- 9-10: Exceptional, precise, with concrete examples and rare technical mastery
- 7-8 : Good answer but lacking depth or specific examples
- 5-6 : Superficial or vague, notable inaccuracies
- 3-4 : Weak, errors or partial understanding
- 0-2 : Incorrect, off-topic, or empty

Follow-up rules:
- Ask a follow-up if the answer is vague, incomplete, or lacks examples (score < 8)
- Do NOT ask a follow-up if the answer is excellent (score >= 8) or empty
- The question must be short (one sentence), direct, and tied to the given answer

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
    "ar": """أنت محكّم صارم لمقابلات التوظيف. لديك السؤال الأصلي، الإجابة الأولى، وإجابة التوضيح.
قيّم الإجابة الكاملة بصرامة. إذا كانت إجابة التوضيح أفضل، يمكن رفع الدرجة قليلاً، لكن لا تكن متساهلاً.
أعد JSON فقط:
{
  "score": <رقم من 0 إلى 10>,
  "verdict": "<ممتاز|جيد جداً|جيد|مقبول|ضعيف>",
  "strengths": ["<نقطة قوة>"],
  "improvements": ["<نقطة تحسين>"],
  "feedback": "<تقييم شامل يأخذ بعين الاعتبار كلتا الإجابتين>"
}""",

    "fr": """Tu es un évaluateur sévère d'entretiens de recrutement. Tu as la question originale, la première réponse et la réponse de clarification.
Évalue l'ensemble avec rigueur. Si la clarification améliore la réponse, tu peux légèrement rehausser le score, mais reste exigeant.
Retourne UNIQUEMENT ce JSON :
{
  "score": <nombre de 0 à 10>,
  "verdict": "<Excellent|Très bien|Bien|Acceptable|Insuffisant>",
  "strengths": ["<point fort>"],
  "improvements": ["<axe d'amélioration>"],
  "feedback": "<évaluation globale tenant compte des deux réponses>"
}""",

    "en": """You are a strict recruitment interview evaluator. You have the original question, first answer, and clarification answer.
Evaluate the complete response with rigor. If the clarification improves the answer, you may slightly raise the score, but remain demanding.
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
    "ar": {"score": 0, "verdict": "ضعيف", "strengths": [], "improvements": ["لم يتم تقديم أي إجابة"], "feedback": "لم يقدم المرشح أي إجابة على هذا السؤال."},
    "fr": {"score": 0, "verdict": "Insuffisant", "strengths": [], "improvements": ["Aucune réponse fournie"], "feedback": "Le candidat n'a fourni aucune réponse à cette question."},
    "en": {"score": 0, "verdict": "Poor", "strengths": [], "improvements": ["No answer provided"], "feedback": "The candidate did not provide any answer to this question."},
}

# ── Prompt résumé global ──────────────────────────────────────────────────────
# Compact et contraint pour éviter la troncature de llama3.2.
# global_verdict supprimé — average_score + decision suffisent.

_GLOBAL_SUMMARY_PROMPT = {
    "fr": """\
Tu es un DRH expérimenté. Voici les résultats d'entretien :
Candidat : {candidate_name}
Poste    : {position_title}
Score moyen pondéré : {avg}/10

Détail par question :
{detail}

Règles de décision (OBLIGATOIRES) :
- score >= 7.0  → recommendation = "Embaucher"
- 5.0 <= score < 7.0 → recommendation = "En attente"
- score < 5.0   → recommendation = "Refuser"

Réponds UNIQUEMENT avec ce JSON (pas de markdown, pas de texte avant/après) :
{{"recommendation":"<Embaucher|En attente|Refuser>","decision_reason":"<1 phrase justifiant la décision>","key_strengths":["<point fort 1>","<point fort 2>"],"key_improvements":["<axe 1>","<axe 2>"],"summary":"<résumé en 2-3 phrases>"}}""",

    "en": """\
You are an experienced HR director. Here are the interview results:
Candidate : {candidate_name}
Position  : {position_title}
Weighted average score: {avg}/10

Per-question detail:
{detail}

Decision rules (MANDATORY):
- score >= 7.0  → recommendation = "Hire"
- 5.0 <= score < 7.0 → recommendation = "On Hold"
- score < 5.0   → recommendation = "Reject"

Reply ONLY with this JSON (no markdown, no text before/after):
{{"recommendation":"<Hire|On Hold|Reject>","decision_reason":"<1 sentence justifying decision>","key_strengths":["<strength 1>","<strength 2>"],"key_improvements":["<improvement 1>","<improvement 2>"],"summary":"<2-3 sentence summary>"}}""",

    "ar": """\
أنت مدير موارد بشرية خبير. إليك نتائج المقابلة:
المرشح  : {candidate_name}
المنصب  : {position_title}
متوسط الدرجة المرجح : {avg}/10

تفاصيل الأسئلة:
{detail}

قواعد القرار (إلزامية):
- score >= 7.0  → recommendation = "توظيف"
- 5.0 <= score < 7.0 → recommendation = "قيد الانتظار"
- score < 5.0   → recommendation = "رفض"

أعد JSON فقط (بدون markdown، بدون نص قبله أو بعده):
{{"recommendation":"<توظيف|قيد الانتظار|رفض>","decision_reason":"<جملة واحدة تبرر القرار>","key_strengths":["<نقطة قوة 1>","<نقطة قوة 2>"],"key_improvements":["<محور 1>","<محور 2>"],"summary":"<ملخص في 2-3 جمل>"}}""",
}


class OllamaLLMService:
    """Service d'évaluation LLM via Ollama (Llama 3 local)."""

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
        lang = language if language in ("ar", "fr", "en") else "fr"
        if not answer or len(answer.strip()) < 5:
            result = dict(_EMPTY_ANSWER_RESULT[lang])
            result["llm_model"] = self.model
            result["evaluated"] = True
            return result
        system = _SYSTEM_PROMPT[lang]
        user   = _USER_PROMPT[lang].format(question=question, answer=answer)
        if position_title:
            suffix = {"ar": f"\n\nالمنصب: {position_title}", "fr": f"\n\nPoste : {position_title}", "en": f"\n\nPosition: {position_title}"}
            user += suffix[lang]
        raw    = await self._call_ollama(system, user)
        parsed = self._parse_json(raw, lang)
        parsed["llm_model"] = self.model
        parsed["evaluated"] = True
        logger.info(f"Évaluation [{lang}] Q score={parsed['score']}/10 verdict={parsed['verdict']}")
        return parsed

    # ── Évaluation avec détection de suivi ────────────────────────────────────

    async def evaluate_with_followup(
        self,
        question: str,
        answer: str,
        language: str = "fr",
        position_title: str = "",
    ) -> dict:
        lang = language if language in ("ar", "fr", "en") else "fr"
        if not answer or len(answer.strip()) < 5:
            result = dict(_EMPTY_ANSWER_RESULT[lang])
            result.update({"llm_model": self.model, "evaluated": True, "needs_followup": False, "followup_question": ""})
            return result
        system = _SYSTEM_PROMPT_FOLLOWUP[lang]
        user   = _USER_PROMPT[lang].format(question=question, answer=answer)
        if position_title:
            suffix = {"ar": f"\n\nالمنصب: {position_title}", "fr": f"\n\nPoste : {position_title}", "en": f"\n\nPosition: {position_title}"}
            user += suffix[lang]
        raw    = await self._call_ollama(system, user)
        parsed = self._parse_followup_json(raw, lang)
        parsed["llm_model"] = self.model
        parsed["evaluated"] = True
        logger.info(
            f"Évaluation+Suivi [{lang}] score={parsed['score']}/10 "
            f"needs_followup={parsed['needs_followup']}"
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
        lang = language if language in ("ar", "fr", "en") else "fr"
        if not followup_answer or len(followup_answer.strip()) < 5:
            return await self.evaluate_answer(question, first_answer, language, position_title)
        system = _SYSTEM_PROMPT_FINAL[lang]
        user   = _USER_PROMPT_FINAL[lang].format(
            question=question, answer=first_answer,
            followup_q=followup_question, followup_a=followup_answer,
        )
        if position_title:
            suffix = {"ar": f"\n\nالمنصب: {position_title}", "fr": f"\n\nPoste : {position_title}", "en": f"\n\nPosition: {position_title}"}
            user += suffix[lang]
        raw    = await self._call_ollama(system, user)
        parsed = self._parse_json(raw, lang)
        parsed["llm_model"] = self.model
        parsed["evaluated"] = True
        return parsed

    # ── Résumé global ─────────────────────────────────────────────────────────

    async def generate_global_summary(
        self,
        answers_eval: list[dict],
        position_title: str,
        candidate_name: str,
        language: str = "fr",
        weighted_avg: Optional[float] = None,
    ) -> dict:
        """
        Génère un résumé global depuis les évaluations individuelles.
        Retourne : recommendation, decision_reason, key_strengths,
                   key_improvements, summary.
        global_verdict supprimé — redondant avec average_score.
        """
        lang = language if language in ("ar", "fr", "en") else "fr"

        if not answers_eval:
            return self._empty_summary(lang)

        # Moyenne pondérée
        if weighted_avg is not None:
            avg = round(weighted_avg, 2)
        else:
            sw = [(float(a.get("score", 0)), float(a.get("weight", 1.0))) for a in answers_eval]
            total_w = sum(w for _, w in sw)
            avg = round(sum(s * w for s, w in sw) / total_w, 2) if total_w > 0 else 0.0

        # Détail compact
        detail_lines = []
        for i, a in enumerate(answers_eval, 1):
            feedback_short = (a.get("feedback") or "")[:80].replace("\n", " ")
            w = a.get("weight", 1.0)
            detail_lines.append(f"Q{i} (score={a.get('score', 0)}/10, poids={w}) : {feedback_short}")
        detail = "\n".join(detail_lines)

        prompt_tpl = _GLOBAL_SUMMARY_PROMPT.get(lang, _GLOBAL_SUMMARY_PROMPT["fr"])
        prompt = prompt_tpl.format(
            candidate_name=candidate_name,
            position_title=position_title,
            avg=avg,
            detail=detail,
        )

        raw    = await self._call_ollama("", prompt)
        result = self._parse_global_json(raw, lang)

        # Garantie de complétude
        result = self._ensure_global_fields(result, answers_eval, avg, lang)
        return result

    # ── HTTP Ollama ───────────────────────────────────────────────────────────

    async def _call_ollama(self, system: str, user: str) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": user})
        payload = {
            "model":    self.model,
            "messages": messages,
            "stream":   False,
            "options":  {"temperature": 0.1, "top_p": 0.85, "num_predict": 512},
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(f"{self.base_url}/api/chat", json=payload)
                resp.raise_for_status()
                content = resp.json().get("message", {}).get("content", "")
                logger.debug(f"Ollama raw: {content[:200]}")
                return content
        except httpx.TimeoutException:
            logger.error("Timeout Ollama")
            return ""
        except Exception as e:
            logger.error(f"Erreur Ollama : {e}")
            return ""

    # ── Parsing par-réponse ───────────────────────────────────────────────────

    def _parse_json(self, raw: str, lang: str) -> dict:
        for pattern in (r"```json\s*([\s\S]+?)\s*```", r"```\s*([\s\S]+?)\s*```", r"(\{[\s\S]+\})"):
            m = re.search(pattern, raw)
            if m:
                try:
                    return self._normalize(json.loads(m.group(1)), lang)
                except json.JSONDecodeError:
                    continue
        logger.warning(f"Parse JSON échoué (per-answer) : {raw[:200]}")
        return self._fallback_result(lang)

    def _parse_followup_json(self, raw: str, lang: str) -> dict:
        for pattern in (r"```json\s*([\s\S]+?)\s*```", r"```\s*([\s\S]+?)\s*```", r"(\{[\s\S]+\})"):
            m = re.search(pattern, raw)
            if m:
                try:
                    obj  = json.loads(m.group(1))
                    base = self._normalize(obj, lang)
                    base["needs_followup"]    = bool(obj.get("needs_followup", False))
                    base["followup_question"] = str(obj.get("followup_question", "")).strip()
                    if base["score"] >= 8:
                        base["needs_followup"]    = False
                        base["followup_question"] = ""
                    return base
                except json.JSONDecodeError:
                    continue
        result = self._fallback_result(lang)
        result["needs_followup"]    = False
        result["followup_question"] = ""
        return result

    # ── Parsing résumé global ─────────────────────────────────────────────────

    def _parse_global_json(self, raw: str, lang: str) -> dict:
        """
        Parser dédié au résumé global.
        Champs attendus : recommendation, decision_reason,
                          key_strengths, key_improvements, summary.
        global_verdict absent — intentionnellement supprimé.
        """
        for pattern in (r"```json\s*([\s\S]+?)\s*```", r"```\s*([\s\S]+?)\s*```", r"(\{[\s\S]+\})"):
            m = re.search(pattern, raw)
            if m:
                try:
                    return self._normalize_global(json.loads(m.group(1)))
                except json.JSONDecodeError:
                    continue
        logger.warning(f"Parse JSON échoué (global) : {raw[:200]}")
        return {"recommendation": "", "decision_reason": "", "key_strengths": [], "key_improvements": [], "summary": ""}

    def _normalize_global(self, obj: dict) -> dict:
        def _list(key):
            val = obj.get(key) or []
            if isinstance(val, list):
                return [str(v) for v in val if v]
            return [str(val).strip()] if isinstance(val, str) and val.strip() else []

        return {
            "recommendation":   str(obj.get("recommendation") or "").strip(),
            "decision_reason":  str(obj.get("decision_reason") or "").strip(),
            "key_strengths":    _list("key_strengths"),
            "key_improvements": _list("key_improvements"),
            "summary":          str(obj.get("summary") or "").strip(),
        }

    def _ensure_global_fields(
        self,
        result: dict,
        answers_eval: list[dict],
        avg: float,
        lang: str,
    ) -> dict:
        """Fallback déterministe pour tous les champs globaux vides."""
        if not result.get("recommendation"):
            if lang == "fr":
                result["recommendation"] = "Embaucher" if avg >= 7 else ("En attente" if avg >= 5 else "Refuser")
            elif lang == "ar":
                result["recommendation"] = "توظيف" if avg >= 7 else ("قيد الانتظار" if avg >= 5 else "رفض")
            else:
                result["recommendation"] = "Hire" if avg >= 7 else ("On Hold" if avg >= 5 else "Reject")

        if not result.get("decision_reason"):
            n = len(answers_eval)
            if lang == "fr":
                result["decision_reason"] = (
                    f"Moyenne pondérée de {avg}/10 sur {n} question(s). "
                    f"Barème : ≥7 = Embaucher, 5–7 = En attente, <5 = Refuser."
                )
            elif lang == "ar":
                result["decision_reason"] = f"متوسط مرجح {avg}/10 على {n} سؤال."
            else:
                result["decision_reason"] = (
                    f"Weighted average {avg}/10 across {n} question(s). "
                    f"Scale: ≥7 = Hire, 5–7 = On Hold, <5 = Reject."
                )

        if not result.get("key_strengths"):
            seen, items = set(), []
            for a in answers_eval:
                for s in (a.get("strengths") or []):
                    if s and s not in seen:
                        seen.add(s); items.append(s)
            result["key_strengths"] = items[:4]

        if not result.get("key_improvements"):
            seen, items = set(), []
            for a in answers_eval:
                for imp in (a.get("improvements") or []):
                    if imp and imp not in seen:
                        seen.add(imp); items.append(imp)
            result["key_improvements"] = items[:4]

        if not result.get("summary"):
            scores_str = ", ".join(
                f"Q{a.get('question_order', i+1)}: {a.get('score', 0)}/10 (×{a.get('weight', 1.0)})"
                for i, a in enumerate(answers_eval)
            )
            reco = result["recommendation"]
            if lang == "fr":
                result["summary"] = (
                    f"Entretien de {len(answers_eval)} question(s) — "
                    f"moyenne pondérée {avg}/10. {scores_str}. "
                    f"Recommandation : {reco}."
                )
            elif lang == "ar":
                result["summary"] = f"مقابلة {len(answers_eval)} سؤال — متوسط {avg}/10. {scores_str}. التوصية : {reco}."
            else:
                result["summary"] = (
                    f"{len(answers_eval)}-question interview — "
                    f"weighted average {avg}/10. {scores_str}. "
                    f"Recommendation: {reco}."
                )

        return result

    # ── Normaliseurs par-réponse ──────────────────────────────────────────────

    def _normalize(self, obj: dict, lang: str) -> dict:
        try:
            score = max(0.0, min(10.0, float(obj.get("score", 5))))
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
        msgs = {"fr": "Évaluation non disponible (erreur LLM).", "en": "Evaluation unavailable (LLM error).", "ar": "التقييم غير متاح."}
        return {"score": 5.0, "verdict": self._score_to_verdict(5.0, lang), "strengths": [], "improvements": [], "feedback": msgs.get(lang, msgs["fr"])}

    def _empty_summary(self, lang: str) -> dict:
        return {"recommendation": "", "decision_reason": "", "key_strengths": [], "key_improvements": [], "summary": ""}

    @staticmethod
    def _score_to_verdict(score: float, lang: str) -> str:
        verdicts = {
            "fr": ["Insuffisant","Insuffisant","Insuffisant","Acceptable","Acceptable","Bien","Bien","Très bien","Très bien","Excellent","Excellent"],
            "en": ["Poor","Poor","Poor","Acceptable","Acceptable","Good","Good","Very Good","Very Good","Excellent","Excellent"],
            "ar": ["ضعيف","ضعيف","ضعيف","مقبول","مقبول","جيد","جيد","جيد جداً","جيد جداً","ممتاز","ممتاز"],
        }
        idx = min(10, max(0, round(score)))
        return verdicts.get(lang, verdicts["fr"])[idx]


# ── Singleton ─────────────────────────────────────────────────────────────────

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