#!/usr/bin/env python3
"""
🔧 Script d'installation des améliorations Avatar + TTS
Applique automatiquement toutes les modifications nécessaires
"""

import sys
from pathlib import Path
import shutil
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent
CLIENT_DIR = PROJECT_ROOT / "client"
UI_DIR = CLIENT_DIR / "ui"

def backup_file(file_path: Path) -> Path:
    """Créer un backup d'un fichier"""
    if not file_path.exists():
        print(f"⚠️ Fichier non trouvé: {file_path}")
        return None
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = file_path.parent / f"{file_path.stem}.backup_{timestamp}{file_path.suffix}"
    
    shutil.copy2(file_path, backup_path)
    print(f"✅ Backup créé: {backup_path.name}")
    return backup_path


def patch_main_window():
    """Patcher main_window.py"""
    
    print("\n" + "="*70)
    print("📝 Modification de main_window.py")
    print("="*70)
    
    file_path = UI_DIR / "main_window.py"
    
    if not file_path.exists():
        print(f"❌ Fichier non trouvé: {file_path}")
        return False
    
    # Backup
    backup_file(file_path)
    
    # Lire le contenu
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    modifications = 0
    
    # 1. Ajouter les variables d'état audio
    if "self.is_audio_playing = False" not in content:
        old_audio_init = """        # Connecter les signaux du lecteur audio
        self.audio_player.mediaStatusChanged.connect(self._on_audio_status_changed)"""
        
        new_audio_init = """        # État de lecture audio
        self.is_audio_playing = False
        self.current_audio_type = None  # 'question', 'welcome', 'complete'
        
        # Connecter TOUS les signaux du lecteur audio pour un contrôle précis
        self.audio_player.mediaStatusChanged.connect(self._on_audio_status_changed)
        self.audio_player.playbackStateChanged.connect(self._on_playback_state_changed)
        self.audio_player.errorOccurred.connect(self._on_audio_error)"""
        
        if old_audio_init in content:
            content = content.replace(old_audio_init, new_audio_init)
            modifications += 1
            print("✅ Ajout des variables d'état audio")
    
    # 2. Ajouter les nouvelles méthodes (avant closeEvent)
    if "_on_playback_state_changed" not in content:
        close_event_pos = content.find("def closeEvent(self, event):")
        
        if close_event_pos != -1:
            new_methods = '''
    def _on_playback_state_changed(self, state):
        """Callback: changement d'état de lecture"""
        from PySide6.QtMultimedia import QMediaPlayer
        
        if state == QMediaPlayer.PlaybackState.PlayingState:
            # Audio en cours de lecture
            self.is_audio_playing = True
            self.video_player.set_speaking()
            self.interview_widget.set_audio_playing()
            
            logger = logging.getLogger(__name__)
            logger.info("🔊 Audio démarré - Avatar en mode speaking")
            
        elif state == QMediaPlayer.PlaybackState.StoppedState:
            # Audio arrêté
            self.is_audio_playing = False
            self.video_player.set_idle()
            
            # Si c'était une question, activer l'enregistrement
            if self.current_audio_type == 'question':
                self.interview_widget.enable_recording(True)
                self.statusBar().showMessage("✅ Question terminée - Vous pouvez répondre")
            
            logger = logging.getLogger(__name__)
            logger.info("⏹️ Audio terminé - Avatar en mode idle")
    
    def _on_audio_error(self, error):
        """Callback: erreur de lecture audio"""
        from PySide6.QtMultimedia import QMediaPlayer
        
        error_messages = {
            QMediaPlayer.Error.NoError: "Pas d'erreur",
            QMediaPlayer.Error.ResourceError: "Erreur de ressource audio",
            QMediaPlayer.Error.FormatError: "Format audio non supporté",
            QMediaPlayer.Error.NetworkError: "Erreur réseau",
            QMediaPlayer.Error.AccessDeniedError: "Accès refusé"
        }
        
        error_msg = error_messages.get(error, "Erreur inconnue")
        self.statusBar().showMessage(f"⚠️ Erreur audio: {error_msg}")
        
        # Fallback: permettre quand même de répondre
        if self.current_audio_type == 'question':
            self.interview_widget.enable_recording(True)
    
    '''
            
            content = content[:close_event_pos] + new_methods + content[close_event_pos:]
            modifications += 2
            print("✅ Ajout de _on_playback_state_changed")
            print("✅ Ajout de _on_audio_error")
    
    # 3. Modifier _play_question_audio
    if "audio_type: str = 'question'" not in content:
        old_play = '''def _play_question_audio(self, audio_url: str):
        """Jouer l'audio d'une question"""
        try:
            full_url = f"{settings.BACKEND_URL}{audio_url}"
            self.audio_player.setSource(QUrl(full_url))
            self.audio_player.play()'''
        
        new_play = '''def _play_question_audio(self, audio_url: str, audio_type: str = 'question'):
        """
        Jouer l'audio avec suivi du type
        
        Args:
            audio_url: URL de l'audio
            audio_type: Type d'audio ('question', 'welcome', 'complete')
        """
        try:
            self.current_audio_type = audio_type
            
            full_url = f"{settings.BACKEND_URL}{audio_url}"
            self.audio_player.setSource(QUrl(full_url))
            self.audio_player.play()
            
            # Désactiver l'enregistrement pendant la lecture
            if audio_type == 'question':
                self.interview_widget.enable_recording(False)'''
        
        if old_play in content:
            content = content.replace(old_play, new_play)
            modifications += 1
            print("✅ Modification de _play_question_audio")
    
    # Sauvegarder
    if modifications > 0:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"\n✅ {modifications} modification(s) appliquée(s)")
        return True
    else:
        print("\n⚠️ Aucune modification nécessaire (déjà à jour)")
        return True


