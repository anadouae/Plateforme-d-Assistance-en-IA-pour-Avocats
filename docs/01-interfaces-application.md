# Sanad — Document des interfaces

**Projet :** Plateforme d’Assistance en Intelligence Artificielle pour Avocats  
**Auteur :** Douae El Assal · ENSA Tétouan · WebVoice  
**Objectif :** décrire clairement les écrans utiles — sans redondance.

---

## 1. Vue d’ensemble

Sanad propose deux zones :


| Zone               | Accès           | Rôle                                                           |
| ------------------ | --------------- | -------------------------------------------------------------- |
| **Site public**    | Sans compte     | Présenter le produit, s’inscrire, se connecter                 |
| **Espace cabinet** | Compte connecté | Travailler : plaidoirie, dossiers, documents, planning, équipe |


**Navigation cabinet (barre latérale) :**  
Tableau de bord · Planning · Plaidoirie · Dossiers · Documents · Équipe (admin) · Paramètres  

> Contrats et Assistant IA (chat libre) sont hors périmètre CDC. Le cœur produit est la **plaidoirie**.

---

## 2. Site public


| Écran                 | Route                             | Ce qu’il permet                                                 |
| --------------------- | --------------------------------- | --------------------------------------------------------------- |
| Accueil               | `/`                               | Présenter Sanad, message produit, accès Connexion / Inscription |
| À propos              | `/about`                          | Contexte et positionnement                                      |
| Fonctionnalités       | `/fonctionnalites`                | Liste des briques métier                                        |
| Sécurité              | `/securite`                       | Engagements confiance / isolation                               |
| Mentions légales      | `/mentions-legales`               | Cadre légal                                                     |
| Confidentialité       | `/confidentialite`                | Traitement des données                                          |
| Connexion             | `/login`                          | Email / mot de passe (2FA optionnel, Google)                    |
| Inscription           | `/register`                       | Créer un cabinet + compte admin                                 |
| Mot de passe oublié   | `/forgot-password`                | Demande de réinitialisation                                     |
| Réinitialisation      | `/reset-password`                 | Nouveau mot de passe                                            |
| Vérification e-mail   | `/verify-email`, `/confirm-email` | Activation du compte                                            |
| Activation invitation | `/activate`                       | Premier mot de passe (invitation équipe)                        |


---

## 3. Espace cabinet — écrans métier

### 3.1 Tableau de bord — `/dashboard`

Point d’entrée après connexion.  

- Accueil personnalisé selon le rôle (avocat / assistant)  
- Accès rapide : **Nouvelle plaidoirie**, **Nouveau dossier** (selon rôle)  
- Aperçu des dossiers récents

### 3.2 Plaidoirie — `/redaction` *(cœur produit)*

**Avocat / admin cabinet**

1. **Dicter** (micro arabe) ou saisir le texte
2. **Transcrire & corriger** (IA) — texte éditable
3. **Générer** le document officiel
4. **Modifier / vérifier** titre et corps librement
5. **Exporter** : PDF / Imprimer ou **DOC**
6. **Classer** dans un dossier du cabinet

**Assistant juridique**

- Consulte les plaidoiries déjà archivées  
- Peut les visualiser et les exporter en **PDF** ou **DOC**  
- Ne dicte pas et ne modifie pas à la place de l’avocat

### 3.3 Dossiers — `/cases`, `/cases/new`, `/cases/[id]`


| Écran   | Contenu                                                                    |
| ------- | -------------------------------------------------------------------------- |
| Liste   | Recherche, filtres statut, ouverture / création                            |
| Nouveau | Client, type, statut, description                                          |
| Détail  | Infos dossier, documents liés, activité ; analyse IA réservée avocat/admin |


### 3.4 Documents — `/documents`, `/documents/[id]`

- Liste des pièces (fichier, dossier, OCR, statut)  
- Détail : aperçu texte extrait, téléchargement, ré-extraction  
- Synthèse / questions document : avocat & admin (pas l’assistant)  
- Suppression : non autorisée pour l’assistant

### 3.5 Planning — `/agenda`

Trois volets : **Agenda** (audiences, délais, RDV) · **Tâches** · **Notes**  
Les éléments peuvent être rattachés à un dossier (préparation de plaidoirie).

### 3.6 Équipe — `/team` *(admin cabinet uniquement)*

- Invitation de membres (e-mail / lien)  
- Attribution des rôles : avocat, assistant, admin  
- Liste des membres du cabinet

### 3.7 Paramètres — `/settings`

- Profil, mot de passe, 2FA  
- Infos cabinet (admin)

---

## 4. Droits par rôle (interfaces)


| Capacité                           | Avocat | Assistant     | Admin cabinet |
| ---------------------------------- | ------ | ------------- | ------------- |
| Dicter / modifier plaidoirie       | Oui    | Non           | Oui           |
| Export PDF / DOC plaidoirie        | Oui    | Oui (lecture) | Oui           |
| Classer plaidoirie dans un dossier | Oui    | Non           | Oui           |
| Gérer dossiers & pièces            | Oui    | Oui           | Oui           |
| Synthèse document                  | Oui    | Non           | Oui           |
| Gérer l’équipe                     | Non    | Non           | Oui           |


---

## 5. Admin plateforme — `/admin/`*

Réservé à `admin_webvoice` (WebVoice) :


| Écran         | Rôle                   |
| ------------- | ---------------------- |
| Tableau admin | Métriques globales     |
| Cabinets      | Activer / suspendre    |
| Logs          | Journal d’audit        |
| Benchmark     | Évaluation corpus / IA |


---

## 6. Principes UX retenus

- **Un cœur visible :** plaidoirie (dictée → correction → modification → PDF/DOC)  
- **Menu léger :** pas de modules secondaires en concurrence avec le cœur  
- **Rôles explicites :** l’assistant prépare ; l’avocat produit  
- **Multilingue :** FR / AR / EN sur l’interface

---

*Sanad · Document interfaces · PFA · ENSA Tétouan · WebVoice*