"""
Service LLM — Évaluation des réponses via Ollama + Llama 3
Pipeline: Transcription → LLM → Score / Feedback multilingue
+ Génération de questions de suivi si la réponse est floue
+ Intégration des données du langage corporel facial (DeepFace + MediaPipe)
+ Calibration RH : injection des corrections passées dans le system prompt
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

# ═════════════════════════════════════════════════════════════════════════════
# ANALYSE FACIALE — Contexte injecté dans le prompt LLM
# ═════════════════════════════════════════════════════════════════════════════

_FACIAL_CONTEXT_PROMPT = {
    "fr": """\

Données du langage corporel observées pendant la réponse (analyse automatique caméra) :
  • Émotion dominante       : {dominant_emotion}
  • Confiance visuelle      : {confidence_score}/10
  • Stress apparent         : {stress_score}/10
  • Engagement              : {engagement_score}/10
  • Contact visuel caméra   : {eye_contact_pct}%
  • Stabilité de posture    : {stability_label}
  • Sourire détecté         : {smile_pct}% du temps
  • Qualité capture         : {frames_with_face}/{frames_total} frames avec visage détecté

Instructions pour l'intégration de ces données :
  - Ces données ENRICHISSENT ton évaluation mais ne la remplacent pas.
  - Le contenu de la réponse pèse 80%, le comportement non-verbal 20%.
  - Si le contact visuel est < 30%, mentionne-le dans les axes d'amélioration.
  - Si le stress apparent est > 7/10, sois légèrement plus bienveillant dans le feedback.
  - Si la qualité de capture est < 30%, ignore entièrement les données faciales.
""",
    "en": """\

Body language data observed during the answer (automated camera analysis):
  • Dominant emotion        : {dominant_emotion}
  • Visual confidence       : {confidence_score}/10
  • Apparent stress         : {stress_score}/10
  • Engagement              : {engagement_score}/10
  • Eye contact with camera : {eye_contact_pct}%
  • Posture stability       : {stability_label}
  • Smile detected          : {smile_pct}% of the time
  • Capture quality         : {frames_with_face}/{frames_total} frames with face detected

Integration instructions:
  - These data ENRICH your evaluation but do not replace it.
  - Answer content weighs 80%, non-verbal behavior 20%.
  - If eye contact < 30%, mention it in improvement areas.
  - If apparent stress > 7/10, be slightly more supportive in feedback.
  - If capture quality < 30%, ignore facial data entirely.
""",
    "ar": """\

بيانات لغة الجسد الملاحظة أثناء الإجابة (تحليل تلقائي بالكاميرا) :
  • المشاعر السائدة          : {dominant_emotion}
  • الثقة البصرية            : {confidence_score}/10
  • الضغط الظاهر             : {stress_score}/10
  • مستوى التفاعل            : {engagement_score}/10
  • التواصل البصري مع الكاميرا : {eye_contact_pct}%
  • ثبات الوضعية             : {stability_label}
  • الابتسام                 : {smile_pct}% من الوقت
  • جودة الالتقاط            : {frames_with_face}/{frames_total} إطار مع وجه مكتشف

تعليمات التكامل :
  - هذه البيانات تُثري تقييمك ولا تحل محله.
  - محتوى الإجابة يمثل 80% والسلوك غير اللفظي 20%.
  - إذا كان التواصل البصري < 30%، اذكره في نقاط التحسين.
  - إذا كان الضغط الظاهر > 7/10، كن أكثر لطفاً في التغذية الراجعة.
  - إذا كانت جودة الالتقاط < 30%، تجاهل البيانات الوجهية كلياً.
