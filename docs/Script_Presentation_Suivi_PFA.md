# Script oral — Premier suivi PFA Sanad

**Fichier PPT :** `Sanad_Premier_Suivi_PFA_v2.pptx`  
**Durée indicative :** ~12–15 minutes (+ questions)  
**Fil rouge à répéter :** *Dicter → Transcrire & corriger → Modifier → Exporter PDF ou DOC*

---

## Slide 1 — Titre

Bonjour Madame / Monsieur,

Je m’appelle Douae El Assal. Je suis étudiante à l’ENSA Tétouan, et je réalise mon Projet de Fin d’Année chez WebVoice.

Le projet s’appelle **Sanad** : une plateforme d’assistance en intelligence artificielle pour avocats.

Le point fort que je vais mettre en avant aujourd’hui : l’avocat **dicte** sa plaidoirie, le texte est **transcrit et corrigé**, il peut le **modifier**, puis l’**exporterer en PDF ou DOC**.

---

## Slide 2 — Objectif de ce suivi

L’objectif de cette présentation est clair.

Je vais présenter la problématique, puis la solution Sanad — en mettant surtout en valeur le parcours plaidoirie.  
Je montrerai ensuite les fonctionnalités, le benchmarking, les exigences, et les interfaces déjà réalisées.  
Enfin, je ferai le point sur l’avancement réel, y compris le VPS, et je validerai avec vous la suite.

---

## Slide 3 — Problématique

La problématique part d’un constat métier.

Même dans un cabinet organisé, le passage de la **parole** de l’avocat à un **document de plaidoirie** exploitable reste lent, manuel, et peu intégré au dossier numérique.

La plaidoirie est souvent dictée ou notée, puis retravaillée hors d’un flux unique.  
Les outils du marché couvrent soit la gestion, soit une dictée isolée, soit une IA générale — rarement le parcours complet jusqu’à un document modifiable et exportable.  
La collaboration avocat / assistant manque aussi d’un espace commun avec droits clairs.

Résultat : du temps perdu sur des tâches techniques, au détriment du travail juridique.  
Sur le marché marocain, la demande de digitalisation métier est réelle, mais encore inégale.

---

## Slide 4 — Solution proposée — Sanad

Face à cela, Sanad propose une plateforme SaaS multi-cabinets pour les avocats marocains.

Le **cœur produit**, c’est la plaidoirie :  
**dicter → transcrite et corrigée → modifiable par l’avocat → export PDF ou DOC**, puis classement dans un dossier.

Autour de ce cœur : dossiers, documents, synthèse, planning et équipe.  
L’IA accélère la transcription et la correction — mais l’avocat reste maître du texte final.  
Message produit : **« Deux gestes. Tout le reste suit. »**

---

## Slide 5 — Cœur Sanad — parcours plaidoirie *(à souligner)*

Voici le parcours que je souhaite vraiment mettre en valeur.

1. **Dicter** — l’avocat parle au micro, ou saisit le texte.  
2. **Transcrire et corriger** — Sanad produit un texte propre, sans inventer le fond juridique.  
3. **Modifier** — l’avocat vérifie, ajoute, corrige librement, comme s’il ouvrait son fichier.  
4. **Exporter** — il imprime en **PDF** ou télécharge en **DOC**.  
5. **Classer** — il range la plaidoirie dans un dossier précis du cabinet.

Ce n’est donc pas une dictée figée : l’avocat garde le contrôle jusqu’au document final.

---

## Slide 6 — Fonctionnalités de la plateforme

Autour de ce cœur, Sanad offre plusieurs briques.

La **plaidoirie** reste centrale : dicter, corriger, modifier, exporter PDF/DOC.  
Puis les **dossiers**, les **documents** avec OCR, la **synthèse**, le **planning**, l’**équipe**, la **sécurité** multi-tenant, et le **multilingue** FR / AR / EN.

Sanad n’est pas un simple chat juridique : c’est une plateforme cabinet, avec la plaidoirie comme cœur métier.

---

## Slide 7 — Exigences fonctionnelles

Ces besoins deviennent des exigences.

Côté accès : inscription, connexion, rôles, invitations.  
Côté priorité : **dictée → transcription et correction → modification → export PDF ou DOC → classement dossier**.  
Puis dossiers, documents, planning, collaboration avocat / assistant / admin, sécurité, et interfaces FR, AR, EN.

---

## Slide 8 — Benchmarking — schéma marché marocain

Pour positionner Sanad, j’ai regardé le marché marocain.

