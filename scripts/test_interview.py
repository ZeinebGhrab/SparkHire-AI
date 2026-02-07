#!/usr/bin/env python3
"""Script pour tester un entretien complet"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
import asyncio
from backend.config import settings

async def test_interview():
    """Tester le flow complet d'un entretien"""
    
    base_url = f"http://{settings.API_HOST}:{settings.API_PORT}"
    
    async with httpx.AsyncClient() as client:
        
        # 1. Login
        print("1️⃣  Login...")
        login_response = await client.post(
            f"{base_url}/auth/login",
            data={
                "username": "rh@stark.tn",
                "password": "admin123"
            }
        )
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.text}")
            return
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        print(f"✅ Logged in, token: {token[:20]}...")
        
        # 2. Lister les postes
        print("\n2️⃣  Lister les postes disponibles...")
        positions_response = await client.get(
            f"{base_url}/interviews/positions",
            headers=headers
        )
        
        positions = positions_response.json()
        
        if not positions:
            print("❌ Aucun poste trouvé. Exécutez d'abord seed_job_positions.py")
            return
        
        print(f"✅ {len(positions)} poste(s) trouvé(s)")
        for pos in positions:
            print(f"   - {pos['title']} ({len(pos['questions'])} questions)")
        
        # 3. Lister les candidats
        print("\n3️⃣  Lister les candidats...")
        candidates_response = await client.get(
            f"{base_url}/candidates",
            headers=headers
        )
        
        candidates = candidates_response.json()
        
        if not candidates:
            print("❌ Aucun candidat trouvé. Créez-en un d'abord.")
            return
        
        print(f"✅ {len(candidates)} candidat(s) trouvé(s)")
        
        # 4. Créer une session d'entretien
        print("\n4️⃣  Créer une session d'entretien...")
        session_data = {
            "candidate_id": candidates[0]["id"],
            "job_position_id": positions[0]["id"],
            "language": "ar"
        }
        
        session_response = await client.post(
            f"{base_url}/interviews/sessions",
            json=session_data,
            headers=headers
        )
        
        if session_response.status_code != 200:
            print(f"❌ Erreur création session: {session_response.text}")
            return
        
        session = session_response.json()
        print(f"✅ Session créée: {session['session_id']}")
        print(f"   Candidat: {candidates[0]['first_name']} {candidates[0]['last_name']}")
        print(f"   Poste: {positions[0]['title']}")
        print(f"   Langue: {session['language']}")
        
        # 5. Instructions
        print("\n" + "="*60)
        print("✅ ENTRETIEN PRÊT!")
        print("="*60)
        print(f"\n🔗 Pour démarrer l'entretien:")
        print(f"   1. Lancez le client: cd client && python main.py")
        print(f"   2. Entrez le session_id: {session['session_id']}")
        print(f"   3. Cliquez sur 'Se connecter'")
        print("\n📊 Pour voir les résultats:")
        print(f"   GET {base_url}/interviews/sessions/{session['session_id']}")
        print("="*60)

if __name__ == "__main__":
    print("🧪 Test du système d'entretien vocal\n")
    asyncio.run(test_interview())