""",
}

_STABILITY_LABELS = {
    "fr": {True: "Bonne (posture stable)",      False: "À améliorer (mouvements fréquents)"},
    "en": {True: "Good (stable posture)",        False: "To improve (frequent movements)"},
    "ar": {True: "جيد (وضعية ثابتة)",           False: "يحتاج تحسين (حركات متكررة)"},
}

_EMOTION_LABELS = {
    "fr": {
        "neutral":  "Neutre",     "happy":    "Joyeux",    "sad":      "Triste",
        "angry":    "En colère",  "fear":     "Craintif",  "surprise": "Surpris",
        "disgust":  "Dégoûté",
    },
    "en": {
        "neutral":  "Neutral",    "happy":    "Happy",     "sad":      "Sad",
        "angry":    "Angry",      "fear":     "Fearful",   "surprise": "Surprised",
        "disgust":  "Disgusted",
    },
    "ar": {
        "neutral":  "محايد",      "happy":    "سعيد",      "sad":      "حزين",
        "angry":    "غاضب",       "fear":     "خائف",      "surprise": "مندهش",
        "disgust":  "مشمئز",
    },
}

# ── Contexte durée de réponse ─────────────────────────────────────────────────

_DURATION_CONTEXT_PROMPT = {
    "fr": """\

Durée de la réponse : {duration_str} (limite autorisée : {max_str})
Ratio d'utilisation : {ratio_pct}%

Instructions pour la durée :
  - Une réponse très courte (< 20% du temps alloué) indique souvent un manque de développement → pénalise le score de -1 à -2 points si le contenu est pauvre.
  - Une réponse équilibrée (40–90% du temps alloué) est idéale → pas d'impact.
  - Une réponse qui utilise 90–100% du temps alloué avec un contenu riche est positive → bonus possible de +0.5 point.
  - Ne pénalise PAS si la réponse est courte mais précise et complète.
  - Mentionne la durée dans le feedback uniquement si elle est significativement trop courte ou si le candidat a semblé à court d'idées.
""",
    "en": """\

Answer duration: {duration_str} (allowed limit: {max_str})
Usage ratio: {ratio_pct}%

Duration instructions:
  - A very short answer (< 20% of allocated time) often indicates lack of development → penalize score by -1 to -2 points if content is poor.
  - A balanced answer (40–90% of allocated time) is ideal → no impact.
  - An answer using 90–100% of allocated time with rich content is positive → possible +0.5 point bonus.
  - Do NOT penalize if the answer is short but precise and complete.
  - Mention duration in feedback only if it is significantly too short or the candidate seemed to run out of ideas.
""",
    "ar": """\

مدة الإجابة : {duration_str} (الحد المسموح به : {max_str})
نسبة الاستخدام : {ratio_pct}%

تعليمات المدة :
  - الإجابة القصيرة جداً (< 20% من الوقت المخصص) تشير غالباً إلى نقص في التطوير → اخصم من -1 إلى -2 نقطة إذا كان المحتوى ضعيفاً.
  - الإجابة المتوازنة (40-90% من الوقت) مثالية → لا تأثير.
  - الإجابة التي تستخدم 90-100% من الوقت مع محتوى غني إيجابية → مكافأة محتملة +0.5 نقطة.
  - لا تعاقب إذا كانت الإجابة قصيرة لكن دقيقة وكاملة.
  - اذكر المدة في التغذية الراجعة فقط إذا كانت قصيرة بشكل ملحوظ أو بدا المرشح نافد الأفكار.
