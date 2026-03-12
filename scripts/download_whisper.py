"""
Télécharge le modèle Whisper dans models/whisper/ du projet.
Usage : python scripts/download_whisper.py [taille]
Tailles : tiny | base | small | medium | large-v3
"""

import sys
import os
from pathlib import Path

# ── Taille du modèle ──────────────────────────────────────────────
MODEL_SIZE = sys.argv[1] if len(sys.argv) > 1 else "medium"

VALID_SIZES = ["tiny", "base", "small", "medium", "large-v2", "large-v3"]
if MODEL_SIZE not in VALID_SIZES:
    print(f"Taille invalide : {MODEL_SIZE}")
    print(f"   Valeurs valides : {', '.join(VALID_SIZES)}")
    sys.exit(1)

# ── Dossier de destination ────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent
MODELS_DIR   = PROJECT_ROOT / "models" / "whisper"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 55)
print(f"  Téléchargement Whisper '{MODEL_SIZE}'")
print(f"  Destination : {MODELS_DIR}")
print("=" * 55)

# ── Tailles indicatives ───────────────────────────────────────────
SIZES_INFO = {
    "tiny":     ("75 MB",   "Très rapide, précision faible"),
    "base":     ("145 MB",  "Rapide, précision correcte"),
    "small":    ("483 MB",  "Bon compromis vitesse/précision"),
    "medium":   ("1.5 GB",  "Recommandé — bonne précision AR/FR/EN"),
    "large-v2": ("3.1 GB",  "Haute précision"),
    "large-v3": ("3.1 GB",  "Meilleure précision disponible"),
}
size_mb, desc = SIZES_INFO.get(MODEL_SIZE, ("?", ""))
print(f"  Taille    : {size_mb}")
print(f"  Qualité   : {desc}")
print()

try:
    from faster_whisper import WhisperModel

    print(f"Téléchargement en cours...")
    print(f"   (stocké dans : {MODELS_DIR / MODEL_SIZE})")
    print()

    # Le paramètre download_root force le dossier de destination
    model = WhisperModel(
        MODEL_SIZE,
        device="cpu",
        compute_type="int8",
        download_root=str(MODELS_DIR),
    )

    print()
    print(f"Whisper '{MODEL_SIZE}' téléchargé avec succès !")
    print(f"   Dossier : {MODELS_DIR}")
    print()

    # ── Test rapide ───────────────────────────────────────────────
    print("Test de transcription...")
    import numpy as np
    dummy_audio = np.zeros(16000, dtype=np.float32)  # 1 seconde de silence

    import tempfile, wave, struct
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = tmp.name

    with wave.open(tmp_path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(b'\x00\x00' * 16000)

    segments, info = model.transcribe(tmp_path, language="fr")
    _ = list(segments)  # consommer le générateur
    os.unlink(tmp_path)

    print(f"Test OK — modèle fonctionnel")
    print()
    print("─" * 55)
    print("  Mettre à jour .env :")
    print(f"  ASR_ENGINE=faster-whisper")
    print(f"  WHISPER_MODEL_SIZE={MODEL_SIZE}")
    print("─" * 55)

except ImportError:
    print("faster-whisper n'est pas installé.")
    print("   Lancer : pip install faster-whisper")
    sys.exit(1)

except Exception as e:
    print(f"Erreur : {e}")
    sys.exit(1)
