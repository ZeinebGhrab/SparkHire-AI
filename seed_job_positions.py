"""
Seed des postes avec questions trilingues (AR / FR / EN)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database import db
from backend.interviews.models import Question
from datetime import datetime


# ============================================================
# QUESTIONS TRILINGUES — DÉVELOPPEUR FULL STACK
# ============================================================

FULLSTACK_QUESTIONS = [
    (1,
     "قدم نفسك باختصار",
     "Présentez-vous brièvement",
     "Introduce yourself briefly",
     120),
    (2,
     "لماذا تريد العمل في هذا المنصب؟",
     "Pourquoi souhaitez-vous occuper ce poste ?",
     "Why do you want this position?",
     90),
    (3,
     "ما هي نقاط قوتك الرئيسية؟",
     "Quels sont vos principaux points forts ?",
     "What are your main strengths?",
     90),
    (4,
     "ما هي نقاط ضعفك؟",
     "Quels sont vos points faibles ?",
     "What are your weaknesses?",
     90),
    (5,
     "صف مشروعاً معقداً عملت عليه",
     "Décrivez un projet complexe sur lequel vous avez travaillé",
     "Describe a complex project you worked on",
     180),
    (6,
     "كيف تتعامل مع الضغط؟",
     "Comment gérez-vous le stress et la pression ?",
     "How do you handle pressure?",
     90),
    (7,
     "أين ترى نفسك بعد 5 سنوات؟",
     "Où vous voyez-vous dans 5 ans ?",
     "Where do you see yourself in 5 years?",
     90),
    (8,
     "ما هي خبرتك في العمل الجماعي؟",
     "Quelle est votre expérience du travail en équipe ?",
     "What is your experience with teamwork?",
     120),
    (9,
     "كيف تتعلم تقنيات جديدة؟",
     "Comment apprenez-vous de nouvelles technologies ?",
     "How do you learn new technologies?",
     90),
    (10,
     "ما هي توقعاتك للراتب؟",
     "Quelles sont vos prétentions salariales ?",
     "What are your salary expectations?",
     60),
    (11,
     "صف موقفاً تعاملت فيه مع خلاف في الفريق",
     "Décrivez une situation où vous avez géré un conflit d'équipe",
     "Describe a situation where you handled a team conflict",
     120),
    (12,
     "ما هي المهارات التقنية التي تتقنها؟",
     "Quelles compétences techniques maîtrisez-vous ?",
     "What technical skills do you master?",
     120),
    (13,
     "كيف تنظم وقتك ومهامك؟",
     "Comment organisez-vous votre temps et vos tâches ?",
     "How do you organize your time and tasks?",
     90),
    (14,
     "ما الذي يحفزك في العمل؟",
     "Qu'est-ce qui vous motive dans votre travail ?",
     "What motivates you at work?",
     90),
    (15,
     "صف خطأً ارتكبته وماذا تعلمت منه",
     "Décrivez une erreur que vous avez commise et ce que vous en avez appris",
     "Describe a mistake you made and what you learned",
     120),
    (16,
     "كيف تبقى محدثاً بأحدث التقنيات؟",
     "Comment restez-vous à jour avec les dernières technologies ?",
     "How do you stay updated with the latest technologies?",
     90),
    (17,
     "ما هو أكبر تحدٍ واجهته مهنياً؟",
     "Quel est le plus grand défi professionnel que vous avez relevé ?",
     "What is the biggest professional challenge you've faced?",
     120),
    (18,
     "هل تفضل العمل بمفردك أم في فريق؟",
     "Préférez-vous travailler seul ou en équipe ?",
     "Do you prefer working alone or in a team?",
     90),
    (19,
     "ما الذي يميزك عن المرشحين الآخرين؟",
     "Qu'est-ce qui vous distingue des autres candidats ?",
     "What sets you apart from other candidates?",
     90),
    (20,
     "هل لديك أي أسئلة لنا؟",
     "Avez-vous des questions à nous poser ?",
     "Do you have any questions for us?",
     120),
]


# ============================================================
# QUESTIONS TRILINGUES — DATA SCIENTIST
# ============================================================

DATA_QUESTIONS = [
    (1,
     "قدم نفسك وخلفيتك في علم البيانات",
     "Présentez-vous et votre parcours en data science",
     "Introduce yourself and your data science background",
     120),
    (2,
     "ما هي أدوات علم البيانات التي تستخدمها يومياً؟",
     "Quels outils de data science utilisez-vous au quotidien ?",
     "What data science tools do you use daily?",
     90),
    (3,
     "اشرح الفرق بين التعلم الآلي والتعلم العميق",
     "Expliquez la différence entre le machine learning et le deep learning",
     "Explain the difference between machine learning and deep learning",
     120),
    (4,
     "كيف تتعامل مع البيانات المفقودة؟",
     "Comment traitez-vous les données manquantes ?",
     "How do you handle missing data?",
     90),
    (5,
     "صف مشروع تحليل بيانات نجحت فيه",
     "Décrivez un projet d'analyse de données réussi",
     "Describe a successful data analysis project",
     180),
    (6,
     "ما هو الفرق بين Overfitting و Underfitting؟",
     "Quelle est la différence entre overfitting et underfitting ?",
     "What is the difference between overfitting and underfitting?",
     90),
    (7,
     "كيف تختار النموذج المناسب للمشكلة؟",
     "Comment choisissez-vous le bon modèle pour un problème donné ?",
     "How do you choose the right model for a problem?",
     120),
    (8,
     "ما هي مقاييس التقييم التي تستخدمها؟",
     "Quelles métriques d'évaluation utilisez-vous ?",
     "What evaluation metrics do you use?",
     90),
    (9,
     "كيف تتعامل مع البيانات غير المتوازنة؟",
     "Comment gérez-vous les données déséquilibrées ?",
     "How do you handle imbalanced data?",
     90),
    (10,
     "ما هي خبرتك في SQL وقواعد البيانات؟",
     "Quelle est votre expérience avec SQL et les bases de données ?",
     "What is your experience with SQL and databases?",
     90),
    (11,
     "كيف تشرح نتائج نموذجك لغير التقنيين؟",
     "Comment expliquez-vous les résultats de votre modèle aux non-techniciens ?",
     "How do you explain your model's results to non-technical stakeholders?",
     120),
    (12,
     "ما هي خبرتك في التحصين والنشر؟",
     "Quelle est votre expérience en déploiement de modèles ?",
     "What is your experience in model deployment?",
     90),
    (13,
     "كيف تضمن جودة البيانات؟",
     "Comment garantissez-vous la qualité des données ?",
     "How do you ensure data quality?",
     90),
    (14,
     "اشرح مفهوم Feature Engineering",
     "Expliquez le concept de Feature Engineering",
     "Explain the concept of Feature Engineering",
     120),
    (15,
     "ما هي تجربتك مع البيانات الكبيرة؟",
     "Quelle est votre expérience avec les big data ?",
     "What is your experience with big data?",
     90),
    (16,
     "كيف تتعامل مع التحيز في النماذج؟",
     "Comment gérez-vous les biais dans vos modèles ?",
     "How do you handle bias in your models?",
     120),
    (17,
     "ما هي أكبر المخاطر في مشاريع علم البيانات؟",
     "Quels sont les plus grands risques dans les projets de data science ?",
     "What are the biggest risks in data science projects?",
     90),
    (18,
     "كيف تتعاون مع فرق الهندسة؟",
     "Comment collaborez-vous avec les équipes d'ingénierie ?",
     "How do you collaborate with engineering teams?",
     90),
    (19,
     "ما هو أكثر ما يثير شغفك في علم البيانات؟",
     "Qu'est-ce qui vous passionne le plus dans la data science ?",
     "What excites you most about data science?",
     90),
    (20,
     "هل لديك أسئلة حول الدور أو الشركة؟",
     "Avez-vous des questions sur le poste ou l'entreprise ?",
     "Do you have questions about the role or company?",
     120),
]


def make_questions(raw_list: list) -> list:
    """Convertit la liste de tuples en objets Question."""
    return [
        Question(
            order=order,
            question_ar=ar,
            question_fr=fr,
            question_en=en,
            max_duration_seconds=duration,
        )
        for order, ar, fr, en, duration in raw_list
    ]


def seed_job_positions():
    """Créer les postes avec questions trilingues."""

    positions = [
        {
            "title":      "Développeur Full Stack",
            "department": "IT",
            "questions":  make_questions(FULLSTACK_QUESTIONS),
        },
        {
            "title":      "Data Scientist",
            "department": "Data",
            "questions":  make_questions(DATA_QUESTIONS),
        },
    ]

    for pos in positions:
        doc = {
            "title":      pos["title"],
            "department": pos["department"],
            "questions":  [q.model_dump() for q in pos["questions"]],
            "created_at": datetime.utcnow(),
        }
        result = db.job_positions.insert_one(doc)
        print(f"✅ Poste créé : {pos['title']} (ID: {result.inserted_id}) "
              f"— {len(pos['questions'])} questions × 3 langues")


if __name__ == "__main__":
    print("🌍 Seed des postes avec questions trilingues AR/FR/EN...")
    seed_job_positions()
    print("✅ Terminé !")
