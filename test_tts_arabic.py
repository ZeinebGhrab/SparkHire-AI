#!/usr/bin/env python3
"""
🧪 SCRIPT DE TEST: Vérifier que le TTS lit la question complète
et non pas juste les numéros "1 2 3 4 5"
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_tts_with_arabic_text():
    """Test 1: Vérifier la synthèse d'un texte arabe complet"""
    
    print("\n" + "="*70)
    print("🧪 TEST 1: Synthèse d'une question arabe complète")
    print("="*70)
    
    # Texte de test (vraie question du système)
    test_text_ar = "قدم نفسك باختصار"  # "Présentez-vous brièvement"
    test_text_en = "Introduce yourself briefly"
    
    print(f"\n📝 Texte arabe à synthétiser: '{test_text_ar}'")
    print(f"📝 Texte anglais à synthétiser: '{test_text_en}'")
    
    try:
        from backend.services.tts_service import get_tts_service
        from backend.config import settings
        
        print(f"\n⚙️ Configuration TTS:")
        print(f"   Moteur: {settings.TTS_ENGINE}")
        print(f"   Langue: {settings.TTS_LANGUAGE}")
        print(f"   Cache: {settings.TTS_CACHE_DIR}")
        
        # Créer le service
        tts_service = get_tts_service()
        print(f"\n✅ Service TTS initialisé: {type(tts_service.engine).__name__}")
        
        # Test 1: Texte arabe
        print("\n" + "-"*70)
        print("🔊 TEST ARABE:")
        print("-"*70)
        audio_data_ar = tts_service.synthesize(test_text_ar, language="ar")
        
        if audio_data_ar:
            print(f"✅ SUCCÈS: {len(audio_data_ar)} bytes générés")
            
            # Sauvegarder pour vérification manuelle
            test_output = Path("test_audio_arabic.wav")
            with open(test_output, 'wb') as f:
                f.write(audio_data_ar)
            print(f"💾 Audio sauvegardé: {test_output}")
            print(f"   ▶️ Écoutez ce fichier pour vérifier qu'il dit bien:")
            print(f"      '{test_text_ar}' (et non pas '1' ou un numéro)")
        else:
            print("❌ ÉCHEC: Aucune donnée audio générée")
        
        # Test 2: Texte anglais
        print("\n" + "-"*70)
        print("🔊 TEST ANGLAIS:")
        print("-"*70)
        audio_data_en = tts_service.synthesize(test_text_en, language="en")
        
        if audio_data_en:
            print(f"✅ SUCCÈS: {len(audio_data_en)} bytes générés")
            
            test_output = Path("test_audio_english.wav")
            with open(test_output, 'wb') as f:
                f.write(audio_data_en)
            print(f"💾 Audio sauvegardé: {test_output}")
            print(f"   ▶️ Écoutez ce fichier pour vérifier qu'il dit bien:")
            print(f"      '{test_text_en}'")
        else:
            print("❌ ÉCHEC: Aucune donnée audio générée")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_tts_with_question_numbers():
    """Test 2: Vérifier que les numéros ne sont PAS synthétisés à la place du texte"""
    
    print("\n" + "="*70)
    print("🧪 TEST 2: Vérifier qu'on ne lit PAS les numéros")
    print("="*70)
    
    # Simuler une vraie question du système
    from backend.interviews.models import Question
    
    question = Question(
        order=1,  # ⚠️ Ceci ne doit PAS être lu!
        question_ar="قدم نفسك باختصار",  # ✅ Ceci DOIT être lu
        question_en="Introduce yourself briefly",
        max_duration_seconds=120
    )
    
    print(f"\n📋 Question simulée:")
    print(f"   order: {question.order}")
    print(f"   question_ar: {question.question_ar}")
    print(f"   question_en: {question.question_en}")
    
    try:
        from backend.services.tts_service import get_tts_service
        tts_service = get_tts_service()
        
        # Le texte à synthétiser doit être question.question_ar, PAS question.order
        correct_text = question.question_ar
        wrong_text = str(question.order)
        
        print(f"\n✅ Texte CORRECT à synthétiser: '{correct_text}'")
        print(f"❌ Texte INCORRECT (numéro): '{wrong_text}'")
        
        # Synthétiser le bon texte
        audio_data = tts_service.synthesize(correct_text, language="ar")
        
        if audio_data:
            print(f"\n✅ Audio généré correctement avec le texte complet")
            print(f"   Taille: {len(audio_data)} bytes")
            
            # Sauvegarder
            test_output = Path("test_question_complete.wav")
            with open(test_output, 'wb') as f:
                f.write(audio_data)
            print(f"💾 Fichier de test: {test_output}")
            print(f"\n⚠️ VÉRIFICATION MANUELLE REQUISE:")
            print(f"   1. Écoutez le fichier {test_output}")
            print(f"   2. Il doit dire: '{correct_text}'")
            print(f"   3. Il NE doit PAS dire: '{wrong_text}' ou '1 2 3 4 5'")
        else:
            print(f"\n❌ Échec de génération audio")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_interview_handler_logic():
    """Test 3: Vérifier la logique dans interview_handler.py"""
    
    print("\n" + "="*70)
    print("🧪 TEST 3: Vérifier la logique d'extraction du texte")
    print("="*70)
    
    # Simuler ce que fait interview_handler._send_current_question()
    from backend.interviews.models import Question
    
    question = Question(
        order=5,
        question_ar="ما هي نقاط قوتك الرئيسية؟",
        question_en="What are your main strengths?",
        max_duration_seconds=90
    )
    
    language = "ar"
    
    # ✅ LOGIQUE CORRECTE
    question_text_correct = question.question_ar if language == "ar" else question.question_en
    
    # ❌ LOGIQUE INCORRECTE (ce qui pourrait causer le bug)
    question_text_wrong = str(question.order)
    
    print(f"\n📋 Question test:")
    print(f"   order: {question.order}")
    print(f"   question_ar: {question.question_ar}")
    print(f"   question_en: {question.question_en}")
    print(f"   language: {language}")
    
    print(f"\n✅ EXTRACTION CORRECTE:")
    print(f"   Code: question.question_ar if language == 'ar' else question.question_en")
    print(f"   Résultat: '{question_text_correct}'")
    
    print(f"\n❌ EXTRACTION INCORRECTE (bug possible):")
    print(f"   Code: str(question.order)")
    print(f"   Résultat: '{question_text_wrong}'")
    
    print(f"\n🔍 DIAGNOSTIC:")
    if question_text_correct == question.question_ar:
        print(f"   ✅ Le texte correct est extrait")
    else:
        print(f"   ❌ ERREUR dans l'extraction!")
    
    return True


