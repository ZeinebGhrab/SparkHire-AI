@echo off
echo ====================================================================
echo NETTOYAGE DU CACHE TTS ET REGENERATION AUDIO ARABE
echo ====================================================================
echo.

echo [1/3] Suppression du cache TTS...
if exist "uploads\tts_cache" (
    del /Q uploads\tts_cache\*.wav 2>nul
    echo OK: Cache TTS nettoye
) else (
    echo Pas de cache a nettoyer
)

echo.
echo [2/3] Suppression des fichiers de test...
del test_audio_arabic.wav 2>nul
del test_audio_english.wav 2>nul
del test_question_complete.wav 2>nul
echo OK: Fichiers de test supprimes

echo.
echo [3/3] Regeneration de l'audio arabe...
echo.

python -c "
from backend.services.tts_service import get_tts_service
from pathlib import Path

print('Initialisation du service TTS...')
tts = get_tts_service()

print('Generation audio arabe: قدم نفسك باختصار')
audio_ar = tts.synthesize('قدم نفسك باختصار', language='ar', use_cache=False)

if audio_ar and len(audio_ar) > 1000:
    with open('test_audio_arabic_NEW.wav', 'wb') as f:
        f.write(audio_ar)
    print(f'✅ Audio arabe genere: {len(audio_ar)} bytes')
    print('   Fichier: test_audio_arabic_NEW.wav')
else:
    print(f'❌ ERREUR: Audio invalide ({len(audio_ar) if audio_ar else 0} bytes)')
    print('   Un fichier audio valide doit faire plus de 1000 bytes')

print('')
print('Generation audio anglais: Introduce yourself briefly')
audio_en = tts.synthesize('Introduce yourself briefly', language='en', use_cache=False)

if audio_en and len(audio_en) > 1000:
    with open('test_audio_english_NEW.wav', 'wb') as f:
        f.write(audio_en)
    print(f'✅ Audio anglais genere: {len(audio_en)} bytes')
    print('   Fichier: test_audio_english_NEW.wav')
else:
    print(f'❌ ERREUR: Audio invalide ({len(audio_en) if audio_en else 0} bytes)')
"

if %errorlevel% neq 0 (
    echo.
    echo ERREUR lors de la generation
    pause
    exit /b 1
)

echo.
echo ====================================================================
echo TERMINÉ !
echo ====================================================================
echo.
echo Fichiers generes:
echo   - test_audio_arabic_NEW.wav (arabe)
echo   - test_audio_english_NEW.wav (anglais)
echo.
echo ECOUTEZ CES FICHIERS:
echo   Si test_audio_arabic_NEW.wav dit bien "قدم نفسك باختصار" en arabe,
echo   alors le probleme est resolu !
echo.
echo   Si vous entendez toujours "1 2 3" ou rien, il y a un probleme
echo   avec gTTS ou ffmpeg.
echo.
pause
