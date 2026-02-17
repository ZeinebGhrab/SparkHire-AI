"""
Moteur TTS avec Coqui-TTS (Open Source)
Alternative gratuite et open-source à Edge-TTS
✅ Support multilingue avec arabe
✅ Qualité vocale élevée
✅ Fonctionne offline
"""

import logging
import os
import tempfile
import threading
from typing import Optional

logger = logging.getLogger(__name__)


class CoquiTTSEngine:
    """Moteur TTS utilisant Coqui-TTS (Open Source)"""
    
    def __init__(self):
        """Initialiser le moteur Coqui-TTS"""
        try:
            from TTS.api import TTS
            
            # Chemin vers le modèle local
            model_path = "models/xtts_v2"
            
            # Vérifier si le modèle existe localement
            if os.path.exists(model_path) and os.path.exists(os.path.join(model_path, "model.pth")):
                logger.info(f"⏳ Chargement du modèle Coqui-TTS depuis: {model_path}")
                logger.info("   ✅ Modèle local détecté (pas de téléchargement)")
                
                # Charger depuis le dossier local
                self.tts = TTS(model_path=model_path, config_path=os.path.join(model_path, "config.json"))
            else:
                logger.info("⏳ Chargement du modèle Coqui-TTS XTTS-v2...")
                logger.warning(f"   ⚠️ Modèle local non trouvé dans {model_path}")
                logger.info("   ⚠️ Téléchargement automatique ~2GB depuis HuggingFace")
                
                # Télécharger automatiquement si absent
                # Ce modèle supporte: ar, en, es, fr, de, it, pt, pl, tr, ru, nl, cs, zh-cn, ja, ko, hu
                self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
            
            logger.info("✅ Coqui-TTS XTTS-v2 chargé avec succès")
            
            # Mapping des langues
            self.languages = {
                "ar": "ar",   # Arabe
                "en": "en",   # Anglais
                "fr": "fr"    # Français
            }
            
            # Paramètres de génération
            self.generation_params = {
                "temperature": 0.7,     # Contrôle la variabilité (0.5-1.0)
                "speed": 1.0,           # Vitesse de parole (0.5-2.0)
            }
            
            logger.info(f"   Langues supportées: {list(self.languages.keys())}")
            logger.info(f"   Paramètres: Temp={self.generation_params['temperature']}, Speed={self.generation_params['speed']}")
            
        except ImportError as e:
            logger.error("❌ Coqui-TTS non installé")
            logger.error("   Solution: pip install TTS")
            raise ImportError("Installez Coqui-TTS: pip install TTS")
        
        except Exception as e:
            logger.error(f"❌ Erreur initialisation Coqui-TTS: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    
    def synthesize(self, text: str, language: str = "ar", speaker_wav: Optional[str] = None) -> bytes:
        """
        Synthétiser texte en audio
        
        Args:
            text: Texte à synthétiser
            language: Code langue (ar, en, fr)
            speaker_wav: Chemin vers fichier WAV pour clonage de voix (optionnel)
        
        Returns:
            bytes: Audio WAV
        """
        try:
            if not text or len(text.strip()) == 0:
                logger.error("❌ Texte vide fourni à Coqui-TTS")
                return b""
            
            # Obtenir le code langue
            lang = self.languages.get(language, "ar")
            
            logger.info(f"🎤 Coqui-TTS: Synthèse audio")
            logger.info(f"   Texte: '{text[:100]}...'")
            logger.info(f"   Langue: {lang}")
            if speaker_wav:
                logger.info(f"   Clonage voix: {speaker_wav}")
            
            # Créer fichier temporaire pour l'output
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                tmp_path = tmp_file.name
            
            try:
                # Paramètres de génération
                generation_kwargs = {
                    "text": text,
                    "language": lang,
                    "file_path": tmp_path,
                    "speed": self.generation_params["speed"]
                }
                
                # Ajouter clonage de voix si spécifié
                if speaker_wav and os.path.exists(speaker_wav):
                    generation_kwargs["speaker_wav"] = speaker_wav
                    logger.info("   Mode: Clonage de voix")
                else:
                    logger.info("   Mode: Voix par défaut")
                
                # Générer l'audio
                logger.info("   ⏳ Génération en cours...")
                self.tts.tts_to_file(**generation_kwargs)
                
                # Lire le fichier généré
                with open(tmp_path, 'rb') as f:
                    audio_data = f.read()
                
                if audio_data and len(audio_data) > 0:
                    logger.info(f"✅ Audio généré: {len(audio_data)} bytes")
                    return audio_data
                else:
                    logger.error("❌ Audio vide généré")
                    return b""
            
            finally:
                # Nettoyer le fichier temporaire
                try:
                    os.unlink(tmp_path)
                except:
                    pass
        
        except Exception as e:
            logger.error(f"❌ Erreur synthèse Coqui-TTS: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return b""
    
    def set_speed(self, speed: float):
        """
        Ajuster la vitesse de parole
        
        Args:
            speed: Vitesse (0.5 = lent, 1.0 = normal, 2.0 = rapide)
        """
        if 0.5 <= speed <= 2.0:
            self.generation_params["speed"] = speed
            logger.info(f"✅ Vitesse ajustée: {speed}")
        else:
            logger.warning(f"⚠️ Vitesse invalide: {speed} (doit être entre 0.5 et 2.0)")
    
    def set_temperature(self, temperature: float):
        """
        Ajuster la température (variabilité de la voix)
        
        Args:
            temperature: Température (0.5 = monotone, 1.0 = varié)
        """
        if 0.5 <= temperature <= 1.0:
            self.generation_params["temperature"] = temperature
            logger.info(f"✅ Température ajustée: {temperature}")
        else:
            logger.warning(f"⚠️ Température invalide: {temperature} (doit être entre 0.5 et 1.0)")


# Test rapide du moteur
if __name__ == "__main__":
    # Configuration du logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*60)
    print("🧪 TEST DU MOTEUR COQUI-TTS")
    print("="*60 + "\n")
    
    try:
        # Initialiser le moteur
        engine = CoquiTTSEngine()
        
        # Texte de test
        test_text = "مرحبا بكم في ستارك ريكروتمنت. أنا مساعدة الموارد البشرية."
        
        # Générer l'audio
        print("\n📝 Génération audio de test...")
        audio = engine.synthesize(test_text, language="ar")
        
        if audio and len(audio) > 0:
            # Sauvegarder pour écoute
            test_file = "test_coqui_output.wav"
            with open(test_file, 'wb') as f:
                f.write(audio)
            print(f"\n✅ Test réussi!")
            print(f"📁 Audio sauvegardé: {test_file}")
            print(f"📊 Taille: {len(audio)} bytes")
            print(f"\n🎧 Écoutez le fichier pour évaluer la qualité!")
        else:
            print("\n❌ Échec de la génération audio")
    
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60 + "\n")