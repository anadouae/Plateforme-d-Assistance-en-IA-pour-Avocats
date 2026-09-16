# Diagrammes LexHub (PFA) — source de vérité

Tous les fichiers ici sont **ancrés sur le code production** (`lexhub.space`).
Ne pas réintroduire les anciens schémas de `docs/diagrammes/` (inscription PENDING, chat RAG autonome, etc.).

## Séquences (UML)

| Fichier | Flux réel |
|---------|-----------|
| `seq-register-otp.puml` (= `seq-otp.puml`) | `request-register-otp` → `verify-register-otp` → `register` → puis `login` |
| `seq-login-turnstile.puml` | `login` + Turnstile après 3 échecs + 2FA optionnel |
| `seq-dictation.puml` | Web Speech **ou** `/transcribe` → `/polish` → `/clarify` → `/compose` → `/revise` |
| `seq-validate-assign.puml` | `/drafts/{id}/validate` \| `/assign` → WS + e-mail → export docx/pdf → `finalized` |
| `seq-document-ocr.puml` | `/documents/upload` → MinIO → extraction → `extracted_text` |
| `seq-billing.puml` | plans / essai / packs → factures **amount > 0** uniquement |

## Autres

| Fichier | Contenu |
|---------|---------|
| `activity-plea.puml` | 5 étapes UI atelier |
| `state-plaidoirie.puml` | `draft` → `validated` → `finalized` |
| `class-lexhub.puml` / `er-lexhub.mmd` | extrait ER (`extracted_text`, pas `ocr_text`) |
| `uc-lexhub.puml` / `.mmd` | cas d'utilisation (export Word **et** PDF) |
| `deploy-lexhub.puml` | VPS Caddy + FE/BE/Celery + PG/Redis/MinIO + cloud |

## Rendu

- Aperçu : [PlantUML online](https://www.plantuml.com/plantuml) / VS Code PlantUML / mermaid.live pour `.mmd`
- Le rapport LaTeX reprend les flux en **TikZ** (chapitre conception) ; ces `.puml` restent la référence éditable.
