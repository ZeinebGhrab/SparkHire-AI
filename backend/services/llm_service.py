"""
Service LLM — Évaluation des réponses via Ollama + Llama 3
Pipeline: Transcription → LLM → Score / Feedback multilingue
+ Génération de questions de suivi si la réponse est floue

CORRECTIONS v2 :
  - _parse_global_json() dédié au résumé global (champs différents des éval par réponse)
  - generate_global_summary() utilise _parse_global_json au lieu de _parse_json
  - Fallback automatique : calcul des champs manquants depuis les évaluations individuelles
  - Prompt global plus court et plus fiable pour llama3.2
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
المعيار: الدقة التقنية، الأمثلة الملموسة، والطلاقة.
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
Critères : précision technique, exemples concrets, fluidité et structure.
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
Criteria: technical accuracy, concrete examples, fluency and structure.
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

# ── Prompts résumé global ─────────────────────────────────────────────────────
# NOTE : Prompt délibérément court et structuré pour llama3.2 qui tronque les
#        longues sorties. Le JSON cible ne contient que les 7 champs nécessaires.

_GLOBAL_SUMMARY_PROMPT = {
    "fr": """\
Tu es un DRH expérimenté. Voici les résultats d'entretien :
Candidat : {candidate_name}
Poste    : {position_title}
Score moyen LLM : {avg}/10

Détail par question :
{detail}

Règles de décision (OBLIGATOIRES) :
- score >= 7.0  → recommendation = "Embaucher"
- 5.0 <= score < 7.0 → recommendation = "En attente"
- score < 5.0   → recommendation = "Refuser"

Réponds UNIQUEMENT avec ce JSON (pas de markdown, pas de texte avant/après) :
{{"global_score":{avg_f},"global_verdict":"{verdict}","recommendation":"<Embaucher|En attente|Refuser>","decision_reason":"<1 phrase justifiant la décision>","key_strengths":["<point fort 1>","<point fort 2>"],"key_improvements":["<axe 1>","<axe 2>"],"summary":"<résumé en 2-3 phrases>"}}""",

    "en": """\
You are an experienced HR director. Here are the interview results:
Candidate : {candidate_name}
Position  : {position_title}
Average LLM score: {avg}/10

Per-question detail:
{detail}

Decision rules (MANDATORY):
- score >= 7.0  → recommendation = "Hire"
- 5.0 <= score < 7.0 → recommendation = "On Hold"
- score < 5.0   → recommendation = "Reject"

Reply ONLY with this JSON (no markdown, no text before/after):
{{"global_score":{avg_f},"global_verdict":"{verdict}","recommendation":"<Hire|On Hold|Reject>","decision_reason":"<1 sentence justifying decision>","key_strengths":["<strength 1>","<strength 2>"],"key_improvements":["<improvement 1>","<improvement 2>"],"summary":"<2-3 sentence summary>"}}""",

    "ar": """\
أنت مدير موارد بشرية خبير. إليك نتائج المقابلة:
المرشح  : {candidate_name}
المنصب  : {position_title}
متوسط الدرجة : {avg}/10

تفاصيل الأسئلة:
{detail}

قواعد القرار (إلزامية):
- score >= 7.0  → recommendation = "توظيف"
- 5.0 <= score < 7.0 → recommendation = "قيد الانتظار"
- score < 5.0   → recommendation = "رفض"

