@echo off
echo ====================================================================
echo COPIE DU SERVICE TTS AVEC SUPPORT FFMPEG LOCAL
echo ====================================================================
echo.

echo Verification des fichiers...

if not exist "tts_service_WITH_LOCAL_FFMPEG.py" (
    echo ERREUR: tts_service_WITH_LOCAL_FFMPEG.py non trouve dans le dossier actuel
    echo.
    echo Ce fichier devrait etre dans:
    echo   C:\Users\Lenovo\Desktop\stark-recruitment-chatbot\
    echo.
    echo Telechargez-le depuis les fichiers fournis.
    pause
    exit /b 1
)

if not exist "backend\services\" (
    echo ERREUR: Dossier backend\services\ non trouve
    pause
    exit /b 1
)

echo.
echo Backup de l'ancien fichier...
if exist "backend\services\tts_service.py" (
    copy backend\services\tts_service.py backend\services\tts_service.py.backup >nul
    echo OK: Backup cree (tts_service.py.backup)
)

echo.
echo Copie du nouveau service TTS...
copy tts_service_WITH_LOCAL_FFMPEG.py backend\services\tts_service.py
if %errorlevel% neq 0 (
    echo ERREUR lors de la copie
    pause
    exit /b 1
)

echo OK: Service TTS mis a jour

echo.
echo ====================================================================
echo TERMINE !
echo ====================================================================
echo.
echo Le service TTS va maintenant:
echo   1. Detecter automatiquement ffmpeg dans models\ffmpeg-8.0.1...
echo   2. Configurer pydub pour l'utiliser
echo   3. Generer de l'audio arabe parfait avec gTTS
echo.
echo Testez maintenant:
echo   python test_tts_arabic.py
echo.
echo Vous devriez voir dans les logs:
echo   "ffmpeg configure depuis: ...models\ffmpeg-8.0.1-essentials_build\bin"
echo.
pause
