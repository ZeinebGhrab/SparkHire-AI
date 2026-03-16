"""
Script de diagnostic — à exécuter depuis la racine du projet :
  python scripts/debug_notification.py

Teste chaque étape du pipeline de notification indépendamment.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database import db
from datetime import datetime
from bson import ObjectId

SEP = "─" * 60

def ok(msg):  print(f"  ✅ {msg}")
def err(msg): print(f"  ❌ {msg}")
def info(msg): print(f"  ℹ️  {msg}")

# ── 1. Connexion MongoDB ──────────────────────────────────────────
print(f"\n{SEP}")
print("ÉTAPE 1 — Connexion MongoDB")
print(SEP)
try:
    db.command("ping")
    ok("MongoDB connecté")
except Exception as e:
    err(f"MongoDB inaccessible : {e}")
    sys.exit(1)

# ── 2. INSERT direct dans db.notifications ────────────────────────
print(f"\n{SEP}")
print("ÉTAPE 2 — INSERT direct dans db.notifications")
print(SEP)
try:
    doc = {
        "recipient_email": "test@debug.tn",
        "type":            "debug_test",
        "title":           "Test diagnostic",
        "message":         "Notification insérée directement par le script de debug",
        "data":            {"source": "debug_notification.py"},
        "priority":        "normal",
        "read":            False,
        "created_at":      datetime.utcnow(),
    }
    result = db.notifications.insert_one(doc)
    ok(f"INSERT OK — _id = {result.inserted_id}")
except Exception as e:
    err(f"INSERT échoué : {e}")
    sys.exit(1)

# ── 3. Vérifier que la collection notifications existe et est lisible
print(f"\n{SEP}")
print("ÉTAPE 3 — Lecture db.notifications")
print(SEP)
count = db.notifications.count_documents({})
ok(f"Total documents dans notifications : {count}")

# ── 4. Recruteurs ─────────────────────────────────────────────────
print(f"\n{SEP}")
print("ÉTAPE 4 — Collection db.recruiters")
print(SEP)
recruiters = list(db.recruiters.find({}, {"email": 1}))
if recruiters:
    ok(f"{len(recruiters)} recruteur(s) trouvé(s) :")
    for r in recruiters:
        info(f"  email = {r.get('email', '?')}")
else:
    err("Aucun recruteur dans db.recruiters — le fallback ne fonctionnera pas !")

# ── 5. Dernières sessions ─────────────────────────────────────────
print(f"\n{SEP}")
print("ÉTAPE 5 — Dernières sessions d'entretien")
print(SEP)
sessions = list(
    db.interview_sessions.find(
        {},
        {"session_id": 1, "status": 1, "created_by": 1, "candidate_id": 1}
    ).sort("created_at", -1).limit(5)
)
if not sessions:
    err("Aucune session trouvée")
else:
    for s in sessions:
        created_by = s.get("created_by", "")
        flag = "✅" if created_by and "@" in str(created_by) else "⚠️ VIDE"
        info(
            f"session_id={s.get('session_id','?')} | "
            f"status={s.get('status','?')} | "
            f"created_by={created_by!r} {flag}"
        )

# ── 6. Simuler _send_completion_notification ──────────────────────
print(f"\n{SEP}")
print("ÉTAPE 6 — Simulation de _send_completion_notification")
print(SEP)

# Prendre la dernière session completed
session = db.interview_sessions.find_one({"status": "completed"})
if not session:
    session = db.interview_sessions.find_one({})

if not session:
    err("Aucune session à tester")
else:
    session_id = session.get("session_id", "?")
    info(f"Session de test : {session_id}")

    created_by = session.get("created_by", "")
    if created_by and "@" in str(created_by):
        emails = [created_by]
        ok(f"created_by trouvé : {created_by}")
    else:
        err(f"created_by absent ou invalide : {created_by!r}")
        all_r = list(db.recruiters.find({}, {"email": 1}))
        emails = [r["email"] for r in all_r if r.get("email")]
        if emails:
            info(f"Fallback recruteurs : {emails}")
        else:
            err("Aucun recruteur dans db.recruiters non plus → 0 notification envoyée")
            emails = []

    if emails:
        # Charger nom candidat
        candidate_name = "Candidat Test"
        cid = session.get("candidate_id", "")
        if cid:
            try:
                cand = db.candidates.find_one({"_id": ObjectId(cid)}, {"first_name":1,"last_name":1})
                if cand:
                    candidate_name = f"{cand.get('first_name','')} {cand.get('last_name','')}".strip()
            except Exception as e:
                info(f"Chargement candidat échoué : {e}")

        # Charger titre poste
        position_title = "Poste Test"
        pid = session.get("job_position_id", "")
        if pid:
            try:
                pos = db.job_positions.find_one({"_id": ObjectId(pid)}, {"title":1})
                if pos:
                    position_title = pos.get("title", "Poste Test")
            except Exception as e:
                info(f"Chargement poste échoué : {e}")

        info(f"Candidat : {candidate_name!r}")
        info(f"Poste    : {position_title!r}")

        for email in emails:
            test_doc = {
                "recipient_email": email,
                "type":            "interview_completed",
                "title":           "Entretien complété",
                "message":         f"Le candidat {candidate_name} a complété son entretien pour le poste {position_title}. Veuillez le consulter.",
                "data": {
                    "session_id":     session_id,
                    "candidate_name": candidate_name,
                    "position_title": position_title,
                },
                "priority":   "high",
                "read":       False,
                "created_at": datetime.utcnow(),
            }
            try:
                r = db.notifications.insert_one(test_doc)
                ok(f"Notification simulée insérée — _id={r.inserted_id} → {email}")
            except Exception as e:
                err(f"INSERT simulé échoué : {e}")

# ── Résumé ────────────────────────────────────────────────────────
print(f"\n{SEP}")
print("RÉSUMÉ — db.notifications (5 dernières)")
print(SEP)
last = list(db.notifications.find({}).sort("created_at", -1).limit(5))
for n in last:
    print(f"  [{n.get('type','?')}] → {n.get('recipient_email','?')} | {n.get('title','?')} | read={n.get('read')}")

print(f"\n{SEP}")
print("Diagnostic terminé.")
print(SEP)