""",
}


def _build_duration_context(
    duration_seconds: float,
    max_duration_seconds: float,
    language: str,
) -> str:
    if duration_seconds <= 0 or max_duration_seconds <= 0:
        return ""

    lang      = language if language in ("ar", "fr", "en") else "fr"
    ratio     = min(1.0, duration_seconds / max_duration_seconds)
    ratio_pct = int(ratio * 100)

    def _fmt(secs: float) -> str:
        m, s = int(secs) // 60, int(secs) % 60
        return f"{m}m{s:02d}s" if m > 0 else f"{s}s"

    tpl = _DURATION_CONTEXT_PROMPT.get(lang, _DURATION_CONTEXT_PROMPT["fr"])
    return tpl.format(
        duration_str=_fmt(duration_seconds),
        max_str=_fmt(max_duration_seconds),
        ratio_pct=ratio_pct,
    )


def _build_facial_context(facial_metrics, language: str) -> str:
    if facial_metrics is None:
        return ""

    detection_rate = getattr(facial_metrics, "face_detection_rate", 0.0)
    frames_total   = getattr(facial_metrics, "frames_analyzed", 0)

    if detection_rate < 0.3 or frames_total == 0:
        return ""

    lang     = language if language in ("ar", "fr", "en") else "fr"
    tpl      = _FACIAL_CONTEXT_PROMPT.get(lang, _FACIAL_CONTEXT_PROMPT["fr"])
    stable   = getattr(facial_metrics, "head_stability", 1.0) > 0.6
    stab_lbl = _STABILITY_LABELS.get(lang, _STABILITY_LABELS["fr"])[stable]
    dom_raw  = getattr(facial_metrics, "dominant_emotion", "neutral")
    dom_lbl  = _EMOTION_LABELS.get(lang, _EMOTION_LABELS["fr"]).get(dom_raw, dom_raw)

    return tpl.format(
        dominant_emotion  = dom_lbl,
        confidence_score  = getattr(facial_metrics, "confidence_score",  5.0),
        stress_score      = getattr(facial_metrics, "stress_score",       5.0),
        engagement_score  = getattr(facial_metrics, "engagement_score",   5.0),
        eye_contact_pct   = int(getattr(facial_metrics, "eye_contact_ratio", 0.0) * 100),
        stability_label   = stab_lbl,
        smile_pct         = int(getattr(facial_metrics, "smile_ratio", 0.0) * 100),
        frames_with_face  = getattr(facial_metrics, "frames_with_face", 0),
        frames_total      = frames_total,
    )


# ═════════════════════════════════════════════════════════════════════════════
# CALIBRATION RH — Contexte few-shot injecté dans le prompt
# ═════════════════════════════════════════════════════════════════════════════

def _build_calibration_context(corrections: list, language: str) -> str:
    """
    Construit le bloc de calibration RH à injecter dans le system prompt.

    Prend les corrections RH passées (score corrigé, forces validées, commentaire)
    et les formate en exemples few-shot compréhensibles par le LLM.

    Retourne une chaîne vide si :
      - la liste est vide
      - aucune correction n'a de delta >= 0.5 pt ni de commentaire significatif

    Le bloc est conçu pour être concaténé directement après le system prompt
    de base. Longueur typique : 200–600 tokens selon le nombre d'exemples.
    """
    if not corrections:
        return ""

    # Ne garder que les exemples instructifs
    meaningful = [
        c for c in corrections
        if abs(c.get("corrected_score", 0) - c.get("original_score", 0)) >= 0.5
        or c.get("hr_comment", "").strip()
        or c.get("strengths_added", [])
    ]
    if not meaningful:
        return ""

    lang = language if language in ("ar", "fr", "en") else "fr"

    _header = {
        "fr": (
            "\n\nCALIBRAGE RH — L'équipe RH a validé les évaluations suivantes pour ce poste. "
            "Adapte ton barème en conséquence :"
        ),
        "en": (
            "\n\nHR CALIBRATION — The HR team has validated the following evaluations for this position. "
            "Adjust your grading scale accordingly:"
        ),
        "ar": (
            "\n\nمعايرة الموارد البشرية — قام فريق الموارد البشرية بالتحقق من التقييمات التالية لهذا المنصب. "
            "اضبط معايير تقييمك وفقاً لذلك :"
        ),
    }

    _direction = {
        "fr": {
            "up":   "LLM avait sous-évalué",
            "down": "LLM avait sur-évalué",
            "same": "score confirmé",
        },
        "en": {
            "up":   "LLM had underscored",
            "down": "LLM had overscored",
            "same": "score confirmed",
        },
        "ar": {
            "up":   "النموذج أعطى درجة أقل من اللازم",
            "down": "النموذج أعطى درجة أعلى من اللازم",
            "same": "الدرجة مؤكدة",
        },
    }

    _footer = {
        "fr": (
            "\n→ Ces exemples définissent le niveau d'exigence RH pour ce poste. "
            "Si une réponse ressemble à ces extraits, applique le même niveau de score."
        ),
        "en": (
            "\n→ These examples define the HR expectation level for this position. "
            "If an answer resembles these excerpts, apply the same scoring level."
        ),
        "ar": (
            "\n→ هذه الأمثلة تحدد مستوى التوقعات لهذا المنصب. "
            "إذا كانت الإجابة مشابهة لهذه المقتطفات، طبّق نفس مستوى التقييم."
        ),
    }

    dir_labels = _direction[lang]
    lines      = [_header[lang]]

    for i, c in enumerate(meaningful, 1):
        orig  = c.get("original_score", 0)
        corr  = c.get("corrected_score", 0)
        delta = corr - orig

        direction = (
            dir_labels["up"]   if delta >= 0.5  else
            dir_labels["down"] if delta <= -0.5 else
            dir_labels["same"]
        )

        strengths    = (c.get("strengths_validated", []) + c.get("strengths_added", []))[:3]
        improvements = c.get("improvements_validated", [])[:3]
        question     = (c.get("question_text", "") or "")[:120]
        excerpt      = (c.get("transcript_excerpt", "") or "")[:150]
        comment      = (c.get("hr_comment", "") or "")[:120]

        if lang == "fr":
            block = (
                f"\nExemple {i} :\n"
                f"  Question           : {question or '—'}\n"
                f"  Extrait réponse    : « {excerpt or '—'} »\n"
                f"  Score LLM initial  : {round(orig, 1)}/10 ({c.get('original_verdict', '')})\n"
                f"  Score RH validé    : {round(corr, 1)}/10 — {direction}\n"
                f"  Forces retenues    : {', '.join(strengths) if strengths else '—'}\n"
                f"  Améliorations      : {', '.join(improvements) if improvements else '—'}\n"
                f"  Commentaire RH     : {comment or '—'}"
            )
        elif lang == "en":
            block = (
                f"\nExample {i}:\n"
                f"  Question           : {question or '—'}\n"
                f"  Answer excerpt     : « {excerpt or '—'} »\n"
                f"  Initial LLM score  : {round(orig, 1)}/10 ({c.get('original_verdict', '')})\n"
                f"  HR validated score : {round(corr, 1)}/10 — {direction}\n"
                f"  Strengths retained : {', '.join(strengths) if strengths else '—'}\n"
                f"  Improvements       : {', '.join(improvements) if improvements else '—'}\n"
                f"  HR comment         : {comment or '—'}"
            )
        else:  # ar
            block = (
                f"\nمثال {i} :\n"
                f"  السؤال                : {question or '—'}\n"
                f"  مقتطف الإجابة          : « {excerpt or '—'} »\n"
                f"  درجة النموذج الأولية   : {round(orig, 1)}/10 ({c.get('original_verdict', '')})\n"
                f"  الدرجة المعتمدة من RH  : {round(corr, 1)}/10 — {direction}\n"
                f"  نقاط القوة             : {', '.join(strengths) if strengths else '—'}\n"
                f"  محاور التحسين          : {', '.join(improvements) if improvements else '—'}\n"
                f"  تعليق فريق التوظيف     : {comment or '—'}"
            )

        lines.append(block)

    lines.append(_footer[lang])
    return "\n".join(lines)


# ═════════════════════════════════════════════════════════════════════════════
#  SERVICE LLM PRINCIPAL
# ═════════════════════════════════════════════════════════════════════════════

class OllamaLLMService:
    """Service d'évaluation LLM via Ollama (Llama 3 local)."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3",
        timeout: float = 60.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.model    = model
        self.timeout  = timeout
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
        logger.info(f"Évaluation [{lang}] score={parsed['score']}/10 verdict={parsed['verdict']}")
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
            result.update({
                "llm_model": self.model, "evaluated": True,
                "needs_followup": False, "followup_question": "",
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
        return parsed

    # ── Évaluation enrichie : facial + durée + calibration RH ────────────────

    async def evaluate_with_facial(
        self,
        question: str,
        answer: str,
        language: str = "fr",
        position_title: str = "",
        facial_metrics=None,
        duration_seconds: float = 0.0,
        max_duration_seconds: float = 0.0,
        calibration_corrections: list | None = None,   # ← NOUVEAU
    ) -> dict:
        """
        Évalue une réponse en intégrant :
          1. Les données du langage corporel facial (MediaPipe + HSEmotion)
          2. La durée de réponse relative au temps alloué
          3. Les corrections RH passées pour ce poste (few-shot calibration)

        Ordre d'injection dans le system prompt :
          _SYSTEM_PROMPT_FOLLOWUP[lang]
            + duration_context
            + facial_context
            + calibration_context    ← en dernier pour qu'il prime sur les autres

        Le contenu de la réponse reste prioritaire (80%).
        Le comportement non-verbal enrichit le feedback (20%).
        La calibration ajuste le niveau d'exigence sur ce poste spécifique.
        """
        lang = language if language in ("ar", "fr", "en") else "fr"

        if not answer or len(answer.strip()) < 5:
            result = dict(_EMPTY_ANSWER_RESULT[lang])
            result.update({
                "llm_model":         self.model,
                "evaluated":         True,
                "needs_followup":    False,
                "followup_question": "",
            })
            return result

        # ── Construire les contextes additionnels ─────────────────────────────
        duration_context    = _build_duration_context(duration_seconds, max_duration_seconds, lang)
        facial_context      = _build_facial_context(facial_metrics, lang)
        calibration_context = _build_calibration_context(calibration_corrections or [], lang)

        # Calibration en dernier : elle doit primer sur le barème de base
        system = (
            _SYSTEM_PROMPT_FOLLOWUP[lang]
            + duration_context
            + facial_context
            + calibration_context
        )

        user = _USER_PROMPT[lang].format(question=question, answer=answer)
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

        # Log enrichi
        dur_info = (
            f"durée={int(duration_seconds)}s/{int(max_duration_seconds)}s "
            f"({int(min(1.0, duration_seconds / max_duration_seconds) * 100) if max_duration_seconds > 0 else '?'}%)"
            if duration_seconds > 0 else "durée=n/a"
        )
        calib_info = (
            f"calibration={len(calibration_corrections)} exemple(s)"
            if calibration_corrections else "calibration=—"
        )
        if facial_metrics and getattr(facial_metrics, "frames_with_face", 0) > 0:
            logger.info(
                f"Évaluation+Facial+Calibration [{lang}] | "
                f"score={parsed['score']}/10 | "
                f"needs_followup={parsed['needs_followup']} | "
                f"{dur_info} | "
                f"émotion={getattr(facial_metrics, 'dominant_emotion', 'n/a')} | "
                f"confiance={getattr(facial_metrics, 'confidence_score', 0)}/10 | "
                f"stress={getattr(facial_metrics, 'stress_score', 0)}/10 | "
                f"contact={int(getattr(facial_metrics, 'eye_contact_ratio', 0)*100)}% | "
                f"{calib_info}"
            )
        else:
            logger.info(
                f"Évaluation+Calibration [{lang}] | "
                f"score={parsed['score']}/10 | "
                f"{dur_info} | {calib_info}"
            )

        return parsed

    # ── Évaluation avec calibration seule (sans facial) ──────────────────────

    async def evaluate_with_calibration(
        self,
        question: str,
        answer: str,
        language: str = "fr",
        position_title: str = "",
        calibration_corrections: list | None = None,
    ) -> dict:
        """
        Évalue une réponse en injectant uniquement les corrections RH comme
        exemples few-shot dans le system prompt.

        Utilisé quand l'analyse faciale n'est pas disponible (caméra absente)
        mais que des corrections de calibration existent pour le poste.
        """
        lang = language if language in ("ar", "fr", "en") else "fr"

        if not answer or len(answer.strip()) < 5:
            result = dict(_EMPTY_ANSWER_RESULT[lang])
            result.update({
                "llm_model":         self.model,
                "evaluated":         True,
                "needs_followup":    False,
                "followup_question": "",
            })
            return result

        calibration_context = _build_calibration_context(calibration_corrections or [], lang)
        system = _SYSTEM_PROMPT_FOLLOWUP[lang] + calibration_context

        user = _USER_PROMPT[lang].format(question=question, answer=answer)
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

        if calibration_corrections:
            logger.info(
                f"Évaluation+Calibration [{lang}] | "
                f"score={parsed['score']}/10 | "
                f"needs_followup={parsed['needs_followup']} | "
                f"{len(calibration_corrections)} exemple(s) calibration"
            )

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
        """
        lang = language if language in ("ar", "fr", "en") else "fr"

        if not answers_eval:
            return self._empty_summary(lang)

        if weighted_avg is not None:
            avg = round(weighted_avg, 2)
        else:
            sw      = [(float(a.get("score", 0)), float(a.get("weight", 1.0))) for a in answers_eval]
            total_w = sum(w for _, w in sw)
            avg     = round(sum(s * w for s, w in sw) / total_w, 2) if total_w > 0 else 0.0

        detail_lines = []
        for i, a in enumerate(answers_eval, 1):
            feedback_short = (a.get("feedback") or "")[:80].replace("\n", " ")
            w = a.get("weight", 1.0)
            facial = a.get("facial_analysis") or {}
            if facial and facial.get("frames_with_face", 0) > 0:
                facial_summary = (
                    f" [confiance={facial.get('confidence_score', '?')}/10 "
                    f"stress={facial.get('stress_score', '?')}/10]"
                )
            else:
                facial_summary = ""
            detail_lines.append(
                f"Q{i} (score={a.get('score', 0)}/10, poids={w}){facial_summary} : {feedback_short}"
            )
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
        for pattern in (
            r"```json\s*([\s\S]+?)\s*```",
            r"```\s*([\s\S]+?)\s*```",
            r"(\{[\s\S]+\})",
        ):
            m = re.search(pattern, raw)
            if m:
                try:
                    return self._normalize(json.loads(m.group(1)), lang)
                except json.JSONDecodeError:
                    continue
        logger.warning(f"Parse JSON échoué (per-answer) : {raw[:200]}")
        return self._fallback_result(lang)

    def _parse_followup_json(self, raw: str, lang: str) -> dict:
        for pattern in (
            r"```json\s*([\s\S]+?)\s*```",
            r"```\s*([\s\S]+?)\s*```",
            r"(\{[\s\S]+\})",
        ):
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
        for pattern in (
            r"```json\s*([\s\S]+?)\s*```",
            r"```\s*([\s\S]+?)\s*```",
            r"(\{[\s\S]+\})",
        ):
            m = re.search(pattern, raw)
            if m:
                try:
                    return self._normalize_global(json.loads(m.group(1)))
                except json.JSONDecodeError:
                    continue
        logger.warning(f"Parse JSON échoué (global) : {raw[:200]}")
        return {
            "recommendation": "", "decision_reason": "",
            "key_strengths": [], "key_improvements": [], "summary": "",
        }

    def _normalize_global(self, obj: dict) -> dict:
        def _list(key):
            val = obj.get(key) or []
            if isinstance(val, list):
                return [str(v) for v in val if v]
            return [str(val).strip()] if isinstance(val, str) and val.strip() else []

        return {
            "recommendation":   str(obj.get("recommendation")  or "").strip(),
            "decision_reason":  str(obj.get("decision_reason")  or "").strip(),
            "key_strengths":    _list("key_strengths"),
            "key_improvements": _list("key_improvements"),
            "summary":          str(obj.get("summary")          or "").strip(),
        }

    def _ensure_global_fields(
        self,
        result: dict,
        answers_eval: list[dict],
        avg: float,
        lang: str,
    ) -> dict:
        if not result.get("recommendation"):
            if lang == "fr":
                result["recommendation"] = (
                    "Embaucher" if avg >= 7 else ("En attente" if avg >= 5 else "Refuser")
                )
            elif lang == "ar":
                result["recommendation"] = (
                    "توظيف" if avg >= 7 else ("قيد الانتظار" if avg >= 5 else "رفض")
                )
            else:
                result["recommendation"] = (
                    "Hire" if avg >= 7 else ("On Hold" if avg >= 5 else "Reject")
                )

        if not result.get("decision_reason"):
            n = len(answers_eval)
            if lang == "fr":
                result["decision_reason"] = (
                    f"Moyenne pondérée de {avg}/10 sur {n} question(s). "
                    f"Barème : ≥7 = Embaucher, 5–7 = En attente, <5 = Refuser."
                )
            elif lang == "ar":
                result["decision_reason"] = (
                    f"متوسط مرجح {avg}/10 على {n} سؤال. المعايير : ≥7 = توظيف، 5-7 = انتظار، <5 = رفض."
                )
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
                f"Q{a.get('question_order', i+1)}: {a.get('score', 0)}/10 "
                f"(×{a.get('weight', 1.0)})"
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
                result["summary"] = (
                    f"مقابلة {len(answers_eval)} سؤال — متوسط مرجح {avg}/10. "
                    f"{scores_str}. التوصية : {reco}."
                )
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
            "strengths":    list(obj.get("strengths",    [])),
            "improvements": list(obj.get("improvements", [])),
            "feedback":     str(obj.get("feedback", "")),
        }

    def _fallback_result(self, lang: str) -> dict:
        msgs = {
            "fr": "Évaluation non disponible (erreur LLM).",
            "en": "Evaluation unavailable (LLM error).",
            "ar": "التقييم غير متاح.",
        }
        return {
            "score":        5.0,
            "verdict":      self._score_to_verdict(5.0, lang),
            "strengths":    [],
            "improvements": [],
            "feedback":     msgs.get(lang, msgs["fr"]),
        }

    def _empty_summary(self, lang: str) -> dict:
        return {
            "recommendation": "", "decision_reason": "",
            "key_strengths": [], "key_improvements": [], "summary": "",
        }

    @staticmethod
    def _score_to_verdict(score: float, lang: str) -> str:
        verdicts = {
            "fr": [
                "Insuffisant", "Insuffisant", "Insuffisant",
                "Acceptable",  "Acceptable",
                "Bien",        "Bien",
                "Très bien",   "Très bien",
                "Excellent",   "Excellent",
            ],
            "en": [
                "Poor",        "Poor",        "Poor",
                "Acceptable",  "Acceptable",
                "Good",        "Good",
                "Very Good",   "Very Good",
                "Excellent",   "Excellent",
            ],
            "ar": [
                "ضعيف",   "ضعيف",   "ضعيف",
                "مقبول",  "مقبول",
                "جيد",    "جيد",
                "جيد جداً", "جيد جداً",
                "ممتاز",  "ممتاز",
            ],
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
            base_url=getattr(settings, "OLLAMA_URL",     "http://localhost:11434"),
            model=getattr(settings,    "OLLAMA_MODEL",   "llama3"),
            timeout=getattr(settings,  "OLLAMA_TIMEOUT", 60.0),
        )
    return _llm_instance