def patch_interview_widget():
    """Patcher interview_widget.py"""
    
    print("\n" + "="*70)
    print("📝 Modification de interview_widget.py")
    print("="*70)
    
    file_path = UI_DIR / "interview_widget.py"
    
    if not file_path.exists():
        print(f"❌ Fichier non trouvé: {file_path}")
        return False
    
    # Backup
    backup_file(file_path)
    
    # Lire le contenu
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    modifications = 0
    
    # 1. Ajouter l'indicateur d'ondes audio
    if "self.audio_wave" not in content:
        # Trouver où insérer (après self.audio_status)
        insert_pos = content.find("card_layout.addWidget(self.audio_status)")
        
        if insert_pos != -1:
            # Trouver la fin de la ligne
            insert_pos = content.find("\n", insert_pos) + 1
            
            wave_code = '''
        # Indicateur de volume audio (animation)
        self.audio_wave = QLabel("▁▂▃▄▅▆▇█")
        self.audio_wave.setFont(QFont(StarkTheme.FONT_FAMILY_MONO, 14))
        self.audio_wave.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.audio_wave.setStyleSheet(f"""
            color: {StarkTheme.ORANGE_ACCENT};
            background: transparent;
            letter-spacing: 2px;
        """)
        self.audio_wave.setVisible(False)  # Caché par défaut
        card_layout.addWidget(self.audio_wave)
        
        # Timer pour animer les ondes
        self.wave_timer = QTimer()
        self.wave_timer.timeout.connect(self._animate_wave)
        self.wave_index = 0
'''
            
            content = content[:insert_pos] + wave_code + content[insert_pos:]
            modifications += 1
            print("✅ Ajout de l'indicateur d'ondes audio")
    
    # 2. Ajouter la méthode _animate_wave (avant set_audio_playing)
    if "_animate_wave" not in content:
        set_audio_pos = content.find("def set_audio_playing(self):")
        
        if set_audio_pos != -1:
            animate_code = '''
    def _animate_wave(self):
        """Animer l'indicateur d'ondes audio"""
        waves = [
            "▁▂▃▄▅▆▇█",
            "█▁▂▃▄▅▆▇",
            "▇█▁▂▃▄▅▆",
            "▆▇█▁▂▃▄▅",
            "▅▆▇█▁▂▃▄",
            "▄▅▆▇█▁▂▃",
            "▃▄▅▆▇█▁▂",
            "▂▃▄▅▆▇█▁"
        ]
        
        self.wave_index = (self.wave_index + 1) % len(waves)
        self.audio_wave.setText(waves[self.wave_index])
    
    '''
            
            content = content[:set_audio_pos] + animate_code + content[set_audio_pos:]
            modifications += 1
            print("✅ Ajout de _animate_wave")
    
    # 3. Modifier set_audio_playing pour ajouter l'animation
    if "self.wave_timer.start(150)" not in content:
        old_set_audio = '''        self.audio_status.setStyleSheet(f"""
            color: {StarkTheme.ORANGE_ACCENT};
            background: {StarkTheme.ORANGE_LIGHT};
            padding: {StarkTheme.SPACING_MD};
            border-radius: {StarkTheme.RADIUS_MEDIUM};
            font-weight: bold;
        """)'''
        
        new_set_audio = '''        self.audio_status.setStyleSheet(f"""
            color: {StarkTheme.ORANGE_ACCENT};
            background: {StarkTheme.ORANGE_LIGHT};
            padding: {StarkTheme.SPACING_MD};
            border-radius: {StarkTheme.RADIUS_MEDIUM};
            font-weight: bold;
        """)
        
        # Afficher et animer les ondes
        self.audio_wave.setVisible(True)
        self.wave_timer.start(150)  # Animation toutes les 150ms'''
        
        if old_set_audio in content:
            content = content.replace(old_set_audio, new_set_audio)
            modifications += 1
            print("✅ Modification de set_audio_playing")
    
    # 4. Modifier set_ready_to_answer pour arrêter l'animation
    if "self.wave_timer.stop()" not in content:
        # Chercher la fin de set_ready_to_answer
        ready_method_start = content.find("def set_ready_to_answer(self):")
        if ready_method_start != -1:
            # Trouver la fin de la méthode (avant la prochaine def ou enable_recording)
            next_def = content.find("\n    def ", ready_method_start + 1)
            
            if next_def != -1:
                # Insérer avant la prochaine méthode
                stop_wave_code = '''
        
        # Cacher les ondes
        self.audio_wave.setVisible(False)
        self.wave_timer.stop()
    '''
                
                content = content[:next_def] + stop_wave_code + content[next_def:]
                modifications += 1
                print("✅ Modification de set_ready_to_answer")
    
    # Ajouter import QTimer si nécessaire
    if "from PySide6.QtCore import" in content and "QTimer" not in content:
        content = content.replace(
            "from PySide6.QtCore import Qt, Signal",
            "from PySide6.QtCore import Qt, Signal, QTimer"
        )
        print("✅ Ajout de l'import QTimer")
    
    # Sauvegarder
    if modifications > 0:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"\n✅ {modifications} modification(s) appliquée(s)")
        return True
    else:
        print("\n⚠️ Aucune modification nécessaire (déjà à jour)")
        return True


