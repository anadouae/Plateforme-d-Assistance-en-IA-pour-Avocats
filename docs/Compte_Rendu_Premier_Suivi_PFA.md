# Compte rendu — Premier suivi PFA

**Projet :** Sanad — Plateforme d’Assistance en Intelligence Artificielle pour Avocats  
**Étudiante :** Douae El Assal  
**Établissement :** ENSA Tétouan  
**Entreprise d’accueil :** WebVoice  
**Type de réunion :** Premier suivi PFA — encadrant école  
**Date :** juillet 2026  

---

## 1. Objet de la réunion

Point d’avancement sur le projet Sanad : cadrage de l’objectif, retours sur la présentation, et orientations fonctionnelles pour la suite.

---

## 2. Objectif du projet (clarifié)

L’encadrant a **confirmé l’objectif essentiel** de Sanad :

> **La transcription de la voix de l’avocat vers un texte de plaidoirie exploitable**  
> (*voice → text / plaidoirie*).

Les autres modules (dossiers, documents, planning, équipe…) restent utiles, mais le **cœur du PFA** est ce parcours plaidoirie.

---

## 3. Points abordés et retours

### 3.1 Gestion de cabinet
La ** de cabinet (comptes, dossiers, organisation du cabinet) a été reconnue comme un **point important**, déjà engagé / en cours dans la réalisation de l’application. Elle doit continuer à être consolidée pendant le développement.

### 3.2 Transcription vocale (dépendance technique)
Questions posées en début de réunion :
- Comment la voix de l’avocat est-elle transcrite ?
- L’outil est-il gratuit ou payant ?
- Quelle est la **dépendance** vis-à-vis de cet outil ?
- Que se passe-t-il si l’outil disparaît ou devient indisponible ?

→ L’encadrant insiste sur la nécessité d’une **solution robuste** (pas une dépendance unique fragile).

### 3.3 LLM / synthèse de documents
Même logique pour les modèles de langage utilisés (correction, synthèse, etc.) :
- Une intégration d’un LLM payant par l’entreprise est envisageable,  
- mais elle reste **risquée** si le fournisseur disparaît ou coupe l’accès.  
→ La plateforme doit pouvoir **continuer à fonctionner** (mode dégradé / alternative).

### 3.4 Synchronisation agenda ↔ affaires
Il a été souligné que **lier le planning (agenda) aux dossiers** rendrait l’application plus pertinente et intéressante (audiences, délais, préparation de plaidoirie rattachés à l’affaire).

### 3.5 Classement des dossiers par domaine + recherche
Proposition : permettre à l’avocat de **classer les dossiers par domaine** (ex. civil, pénal, commercial…) et de **rechercher / filtrer** par domaine.  
Justification évoquée : les plaidoiries se **ressemblent souvent par domaine** ; un classement et une recherche adaptés facilitent la réutilisation et le travail quotidien.

### 3.6 Tendance marché (contexte)
Mention d’une tendance actuelle dans le domaine LegalTech : analyse IA de l’ensemble des pièces d’une affaire pour estimer l’intérêt du dossier, éventuellement générer des éléments de plaidoirie, ou donner une estimation (ex. prix / charge).  
→ Point de **veille / tendance**, à garder en tête sans sortir du cœur du PFA (plaidoirie vocale).

### 3.7 Benchmarking
Conseil méthodologique : présenter le benchmarking sous forme de **tableau avec critères cochables** (OK / Non OK) pour comparer clairement Sanad aux solutions existantes.

### 3.8 Présentation (forme)
La présentation a été jugée un peu **redondante** (informations répétées).  
→ Retour de forme pour les prochaines livraisons ; à alléger.

---

## 4. Décisions / orientations retenues

| Priorité | Orientation |
|----------|-------------|
| 1 | Garder le **cœur produit** = voix → plaidoirie (texte corrigé / document) |
| 2 | Traiter sérieusement les **dépendances** (STT et LLM) : alternatives / mode dégradé |
| 3 | Continuer / consolider la **gestion de cabinet** |
| 4 | Améliorer **agenda ↔ dossiers** |
| 5 | Ajouter **domaine + recherche/filtre** sur les dossiers |
| 6 | Refondre le **benchmark** en grille OK / Non OK |
| 7 | Alléger les prochaines présentations (moins de répétitions) |

---

## 5. Suite à donner

- Intégrer les retours dans la feuille de route jusqu’au prochain suivi  
- Préparer des réponses techniques claires sur STT et LLM (voir note jointe *Solutions & risques*)  
- Mettre à jour maquettes / exigences si besoin (domaine, sync agenda)  
- Préparer une démo centrée sur le parcours plaidoirie  

---

## 6. Conclusion

Le premier suivi a permis de **recentrer l’objectif** sur la plaidoirie vocale, et d’identifier des axes d’amélioration concrets : robustesse des outils IA, synchronisation agenda–dossiers, classement par domaine, et clarté du benchmarking. La gestion de cabinet reste un pilier à consolider.

---

*Compte rendu — Premier suivi PFA · Sanad · Douae El Assal · ENSA Tétouan · WebVoice*
