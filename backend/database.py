from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Charger les variables d'environnement depuis .env
load_dotenv()

# Récupérer l'URL de MongoDB (par défaut : localhost)
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGODB_DB_NAME", "stark_recruitment")

# Créer le client MongoDB
client = MongoClient(MONGODB_URL)

# Exposer la base de données comme un objet global nommé `db`
db = client[DB_NAME]