#!/usr/bin/env python3
"""
🔧 Script de correction - Ajouter les méthodes manquantes
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
CLIENT_DIR = PROJECT_ROOT / "client"
UI_DIR = CLIENT_DIR / "ui"

def fix_main_window():
    """Ajouter les méthodes manquantes à main_window.py"""
    
    print("\n" + "="*70)
    print("🔧 CORRECTION DE main_window.py")
    print("="*70)
    
    file_path = UI_DIR / "main_window.py"
    
    if not file_path.exists():
        print(f"❌ Fichier non trouvé: {file_path}")
        return False
    
    # Lire le contenu
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Vérifier si les méthodes existent déjà
    if "_on_playback_state_changed" in content:
        print("✅ Les méthodes existent déjà")
        return True
    
    # Trouver où insérer (juste avant closeEvent)
    close_event_pos = content.find("    def closeEvent(self, event):")
    
    if close_event_pos == -1:
        print("❌ Impossible de trouver closeEvent")
        return False
    
    # Code des méthodes à ajouter
    new_methods = '''
    def _on_playback_state_changed(self, state):
        """Callback: changement d'état de lecture"""
        from PySide6.QtMultimedia import QMediaPlayer
        
        if state == QMediaPlayer.PlaybackState.PlayingState:
            # Audio en cours de lecture
            self.is_audio_playing = True
            self.video_player.set_speaking()
            self.interview_widget.set_audio_playing()
            
            import logging
            logger = logging.getLogger(__name__)
            logger.info("🔊 Audio démarré - Avatar en mode speaking")
            
        elif state == QMediaPlayer.PlaybackState.StoppedState:
            # Audio arrêté
            self.is_audio_playing = False
            self.video_player.set_idle()
            
            # Si c'était une question, activer l'enregistrement
            if hasattr(self, 'current_audio_type') and self.current_audio_type == 'question':
                self.interview_widget.enable_recording(True)
                self.statusBar().showMessage("✅ Question terminée - Vous pouvez répondre")
            
            import logging
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
        if hasattr(self, 'current_audio_type') and self.current_audio_type == 'question':
            self.interview_widget.enable_recording(True)
    
    '''
    
    # Insérer les méthodes
    content = content[:close_event_pos] + new_methods + content[close_event_pos:]
    
    # Sauvegarder
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Méthodes ajoutées avec succès!")
    print("   • _on_playback_state_changed")
    print("   • _on_audio_error")
    
    return True


def fix_interview_widget():
    """Ajouter les méthodes manquantes à interview_widget.py"""
    
    print("\n" + "="*70)
    print("🔧 CORRECTION DE interview_widget.py")
    print("="*70)
    
    file_path = UI_DIR / "interview_widget.py"
    
    if not file_path.exists():
        print(f"❌ Fichier non trouvé: {file_path}")
        return False
    
    # Lire le contenu
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Vérifier si la méthode existe déjà
    if "_animate_wave" in content:
        print("✅ La méthode _animate_wave existe déjà")
        return True
    
    # Trouver où insérer (juste avant update_question)
    update_question_pos = content.find("    def update_question(self, progress: dict):")
    
    if update_question_pos == -1:
        print("❌ Impossible de trouver update_question")
        return False
    
    # Code de la méthode à ajouter
    animate_method = '''
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
    
    # Insérer la méthode
    content = content[:update_question_pos] + animate_method + content[update_question_pos:]
    
    # Sauvegarder
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Méthode _animate_wave ajoutée avec succès!")
    
    return True


def main():
    """Point d'entrée principal"""
    
    print("\n" + "="*70)
    print("🔧 CORRECTION DES MÉTHODES MANQUANTES")
    print("="*70)
    print("\nCe script va ajouter les méthodes manquantes:")
    print("  • _on_playback_state_changed dans main_window.py")
    print("  • _on_audio_error dans main_window.py")
    print("  • _animate_wave dans interview_widget.py")
    
    input("\n⏸️  Appuyez sur Entrée pour continuer...")
    
    # Vérifier les dossiers
    if not UI_DIR.exists():
        print(f"\n❌ Dossier ui non trouvé: {UI_DIR}")
        return False
    
    # Appliquer les corrections
    success = True
    
    success &= fix_main_window()
    success &= fix_interview_widget()
    
    # Résumé
    print("\n" + "="*70)
    
    if success:
        print("✅ CORRECTION TERMINÉE AVEC SUCCÈS!")
        print("="*70)
        print("\nMaintenant vous pouvez:")
        print("  1. Tester: python -m client.main")
        print("  2. Le client devrait démarrer sans erreur")
    else:
        print("⚠️ CORRECTION INCOMPLÈTE")
        print("="*70)
        print("\nVérifiez les erreurs ci-dessus")
    
    return success


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️ Correction annulée")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
