# Diagrammes UML — Sanad (pack complet)

**~50 fichiers PlantUML** couvrant la plateforme.

## Comment utiliser

1. Ouvre **`PLANTUML-COMPLET.md`** — tous les codes sont dedans  
2. Ou ouvre un fichier `.puml` + extension PlantUML (Cursor)  
3. Ou colle sur https://www.plantuml.com/plantuml/uml  

## Par catégorie

### Acteurs & cas d’utilisation
| Fichier | Contenu |
|---------|---------|
| `01-diagramme-acteurs.puml` | Acteurs humains + systèmes |
| `25-cas-utilisation-plateforme.puml` | **UC global complet** |
| `22-cas-utilisation-plaidoirie.puml` | UC plaidoirie |
| `23-cas-utilisation-assistant.puml` | UC assistant |
| `32-cas-utilisation-dossiers-docs.puml` | UC dossiers & documents |
| `33-cas-utilisation-planning.puml` | UC planning |
| `34-cas-utilisation-auth.puml` | UC authentification |
| `35-cas-utilisation-equipe-admin.puml` | UC équipe & admin |
| `50-matrice-droits.puml` | Matrice des droits |

### Séquences
| Fichier | Contenu |
|---------|---------|
| `26-sequence-plaidoirie.puml` | Parcours plaidoirie |
| `27-sequence-login.puml` | Connexion |
| `37-sequence-2fa.puml` | 2FA |
| `38-sequence-reset-password.puml` | Reset MDP |
| `30-sequence-inscription.puml` | Inscription |
| `29-sequence-invitation.puml` | Invitation équipe |
| `36-sequence-creer-dossier.puml` | Créer dossier |
| `28-sequence-upload.puml` | Upload document |
| `40-sequence-ocr-pipeline.puml` | Pipeline OCR |
| `41-sequence-planning.puml` | Événement planning |
| `42-sequence-synthese.puml` | Synthèse document |
| `31-sequence-assistant-consultation.puml` | Assistant consulte |
| `39-sequence-admin-approuver.puml` | Approuver cabinet |
| `07`–`13` | Séquences détaillées (legacy) |

### Activités & états
| Fichier | Contenu |
|---------|---------|
| `43-activite-plaidoirie.puml` | Activité plaidoirie |
| `44-activite-inscription.puml` | Activité inscription |
| `18-etat-document.puml` | États document |
| `45-etat-cabinet.puml` | États cabinet |
| `46-etat-dossier.puml` | États dossier |

### Architecture / stack / données
| Fichier | Contenu |
|---------|---------|
| `20-architecture-principale.puml` | Architecture |
| `21-stack-technologique.puml` | Stack |
| `24-deploiement-docker.puml` | Déploiement |
| `48-composants.puml` | Composants |
| `49-packages.puml` | Packages |
| `05-diagramme-classes-domaine.puml` | Classes domaine |
| `47-mcd-entite-relation.puml` | MCD / ER |

### Legacy (encore utiles)
`02` à `19` — versions antérieures (chat/IA) ; préférer les numéros **20+** pour le cœur plaidoirie.
