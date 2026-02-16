"""
Moteur TTS avec Edge-TTS (Microsoft)
Voix arabes féminines de haute qualité
"""

import logging
import asyncio
import tempfile
import os
import threading

logger = logging.getLogger(__name__)


class EdgeTTSEngine:
    """Moteur TTS utilisant Edge-TTS (Microsoft) avec voix féminine"""
    
    def __init__(self):
        try:
            import edge_tts
            self.edge_tts = edge_tts
            
            # Voix féminines arabes disponibles
            self.voices = {
                # "ar": "ar-SA-ZariyahNeural",  # Voix féminine saoudienne (MEILLEURE)
                # "ar": "ar-EG-SalmaNeural",  # Voix féminine égyptienne
                # "ar": "ar-AE-FatimaNeural",  # Voix féminine émiratie
                # "ar": "ar-TN-ReemNeural",    # Voix féminine tunisienne
                "ar": "ar-LB-LaylaNeural",     # Voix féminine Libanaise 
                "en": "en-US-AriaNeural",      # Voix féminine anglaise
                "fr": "fr-FR-DeniseNeural"     # Voix féminine française
            }
            
            logger.info("Edge-TTS initialisé avec voix féminine")
            logger.info(f"   Voix arabe: {self.voices['ar']}")
            
        except ImportError as e:
            logger.error(f"Import Error: {e}")
            raise ImportError("Edge-TTS non installé: pip install edge-tts")
    
    def synthesize(self, text: str, language: str = "ar") -> bytes:
        """Synthétiser texte en audio avec voix féminine"""
        try:
            if not text or len(text.strip()) == 0:
                logger.error("Texte vide fourni à Edge-TTS")
                return b""
            
            # Choisir la voix appropriée
            voice = self.voices.get(language, self.voices["ar"])
            
            logger.info(f"Edge-TTS: Synthèse avec voix féminine")
            logger.info(f"   Texte: '{text[:100]}...'")
            logger.info(f"   Langue: {language}")
            logger.info(f"   Voix: {voice}")
            
            # Utiliser un thread séparé avec sa propre boucle asyncio
            result = {'audio': None, 'error': None}
            
            def run_synthesis():
                """Exécuter la synthèse dans un thread séparé"""
                try:
                    # Créer une nouvelle boucle asyncio pour ce thread
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    
                    try:
                        # Exécuter la synthèse
                        audio_data = new_loop.run_until_complete(
                            self._synthesize_async(text, voice)
                        )
                        result['audio'] = audio_data
                    finally:
                        new_loop.close()
                        
                except Exception as e:
                    result['error'] = e
            
            # Lancer dans un thread et attendre
            thread = threading.Thread(target=run_synthesis)
            thread.start()
            thread.join(timeout=30)  # Timeout de 30 secondes
            
            if thread.is_alive():
                logger.error("Timeout lors de la synthèse")
                return b""
            
            if result['error']:
                raise result['error']
            
            audio_data = result['audio']
            
            if audio_data and len(audio_data) > 0:
                logger.info(f"Audio généré: {len(audio_data)} bytes")
                return audio_data
            else:
                logger.error("Audio vide généré")
                return b""
        
        except Exception as e:
            logger.error(f"Erreur synthèse Edge-TTS: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return b""
    
    async def _synthesize_async(self, text: str, voice: str) -> bytes:
        """Méthode async pour générer l'audio"""
        
        # Créer un fichier temporaire
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            # Générer l'audio
            communicate = self.edge_tts.Communicate(text, voice)
            await communicate.save(tmp_path)
            
            # Lire le fichier
            with open(tmp_path, 'rb') as f:
                audio_data = f.read()
            
            # Convertir MP3 en WAV si nécessaire
            audio_data = self._convert_to_wav(audio_data)
            
            return audio_data
        
        finally:
            # Nettoyer
            try:
                os.unlink(tmp_path)
            except:
                pass
    
    def _convert_to_wav(self, mp3_data: bytes) -> bytes:
        """Convertir MP3 en WAV"""
        try:
            from pydub import AudioSegment
            import io
            
            # Charger MP3
            audio = AudioSegment.from_mp3(io.BytesIO(mp3_data))
            
            # Convertir en WAV
            wav_io = io.BytesIO()
            audio.export(wav_io, format="wav")
            
            return wav_io.getvalue()
        
        except Exception as e:
            logger.warning(f"Conversion WAV échouée: {e}")
            # Retourner le MP3 brut si la conversion échoue
            return mp3_data