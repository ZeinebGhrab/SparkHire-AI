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
    
    base_url = f"http://127.0.0.1:{settings.API_PORT}"

    
    async with httpx.AsyncClient() as client:
        
        # 1. Login
        print("Login...")
        login_response = await client.post(
            f"{base_url}/auth/login",
            data={
                "username": "rh@stark.tn",
                "password": "admin123"
            }
        )
        
        if login_response.status_code != 200:
            print(f"Login failed: {login_response.text}")
            return
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        print(f"Logged in, token: {token[:20]}...")
        
        # 2. Lister les postes
        print("\nLister les postes disponibles...")
        positions_response = await client.get(
            f"{base_url}/interviews/positions",
            headers=headers
        )
        
        positions = positions_response.json()
        
        if not positions:
            print("Aucun poste trouvé. Exécutez d'abord seed_job_positions.py")
            return
        
        print(f"{len(positions)} poste(s) trouvé(s)")
        for pos in positions:
            print(f"   - {pos['title']} ({len(pos['questions'])} questions)")
        
        # 3. Lister les candidats
        print("\nLister les candidats...")
        candidates_response = await client.get(
            f"{base_url}/candidates/",
            headers=headers
        )
        
        # Vérifier le status code
        if candidates_response.status_code != 200:
            print(f"Erreur récupération candidats: {candidates_response.status_code}")
            print(f"   Réponse: {candidates_response.text}")
            candidates = []
        else:
            try:
                candidates = candidates_response.json()
            except Exception as e:
                print(f"Erreur parsing JSON: {e}")
                candidates = []
        
        # 4. Créer un candidat si aucun n'existe
        if not candidates:
            print("Aucun candidat trouvé. Création d'un candidat de test...")
            
            candidate_data = {
                "first_name": "Ahmed",
                "last_name": "Ben Ali",
                "contact": {
                    "email": "ahmed.benali@example.com",
                    "phone": "+216 12 345 678"
                },
                "skills": ["Python", "FastAPI", "MongoDB", "React"],
                "experiences": [
                    {
                        "title": "Développeur Full Stack",
                        "company": "Tech Corp",
                        "location": "Tunis, Tunisie",
                        "start_date": "2022-01",
                        "currently_working": True,
                        "description": "Développement d'applications web",
                        "technologies": ["Python", "React", "PostgreSQL"]
                    }
                ],
                "education": [
                    {
                        "degree": "Licence",
                        "field": "Informatique",
                        "institution": "ISIMS Sfax",
                        "start_date": "2019-09",
                        "end_date": "2022-06",
                        "currently_studying": False
                    }
                ]
            }
            
            create_candidate_response = await client.post(
                f"{base_url}/candidates/",
                json=candidate_data,
                headers=headers
            )
            
            if create_candidate_response.status_code == 200:
                new_candidate = create_candidate_response.json()
                candidates = [new_candidate]
                print(f"Candidat créé: {new_candidate['first_name']} {new_candidate['last_name']}")
            else:
                print(f"Erreur création candidat: {create_candidate_response.text}")
                return
        else:
            print(f"{len(candidates)} candidat(s) trouvé(s)")
            for c in candidates:
                print(f"   - {c['first_name']} {c['last_name']} ({c['contact']['email']})")
        
        # 5. Créer une session d'entretien
        print("\n4️Créer une session d'entretien...")
        session_data = {
            "candidate_id": candidates[0]["_id"],
            "job_position_id": positions[0]["_id"],
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
        print(f"   Statut: {session['status']}")
        
        # 6. Instructions
        print("\n" + "="*70)
        print("✅ ENTRETIEN PRÊT!")
        print("="*70)
        print(f"\n🔗 Pour démarrer l'entretien:")
        print(f"   1. Lancez le client: python client/main.py")
        print(f"   2. Entrez le session_id: {session['session_id']}")
        print(f"   3. Cliquez sur 'Se connecter'")
        print("\n📊 Pour voir les résultats:")
        print(f"   GET {base_url}/interviews/sessions/{session['session_id']}")
        print("\n💡 Ou testez via WebSocket:")
        print(f"   python scripts/test_websocket.py {session['session_id']}")
        print("="*70)

if __name__ == "__main__":
    print("🧪 Test du système d'entretien vocal\n")
    asyncio.run(test_interview())