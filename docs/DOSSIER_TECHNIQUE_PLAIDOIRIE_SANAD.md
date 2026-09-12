# Dossier technique — Plaidoirie Sanad (LexHub)

**Destinataire :** encadrant / revue technique  
**Produit :** Sanad — assistant de مرافعة pour avocats marocains  
**Principe validé :** dictée (brut) → mise en page structurée ; l’IA n’invente ni faits, ni articles, ni montants ; placeholder `……` si manque.

---

## Clarification « template »

Dans Sanad, le **template n’est plus une bibliothèque de modèles métier** (civil / famille / …).  
C’est un **canevas de mise en page** unique, aligné sur la pratique pédagogique de la plaidoirie :

`افتتاح → (الشكل) → الوقائع → المناقشة → لهذه الأسباب → خاتمة`

**Sources / appuis (pas un format BO unique) :**

1. Doctrine & pédagogie « فن المرافعة » — structure classique du discours judiciaire (ouverture, corps, conclusion / demandes).  
2. *Guide des techniques de plaidoirie* (méthode chronologique : préparation → organisation des moyens → prononcé) — ex. présentation MarocDroit.  
3. **قانون المسطرة المدنية** (Dahir 1.74.447) — logique du **مقال** : الوقائع + الوسائل + الطلبات (la plaidoirie reprend la même logique narrative).  
4. Cours marocains « إجراءات الدعوى » — contenu attendu du dossier (faits, moyens, demandes).  
5. Usage enseigné en formation avocat / barreaux : rubriques « أولاً في الشكل / ثانياً في الموضوع / لهذه الأسباب ».  
6. Loi profession avocat **28-08** (et évolutions) : l’avocat reste maître de la défense ; l’outil n’est qu’une aide à la rédaction.

> Formulation honnête pour l’oral : « Ce n’est pas un texte officiel unique au Bulletin Officiel ; c’est un **canevas de présentation** largement enseigné et utilisé, sous contrôle de l’avocat. »

---

## Livrable 1 — Workflow backend exact

### Stack réelle Sanad (pas théorique GPT-4 only)

| Étape | Techno Sanad |
|--------|----------------|
| Audio navigateur / mobile | `MediaRecorder` (WebM/Opus) |
| Aperçu live (optionnel) | Web Speech API (Chrome) — **aperçu seulement** |
| Transcription finale | **Whisper local** (`faster-whisper` / `whisper_stt.py`) sur le serveur |
| Nettoyage | `polish` + `arabic_text_fix` / lexicon |
| Structuration | LLM via `free_llm_router` (Mistral cloud free-tier, etc.) — **pas d’invention** |
| Persistance | PostgreSQL (`plaidoirie_drafts`) |
| Export | `python-docx` (.docx) + export HTML/PDF côté FE |

### Flux de données (étape par étape)

```
[Navigateur]
  MediaRecorder.start()
  → chunks audio
  → POST /api/dictation/transcribe  (multipart file + language=ar|fr)
[Backend]
  whisper_stt.transcribe_audio_bytes()
  → texte brut
[Navigateur]
  affiche تفريغ ; optionnel POST /api/dictation/polish
[Navigateur]
  POST /api/dictation/compose
  { text, doc_type: "plaidoirie", plaidoirie_type: "libre", language: "ar" }
[Backend]
  build_plaidoirie_system("libre")  → system prompt
  free_llm_router → TITLE / BODY / CHECKS
  parse + repair_arabic_stt
[Navigateur]
  Document éditable → export
  POST /api/plaidoirie-templates/drafts  (historique)
  GET/POST export Word : backend docx_export OU FE downloadOfficialArabicDoc
```

### Exemples d’API (réels)

```http
POST /api/dictation/transcribe
Authorization: Bearer <jwt>
Content-Type: multipart/form-data
file: dictation.webm
language: ar
```

```http
POST /api/dictation/compose
Authorization: Bearer <jwt>
Content-Type: application/json

{
  "text": "السيد الرئيس موكلي ... نلتمس ...",
  "doc_type": "plaidoirie",
  "plaidoirie_type": "libre",
  "polish_first": true,
  "language": "ar"
}
```

Réponse typique :

```json
{
  "title": "مرافعة في ملف …",
  "body": "السيد رئيس المحكمة المحترم،\n\nثانياً — في الوقائع:\n…",
  "checks": ["استكمال رقم الملف"],
  "provider": "mistral|ollama|none",
  "polished": "…"
}
```

---

## Livrable 2 — Prompt système (exclusif)

Fichier source de vérité : `backend/app/services/plaidoirie_prompt.py`  
(`PLAIDOIRIE_AGENT_SYSTEM`)

Extrait des règles **non négociables** :

- Interdiction d’inventer : فصول، مبالغ، أسماء، أرقام ملفات absents du source  
- Manque → `……` + ligne dans `CHECKS`  
- Autorisé seulement : titres de sections, formules d’ouverture/clôture, ponctuation, ordre des paragraphes  
- Sortie stricte : `TITLE` / `BODY` / `CHECKS`

