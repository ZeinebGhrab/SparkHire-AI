import os
from pathlib import Path
from pymongo import MongoClient
from dotenv import load_dotenv
import bcrypt

# Charger .env
project_root = Path(__file__).parent.parent
load_dotenv(project_root / ".env")

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGODB_DB_NAME", "stark_recruitment")
EMAIL = "rh@stark.tn"
PASSWORD = "admin123"

def create_admin_user():
    print(f"Connexion à MongoDB : {MONGODB_URL}")
    client = MongoClient(MONGODB_URL)
    db = client[DB_NAME]

    # Vérifier si existe déjà
    if db.recruiters.find_one({"email": EMAIL}):
        print(f"Recruteur '{EMAIL}' existe déjà.")
        return

    # Hacher le mot de passe avec bcrypt
    hashed = bcrypt.hashpw(PASSWORD.encode('utf-8'), bcrypt.gensalt())
    
    # Insérer
    result = db.recruiters.insert_one({
        "email": EMAIL,
        "password_hash": hashed
    })
    print(f"Admin créé ! ID: {result.inserted_id}")

if __name__ == "__main__":
    print("Création du recruteur administrateur...")
    create_admin_user()