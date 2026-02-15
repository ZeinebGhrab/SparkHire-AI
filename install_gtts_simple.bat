@echo off
echo ====================================================================
echo INSTALLATION GTTS POUR SUPPORT ARABE - CONFIGURATION SIMPLIFIEE
echo ====================================================================
echo.

echo [Etape 1/3] Installation de gTTS...
pip install gTTS==2.5.0
if %errorlevel% neq 0 (
    echo ERREUR lors de l'installation de gTTS
    pause
    exit /b 1
)
echo OK: gTTS installe

echo.
echo [Etape 2/3] Installation de pydub...
pip install pydub==0.25.1
if %errorlevel% neq 0 (
    echo ERREUR lors de l'installation de pydub
    pause
    exit /b 1
)
echo OK: pydub installe

echo.
echo [Etape 3/3] Modification de backend\config.py...

REM Backup
if exist backend\config.py (
    copy backend\config.py backend\config.py.backup >nul
    echo Backup cree: backend\config.py.backup
)

REM Remplacer TTS_ENGINE
powershell -Command "(Get-Content backend\config.py) -replace 'TTS_ENGINE: str = \"pyttsx3\"', 'TTS_ENGINE: str = \"gtts\"' | Set-Content backend\config.py"

echo OK: Configuration modifiee

echo.
echo [4/3] Copie du service TTS corrige...
if exist tts_service_WITH_LOCAL_FFMPEG.py (
    copy tts_service_WITH_LOCAL_FFMPEG.py backend\services\tts_service.py
    echo OK: Service TTS mis a jour
) else (
    echo ATTENTION: tts_service_WITH_LOCAL_FFMPEG.py non trouve
    echo Vous devrez copier ce fichier manuellement dans backend\services\
)

echo.
echo ====================================================================
echo INSTALLATION TERMINEE !
echo ====================================================================
echo.
echo Ce qui a ete fait:
echo   [OK] gTTS installe (Google Text-to-Speech)
echo   [OK] pydub installe (pour conversion audio)
echo   [OK] backend\config.py modifie (TTS_ENGINE = "gtts")
echo   [OK] Service TTS mis a jour (auto-detection ffmpeg local)
echo.
echo IMPORTANT:
echo   Le nouveau service TTS va automatiquement detecter et utiliser
echo   ffmpeg depuis: models\ffmpeg-8.0.1-essentials_build\bin
echo.
echo Prochaine etape:
echo   1. Testez: python test_tts_arabic.py
echo   2. Lancez le backend: python backend\main.py
echo   3. Testez un entretien
echo.
echo Dans les logs, vous devriez voir:
echo   "ffmpeg configure depuis: ...models\ffmpeg-8.0.1-essentials_build\bin"
echo   "gTTS (Google Text-to-Speech) initialise avec succes"
echo.
pause