Le prompt complet est versionné dans le dépôt (à coller tel quel pour la revue).

---

## Livrable 3 — Architecture UI des 5 écrans

**Framework :** **Next.js (App Router) + React** — déjà en production sur https://lexhub.space  
*(Flutter non utilisé pour ce parcours.)*

| # | Écran | Composant | Rôle |
|---|--------|-----------|------|
| 0 | إملاء | `plaidoirie-workspace.tsx` step 0 | Micro, VoiceOrb, caption live |
| 1 | تفريغ | step 1 | Texte éditable + تصحيح |
| 2 | إعدادات | step 2 | Dossier optionnel, priorité, **توليد الوثيقة** |
| 3 | وثيقة | step 3 + `document-workspace.tsx` | Édition titre/corps |
| 4 | تصدير | step 4 | Word / PDF / succès « جاهز للجلسة » |

Navigation : `PleaStepCarousel` + `goStep(i)`  
Entrée produit : `/redaction` → CTA « ابدأ الإملاء » → `/redaction/libre`  
Plus de grille de modèles métier.

---

## Livrable 4 — Schéma base de données (PostgreSQL)

Tables pertinentes (SQLAlchemy / Alembic) :

```sql
-- Utilisateurs (avocats / cabinet)
users (
  id UUID PK,
  email VARCHAR UNIQUE,
  hashed_password VARCHAR,
  full_name VARCHAR,
  full_name_ar VARCHAR NULL,
  role ENUM,              -- avocat | admin_cabinet | assistant | ...
  cabinet_id UUID FK → cabinets.id,
  is_active BOOLEAN,
  is_verified BOOLEAN,
  created_at TIMESTAMPTZ
);

cabinets (
  id UUID PK,
  name VARCHAR,
  name_ar VARCHAR NULL,
  logo_path VARCHAR NULL,
  ...
);

-- Dossiers (optionnels pour une مرافعة)
cases (
  id UUID PK,
  reference VARCHAR UNIQUE,
  client_name VARCHAR,
  case_type VARCHAR,
  status VARCHAR,
  cabinet_id UUID FK,
  responsible_id UUID FK → users.id,
  ...
);

-- Versions / traces de plaidoiries générées
plaidoirie_drafts (
  id UUID PK,
  cabinet_id UUID FK,
  user_id UUID FK,
  case_id UUID NULL FK,
  title VARCHAR,
  body TEXT,                 -- document final (version)
  template_id VARCHAR NULL,  -- 'libre'
  checks_json TEXT NULL,    -- checklist …… 
  created_at TIMESTAMPTZ,
  updated_at TIMESTAMPTZ
);

-- Documents classés dans un dossier (export sauvegardé)
documents (
  id UUID PK,
  case_id UUID FK,
  original_name VARCHAR,
  storage_path VARCHAR,
  status VARCHAR,
  extracted_text_preview TEXT NULL,
  ...
);
```

**Transcriptions brutes :** aujourd’hui tenues en session UI (`raw` / `polished`) puis fusionnées à la composition ; la trace durable est `plaidoirie_drafts` (et éventuellement `documents` si classé).  
Évolution possible : table `dictation_sessions(raw_text, polished_text, audio_path, created_at)`.

---

## Livrable 5 — Export technique

| Format | Bibliothèque | Emplacement |
|--------|--------------|-------------|
| **Word .docx** | **`python-docx`** | `backend/app/services/docx_export.py` — en-tête, RTL, logo cabinet, armoiries optionnelles |
| **PDF** | Export navigateur / HTML→PDF côté FE (`export-official-doc.ts`) | Impression qualité + téléchargement |
| **.doc legacy** | HTML Word-compatible (FE) | Compatibilité ancienne |

Exemple Python (déjà en prod) :

```python
from docx import Document
# build_plaidoirie_docx(title, body, cabinet_logo_bytes=..., ...)
```

Logo : upload cabinet (`cabinets.logo_path`) injecté à l’export.

---

## Feuille de route développeur (état)

| Item | Statut |
|------|--------|
| Dictée → Whisper local | ✅ |
| Live caption Chrome | ✅ |
| Compose + prompt anti-invention | ✅ |
| 5 écrans Next.js | ✅ |
| Entrée sans bibliothèque de modèles | ✅ (ce lot) |
| Historique drafts | ✅ |
| Export docx + PDF | ✅ |
| Table `dictation_sessions` dédiée | ⬜ optionnel |

---

## Phrase de synthèse pour l’encadrant

> Sanad implémente le flux validé (brut → mise en page). Le « template » est un **canevas formel marocain classique**, sourcé par la pédagogie de la plaidoirie et la logique procédurale (faits / moyens / demandes), **sans invention de contenu**. Stack : Next.js + FastAPI + Whisper local + LLM de structuration + PostgreSQL + python-docx.
