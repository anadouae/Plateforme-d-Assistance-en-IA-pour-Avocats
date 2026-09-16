# Prompt — Diagramme de cas d’utilisation UML LexHub (complet)

Copie-colle le bloc ci-dessous dans ChatGPT / Claude / Mermaid / PlantUML / Visual Paradigm.

---

## PROMPT À COPIER

```
Tu es un expert UML 2.5. Produis un DIAGRAMME DE CAS D’UTILISATION professionnel pour le système LexHub.

=== CONTEXTE PRODUIT ===
LexHub (https://lexhub.space) est un SaaS / système d’information de cabinet d’avocats au Maroc.
Cœur métier : dossier → pièces → plaidoirie (atelier en 5 étapes) → livrable Word (.docx).
L’IA (STT, OCR, LLM) est un SERVICE partagé, jamais le maître des faits.
Isolation multi-tenant stricte par cabinet (secret professionnel, loi 28-08).

=== FRONTIÈRE DU SYSTÈME ===
Nom du système (rectangle / package) : « LexHub »
À l’intérieur du système uniquement les cas d’utilisation.
À l’extérieur : tous les acteurs (principaux à gauche, secondaires à droite).

Ne PAS mettre comme cas d’utilisation métier :
- connexion / OTP / Turnstile (contrôles techniques d’accès)
- CRUD banal sans valeur métier LexHub

=== ACTEURS PRINCIPAUX (humains, initiants) ===
1) Avocat
   - Mène l’atelier de plaidoirie
   - Gère dossiers, pièces, planning
   - Valide / assigne / exporte
   - Ne gère PAS l’abonnement ni l’équipe

2) Assistant juridique
   - Consulte uniquement les plaidoiries déjà VALIDÉES ou FINALISÉES
   - Peut exporter Word sur ces plaidoiries
   - Ne dicte PAS, ne lance PAS la rédaction IA / synthèse / clé de barre

3) Admin cabinet
   - Hérite de TOUT le périmètre Avocat (généralisation UML : Admin cabinet → Avocat)
   - En plus : invitations équipe, abonnement, logo/charte, parrainage

4) Admin plateforme (WebVoice)
   - Supervise les cabinets (suspendre, plans globaux)
   - N’ouvre JAMAIS le contenu des dossiers / plaidoiries

=== ACTEURS SECONDAIRES (systèmes externes, support) ===
Place-les à droite du système :
5) Service STT / Whisper (OpenAI) — transcription audio fichier
6) Service LLM (OpenAI) — correction de forme / rédaction assistée
7) Service OCR cloud — extraction texte des pièces
8) Messagerie e-mail (SMTP / Resend) — OTP, invitations, notifications
9) Navigateur Web Speech API — dictée micro temps réel (acteur technique optionnel)

Règle : un acteur secondaire n’initie pas le cas ; il est appelé via <<include>> depuis un cas principal.

=== PACKAGES INTERNES (groupes de cas) ===
A) Atelier de plaidoirie
B) Espace cabinet
C) Collaboration & équipe
D) Facturation / abonnement
E) Supervision plateforme

=== CAS D’UTILISATION PRINCIPAUX (à dessiner) ===

[Package A — Atelier]
UC-A1  Gérer le dossier et les pièces (identité juridique, domaine, OCR)
UC-A2  Dicter au micro OU importer un fichier audio (WAV/MP3/OGG/M4A/WebM)
UC-A3  Corriger la forme (arabe fusḥā, surlignage, refus du non-sens)
UC-A4  Rédiger / composer la plaidoirie (ancrage dossier + pièces + dictée)
UC-A5  Clarifier les manques (questions / feuille de clarification — intégré à A3–A4)
UC-A6  Réviser la plaidoirie via chat (révision assistée)
UC-A7  Valider le brouillon (statut draft → validated)
UC-A8  Assigner un assistant (met en avant ; inclut validation si besoin)
UC-A9  Exporter le document officiel Word (.docx) (statut → finalized)

[Package B — Espace cabinet]
UC-B1  Consulter les plaidoiries validées / finalisées
UC-B2  Gérer le planning (audiences, délais, rappels)
UC-B3  Consulter le journal d’activité / notifications
UC-B4  Générer une fiche orale d’audience (clé de barre) — avocat / admin cabinet seulement
UC-B5  Synthèse / questions sur une pièce (OCR) — avocat / admin cabinet seulement

[Package C — Collaboration]
UC-C1  Inviter un membre par e-mail (avocat ou assistant)
UC-C2  Accepter une invitation / rejoindre le cabinet
UC-C3  Gérer les rôles de l’équipe

[Package D — Facturation]
UC-D1  Consulter le plan et les quotas / crédits
UC-D2  Gérer l’abonnement (changer de plan, essai)
UC-D3  Acheter un pack de crédits (abonné payant actif uniquement)
UC-D4  Gérer les sièges supplémentaires (plan Cabinet)
UC-D5  Utiliser le parrainage inter-cabinets

[Package E — Supervision]
UC-E1  Superviser / lister les cabinets
UC-E2  Suspendre ou réactiver un cabinet
UC-E3  Gérer les plans globaux / leads commerciaux Entreprise

=== RELATIONS ACTEUR ↔ CAS (associations) ===

Avocat → UC-A1, A2, A3, A4, A5, A6, A7, A8, A9, B2, B3, B4, B5

Assistant → UC-B1, A9 (export seulement sur validées), éventuellement dépôt de pièces limité
  (PAS A2–A6 rédaction IA, PAS B4/B5 IA lourde)

Admin cabinet → tous les cas de l’Avocat (via héritage)
  + UC-C1, C3, D1–D5

Admin plateforme → UC-E1, E2, E3 uniquement

=== RELATIONS ENTRE CAS ===

<<include>> (obligatoire / toujours) :
- UC-A2 include Service STT (si import fichier) OU Web Speech (si micro)
- UC-A3 include Service LLM (correction forme)
- UC-A4 include Service LLM (composition)
- UC-A8 include UC-A7 (assigner implique valider si brouillon)
- UC-A1 (pièces) include Service OCR (quand upload document)
- UC-C1 include Messagerie e-mail
- UC-A9 peut être lié à validation préalable (précondition : texte prêt)

<<extend>> (optionnel) :
- UC-A5 extend UC-A3 ou UC-A4 (clarification seulement s’il y a des manques)
- Turnstile : NE PAS en faire un cas ; noter en note hors diagramme « anti-abus login »

Généralisation :
- Admin cabinet ──▷ Avocat  (flèche blanche UML)

=== PRÉSENTATION GRAPHIQUE EXIGÉE ===
- Format paysage, lisible, style UML strict
- Acteurs principaux à GAUCHE, secondaires à DROITE
- Ellipse pour chaque cas, noms courts (max 4–5 mots)
- Packages A–E visibles dans le rectangle LexHub
- Légende :
  • trait plein = association acteur–cas
  • tirets <<include>> / <<extend>>
  • flèche blanche = généralisation
- Langue : FRANÇAIS
- Titre : « Diagramme de cas d’utilisation — LexHub (production) »
- Sous-titre : « SI cabinet avocats Maroc · lexhub.space »

=== SORTIE DEMANDÉE ===
1) D’abord le code Mermaid (flowchart ou C4 si besoin, mais privilégie un diagramme clair)
2) Puis le même modèle en PlantUML (@startuml … @enduml)
3) Puis un tableau récapitulatif :
   | Cas | Acteur(s) principal(aux) | Acteur(s) secondaire(s) | Include / Extend |

Ne rajoute pas de cas hors liste. Ne transforme pas LexHub en « chatbot IA ».
```

---

## Récap rapide (pour toi)

| Type | Qui |
|------|-----|
| **Principaux** | Avocat, Assistant, Admin cabinet, Admin plateforme |
| **Secondaires** | STT/Whisper, LLM, OCR, E-mail, (Web Speech) |
| **Système** | LexHub |
| **Cœur** | Atelier A1–A9 |
| **Héritage** | Admin cabinet → Avocat |
| **Include clés** | Assigner ⊃ Valider ; Audio ⊃ STT ; Rédiger/Corriger ⊃ LLM |

## Fichiers déjà dans le repo

- `docs/rapport-pfa/diagrams/uc-lexhub.mmd` — version courte Mermaid  
- `docs/rapport-pfa/diagrams/uc-lexhub.puml` — PlantUML  

Cette prompt est la version **détaillée** pour générer un diagramme plus complet (avec secondaires).
