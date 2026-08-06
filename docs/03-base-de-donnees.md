# Sanad — Description de la base de données

**SGBD :** PostgreSQL 16  
**Principe :** multi-tenant (chaque cabinet est isolé via `cabinet_id`)  
**Fichiers binaires :** stockés dans **MinIO** (pas en BLOB en base)  
**Auteur :** Douae El Assal · PFA · ENSA Tétouan · WebVoice

---

## 1. À quoi sert la base ?

La base PostgreSQL stocke **toutes les données métier** de Sanad :

- les cabinets et leurs utilisateurs  
- les dossiers (affaires)  
- les métadonnées des documents / plaidoiries archivées  
- le planning (agenda, tâches, notes)  
- la sécurité (jetons e-mail, journal d’audit)  

Le **contenu des fichiers** (PDF, images, HTML de plaidoirie) est dans **MinIO** ; la base ne garde que le chemin (`storage_path`) et le texte extrait.

```
cabinets ──< users
cabinets ──< cases ──< documents
                │──< agenda_events
                │──< case_tasks
                │──< case_notes
users ──< email_tokens
audit_logs (traçabilité)
```

---

## 2. Table `cabinets`

### Utilité
Représente un **cabinet d’avocats** (le « tenant »).  
Tout le reste (users, dossiers, docs) appartient à un cabinet. Sans cette table, pas d’isolation multi-cabinets.

| Colonne | Signification |
|---------|----------------|
| `id` | Identifiant unique du cabinet (UUID) |
| `name` | Nom du cabinet (ex. « Cabinet Démo Atlas ») |
| `city` | Ville du cabinet |
| `address` | Adresse postale |
| `barreau` | Barreau d’appartenance |
| `ice` | Identifiant fiscal ICE (optionnel) |
| `ai_custom_prompt` | Instructions IA éventuelles propres au cabinet (config) |
| `status` | État du cabinet : `pending` (en attente d’approbation), `active`, `suspended` |
| `created_at` | Date de création du cabinet |

---

## 3. Table `users`

### Utilité
Stocke les **comptes** (avocat, assistant, admin cabinet, admin plateforme).  
Chaque utilisateur est rattaché à **un seul** cabinet (`cabinet_id`).

| Colonne | Signification |
|---------|----------------|
| `id` | Identifiant unique de l’utilisateur |
| `email` | Adresse e-mail de connexion (**unique**) |
| `hashed_password` | Mot de passe **hashé** (jamais en clair) |
| `full_name` | Nom affiché (ex. « Me Douae El Assal ») |
| `phone` | Téléphone (optionnel) |
| `role` | Rôle : `avocat`, `assistant_juridique`, `admin_cabinet`, `admin_webvoice` |
| `is_active` | Compte autorisé à se connecter (`true` / `false`) |
| `is_verified` | E-mail vérifié (`true` après clic sur le lien) |
| `failed_login_attempts` | Nombre d’échecs de connexion (anti-bruteforce) |
| `locked_until` | Date jusqu’à laquelle le compte est verrouillé (si trop d’échecs) |
| `google_id` | Identifiant Google si connexion OAuth |
| `totp_secret` | Secret pour l’authentification à 2 facteurs (TOTP) |
| `totp_enabled` | 2FA activée ou non |
| `cabinet_id` | **FK** → cabinet auquel appartient l’utilisateur |
| `created_at` | Date de création du compte |

---

## 4. Table `cases` (dossiers)

### Utilité
Représente une **affaire / dossier** du cabinet.  
C’est le conteneur central : on y rattache documents, plaidoiries archivées, événements, tâches, notes.

| Colonne | Signification |
|---------|----------------|
| `id` | Identifiant unique du dossier |
| `reference` | Référence visible (ex. `WV-2026-0001`), **unique** |
| `client_name` | Nom du client |
| `case_type` | Type d’affaire (civil, pénal, commercial…) |
| `status` | Statut : `En cours`, `Urgent`, `Clôturé` |
| `description` | Description libre du dossier |
| `tags` | Mots-clés / étiquettes (texte) |
| `cabinet_id` | **FK** → cabinet propriétaire |
| `responsible_id` | **FK** → utilisateur responsable (souvent l’avocat) |
| `opened_at` | Date d’ouverture du dossier |
| `updated_at` | Dernière modification |

---

## 5. Table `documents`

### Utilité
Métadonnées des **pièces** et des **plaidoiries classées** dans un dossier.  
Le fichier réel est dans MinIO ; ici on garde le lien, le type, le texte OCR, le statut de traitement.

| Colonne | Signification |
|---------|----------------|
| `id` | Identifiant unique du document |
| `filename` | Nom technique côté stockage |
| `original_name` | Nom du fichier vu par l’utilisateur (ex. `plaidoirie_….html`) |
| `mime_type` | Type MIME (`application/pdf`, `text/html`…) |
| `file_size` | Taille en octets |
| `storage_path` | Chemin MinIO (ex. `{cabinet_id}/{case_id}/{fichier}`) |
| `extracted_text` | Texte extrait (OCR / parsing) pour consultation / IA |
| `ocr_score` | Score de qualité OCR (0–100, optionnel) |
| `status` | Pipeline : `pending` → `processing` → `indexed` (ou `failed`) |
| `case_id` | **FK** → dossier auquel appartient le document |
| `cabinet_id` | **FK** → cabinet (isolation) |
| `uploaded_by` | **FK** → utilisateur qui a déposé le fichier |
| `created_at` | Date d’upload |

