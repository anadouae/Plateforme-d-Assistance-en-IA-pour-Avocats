# LexHub — Audit produit & plan go-to-market

**Objectif :** un produit vendable sous la marque **LexHub**.  
Le seul gap client assumé : **paiement carte réel** (CMI / PayZone).  
Tout le reste doit paraître fini, cohérent, professionnel.

---

## Positionnement

Sanad = ancien nom de code du prototype.  
**LexHub** = marque commerciale et produit déployé (https://lexhub.space).  
Tout résidu « sanad » visible (base, Docker, docs démo) est une **dette de rebrand**, pas un choix produit.

---

## P0 — Marque : fermer Sanad

| Problème | Où | Solution |
|----------|-----|----------|
| Base / user SQL `sanad` | Adminer, Postgres | Migration → `lexhub` |
| Conteneurs & `/opt/sanad` | VPS | Renommer projet → `/opt/lexhub` |
| Classes UI `sanad-*` | Frontend | Alias `lexhub-*` puis purge |
| Comptes `@sanad.ma` | Guides, README | `@lexhub.space` / démo LexHub |
| Images Docker `sanad-*` | CI | Retag `lexhub-*` |
| Docs / PPT titrés Sanad | Livrables | Livrables finals 100 % LexHub |

**Phrase orale :** *« Sanad était le nom de code interne ; la marque et le produit s’appellent LexHub. L’alignement technique du nom interne est en cours. »*

---

## P0 — Sécurité / ops

| Problème | Solution |
|----------|----------|
| Adminer sur `https://lexhub.space/_ops/db/` | Retirer du public ; bastion SSH / VPN |
| Mot de passe DB `sanad_secret` | Rotation forte |
| SSH / secrets dans `scripts/` | Env + clés SSH uniquement |
| Credentials dans docs de test | Révoquer + supprimer |

---

## Paiement — seul gap produit assumé

**Déjà là :** plans, essai, packs, PAYG, sièges, factures, checkout UI, webhooks stub.  
**À activer :** agrément marchand + `BILLING_PAYMENT_MOCK=false` + webhooks signés + soft launch.

**Message marketing :** *« LexHub est prêt commercialement ; l’encaissement carte s’active avec l’opérateur — l’environnement technique est déjà en place. »*

---

## Confusion UX à clarifier

1. **Brouillon / Validée / Finalisée** — Validée = équipe ; Finalisée = export.  
2. **Quotas** jour / mois / essai / packs — une phrase claire par popup.  
3. **PDF = qualité Word** (RTL, logo, puces).  
4. **Assistant IA** : jamais « c’est fait » sans changement réel.  
5. Pas d’alertes « infos manquantes » à l’export.

---

## Plan d’attaque

### Vague A — 7 jours (marque + sécu)
1. Couper Adminer public  
2. Rotation secrets  
3. Zéro Sanad visible utilisateur  
4. Comptes démo LexHub + guides  
5. Marque unique (landing, e-mails, factures)

### Vague B — 2–3 semaines (nom technique)
6. Migration DB `sanad` → `lexhub`  
7. `/opt/lexhub` + compose `lexhub`  
8. Images / tokens CSS LexHub  
9. QA export + atelier 5 étapes

### Vague C — go-to-market
10. Dossier CMI / PayZone  
11. Sandbox → mock off  
12. Soft launch cabinets pilotes  

---

## Critère « vrai produit »

- [ ] LexHub partout côté client  
- [ ] `lexhub` en base / Docker / VPS  
- [ ] Pas d’Adminer public ; secrets rotatés  
- [ ] Export audience-ready  
- [ ] Seul manque client = encaissement réel  
- [ ] Isolation cabinets démontrable  

---

*Document de pilotage produit · septembre 2026 · LexHub*
