import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database import db
from backend.interviews.models import Question
from datetime import datetime

def seed_job_positions():
    """Créer des postes avec questions prédéfinies"""
    
    # Poste 1: Développeur Full Stack
    fullstack_questions = [
        Question(
            order=1,
            question_ar="قدم نفسك باختصار",
            question_en="Introduce yourself briefly",
            max_duration_seconds=120,
            evaluation_criteria=["Clarté", "Expérience", "Motivation"]
        ),
        Question(
            order=2,
            question_ar="لماذا تريد العمل في هذا المنصب؟",
            question_en="Why do you want this position?",
            max_duration_seconds=90
        ),
        Question(
            order=3,
            question_ar="ما هي نقاط قوتك الرئيسية؟",
            question_en="What are your main strengths?",
            max_duration_seconds=90
        ),
        Question(
            order=4,
            question_ar="ما هي نقاط ضعفك؟",
            question_en="What are your weaknesses?",
            max_duration_seconds=90
        ),
        Question(
            order=5,
            question_ar="صف مشروعاً معقداً عملت عليه",
            question_en="Describe a complex project you worked on",
            max_duration_seconds=180
        ),
        Question(
            order=6,
            question_ar="كيف تتعامل مع الضغط؟",
            question_en="How do you handle pressure?",
            max_duration_seconds=90
        ),
        Question(
            order=7,
            question_ar="أين ترى نفسك بعد 5 سنوات؟",
            question_en="Where do you see yourself in 5 years?",
            max_duration_seconds=90
        ),
        Question(
            order=8,
            question_ar="ما هي خبرتك في العمل الجماعي؟",
            question_en="What is your experience with teamwork?",
            max_duration_seconds=120
        ),
        Question(
            order=9,
            question_ar="كيف تتعلم تقنيات جديدة؟",
            question_en="How do you learn new technologies?",
            max_duration_seconds=90
        ),
        Question(
            order=10,
            question_ar="ما هي توقعاتك للراتب؟",
            question_en="What are your salary expectations?",
            max_duration_seconds=60
        ),
        # 10 questions supplémentaires...
        Question(
            order=11,
            question_ar="صف موقفاً تعاملت فيه مع خلاف في الفريق",
            question_en="Describe a situation where you handled a team conflict",
            max_duration_seconds=120
        ),
        Question(
            order=12,
            question_ar="ما هي المهارات التقنية التي تتقنها؟",
            question_en="What technical skills do you master?",
            max_duration_seconds=120
        ),
        Question(
            order=13,
            question_ar="كيف تنظم وقتك ومهامك؟",
            question_en="How do you organize your time and tasks?",
            max_duration_seconds=90
        ),
        Question(
            order=14,
            question_ar="ما الذي يحفزك في العمل؟",
            question_en="What motivates you at work?",
            max_duration_seconds=90
        ),
        Question(
            order=15,
            question_ar="صف خطأً ارتكبته وماذا تعلمت منه",
            question_en="Describe a mistake you made and what you learned",
            max_duration_seconds=120
        ),
        Question(
            order=16,
            question_ar="كيف تبقى محدثاً بأحدث التقنيات؟",
            question_en="How do you stay updated with the latest technologies?",
            max_duration_seconds=90
        ),
        Question(
            order=17,
            question_ar="ما هو أكبر تحدٍ واجهته مهنياً؟",
            question_en="What is the biggest professional challenge you've faced?",
            max_duration_seconds=120
        ),
        Question(
            order=18,
            question_ar="هل تفضل العمل بمفردك أم في فريق؟",
            question_en="Do you prefer working alone or in a team?",
            max_duration_seconds=90
        ),
        Question(
            order=19,
            question_ar="ما الذي يميزك عن المرشحين الآخرين؟",
            question_en="What sets you apart from other candidates?",
            max_duration_seconds=90
        ),
        Question(
            order=20,
            question_ar="هل لديك أي أسئلة لنا؟",
            question_en="Do you have any questions for us?",
            max_duration_seconds=120
        )
    ]
    
    fullstack_position = {
        "title": "Développeur Full Stack",
        "department": "IT",
        "questions": [q.model_dump() for q in fullstack_questions],
        "created_at": datetime.utcnow()
    }
    
    # Insérer
    result = db.job_positions.insert_one(fullstack_position)
    print(f"Poste créé: {fullstack_position['title']} (ID: {result.inserted_id})")
    
    # Poste 2: Data Scientist (exemple)
    datascience_questions = [
        Question(
            order=i,
            question_ar=f"سؤال {i} لعالم البيانات",
            question_en=f"Data Scientist question {i}",
            max_duration_seconds=120
        )
        for i in range(1, 21)
    ]
    
    datascience_position = {
        "title": "Data Scientist",
        "department": "Data",
        "questions": [q.model_dump() for q in datascience_questions],
        "created_at": datetime.utcnow()
    }
    
    result = db.job_positions.insert_one(datascience_position)
    print(f"✅ Poste créé: {datascience_position['title']} (ID: {result.inserted_id})")

if __name__ == "__main__":
    print("Seed des postes avec questions...")
    seed_job_positions()
    print("Terminé!")