أعد JSON فقط (بدون markdown، بدون نص قبله أو بعده):
{{"global_score":{avg_f},"global_verdict":"{verdict}","recommendation":"<توظيف|قيد الانتظار|رفض>","decision_reason":"<جملة واحدة تبرر القرار>","key_strengths":["<نقطة قوة 1>","<نقطة قوة 2>"],"key_improvements":["<محور 1>","<محور 2>"],"summary":"<ملخص في 2-3 جمل>"}}""",
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
        logger.info(f"Évaluation LLM [{lang}] | score={parsed['score']}/10 | verdict={parsed['verdict']}")
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
        logger.info(f"Évaluation Finale LLM [{lang}] | score={parsed['score']}/10 | verdict={parsed['verdict']}")
        return parsed

    # ── Résumé global ─────────────────────────────────────────────────────────

    async def generate_global_summary(
        self,
        answers_eval: list[dict],
        position_title: str,
        candidate_name: str,
        language: str = "fr",
        weighted_avg: Optional[float] = None,   # moyenne pondérée calculée par EvaluationService
    ) -> dict:
        """
        Génère un résumé global structuré depuis les évaluations individuelles.

        CORRECTION v2 :
          - Utilise _parse_global_json (parser dédié, pas le parser par-réponse)
          - Prompt court et contraint pour éviter la troncature de llama3.2
          - Fallback automatique complet depuis les évaluations individuelles
            si le LLM retourne un JSON incomplet ou invalide
        """
        lang = language if language in ("ar", "fr", "en") else "fr"

        if not answers_eval:
            return self._empty_summary(lang)

        # Moyenne pondérée — utilise weighted_avg si fourni par EvaluationService,
        # sinon recalcule depuis les champs weight stockés dans chaque réponse.
        if weighted_avg is not None:
            avg = round(weighted_avg, 2)
        else:
            sw = [(float(a.get("score", 0)), float(a.get("weight", 1.0))) for a in answers_eval]
            total_w = sum(w for _, w in sw)
            avg = round(sum(s * w for s, w in sw) / total_w, 2) if total_w > 0 else 0.0

        verdict_computed = self._score_to_verdict(avg, lang)

        # ── Détail compact pour le prompt ────────────────────────────────────
        detail_lines = []
        for i, a in enumerate(answers_eval, 1):
            feedback_short = (a.get("feedback") or "")[:80].replace("\n", " ")
            w = a.get("weight", 1.0)
            detail_lines.append(
                f"Q{i} (score={a.get('score', 0)}/10, poids={w}) : {feedback_short}"
            )
        detail = "\n".join(detail_lines)

        # ── Prompt renforcé ───────────────────────────────────────────────────
        prompt_tpl = _GLOBAL_SUMMARY_PROMPT.get(lang, _GLOBAL_SUMMARY_PROMPT["fr"])
        prompt = prompt_tpl.format(
            candidate_name=candidate_name,
            position_title=position_title,
            avg=avg,
            avg_f=avg,
            verdict=verdict_computed,
            detail=detail,
        )

        raw    = await self._call_ollama("", prompt)
        result = self._parse_global_json(raw, lang, avg_fallback=avg)

        # ── Garantie : tous les champs sont présents et non vides ─────────────
        result = self._ensure_global_fields(result, answers_eval, avg, lang)

        logger.info(
            f"Résumé global [{lang}] | score={result['global_score']}/10 "
            f"| verdict={result['global_verdict']} "
            f"| recommendation={result['recommendation']}"
        )
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
            "options": {"temperature": 0.1, "top_p": 0.85, "num_predict": 512},
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(f"{self.base_url}/api/chat", json=payload)
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

    # ── Parsing par-réponse ───────────────────────────────────────────────────

    def _parse_json(self, raw: str, lang: str) -> dict:
        """Extrait et valide le JSON d'une évaluation individuelle."""
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
                    base["needs_followup"]    = bool(obj.get("needs_followup", False))
                    base["followup_question"] = str(obj.get("followup_question", "")).strip()
                    if base["score"] >= 8:
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

    # ── Parsing résumé global (NOUVEAU) ──────────────────────────────────────

    def _parse_global_json(self, raw: str, lang: str, avg_fallback: float = 0.0) -> dict:
        """
        Parser dédié au résumé global.
        Champs attendus : global_score, global_verdict, recommendation,
                          decision_reason, key_strengths, key_improvements, summary

        Contrairement à _parse_json (per-answer), ce parser ne normalise PAS
        les champs vers {score, verdict, ...} — il conserve les noms globaux.
        """
        for pattern in (
            r"```json\s*([\s\S]+?)\s*```",
            r"```\s*([\s\S]+?)\s*```",
            r"(\{[\s\S]+\})",
        ):
            m = re.search(pattern, raw)
            if m:
                try:
                    obj = json.loads(m.group(1))
                    return self._normalize_global(obj, lang, avg_fallback)
                except json.JSONDecodeError:
                    continue

        logger.warning(f"Impossible de parser le résumé global LLM : {raw[:300]}")
        return self._empty_global(lang, avg_fallback)

    def _normalize_global(self, obj: dict, lang: str, avg_fallback: float) -> dict:
        """Normalise un objet JSON de résumé global."""
        # global_score : peut être dans "global_score" ou "score"
        raw_score = obj.get("global_score") or obj.get("score") or avg_fallback
        try:
            global_score = float(raw_score)
            global_score = max(0.0, min(10.0, global_score))
        except (TypeError, ValueError):
            global_score = avg_fallback

        # global_verdict
        global_verdict = str(obj.get("global_verdict") or obj.get("verdict") or "").strip()
        if not global_verdict:
            global_verdict = self._score_to_verdict(global_score, lang)

        # recommendation
        recommendation = str(obj.get("recommendation") or "").strip()

        # decision_reason
        decision_reason = str(obj.get("decision_reason") or "").strip()

        # key_strengths / key_improvements
        def _list(key):
            val = obj.get(key) or []
            if isinstance(val, list):
                return [str(v) for v in val if v]
            if isinstance(val, str) and val.strip():
                return [val.strip()]
            return []

        key_strengths    = _list("key_strengths")
        key_improvements = _list("key_improvements")

        # summary
        summary = str(obj.get("summary") or "").strip()

        return {
            "global_score":     round(global_score, 2),
            "global_verdict":   global_verdict,
            "recommendation":   recommendation,
            "decision_reason":  decision_reason,
            "key_strengths":    key_strengths,
            "key_improvements": key_improvements,
            "summary":          summary,
        }

    def _empty_global(self, lang: str, avg_fallback: float = 0.0) -> dict:
        """Résumé global vide (base pour le fallback)."""
        return {
            "global_score":     avg_fallback,
            "global_verdict":   self._score_to_verdict(avg_fallback, lang),
            "recommendation":   "",
            "decision_reason":  "",
            "key_strengths":    [],
            "key_improvements": [],
            "summary":          "",
        }

    def _ensure_global_fields(
        self,
        result: dict,
        answers_eval: list[dict],
        avg: float,
        lang: str,
    ) -> dict:
        """
        Garantit que tous les champs du résumé global sont remplis.
        Si le LLM n'a pas retourné certains champs, les calcule depuis
        les évaluations individuelles (fallback déterministe).
        """
        # ── global_score ──────────────────────────────────────────────────
        if not result.get("global_score"):
            result["global_score"] = avg

        # ── global_verdict ────────────────────────────────────────────────
        if not result.get("global_verdict"):
            result["global_verdict"] = self._score_to_verdict(result["global_score"], lang)

        # ── recommendation ────────────────────────────────────────────────
        if not result.get("recommendation"):
            score = result["global_score"]
            if lang == "fr":
                result["recommendation"] = "Embaucher" if score >= 7 else ("En attente" if score >= 5 else "Refuser")
            elif lang == "ar":
                result["recommendation"] = "توظيف" if score >= 7 else ("قيد الانتظار" if score >= 5 else "رفض")
            else:
                result["recommendation"] = "Hire" if score >= 7 else ("On Hold" if score >= 5 else "Reject")

        # ── decision_reason ───────────────────────────────────────────────
        if not result.get("decision_reason"):
            score = result["global_score"]
            n     = len(answers_eval)
            if lang == "fr":
                result["decision_reason"] = (
                    f"Score moyen de {score}/10 sur {n} question(s). "
                    f"{result['recommendation']} — {result['global_verdict']}."
                )
            elif lang == "ar":
                result["decision_reason"] = (
                    f"متوسط الدرجة {score}/10 على {n} سؤال(أسئلة). "
                    f"{result['recommendation']} — {result['global_verdict']}."
                )
            else:
                result["decision_reason"] = (
                    f"Average score {score}/10 across {n} question(s). "
                    f"{result['recommendation']} — {result['global_verdict']}."
                )

        # ── key_strengths — agrège les strengths individuelles ─────────────
        if not result.get("key_strengths"):
            seen = set()
            strengths = []
            for a in answers_eval:
                for s in (a.get("strengths") or []):
                    if s and s not in seen:
                        seen.add(s); strengths.append(s)
            result["key_strengths"] = strengths[:4]  # max 4

        # ── key_improvements — agrège les improvements individuelles ───────
        if not result.get("key_improvements"):
            seen = set()
            improvements = []
            for a in answers_eval:
                for imp in (a.get("improvements") or []):
                    if imp and imp not in seen:
                        seen.add(imp); improvements.append(imp)
            result["key_improvements"] = improvements[:4]  # max 4

        # ── summary ───────────────────────────────────────────────────────
        if not result.get("summary"):
            score = result["global_score"]
            reco  = result["recommendation"]
            verdicts_str = ", ".join(
                f"Q{a.get('question_order', i+1)}: {a.get('score', 0)}/10"
                for i, a in enumerate(answers_eval)
            )
            if lang == "fr":
                result["summary"] = (
                    f"L'entretien de {len(answers_eval)} question(s) a donné un score moyen de {score}/10. "
                    f"Détail : {verdicts_str}. "
                    f"Décision : {reco}."
                )
            elif lang == "ar":
                result["summary"] = (
                    f"أسفر الاختبار عن متوسط {score}/10 على {len(answers_eval)} سؤال. "
                    f"التفاصيل : {verdicts_str}. "
                    f"القرار : {reco}."
                )
            else:
                result["summary"] = (
                    f"The {len(answers_eval)}-question interview yielded an average score of {score}/10. "
                    f"Detail: {verdicts_str}. "
                    f"Decision: {reco}."
                )

        return result

    # ── Normaliseurs par-réponse ──────────────────────────────────────────────

    def _normalize(self, obj: dict, lang: str) -> dict:
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
        msgs = {"fr": "Aucune réponse à évaluer.", "en": "No answers to evaluate.", "ar": "لا توجد إجابات للتقييم."}
        return {
            "global_score":     0.0,
            "global_verdict":   self._score_to_verdict(0.0, lang),
            "recommendation":   "",
            "decision_reason":  "",
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