# Comprendre Sanad pour l’oral — explication simple et complète

Lis ce document **à voix haute** une fois. Ensuite tu pourras expliquer aux professeurs sans paniquer.

---

## 0. L’idée en une phrase

**Sanad n’est pas “ChatGPT”.**  
C’est une **usine en plusieurs machines** :

1. Une machine qui **écoute** (Whisper) → transforme l’audio en texte  
2. Une machine qui **écrit mieux / structure** (Ollama ou cloud) → corrige et met en forme  
3. Une application web qui **affiche** et **sauve** dans le cabinet (dossiers, Word, PDF)

Si une machine IA tombe, l’avocat peut **encore taper** et **exporterer**. C’est ça, la “résilience”.

---

## 1. Les “fournisseurs” — c’est quoi ?

Un **fournisseur** = un service qui fait un travail IA pour toi.

| Fournisseur | Type | Ce qu’il fait chez Sanad |
|-------------|------|---------------------------|
| **Whisper** (local) | STT (speech-to-text) | Audio → texte |
| **Ollama** (local) | LLM (grand modèle de langue) | Corrige / structure / synthétise |
| **Groq / Kimi / Mistral cloud** | LLM cloud (optionnel) | Secours si Ollama est lent ou down |
| **Chrome Web Speech** | STT navigateur | Secours micro si Whisper down |

**Phrase pour le prof :**  
> « On a plusieurs fournisseurs derrière la même interface. Si l’un tombe, on bascule ou on continue sans IA. »

---

## 2. Whisper local — comment on extrait le texte de l’audio

### 2.1 Analogie
Whisper = un **secrétaire qui écoute un enregistrement** et écrit ce qu’il entend.  
Il ne “réfléchit” pas au droit. Il **transcrit**.

### 2.2 Où il tourne
- Dans le **conteneur backend** Docker (pas dans le navigateur)
- Bibliothèque : **faster-whisper** (implémentation rapide d’OpenAI Whisper)
- Modèle : souvent `small`, sur **CPU** (donc un peu lent, mais gratuit / local)

### 2.3 Le parcours exact (micro)

```
Avocat parle au micro
    ↓
Le navigateur ENREGISTRE l’audio (fichier webm)
    ↓
Sanad envoie ce fichier au backend : POST /api/dictation/transcribe
    ↓
faster-whisper charge le modèle (une fois) et écoute le fichier
    ↓
Il sort du TEXTE (arabe)
    ↓
On “répare” un peu l’arabe (lettre ة, mots juridiques)
    ↓
Le texte apparaît dans la zone de dictée
```

### 2.4 Le parcours fichier audio (mp3 / wav…)
Exactement la même API.  
Différence : l’audio vient d’un **upload**, pas du micro.

### 2.5 Pourquoi “arabe forcé” ?
Si on laisse “auto”, Whisper peut se tromper et sortir du français.  
Pour les avocats marocains, on force `language="ar"` + un **prompt initial** avec des mots juridiques arabes (محكمة، مرافعة، نفقة…).

### 2.6 Longues dictées
Un gros fichier d’un coup = long + risque de timeout.  
Donc le frontend coupe ~toutes les **55 secondes**, envoie chaque morceau, et **ajoute** le texte progressivement.

### 2.7 Ce que Whisper N’EST PAS
- Ce n’est **pas** Ollama  
- Ce n’est **pas** la correction juridique  
- Ce n’est **pas** la synthèse de PDF  

**Phrase orale :**  
> « Whisper transforme la voix en texte brut. Ensuite seulement, un LLM peut corriger la forme. »

---

## 3. Ollama — c’est quoi ? À quoi ça sert ?

### 3.1 Analogie
Ollama = une **application sur le serveur** qui fait tourner des modèles de langue **localement** (comme avoir un petit ChatGPT chez soi, sans envoyer les données au cloud si on veut).

### 3.2 Ce qu’Ollama fait chez Sanad
Après la transcription, quand tu cliques **Corriger** ou **Générer le document** ou **Synthèse** :

```
Texte brut (ou texte du PDF)
    ↓
Backend envoie une requête à Ollama (http://ollama:11434)
    ↓
Le modèle (ex. mistral / sanad-legal) répond
    ↓
Sanad affiche le texte corrigé / la plaidoirie / la synthèse
```

### 3.3 Différence Whisper vs Ollama (À APPRENDRE PAR CŒUR)