def main():
    """Point d'entrée principal"""
    
    print("\n" + "="*70)
    print("🚀 INSTALLATION DES AMÉLIORATIONS AVATAR + TTS")
    print("="*70)
    print("\nCe script va modifier automatiquement:")
    print("  • client/ui/main_window.py")
    print("  • client/ui/interview_widget.py")
    print("\nDes backups seront créés automatiquement.")
    
    input("\n⏸️  Appuyez sur Entrée pour continuer ou Ctrl+C pour annuler...")
    
    # Vérifier les fichiers
    if not CLIENT_DIR.exists():
        print(f"\n❌ Dossier client non trouvé: {CLIENT_DIR}")
        return False
    
    if not UI_DIR.exists():
        print(f"\n❌ Dossier ui non trouvé: {UI_DIR}")
        return False
    
    # Appliquer les patches
    success = True
    
    success &= patch_main_window()
    success &= patch_interview_widget()
    
    # Résumé
    print("\n" + "="*70)
    
    if success:
        print("✅ INSTALLATION TERMINÉE AVEC SUCCÈS!")
        print("="*70)
        print("\nProchaines étapes:")
        print("  1. Testez: python test_avatar_sync.py")
        print("  2. Lancez le backend: python backend/main.py")
        print("  3. Lancez le client: python client/main.py")
        print("\nVous devriez maintenant voir:")
        print("  • Avatar synchronisé avec l'audio")
        print("  • Ondes audio animées pendant la lecture")
        print("  • Messages dans les logs")
    else:
        print("⚠️ INSTALLATION INCOMPLÈTE")
        print("="*70)
        print("\nCertains fichiers n'ont pas pu être modifiés.")
        print("Consultez le guide: GUIDE_INTEGRATION_AVATAR_TTS.md")
    
    return success


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️ Installation annulée par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