**Lien avec la plaidoirie :** quand l’avocat clique « Enregistrer dans un dossier », Sanad crée une ligne `documents` + un fichier dans MinIO.

---

## 6. Table `agenda_events`

### Utilité
Événements du **planning** : audiences, délais, rendez-vous, etc.  
Peuvent être liés à un dossier (`case_id` optionnel).

| Colonne | Signification |
|---------|----------------|
| `id` | Identifiant de l’événement |
| `cabinet_id` | **FK** → cabinet |
| `user_id` | **FK** → créateur |
| `case_id` | **FK** → dossier lié (optionnel) |
| `title` | Titre (ex. « Audience tribunal ») |
| `description` | Détails |
| `event_type` | Type : `audience`, `deadline`, `rdv`, `other` |
| `starts_at` | Date/heure de début |
| `ends_at` | Date/heure de fin (optionnel) |
| `meet_url` | Lien visioconférence (optionnel) |
| `created_at` | Date de création |

---

## 7. Table `case_tasks`

### Utilité
**Tâches** du cabinet / dossier (todo → doing → done), pour organiser le travail (préparation plaidoirie, pièces à récupérer…).

| Colonne | Signification |
|---------|----------------|
| `id` | Identifiant de la tâche |
| `cabinet_id` | **FK** → cabinet |
| `user_id` | **FK** → créateur / propriétaire |
| `case_id` | **FK** → dossier (optionnel) |
| `title` | Intitulé de la tâche |
| `description` | Détail |
| `status` | `todo`, `doing`, `done` |
| `due_at` | Date d’échéance (optionnel) |
| `created_at` | Création |
| `updated_at` | Dernière mise à jour |

---

## 8. Table `case_notes`

### Utilité
**Notes internes** (mémos) liées au cabinet ou à un dossier — séparées du chat IA.

| Colonne | Signification |
|---------|----------------|
| `id` | Identifiant de la note |
| `cabinet_id` | **FK** → cabinet |
| `user_id` | **FK** → auteur |
| `case_id` | **FK** → dossier (optionnel) |
| `title` | Titre de la note |
| `body` | Contenu texte |
| `created_at` | Création |
| `updated_at` | Modification |

---

## 9. Table `email_tokens`

### Utilité
Jetons sécurisés pour les actions par e-mail : **vérifier l’adresse**, **réinitialiser le mot de passe**, **accepter une invitation** d’équipe.  
On stocke un **hash** du jeton, jamais le jeton brut.

| Colonne | Signification |
|---------|----------------|
| `id` | Identifiant |
| `user_id` | **FK** → utilisateur concerné |
| `token_hash` | Empreinte du jeton (**unique**) |
| `token_type` | `verify_email`, `reset_password`, `team_invite` |
| `expires_at` | Date d’expiration |
| `used_at` | Date d’utilisation (null si pas encore utilisé) |
| `created_at` | Création |

---

## 10. Table `audit_logs`

### Utilité
**Journal de traçabilité** : qui a fait quoi, quand, depuis quelle IP.  
Utile pour l’admin plateforme et la sécurité. Pas de FK strictes (on garde l’historique même si un user est modifié).

| Colonne | Signification |
|---------|----------------|
| `id` | Identifiant du log |
| `user_id` | Utilisateur auteur de l’action (peut être null) |
| `cabinet_id` | Cabinet concerné (peut être null) |
| `action` | Code d’action (ex. `auth.login`, `document.upload`) |
| `ip_address` | Adresse IP |
| `details` | Détails complémentaires (texte / JSON) |
| `created_at` | Horodatage |

---

## 11. Ce qui n’est PAS dans PostgreSQL

| Stockage | Contenu |
|----------|---------|
| **MinIO** | Fichiers PDF, images, plaidoiries HTML/DOC… |
| **Redis** | Files Celery, cache court |
| **ChromaDB** | Vecteurs pour recherche sémantique |
| **Ollama / LLM** | Inférence IA (pas de données métier persistées ici) |

---

## 12. Récapitulatif — utilité en une ligne (aligné CDC plaidoirie)

| Table | Utilité |
|-------|---------|
| `cabinets` | Isoler chaque cabinet (tenant) |
| `users` | Comptes et rôles (avocat / assistant / admin) |
| `cases` | Affaires / dossiers |
| `documents` | Pièces + plaidoiries archivées (métadonnées) |
| `agenda_events` | Planning (audiences, délais, RDV) |
| `case_tasks` | Tâches à faire |
| `case_notes` | Notes internes |
| `email_tokens` | Liens e-mail sécurisés |
| `audit_logs` | Traçabilité sécurité |

> Hors périmètre CDC : `chat_sessions` / `chat_messages` (retirées).

---

*Sanad · Document base de données · PFA · ENSA Tétouan · WebVoice · Douae El Assal*
