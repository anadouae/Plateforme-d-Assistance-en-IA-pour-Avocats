Fixtures de test Sanad
======================

sanad-test-document.pdf
  Petit PDF bilingue (FR/AR) avec parties, date, montant, clause.

sanad-test-audio.wav
  Dictée parlée (français, synthèse vocale Windows SAPI) pour Whisper.
  Contient approximativement :
  « Bonjour Sanad. Dossier test 2026. Société Atlas.
    Montant vingt-cinq mille dirhams. Clause de résiliation… »
  Taille attendue : > 200 KB (pas un silence de 4 s).

Régénérer l’audio (PowerShell Windows) :
  Add-Type -AssemblyName System.Speech
  $s = New-Object System.Speech.Synthesis.SpeechSynthesizer
  $s.SetOutputToWaveFile("backend\scripts\fixtures\sanad-test-audio.wav")
  $s.Speak("Bonjour Sanad. Dossier test deux mille vingt six. ...")
  $s.Dispose()

Upload depuis un dossier dans l’app, ou via :
  POST /api/documents/upload  (case_id + file)

Smoke E2E :
  python backend/scripts/smoke_e2e.py