Gestion de cabinet : SmartAvocat, Avocato, AvocatPro — utiles, mais sans ce flux plaidoirie complet.  
IA juridique : Legaliq, Kanoun, Adala — utiles sur le contenu, mais pas comme SaaS cabinet avec export métier intégré.  
Dictée desktop : Dragon Legal via Diskod — dictée seule, pas de parcours Sanad jusqu’au dossier.

Sur le schéma : offre d’un côté, limite face au besoin Sanad de l’autre.

---

## Slide 9 — Résultat du benchmark — où se place Sanad ?

Le résultat est net.

Ce qui manque aujourd’hui : un SaaS qui relie **dictée → transcription/correction → modification → PDF/DOC → dossier**.  
Sanad vise exactement cet espace.  
Ce n’est pas « une IA de plus » : c’est le **flux métier intégré** qui manque sur le marché.

---

## Slide 10 — Espaces distincts — Avocat & Assistant

Les rôles sont clairs.

**Avocat** : il dicte, voit le texte transcrit et corrigé, le modifie, l’exporte en PDF ou DOC, et le classe dans un dossier.  
**Assistant** : il consulte les plaidoiries réalisées, peut les imprimer ou exporter en PDF/DOC, prépare les pièces — mais ne dicte pas à la place de l’avocat.

---

## Slide 11 — UI — site public

Voici la première implémentation côté site public : accueil, connexion, inscription du cabinet.  
C’est le point d’entrée pour ouvrir un espace Sanad.

---

## Slide 12 — UI — cœur métier *(à souligner)*

Voici le cœur métier.

Le tableau de bord oriente vers la plaidoirie.  
L’écran plaidoirie matérialise le parcours : **dicter, corriger, modifier, exporter PDF ou DOC, classer**.  
Les modules dossiers et documents permettent de rattacher l’affaire et les pièces.

C’est l’écran le plus important pour comprendre Sanad.

---

## Slide 13 — UI — Planning, Équipe, Paramètres, Sécurité

Autour du cœur : planning lié aux dossiers, équipe avec rôles, paramètres cabinet, et page sécurité publique.  
Cela montre que Sanad est pensé comme une plateforme cabinet complète.

---

## Slide 14 — Architecture principale *(diagramme)*

Voici le **diagramme principal** de Sanad.  
Le navigateur parle au frontend Next.js, qui appelle l’API FastAPI.  
Derrière : PostgreSQL pour les données métier, MinIO pour les fichiers, Redis pour les tâches, et l’IA pour la correction.  
Tout est isolé par cabinet.

---

## Slide 15 — Schémas parcours & couches

À gauche : le parcours plaidoirie en cinq étapes.  
À droite : les couches techniques, de l’interface jusqu’à la persistance.

---

## Slide 16 — Base de données — vue d’ensemble

Voici la vue d’ensemble du modèle de données : cabinets, users, dossiers, documents, planning…  
Le détail des colonnes est dans le document `03-base-de-donnees.md`.  
Les fichiers binaires sont dans MinIO, pas en base.

---

## Slide 17 — Documentation livrée

J’ai aussi préparé trois documents : interfaces, conception, et base de données, plus les diagrammes et les captures d’écran.

---

## Slide 18 — État d’avancement (réaliste)

Je préfère être transparente.

Nous avons une **première implémentation** — le projet n’est pas terminé.  
En place : le parcours plaidoirie (dictée, correction, édition, export PDF/DOC, classement) plus dossiers, documents, équipe.  
En cours : tests, consolidation, fiabilisation.  
VPS : clé SSH transmise ; accès encore en validation avec l’entreprise.

---

## Slide 19 — Prochaines étapes

Ensuite : fiabiliser le parcours dicter → corriger → modifier → PDF/DOC → dossier ; renforcer synthèse et planning ; déployer sur VPS ; préparer une démo courte de ce flux ; avancer le rapport PFA ; intégrer vos retours.

---

## Slide 20 — Conclusion

Pour conclure.

Le cœur de Sanad, c’est simple à retenir :  
**l’avocat dicte → le texte est transcrit et corrigé → il modifie → il exporte en PDF ou DOC.**

Ce n’est pas une IA isolée : c’est un flux métier intégré au dossier et à l’équipe.  
Le benchmark confirme ce manque sur le marché marocain.  
La première implémentation est en place ; la consolidation continue.

Je suis prête à répondre à vos questions. Merci pour votre attention.

---

## Phrase clé (si on te coupe / question)

> « Avec Sanad, l’avocat dicte sa plaidoirie ; elle est transcrite et corrigée ; il peut la modifier, puis l’exporterer en PDF ou DOC, et la classer dans un dossier. »

---

*Sanad · Premier suivi PFA · ENSA Tétouan · WebVoice · Douae El Assal*
