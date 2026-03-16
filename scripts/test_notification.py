"""
Test rapide du système de notification.
Usage : python scripts/test_notification.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
import asyncio

BASE_URL = "http://localhost:8000"
USERNAME = "rh@stark.tn"
PASSWORD = "admin123"


async def test():
    async with httpx.AsyncClient(timeout=30.0) as client:

        # ── 1. Login ──────────────────────────────────────────────────────────
        print("1️⃣  Login...")
        r = await client.post(f"{BASE_URL}/auth/login",
                              data={"username": USERNAME, "password": PASSWORD})
        if r.status_code != 200:
            print(f"❌ Login échoué : {r.text}")
            return
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print(f"✅ Token obtenu : {token[:30]}...")

        # ── 2. Compteur avant ─────────────────────────────────────────────────
        r = await client.get(f"{BASE_URL}/notifications/unread-count", headers=headers)
        count_before = r.json().get("unread_count", 0)
        print(f"\n2️⃣  Notifications non lues AVANT : {count_before}")

        # ── 3. Récupérer une session existante ────────────────────────────────
        print("\n3️⃣  Récupération des sessions...")
        r = await client.get(f"{BASE_URL}/interviews/sessions?limit=5", headers=headers)
        sessions = r.json()
        if not sessions:
            print("❌ Aucune session trouvée — crée d'abord une session via Postman ou test_interview.py")
            return

        # Prendre la première session non-completed
        session = None
        for s in sessions:
            if s["status"] not in ("completed",):
                session = s
                break

        if not session:
            # Toutes sont completed → prendre la première quand même
            session = sessions[0]

        session_id = session["session_id"]
        print(f"   Session : {session_id} | status={session['status']} | created_by={session.get('created_by', '?')}")

        # ── 4. Forcer status → completed ──────────────────────────────────────
        print(f"\n4️⃣  PATCH status → completed...")
        r = await client.patch(
            f"{BASE_URL}/interviews/sessions/{session_id}/status?status=completed",
            headers=headers
        )
        if r.status_code != 200:
            print(f"❌ PATCH échoué : {r.text}")
            return
        print(f"✅ Statut mis à jour : {r.json().get('status')}")

        # ── 5. Compteur après ─────────────────────────────────────────────────
        await asyncio.sleep(0.5)  # laisser le temps à MongoDB
        r = await client.get(f"{BASE_URL}/notifications/unread-count", headers=headers)
        count_after = r.json().get("unread_count", 0)
        print(f"\n5️⃣  Notifications non lues APRÈS : {count_after}")

        if count_after > count_before:
            print(f"\n✅ SUCCÈS — {count_after - count_before} notification(s) créée(s) !")
        else:
            print(f"\n❌ ÉCHEC — le compteur n'a pas augmenté ({count_before} → {count_after})")
            print("   Vérifie les logs du serveur pour voir l'erreur.")

        # ── 6. Afficher les dernières notifications ───────────────────────────
        print("\n6️⃣  Dernières notifications :")
        r = await client.get(f"{BASE_URL}/notifications/?limit=5", headers=headers)
        notifs = r.json()
        if not notifs:
            print("   Aucune notification.")
        for n in notifs:
            print(f"   [{n['type']}] → {n['recipient_email']} | {n['message'][:80]} | read={n['read']}")


if __name__ == "__main__":
    asyncio.run(test())