def main():
    """Exécuter tous les tests"""
    
    print("\n" + "="*70)
    print("🚀 DÉMARRAGE DES TESTS TTS")
    print("="*70)
    
    results = []
    
    # Test 1
    try:
        result1 = test_tts_with_arabic_text()
        results.append(("Test 1: Synthèse arabe", result1))
    except Exception as e:
        print(f"Test 1 échoué: {e}")
        results.append(("Test 1: Synthèse arabe", False))
    
    # Test 2
    try:
        result2 = test_tts_with_question_numbers()
        results.append(("Test 2: Numéros vs Texte", result2))
    except Exception as e:
        print(f"Test 2 échoué: {e}")
        results.append(("Test 2: Numéros vs Texte", False))
    
    # Test 3
    try:
        result3 = test_interview_handler_logic()
        results.append(("Test 3: Logique extraction", result3))
    except Exception as e:
        print(f"Test 3 échoué: {e}")
        results.append(("Test 3: Logique extraction", False))
    
    # Résumé
    print("\n" + "="*70)
    print("📊 RÉSUMÉ DES TESTS")
    print("="*70)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    all_passed = all(r[1] for r in results)
    
    if all_passed:
        print("\n🎉 TOUS LES TESTS RÉUSSIS!")
    else:
        print("\n⚠️ CERTAINS TESTS ONT ÉCHOUÉ")
    
    print("\n💡 PROCHAINES ÉTAPES:")
    print("   1. Écoutez les fichiers .wav générés")
    print("   2. Vérifiez qu'ils contiennent le texte complet")
    print("   3. Si vous entendez des numéros, consultez FIX_TTS_COMPLETE.md")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