| | Whisper | Ollama |
|--|---------|--------|
| Entrée | **Audio** | **Texte** |
| Sortie | Texte brut | Texte amélioré / structuré |
| Rôle | Écouter | Comprendre / reformuler |
| Quand | Dictée / fichier audio | Corriger, composer, synthétiser |

Si le prof demande « c’est la même IA ? » → **Non. Deux outils différents.**

---

## 4. Les “fournisseurs” LLM — comment ça s’enchaîne

Ordre typique (simplifié) :

1. Essayer **Ollama local** (rapide, privé, gratuit une fois installé)  
2. Si échec / timeout → essayer un **cloud** (Groq, Kimi…) si clé API présente  
3. Si tout échoue → **mode dégradé** : on garde le texte brut, l’avocat édite et exporte quand même

**Phrase :**  
> « L’IA est un accélérateur. Sans elle, le cabinet n’est pas bloqué. »

---

## 5. Synthèse d’une pièce (PDF) — ce n’est pas Whisper

```
Avocat uploade un PDF
    ↓
OCR / extraction de texte (Tesseract, etc.)  ← ça lit les pixels / le PDF
    ↓
Le TEXTE est envoyé à un LLM (Ollama ou cloud)
    ↓
Le LLM produit une synthèse structurée (parties, dates, risques…)
```

Whisper n’intervient **pas** ici (sauf si c’était un fichier audio).

---

## 6. Schéma mental complet (plaidoirie)

```
[Micro / Fichier audio]
         │
         ▼
   WHISPER (local)     ← STT : son → texte
         │
         ▼
   Texte brut arabe
         │
         ▼
   OLLAMA / LLM        ← polish + compose
         │
         ▼
   Document officiel → Word / PDF → Dossier
```

---

## 7. Docker — pourquoi on “publie des images”

Une **image Docker** = une “boîte déjà préparée” avec le logiciel dedans.

| Image | Dedans | Rôle |
|-------|--------|------|
| `sanad-backend` | FastAPI + Whisper + OCR | API + transcription |
| `sanad-frontend` | Next.js | Ce que tu vois dans le navigateur |
| `sanad-celery` | Workers | Traitement jobs (OCR long) |
| `ollama` | Ollama | LLM local |
| `postgres` | Base de données | Stocke users, dossiers… |

**Publier sur Docker Hub** = mettre ces boîtes sur Internet pour les télécharger ailleurs (VPS, autre PC) **sans tout reconstruire**.

**Phrase :**  
> « GitHub = le code source. Docker Hub = les binaires prêts à démarrer. »

---

## 8. Questions professeurs → réponses courtes

**Q : Comment vous transcrivez la voix ?**  
R : Enregistrement navigateur → API backend → **faster-whisper local**, langue arabe forcée.

**Q : C’est gratuit / payant ?**  
R : Whisper + Ollama locaux = pas de coût API obligatoire. Les cloud (Groq…) sont optionnels en secours.

**Q : Et si Whisper disparaît ?**  
R : Upload audio autre moteur, Chrome STT, ou saisie manuelle. Architecture interchangeable.

**Q : Ollama c’est quoi ?**  
R : Runtime local pour modèles LLM. Il corrige/structure le **texte**, il n’écoute pas l’audio.

**Q : Différence Whisper / Ollama ?**  
R : Whisper = oreilles. Ollama = plume (rédaction).

**Q : L’IA invente-t-elle le droit ?**  
R : Non pour la synthèse (extraction du document). Pour la plaidoirie, l’avocat **valide** toujours le texte final.

**Q : Pourquoi PostgreSQL pas SQLite ?**  
R : SaaS multi-cabinets, accès concurrents, Docker/prod. SQLite = fichier local de test, pas notre prod.

---

## 9. Mini-script de 45 secondes (si tu stresses)

> « Sanad transforme la voix de l’avocat en plaidoirie.  
> D’abord **Whisper local** convertit l’audio en texte arabe.  
> Ensuite un **LLM via Ollama** — ou un cloud en secours — corrige et structure le document.  
> Le résultat est exporté en Word/PDF et classé dans le dossier.  
> Si l’IA tombe, l’édition et l’export restent possibles.  
> Ce n’est pas une dépendance unique : c’est une chaîne avec des alternatives. »

---

## 10. Ce que TU dois retenir ce soir (3 phrases)

1. **Whisper** = audio → texte (local).  
2. **Ollama** = texte → texte mieux / structuré (local).  
3. **Cloud / Chrome / saisie** = secours pour ne jamais bloquer l’avocat.

---

*Document pédagogique oral · Douae El Assal · Sanad PFA*
