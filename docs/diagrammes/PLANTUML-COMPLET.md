# Pack PlantUML COMPLET — Sanad\n\n**Tout le code est ici.** Ouvre chaque section ou le fichier .puml correspondant.\n\nPrévisualiser : https://www.plantuml.com/plantuml/uml\n\n---\n\n## Catalogue (50 diagrammes)\n\n| # | Fichier |\n|---|---------|\n| 1 | 01-diagramme-acteurs.puml |\n| 2 | 02-cas-utilisation-global.puml |\n| 3 | 03-cas-utilisation-auth.puml |\n| 4 | 04-cas-utilisation-ia.puml |\n| 5 | 05-diagramme-classes-domaine.puml |\n| 6 | 06-diagramme-classes-services.puml |\n| 7 | 07-sequence-inscription-cabinet.puml |\n| 8 | 08-sequence-authentification.puml |\n| 9 | 09-sequence-upload-document.puml |\n| 10 | 10-sequence-chat-ia-rag.puml |\n| 11 | 11-sequence-synthese-document.puml |\n| 12 | 12-sequence-invitation-equipe.puml |\n| 13 | 13-sequence-admin-webvoice.puml |\n| 14 | 14-architecture-systeme.puml |\n| 15 | 15-architecture-composants.puml |\n| 16 | 16-stack-technologique.puml |\n| 17 | 17-deploiement.puml |\n| 18 | 18-etat-document.puml |\n| 19 | 19-activite-pipeline-ia.puml |\n| 20 | 20-architecture-principale.puml |\n| 21 | 21-stack-technologique.puml |\n| 22 | 22-cas-utilisation-plaidoirie.puml |\n| 23 | 23-cas-utilisation-assistant.puml |\n| 24 | 24-deploiement-docker.puml |\n| 25 | 25-cas-utilisation-plateforme.puml |\n| 26 | 26-sequence-plaidoirie.puml |\n| 27 | 27-sequence-login.puml |\n| 28 | 28-sequence-upload.puml |\n| 29 | 29-sequence-invitation.puml |\n| 30 | 30-sequence-inscription.puml |\n| 31 | 31-sequence-assistant-consultation.puml |\n| 32 | 32-cas-utilisation-dossiers-docs.puml |\n| 33 | 33-cas-utilisation-planning.puml |\n| 34 | 34-cas-utilisation-auth.puml |\n| 35 | 35-cas-utilisation-equipe-admin.puml |\n| 36 | 36-sequence-creer-dossier.puml |\n| 37 | 37-sequence-2fa.puml |\n| 38 | 38-sequence-reset-password.puml |\n| 39 | 39-sequence-admin-approuver.puml |\n| 40 | 40-sequence-ocr-pipeline.puml |\n| 41 | 41-sequence-planning.puml |\n| 42 | 42-sequence-synthese.puml |\n| 43 | 43-activite-plaidoirie.puml |\n| 44 | 44-activite-inscription.puml |\n| 45 | 45-etat-cabinet.puml |\n| 46 | 46-etat-dossier.puml |\n| 47 | 47-mcd-entite-relation.puml |\n| 48 | 48-composants.puml |\n| 49 | 49-packages.puml |\n| 50 | 50-matrice-droits.puml |\n\n---\n\n## 01-diagramme-acteurs.puml\n\n`plantuml\n@startuml sanad-diagramme-acteurs
title Diagramme des acteurs — Plateforme Sanad
skinparam actorStyle awesome
skinparam shadowing false
skinparam backgroundColor #F5F0E8

actor "Avocat" as Avocat
actor "Assistant juridique" as Assistant
actor "Admin cabinet" as AdminCabinet
actor "Admin WebVoice" as AdminWV
actor "Cabinet d'avocats\n<<organisation>>" as Cabinet

actor "Google OAuth\n<<system>>" as Google
actor "Serveur SMTP\n<<system>>" as SMTP
actor "Ollama / LLM cloud\n<<system>>" as LLM
actor "MinIO\n<<system>>" as MinIO

rectangle "Système Sanad" as Sanad

Cabinet --|> AdminCabinet
Cabinet --|> Avocat
Cabinet --|> Assistant

Avocat --> Sanad : utilise (cœur plaidoirie)
Assistant --> Sanad : utilise (préparation)
AdminCabinet --> Sanad : administre cabinet
AdminWV --> Sanad : supervise plateforme

Google --> Sanad : OAuth
SMTP --> Sanad : emails
LLM --> Sanad : correction / synthèse
MinIO --> Sanad : fichiers

note right of Avocat
  Dicter, corriger, modifier,
  exporter PDF/DOC, classer,
  dossiers, documents, planning
end note

note right of Assistant
  Dossiers, pièces, planning,
  consulter / exporter plaidoiries
  PAS de dictée plaidoirie
end note

note right of AdminCabinet
  Équipe, invitations, rôles,
  paramètres cabinet + métier
end note

note bottom of AdminWV
  Approuver / suspendre cabinets,
  métriques, audit — sans contenu client
end note
@enduml\n`\n\n---\n\n## 02-cas-utilisation-global.puml\n\n`plantuml\n@startuml sanad-cas-utilisation-global
' ============================================================
' Sanad — Diagramme de cas d'utilisation (vue globale)
' ============================================================

left to right direction
skinparam packageStyle rectangle
skinparam shadowing false

title Cas d'utilisation globaux — Sanad

actor "Avocat" as A
actor "Assistant\njuridique" as AS
actor "Admin\ncabinet" as AC
actor "Admin\nWebVoice" as AW

rectangle "Plateforme Sanad" {

  package "Authentification" {
    usecase "S'inscrire\n(créer cabinet)" as UC01
    usecase "Se connecter\n(JWT)" as UC02
    usecase "Vérifier email" as UC03
    usecase "Réinitialiser\nmot de passe" as UC04
    usecase "Activer 2FA" as UC05
    usecase "Connexion\nGoogle OAuth" as UC06
  }

  package "Gestion dossiers" {
    usecase "Créer un dossier" as UC10
    usecase "Consulter dossiers" as UC11
    usecase "Modifier un dossier" as UC12
    usecase "Rechercher / filtrer\ndossiers" as UC13
    usecase "Consulter timeline\nd'activité" as UC14
  }

  package "Gestion documents" {
    usecase "Uploader document\n(PDF/DOCX/image)" as UC20
    usecase "Consulter documents" as UC21
    usecase "Supprimer document" as UC22
    usecase "Suivre statut\ntraitement (OCR)" as UC23
  }

  package "Intelligence artificielle" {
    usecase "Poser question\n(assistant IA)" as UC30
    usecase "Obtenir synthèse\ndocumentaire" as UC31
    usecase "Analyser document\n(questions libres)" as UC32
    usecase "Exporter réponse\nen PDF" as UC33
    usecase "Consulter historique\nconversations" as UC34
  }

  package "Administration cabinet" {
    usecase "Inviter\ncollaborateur" as UC40
    usecase "Gérer rôles\néquipe" as UC41
    usecase "Configurer\nparamètres cabinet" as UC42
    usecase "Changer mot\nde passe" as UC43
  }

  package "Administration plateforme" {
    usecase "Activer /\nsuspendre cabinet" as UC50
    usecase "Consulter\nmétriques" as UC51
    usecase "Consulter logs\nd'audit" as UC52
  }

  package "Transversal" {
    usecase "Changer langue\n(FR/AR/EN)" as UC60
    usecase "Journaliser action\n(audit)" as UC61
  }
}

' --- Relations acteurs ---
AC --> UC01
AC --> UC02
AC --> UC05
AC --> UC06
AC --> UC10
AC --> UC11
AC --> UC12
AC --> UC13
AC --> UC14
AC --> UC20
AC --> UC21
AC --> UC22
AC --> UC23
AC --> UC30
AC --> UC31
AC --> UC32
AC --> UC33
AC --> UC34
AC --> UC40
AC --> UC41
AC --> UC42
AC --> UC43
AC --> UC60

A --> UC02
A --> UC05
A --> UC06
A --> UC10
A --> UC11
A --> UC12
A --> UC13
A --> UC14
A --> UC20
A --> UC21
A --> UC22
A --> UC23
A --> UC30
A --> UC31
A --> UC32
A --> UC33
A --> UC34
A --> UC43
A --> UC60

AS --> UC02
AS --> UC11
AS --> UC20
AS --> UC21
AS --> UC23
AS --> UC43
AS --> UC60

AW --> UC50
AW --> UC51
AW --> UC52

' --- Include / Extend ---
UC02 ..> UC61 : <<include>>
UC30 ..> UC61 : <<include>>
UC20 ..> UC61 : <<include>>
UC01 ..> UC03 : <<include>>
UC02 <.. UC05 : <<extend>>\n[si 2FA activée]
UC02 <.. UC06 : <<extend>>
UC30 ..> UC33 : <<extend>>
UC20 ..> UC23 : <<include>>

note bottom of UC30
  Routage automatique :
  Document → Dossier →
  Corpus RAG → Web
end note

@enduml\n`\n\n---\n\n## 03-cas-utilisation-auth.puml\n\n`plantuml\n@startuml sanad-cas-utilisation-auth
' ============================================================
' Sanad — Cas d'utilisation : Authentification & sécurité
' ============================================================

left to right direction
skinparam shadowing false

title Cas d'utilisation — Authentification et sécurité

actor "Utilisateur" as U
actor "Google OAuth\n<<system>>" as G
actor "Serveur SMTP\n<<system>>" as M

rectangle "Module Auth Sanad" {

  usecase "Inscription cabinet" as UC1
  usecase "Valider données\ninscription" as UC1a
  usecase "Créer tenant\n(cabinet isolé)" as UC1b
  usecase "Envoyer email\nvérification" as UC1c

  usecase "Vérifier email\n(activation compte)" as UC2

  usecase "Connexion JWT" as UC3
  usecase "Vérifier identifiants\n(bcrypt)" as UC3a
  usecase "Vérifier statut\ncabinet" as UC3b
  usecase "Générer tokens\n(access + refresh)" as UC3c
  usecase "Bloquer après\n5 échecs" as UC3d

  usecase "Saisir code 2FA\n(TOTP)" as UC4
  usecase "Configurer 2FA\n(QR code)" as UC5
  usecase "Désactiver 2FA" as UC6

  usecase "Connexion Google" as UC7
  usecase "Vérifier ID token" as UC7a

  usecase "Mot de passe oublié" as UC8
  usecase "Réinitialiser MDP" as UC9
  usecase "Rafraîchir token\n(refresh)" as UC10
  usecase "Déconnexion" as UC11
  usecase "Journaliser\n(auth.audit)" as UC12
}

U --> UC1
U --> UC2
U --> UC3
U --> UC4
U --> UC5
U --> UC6
U --> UC7
U --> UC8
U --> UC9
U --> UC10
U --> UC11

G --> UC7a
M --> UC1c
M --> UC8

UC1 ..> UC1a : <<include>>
UC1 ..> UC1b : <<include>>
UC1 ..> UC1c : <<include>>
UC1c ..> UC12 : <<include>>

UC3 ..> UC3a : <<include>>
UC3 ..> UC3b : <<include>>
UC3 ..> UC3c : <<include>>
UC3 ..> UC12 : <<include>>
UC3 <.. UC4 : <<extend>>\n[totp_enabled=true]
UC3 <.. UC3d : <<extend>>\n[5 échecs]

UC7 ..> UC7a : <<include>>
UC7 ..> UC3c : <<include>>

UC5 ..> UC4 : <<include>>
UC6 ..> UC4 : <<include>>

UC8 ..> UC12 : <<include>>
UC9 ..> UC12 : <<include>>

@enduml\n`\n\n---\n\n## 04-cas-utilisation-ia.puml\n\n`plantuml\n@startuml sanad-cas-utilisation-ia
' ============================================================
' Sanad — Cas d'utilisation : Assistant IA & analyse documentaire
' ============================================================

left to right direction
skinparam shadowing false

title Cas d'utilisation — Intelligence artificielle

actor "Avocat" as A
actor "Groq API" as G
actor "ChromaDB" as C
actor "Web Search" as W

rectangle "Module IA Sanad" {

  usecase "Poser question\nassistant IA" as UC1
  usecase "Router la question\n(agent.py)" as UC2

  usecase "Recherche document\nspécifique" as UC2a
  usecase "Recherche vecteurs\ndossier" as UC2b
  usecase "Recherche corpus\njuridique (RAG)" as UC2c
  usecase "Recherche web\ncomplémentaire" as UC2d

  usecase "Récupérer extraits\n+ citations" as UC3
  usecase "Rédiger réponse\n(Groq Llama 3.3)" as UC4
  usecase "Calculer score\nde confiance" as UC5
  usecase "Streamer réponse\n(SSE)" as UC6
  usecase "Afficher disclaimer\njuridique" as UC7
  usecase "Alerter confiance\n< 60 %" as UC8

  usecase "Synthèse automatique\ndocument" as UC10
  usecase "Extraire parties" as UC10a
  usecase "Extraire dates /\nmontants" as UC10b
  usecase "Identifier clauses\nà risque" as UC10c

  usecase "Question libre\nsur document" as UC11
  usecase "Citer paragraphe\nsource" as UC11a

  usecase "Exporter réponse\nPDF" as UC12
  usecase "Consulter historique\nchat" as UC13
  usecase "Fallback Ollama\n(si Groq down)" as UC14
  usecase "Journaliser requête IA" as UC15
}

A --> UC1
A --> UC10
A --> UC11
A --> UC12
A --> UC13

G --> UC4
C --> UC3
W --> UC3

UC1 ..> UC2 : <<include>>
UC2 ..> UC2a : <<extend>>\n[document_id fourni]
UC2 ..> UC2b : <<extend>>\n[case_id fourni]
UC2 ..> UC2c : <<extend>>\n[question juridique]
UC2 ..> UC2d : <<extend>>\n[corpus insuffisant]

UC2a ..> UC3 : <<include>>
UC2b ..> UC3 : <<include>>
UC2c ..> UC3 : <<include>>
UC2d ..> UC3 : <<include>>

UC3 ..> UC4 : <<include>>
UC4 ..> UC5 : <<include>>
UC4 ..> UC6 : <<include>>
UC4 ..> UC7 : <<include>>
UC5 <.. UC8 : <<extend>>\n[score < 60]
UC4 <.. UC14 : <<extend>>\n[Groq indisponible]
UC1 ..> UC15 : <<include>>

UC10 ..> UC10a : <<include>>
UC10 ..> UC10b : <<include>>
UC10 ..> UC10c : <<include>>
UC10 ..> UC3 : <<include>>
UC10 ..> UC4 : <<include>>

UC11 ..> UC11a : <<include>>
UC11 ..> UC2a : <<include>>

UC1 <.. UC12 : <<extend>>

note right of UC2
  Principe directeur :
  L'IA ne répond JAMAIS
  de mémoire. Elle cherche
  d'abord, puis rédige.
end note

@enduml\n`\n\n---\n\n## 05-diagramme-classes-domaine.puml\n\n`plantuml\n@startuml sanad-classes-domaine
' ============================================================
' Sanad — Diagramme de classes (modèle domaine)
' Aligné sur backend/app/models/__init__.py
' ============================================================

skinparam classAttributeIconSize 0
skinparam shadowing false
skinparam class {
  BackgroundColor #F8FAFC
  BorderColor #1E40AF
  ArrowColor #1E40AF
}

title Diagramme de classes — Modèle domaine Sanad

enum UserRole {
  AVOCAT
  ASSISTANT_JURIDIQUE
  ADMIN_CABINET
  ADMIN_WEBVOICE
}

enum CabinetStatus {
  ACTIVE
  SUSPENDED
  PENDING
}

enum DocumentStatus {
  PENDING
  PROCESSING
  INDEXED
  FAILED
}

enum TokenType {
  VERIFY_EMAIL
  RESET_PASSWORD
  TEAM_INVITE
}

class Cabinet {
  - id : UUID
  - name : String
  - city : String
  - address : Text
  - barreau : String
  - ice : String {optional}
  - status : CabinetStatus
  - created_at : DateTime
}

class User {
  - id : UUID
  - email : String {unique}
  - hashed_password : String
  - full_name : String
  - phone : String {optional}
  - role : UserRole
  - is_active : Boolean
  - is_verified : Boolean
  - failed_login_attempts : Integer
  - locked_until : DateTime {optional}
  - google_id : String {optional}
  - totp_secret : String {optional}
  - totp_enabled : Boolean
  - cabinet_id : UUID
  - created_at : DateTime
}

class Case {
  - id : UUID
  - reference : String {unique, WV-AAAA-XXXX}
  - client_name : String
  - case_type : String
  - status : String
  - description : Text {optional}
  - tags : String {optional}
  - cabinet_id : UUID
  - responsible_id : UUID
  - opened_at : DateTime
  - updated_at : DateTime
}

class Document {
  - id : UUID
  - filename : String
  - original_name : String
  - mime_type : String
  - file_size : Integer
  - storage_path : String
  - extracted_text : Text {optional}
  - ocr_score : Integer {optional}
  - status : DocumentStatus
  - case_id : UUID
  - cabinet_id : UUID
  - uploaded_by : UUID
  - created_at : DateTime
}

class ChatMessage {
  - id : UUID
  - case_id : UUID {optional}
  - cabinet_id : UUID
  - user_id : UUID
  - question : Text
  - answer : Text
  - source_type : String
  - sources : Text {JSON}
  - confidence_score : Integer
  - created_at : DateTime
}

class AuditLog {
  - id : UUID
  - user_id : UUID {optional}
  - cabinet_id : UUID {optional}
  - action : String
  - ip_address : String {optional}
  - details : Text {optional}
  - created_at : DateTime
}

class EmailToken {
  - id : UUID
  - user_id : UUID
  - token_hash : String {unique}
  - token_type : TokenType
  - expires_at : DateTime
  - used_at : DateTime {optional}
  - created_at : DateTime
}

' --- Associations ---
Cabinet "1" *-- "0..*" User : emploie >
Cabinet "1" *-- "0..*" Case : contient >
User "1" -- "0..*" Case : responsable >
Case "1" *-- "0..*" Document : contient >
Case "0..1" *-- "0..*" ChatMessage : historise >
User "1" -- "0..*" ChatMessage : pose >
User "1" -- "0..*" EmailToken : possède >
User "1" -- "0..*" AuditLog : génère >
Cabinet "1" -- "0..*" AuditLog : concerne >

User ..> UserRole : utilise
Cabinet ..> CabinetStatus : utilise
Document ..> DocumentStatus : utilise
EmailToken ..> TokenType : utilise

note right of Cabinet
  **Règle multi-tenant**
  Chaque cabinet = tenant isolé.
  Données invisibles entre cabinets.
end note

note bottom of Document
  stockage_path → MinIO (chiffré AES-256)
  extracted_text → indexé dans ChromaDB
end note

@enduml\n`\n\n---\n\n## 06-diagramme-classes-services.puml\n\n`plantuml\n@startuml sanad-classes-services
' ============================================================
' Sanad — Diagramme de classes (couche services)
' ============================================================

skinparam shadowing false

title Diagramme de classes — Services applicatifs et IA

package "API Layer" <<Rectangle>> {
  class AuthAPI {
    + register()
    + login()
    + googleLogin()
    + setup2fa()
    + enable2fa()
    + refresh()
  }
  class CasesAPI {
    + listCases()
    + createCase()
    + getCase()
    + updateCase()
  }
  class DocumentsAPI {
    + upload()
    + getDocument()
    + deleteDocument()
    + getSynthesis()
    + askDocument()
  }
  class ChatAPI {
    + chat()
    + chatStream()
    + getHistory()
  }
  class AdminAPI {
    + listCabinets()
    + approveCabinet()
    + suspendCabinet()
    + getMetrics()
    + getAuditLogs()
  }
}

package "Services" <<Rectangle>> {
  class AuthService {
    - hashPassword()
    - verifyPassword()
    - createTokens()
    - checkLockout()
  }
  class EmailService {
    + sendVerification()
    + sendPasswordReset()
    + sendTeamInvite()
  }
  class TokenService {
    + createToken()
    + consumeToken()
  }
  class TotpService {
    + generateSecret()
    + verifyCode()
    + generateQR()
  }
  class GoogleOAuthService {
    + verifyIdToken()
  }
  class StorageService {
    + uploadEncrypted()
    + downloadDecrypted()
    + delete()
  }
  class DocumentPipeline {
    + extractText()
    + runOCR()
    + indexVectors()
    + processAsync()
  }
  class AgentRouter {
    + route(question, context)
    - routeDocument()
    - routeCase()
    - routeRAG()
    - routeWeb()
  }
  class RAGService {
    + searchCorpus()
    + searchCase()
    + searchDocument()
  }
  class LLMService {
    + generate()
    + generateStream()
    - fallbackOllama()
  }
  class WebSearchService {
    + search()
  }
  class SynthesisService {
    + synthesize()
  }
  class AuditService {
    + log(action, user, details)
  }
}

package "Infrastructure" <<Rectangle>> {
  class PostgreSQL <<database>> {
    users, cabinets, cases,
    documents, audit_logs
  }
  class ChromaDB <<database>> {
    embeddings corpus + docs
  }
  class MinIO <<database>> {
    fichiers chiffrés
  }
  class Redis <<database>> {
    broker Celery
  }
  class CeleryWorker <<component>> {
    tâches async OCR/index
  }
}

' --- Dépendances ---
AuthAPI --> AuthService
AuthAPI --> EmailService
AuthAPI --> TokenService
AuthAPI --> TotpService
AuthAPI --> GoogleOAuthService
AuthAPI --> AuditService

CasesAPI --> PostgreSQL
DocumentsAPI --> StorageService
DocumentsAPI --> DocumentPipeline
DocumentsAPI --> SynthesisService
DocumentsAPI --> AuditService

ChatAPI --> AgentRouter
ChatAPI --> AuditService

AdminAPI --> PostgreSQL
AdminAPI --> AuditService

AuthService --> PostgreSQL
DocumentPipeline --> StorageService
DocumentPipeline --> CeleryWorker
DocumentPipeline --> ChromaDB
CeleryWorker --> Redis

AgentRouter --> RAGService
AgentRouter --> WebSearchService
AgentRouter --> LLMService
RAGService --> ChromaDB
StorageService --> MinIO
LLMService --> GroqAPI : <<external>>
WebSearchService --> TavilyAPI : <<external>>

@enduml\n`\n\n---\n\n## 07-sequence-inscription-cabinet.puml\n\n`plantuml\n@startuml sanad-sequence-inscription
' ============================================================
' Sanad — Séquence : Inscription cabinet
' Scénario D-05 / F-01
' ============================================================

skinparam shadowing false
skinparam sequenceMessageAlign center

title Diagramme de séquence — Inscription d'un cabinet

actor "Admin cabinet\n(futur)" as U
participant "Frontend\nNext.js" as FE
participant "AuthAPI\nFastAPI" as API
participant "AuthService" as Auth
database "PostgreSQL" as DB
participant "EmailService\nSMTP" as Mail
participant "AuditService" as Audit

== Inscription ==

U -> FE : Remplir formulaire\n(nom cabinet, barreau, email, MDP)
FE -> FE : Valider robustesse MDP\n(8+ chars, maj, chiffre, symbole)
FE -> API : POST /api/auth/register\n(RegisterRequest)

API -> Auth : hashPassword(mdp)
Auth --> API : hashed_password

API -> DB : INSERT Cabinet\n(status=PENDING)
DB --> API : cabinet_id

API -> DB : INSERT User\n(role=ADMIN_CABINET,\nis_active=false, is_verified=false)
DB --> API : user_id

API -> DB : INSERT EmailToken\n(type=VERIFY_EMAIL, expire=24h)
DB --> API : token

API -> Mail : sendVerificationEmail(email, token)
Mail --> API : OK

API -> Audit : log("auth.register", user)
Audit -> DB : INSERT audit_log

API --> FE : 201 { message: "Vérifiez votre email" }
FE --> U : Page "Vérifiez votre email"

== Vérification email ==

U -> FE : Cliquer lien email\n/api/auth/verify-email?token=...
FE -> API : GET /api/auth/verify-email?token=...
API -> DB : SELECT EmailToken\nWHERE hash=token AND not expired
DB --> API : token valide
API -> DB : UPDATE User\nis_verified=true
API -> DB : UPDATE EmailToken\nused_at=now()
API -> Audit : log("auth.email_verified")
API --> FE : { message: "Email vérifié" }
FE --> U : Redirection login

note over DB
  Le cabinet reste PENDING
  jusqu'à activation par
  Admin WebVoice
end note

@enduml\n`\n\n---\n\n## 08-sequence-authentification.puml\n\n`plantuml\n@startuml sanad-sequence-auth
' ============================================================
' Sanad — Séquence : Authentification (JWT + 2FA + OAuth)
' ============================================================

skinparam shadowing false

title Diagramme de séquence — Authentification

actor "Utilisateur" as U
participant "Frontend" as FE
participant "AuthAPI" as API
participant "AuthService" as Auth
participant "TotpService" as TOTP
participant "GoogleOAuth" as Google
database "PostgreSQL" as DB
participant "AuditService" as Audit

== Connexion classique (JWT) ==

U -> FE : Saisir email + mot de passe
FE -> API : POST /api/auth/login\n{ email, password }

API -> DB : SELECT User WHERE email=?
DB --> API : user

alt Compte verrouillé (locked_until > now)
  API --> FE : 403 "Compte verrouillé"
else Identifiants incorrects
  API -> DB : failed_login_attempts++
  alt failed_login_attempts >= 5
    API -> DB : locked_until = now + 15min
  end
  API -> Audit : log("auth.login_failed")
  API --> FE : 401 "Identifiants incorrects"
else Identifiants corrects
  API -> DB : Vérifier is_verified, is_active
  API -> DB : Vérifier Cabinet.status\n(ACTIVE requis)

  opt totp_enabled = true
    alt totp_code absent
      API --> FE : 403 "2FA_REQUIRED"
      FE --> U : Afficher champ code 2FA
      U -> FE : Saisir code TOTP
      FE -> API : POST /login { email, password, totp_code }
    end
    API -> TOTP : verify(secret, code)
    alt code invalide
      API -> Audit : log("auth.2fa_failed")
      API --> FE : 401 "Code 2FA invalide"
    end
  end

  API -> DB : failed_login_attempts = 0
  API -> Auth : createAccessToken() + createRefreshToken()
  API -> Audit : log("auth.login_success")
  API --> FE : TokenResponse\n{ access_token, refresh_token, user }
  FE -> FE : Stocker JWT (localStorage)
  FE --> U : Redirection dashboard
end

== Connexion Google OAuth ==

U -> FE : Cliquer "Continuer avec Google"
FE -> Google : Google Identity Services\n(obtenir id_token)
Google --> FE : id_token
FE -> API : POST /api/auth/google\n{ id_token }
API -> Google : verifyIdToken(id_token)
Google --> API : { email, google_id, name }
API -> DB : SELECT User WHERE email=?
alt Compte inexistant
  API --> FE : 404 "Inscrivez votre cabinet d'abord"
else Compte valide
  API -> DB : UPDATE google_id
  API -> Auth : createTokens()
  API -> Audit : log("auth.google_login")
  API --> FE : TokenResponse
  FE --> U : Redirection dashboard
end

== Refresh token ==

FE -> API : POST /api/auth/refresh\n{ refresh_token }
API -> Auth : decodeToken(refresh_token)
API -> DB : Vérifier user actif
API -> Auth : createAccessToken() + createRefreshToken()
API --> FE : Nouveaux tokens

@enduml\n`\n\n---\n\n## 09-sequence-upload-document.puml\n\n`plantuml\n@startuml sanad-sequence-upload
' ============================================================
' Sanad — Séquence : Upload et traitement document
' Scénario D-02 / F-11 à F-14
' ============================================================

skinparam shadowing false

title Diagramme de séquence — Upload document (OCR + indexation)

actor "Avocat /\nAssistant" as U
participant "Frontend" as FE
participant "DocumentsAPI" as API
participant "StorageService\n(MinIO)" as MinIO
database "PostgreSQL" as DB
queue "Redis\n(Celery)" as Redis
participant "CeleryWorker" as Worker
participant "DocumentPipeline" as Pipeline
participant "ChromaDB\n+ BGE-M3" as Chroma
participant "AuditService" as Audit

== Upload ==

U -> FE : Sélectionner fichier\n(PDF/DOCX/image, max 50 Mo)
FE -> FE : Valider type MIME + taille
FE -> API : POST /api/documents/upload\n(multipart: file + case_id)\nAuthorization: Bearer JWT

API -> API : Vérifier JWT + rôle\n+ cabinet_id du dossier
API -> MinIO : uploadEncrypted(file)\nFernet AES-256
MinIO --> API : storage_path

API -> DB : INSERT Document\n(status=PENDING, storage_path)
DB --> API : document_id

API -> Redis : enqueue process_document(document_id)
API -> Audit : log("document.upload", user, doc_id)
API --> FE : 201 DocumentResponse\n{ id, status: "pending" }

FE --> U : Badge "En attente"
FE -> FE : Démarrer polling statut\n(toutes les 3s)

== Traitement asynchrone (Celery) ==

Redis -> Worker : process_document(document_id)
Worker -> DB : UPDATE status = PROCESSING
Worker -> MinIO : downloadDecrypted(storage_path)
MinIO --> Worker : fichier brut

Worker -> Pipeline : extractText(file)

alt PDF natif
  Pipeline -> Pipeline : PyMuPDF extraction
else DOCX
  Pipeline -> Pipeline : python-docx extraction
else Image / PDF scanné
  Pipeline -> Pipeline : pdf2image + Tesseract\n(fra + ara)
  Pipeline -> Pipeline : Calculer ocr_score
end

Pipeline --> Worker : extracted_text, ocr_score

Worker -> DB : UPDATE extracted_text, ocr_score

alt ocr_score < 70
  Worker -> DB : ocr_alert = true
end

Worker -> Chroma : indexDocument(text, embeddings BGE-M3)\ncollection = cabinet_id + case_id
Chroma --> Worker : indexed

alt Indexation réussie
  Worker -> DB : UPDATE status = INDEXED
else Erreur
  Worker -> DB : UPDATE status = FAILED
end

== Polling frontend ==

loop jusqu'à INDEXED ou FAILED
  FE -> API : GET /api/documents/{id}
  API -> DB : SELECT Document
  API --> FE : { status, ocr_score, ocr_alert }
end

FE --> U : Badge "Indexé" ou "Échec"\n+ alerte OCR si < 70%

@enduml\n`\n\n---\n\n## 10-sequence-chat-ia-rag.puml\n\n`plantuml\n@startuml sanad-sequence-chat-ia
' ============================================================
' Sanad — Séquence : Chat IA avec routage multi-sources
' Scénario D-01, D-03, D-04 / F-20 à F-27
' ============================================================

skinparam shadowing false

title Diagramme de séquence — Assistant IA (routage + SSE)

actor "Avocat" as U
participant "Frontend\nChatPanel" as FE
participant "ChatAPI" as API
participant "AgentRouter\nagent.py" as Agent
participant "RAGService\nChromaDB" as RAG
participant "WebSearch\nTavily/DDG" as Web
participant "LLMService\nGroq" as LLM
database "PostgreSQL" as DB
participant "AuditService" as Audit

== Poser une question ==

U -> FE : Saisir question\n+ contexte (case_id / document_id)
FE -> API : POST /api/chat/stream\n{ question, case_id?, document_id? }\nAuthorization: Bearer JWT

API -> API : Vérifier JWT + rôle\n(avocat ou admin_cabinet)
API -> Agent : route(question, context)

alt document_id fourni
  Agent -> RAG : searchDocument(doc_id, question)
  RAG --> Agent : extraits + scores
  note right : source_type = "document"
else case_id fourni
  Agent -> RAG : searchCase(case_id, question)
  RAG --> Agent : extraits documents du dossier
  note right : source_type = "document"
else question juridique générale
  Agent -> RAG : searchCorpus(question)\n(DOC, CPP, CPC)
  RAG --> Agent : articles + paragraphes
  note right : source_type = "rag"

  alt corpus insuffisant (score < seuil)
    Agent -> Web : search(question)
    Web --> Agent : résultats web
    note right : source_type = "rag+web"
  end
end

Agent -> Agent : Construire prompt\n(extraits + citations + question)
Agent -> Agent : Calculer confidence_score

alt Aucune source pertinente
  Agent --> API : { answer: "Aucune source trouvée",\nconfidence: 0 }
else Sources trouvées
  API --> FE : SSE event: meta\n{ source_type, confidence, sources[] }

  Agent -> LLM : generateStream(prompt)

  loop tokens streaming
    LLM --> Agent : token
    Agent --> API : SSE event: token\n{ content: "..." }
    API --> FE : EventSource onmessage
    FE --> U : Affichage progressif\n+ curseur animé
  end

  opt confidence_score < 60
    FE --> U : Alerte ambre\n"Score faible — vérifiez sources"
  end

  FE --> U : Afficher citations\n+ disclaimer juridique
end

API -> DB : INSERT ChatMessage\n(question, answer, sources, score)
API -> Audit : log("chat.query", user,\nsource_type, confidence, duration)
API --> FE : SSE event: done\n{ id: message_id }

opt Export PDF
  U -> FE : Cliquer "Exporter PDF"
  FE -> FE : exportAiResponsePdf(result)\n→ fenêtre impression
end

@enduml\n`\n\n---\n\n## 11-sequence-synthese-document.puml\n\n`plantuml\n@startuml sanad-sequence-synthese
' ============================================================
' Sanad — Séquence : Synthèse automatique document
' Scénario D-02 / F-30 à F-32
' ============================================================

skinparam shadowing false

title Diagramme de séquence — Synthèse documentaire

actor "Avocat" as U
participant "Frontend\nSynthesisPanel" as FE
participant "DocumentsAPI" as API
participant "SynthesisService" as Synth
participant "RAGService" as RAG
participant "LLMService\nGroq" as LLM
database "PostgreSQL" as DB
participant "AuditService" as Audit

== Demande de synthèse ==

U -> FE : Ouvrir document indexé\n+ cliquer "Synthèse"
FE -> FE : Afficher skeleton loading
FE -> API : GET /api/documents/{id}/synthese\nAuthorization: Bearer JWT

API -> API : Vérifier JWT + cabinet_id
API -> DB : SELECT Document\nWHERE status=INDEXED
DB --> API : document + extracted_text

alt Document non indexé
  API --> FE : 400 "Document en cours de traitement"
  FE --> U : Message d'attente
else Document prêt
  API -> Synth : synthesize(document)

  Synth -> RAG : searchDocument(id, "synthèse complète")
  RAG --> Synth : texte structuré

  Synth -> LLM : generate(prompt_synthèse)\n"Extraire : parties, dates,\nmontants, clauses à risque"

  note over LLM
    Objectif performance :
    PDF 20 pages < 30 secondes
  end note

  LLM --> Synth : JSON structuré\n{ parties[], dates[], amounts[],\nrisk_clauses[], summary }

  Synth -> Synth : Construire citations\n(paragraphes sources)
  Synth -> Synth : Ajouter disclaimer

  API -> Audit : log("document.synthesis", user, doc_id)
  API --> FE : SynthesisResult\n{ parties, dates, amounts,\nrisk_clauses, attention_points,\nsummary, sources, disclaimer }

  FE --> U : Grille synthèse pro\n(parties | dates | montants)\n+ alertes clauses à risque
end

== Question libre sur le document ==

U -> FE : Poser question ciblée\nsur le bail
FE -> API : POST /api/documents/{id}/ask\n{ question }
API -> RAG : searchDocument(id, question)
RAG --> API : paragraphe exact
API -> LLM : generate(prompt + extrait)
LLM --> API : réponse avec citation
API --> FE : AIResult\n{ answer, sources[], confidence }
FE --> U : Réponse citant\nle paragraphe exact (D-03)

@enduml\n`\n\n---\n\n## 12-sequence-invitation-equipe.puml\n\n`plantuml\n@startuml sanad-sequence-invitation
' ============================================================
' Sanad — Séquence : Invitation collaborateur
' Scénario D-05 / F-06
' ============================================================

skinparam shadowing false

title Diagramme de séquence — Invitation d'un collaborateur

actor "Admin cabinet" as AC
actor "Nouveau\ncollaborateur" as NC
participant "Frontend" as FE
participant "TeamAPI" as API
participant "AuthService" as Auth
database "PostgreSQL" as DB
participant "EmailService" as Mail
participant "AuditService" as Audit

== Invitation ==

AC -> FE : Équipe → Inviter\n(email, nom, rôle)
FE -> API : POST /api/team/invite\n{ email, full_name, role }\nAuthorization: Bearer JWT

API -> API : Vérifier rôle = admin_cabinet
API -> DB : Vérifier email non existant\ndans le cabinet

API -> Auth : hashPassword(temp_password)
API -> DB : INSERT User\n(role=assistant|avocat,\nis_active=true, is_verified=false)
DB --> API : user_id

API -> DB : INSERT EmailToken\n(type=TEAM_INVITE, expire=72h)
API -> Mail : sendTeamInvite(email, token, cabinet_name)
Mail --> NC : Email invitation

API -> Audit : log("team.invite", admin, email)
API --> FE : { message: "Invitation envoyée" }
FE --> AC : Confirmation

== Activation par le collaborateur ==

NC -> FE : Cliquer lien invitation
FE -> API : GET lien → page set-password
NC -> FE : Définir mot de passe
FE -> API : POST /api/auth/activate-invite\n{ token, password }
API -> DB : Valider EmailToken
API -> DB : UPDATE User\nis_verified=true, password=hash
API -> Audit : log("team.member_activated")
API --> FE : TokenResponse
FE --> NC : Redirection dashboard

note over NC
  Si rôle = assistant_juridique :
  accès upload + consultation
  PAS de chat IA ni suppression
end note

@enduml\n`\n\n---\n\n## 13-sequence-admin-webvoice.puml\n\n`plantuml\n@startuml sanad-sequence-admin
' ============================================================
' Sanad — Séquence : Administration WebVoice
' F-40 à F-42
' ============================================================

skinparam shadowing false

title Diagramme de séquence — Back-office Admin WebVoice

actor "Admin\nWebVoice" as AW
participant "Frontend\n/admin" as FE
participant "AdminAPI" as API
database "PostgreSQL" as DB
participant "AuditService" as Audit

== Connexion admin ==

AW -> FE : Login admin@webvoice.ma
FE -> API : POST /api/auth/login
API --> FE : TokenResponse\n(role=admin_webvoice)
FE -> FE : Redirection /admin\n(pas de dashboard cabinet)

== Consulter métriques ==

AW -> FE : Ouvrir dashboard admin
FE -> API : GET /api/admin/metrics
API -> API : Vérifier role=admin_webvoice
API -> DB : COUNT cabinets (active, suspended)
API -> DB : COUNT users, documents, chat_messages
API -> DB : AVG confidence_score (today)
API --> FE : AdminMetrics\n{ active_cabinets, total_users,\nchat_requests_today, avg_confidence }
FE --> AW : Cartes métriques

== Lister et gérer cabinets ==

AW -> FE : Liste des cabinets
FE -> API : GET /api/admin/cabinets
API -> DB : SELECT cabinets + counts\n(users, docs, cases, chats)
API --> FE : AdminCabinet[]

AW -> FE : Approuver cabinet PENDING
FE -> API : PATCH /api/admin/cabinets/{id}/approve
API -> DB : UPDATE Cabinet\nstatus = ACTIVE
API -> DB : UPDATE Users\nis_active = true
API -> Audit : log("admin.cabinet_approved", cabinet_id)
API --> FE : { message: "Cabinet activé" }
FE --> AW : Statut mis à jour

opt Suspendre cabinet
  AW -> FE : Suspendre cabinet
  FE -> API : PATCH /api/admin/cabinets/{id}/suspend
  API -> DB : UPDATE Cabinet status=SUSPENDED
  API -> Audit : log("admin.cabinet_suspended")
  API --> FE : Confirmation
end

== Consulter audit logs ==

AW -> FE : Onglet Audit
FE -> API : GET /api/admin/audit-logs
API -> DB : SELECT audit_logs\nORDER BY created_at DESC\nLIMIT 100
API --> FE : AuditLog[]\n(action, user_id, ip, details, date)
FE --> AW : Tableau logs

note over AW, DB
  **Règle de confidentialité**
  L'admin WebVoice accède aux
  métriques et logs agrégés
  mais JAMAIS au contenu des
  documents ou conversations.
end note

@enduml\n`\n\n---\n\n## 14-architecture-systeme.puml\n\n`plantuml\n@startuml sanad-architecture-systeme
' ============================================================
' Sanad — Architecture système (C4 Niveau 1)
' ============================================================

skinparam shadowing false
skinparam rectangle {
  BackgroundColor #EFF6FF
  BorderColor #1E40AF
}

title Architecture système — Vue C4 (Niveau 1)

actor "Avocat" as Avocat
actor "Admin cabinet" as AdminC
actor "Admin WebVoice" as AdminW

rectangle "Système Sanad\n(Avocat AI Assistance)" as Sanad {
  rectangle "Frontend Web\n(Next.js 14)" as Front
  rectangle "API Backend\n(FastAPI)" as Back
  rectangle "Workers\n(Celery)" as Workers
  rectangle "Moteur IA\n(Agent + RAG)" as IA
}

database "PostgreSQL\n(métadonnées)" as PG
database "ChromaDB\n(vecteurs)" as Chroma
database "MinIO\n(fichiers chiffrés)" as MinIO
database "Redis\n(queue)" as Redis

cloud "Groq API\n(LLM)" as Groq
cloud "Tavily / DDG\n(web)" as Web
cloud "Google OAuth" as Google
cloud "SMTP\n(email)" as SMTP

Avocat --> Front : HTTPS\n(navigateur)
AdminC --> Front : HTTPS
AdminW --> Front : HTTPS

Front --> Back : REST API + SSE\n(JWT Bearer)
Back --> PG : SQLAlchemy ORM
Back --> Redis : enqueue tasks
Workers --> Redis : consume tasks
Workers --> MinIO : read/write fichiers
Workers --> Chroma : indexation BGE-M3
Back --> IA : routage questions
IA --> Chroma : recherche vectorielle
IA --> Groq : génération réponses
IA --> Web : recherche complémentaire
Back --> Google : vérif OAuth token
Back --> SMTP : emails transactionnels

note bottom of Sanad
  **Isolation multi-tenant**
  Chaque cabinet = espace isolé
  Chiffrement AES-256 (Fernet)
  Audit logs 5 ans
end note

@enduml\n`\n\n---\n\n## 15-architecture-composants.puml\n\n`plantuml\n@startuml sanad-architecture-composants
' ============================================================
' Sanad — Diagramme de composants
' ============================================================

skinparam componentStyle rectangle
skinparam shadowing false

title Diagramme de composants — Décomposition interne Sanad

package "Frontend (Next.js 14)" {
  component "Pages App Router" as Pages
  component "Composants UI" as UI
  component "State Zustand" as State
  component "API Client" as ApiClient

  note right of Pages
    Landing/Auth, Dashboard,
    Dossiers, Documents,
    Assistant IA, Paramètres,
    Admin WebVoice
  end note

  note right of UI
    AppShell, ChatPanel SSE,
    SynthesisPanel, DocumentUpload,
    AIResponseCard, LanguageSwitch
  end note
}

package "Backend (FastAPI)" {
  component "API Routers" as Routers
  component "Middleware" as MW
  component "Services métier" as SvcBiz
  component "Services IA" as SvcIA

  note right of Routers
    auth, cases, documents,
    chat, team, admin
  end note

  note right of SvcBiz
    document_pipeline, agent,
    email, tokens, totp,
    google_oauth, encryption
  end note

  note right of SvcIA
    BGE-M3, ChromaDB, Groq,
    web search, synthesis,
    ollama fallback
  end note
}

package "Workers (Celery)" {
  component "celery_app" as Celery
  component "process_document" as TaskDoc
}

package "Persistance" {
  database "PostgreSQL" as PG
  database "ChromaDB" as Chroma
  database "MinIO" as MinIO
  database "Redis" as Redis
}

cloud "Services externes" {
  component "Groq API" as Groq
  component "Tavily / DDG" as Tavily
  component "Google OAuth" as Google
  component "SMTP" as SMTP
}

Pages --> UI
Pages --> State
Pages --> ApiClient
ApiClient --> Routers : HTTP/HTTPS

Routers --> MW
Routers --> SvcBiz
Routers --> SvcIA
Routers --> PG

SvcBiz --> MinIO
SvcBiz --> Celery
Celery --> Redis
TaskDoc --> SvcBiz
TaskDoc --> Chroma

SvcIA --> Chroma
SvcIA --> Groq
SvcIA --> Tavily
SvcBiz --> SMTP
SvcBiz --> Google

@enduml\n`\n\n---\n\n## 16-stack-technologique.puml\n\n`plantuml\n@startuml sanad-stack-technologique
' ============================================================
' Sanad — Diagramme stack technologique
' ============================================================

skinparam shadowing false
skinparam rectangle {
  BackgroundColor #F0FDF4
  BorderColor #166534
}

title Stack technologique — Sanad Avocat AI Assistance

together {
  rectangle "**Couche Présentation**" as L1 {
    card "Next.js 14\n(App Router)" as nextjs
    card "TypeScript" as ts
    card "Tailwind CSS" as tw
    card "Zustand" as zu
    card "Framer Motion" as fm
    card "React Three Fiber" as r3f
    card "Lucide Icons" as lucide
  }
}

together {
  rectangle "**Couche API / Logique**" as L2 {
    card "FastAPI" as fastapi
    card "Pydantic v2" as pydantic
    card "SQLAlchemy 2" as sqlalchemy
    card "Alembic" as alembic
    card "Celery" as celery
    card "python-jose\n(JWT)" as jwt
    card "bcrypt" as bcrypt
    card "Fernet\n(AES-256)" as fernet
  }
}

together {
  rectangle "**Couche Données**" as L3 {
    card "PostgreSQL\n(Neon)" as pg
    card "ChromaDB" as chroma
    card "Redis" as redis
    card "MinIO\n(S3-compatible)" as minio
  }
}

together {
  rectangle "**Couche Intelligence Artificielle**" as L4 {
    card "BGE-M3\n(embeddings FR/AR)" as bge
    card "Groq\nLlama 3.3 70B" as groq
    card "Ollama\n(fallback local)" as ollama
    card "Tesseract\nOCR fra+ara" as ocr
    card "PyMuPDF" as pymupdf
    card "Tavily /\nDuckDuckGo" as web
    card "agent.py\n(routage)" as agent
  }
}

together {
  rectangle "**Couche Infrastructure**" as L5 {
    card "Docker Compose\n(8 services)" as docker
    card "Vercel\n(frontend prod)" as vercel
    card "Render / Railway\n(backend prod)" as render
    card "Sentry\n(monitoring)" as sentry
    card "GitHub Actions\n(CI/CD)" as gha
    card "MailHog / SMTP" as mail
  }
}

L1 -[hidden]down- L2
L2 -[hidden]down- L3
L3 -[hidden]down- L4
L4 -[hidden]down- L5

note bottom of L4
  **Principe IA**
  ChromaDB + Web → extraits
  Groq → rédaction finale
  Jamais de réponse sans source
end note

@enduml\n`\n\n---\n\n## 17-deploiement.puml\n\n`plantuml\n@startuml sanad-deploiement
' ============================================================
' Sanad — Diagramme de déploiement
' Dev (Docker Compose) + Cible production
' ============================================================

skinparam shadowing false
skinparam node {
  BackgroundColor #F8FAFC
  BorderColor #334155
}

title Diagramme de déploiement — Sanad

node "Poste développeur" as Dev {
  artifact "Navigateur" as Browser
}

node "Docker Host\n(localhost)" as Docker {

  node "frontend:3000" as FE {
    component [Next.js dev server] as NextDev
  }

  node "backend:8001" as BE {
    component [Uvicorn\nFastAPI] as Uvicorn
  }

  node "celery-worker" as CW {
    component [Celery Worker\nconcurrency=2] as Worker
  }

  node "postgres:5432" as PG {
    database "PostgreSQL 16" as Postgres
  }

  node "redis:6379" as RD {
    database "Redis 7" as Redis
  }

  node "minio:9000" as MI {
    database "MinIO" as MinIO
  }

  node "mailhog:8025" as MH {
    component [MailHog UI] as MailHog
  }

  node "chromadb\n(volume)" as CH {
    database "ChromaDB\n/data/chromadb" as Chroma
  }
}

cloud "Services cloud" as Cloud {
  node "Neon\n(optionnel)" as Neon {
    database "PostgreSQL\ncloud" as NeonDB
  }
  node "Groq API" as Groq
  node "Tavily API" as Tavily
  node "Google OAuth" as Google
}

node "Production (cible Sprint 4)" as Prod {
  node "Vercel" as Vercel {
    component [Next.js\nbuild statique/SSR] as NextProd
  }
  node "Render / Railway" as Render {
    component [FastAPI + Celery] as BackProd
  }
  node "Sentry" as Sentry {
    component [Error tracking] as SentryApp
  }
}

' --- Dev ---
Browser --> NextDev : HTTP :3000
Browser --> Uvicorn : HTTP :8001\n(API + SSE)
NextDev --> Uvicorn : NEXT_PUBLIC_API_URL
Uvicorn --> Postgres : DATABASE_URL
Uvicorn --> Redis : CELERY_BROKER
Worker --> Redis : consume
Worker --> MinIO : fichiers
Worker --> Chroma : embeddings
Uvicorn --> Chroma : RAG queries
Uvicorn --> Groq : LLM
Uvicorn --> Tavily : web search
Uvicorn --> MailHog : SMTP :1025
Uvicorn --> Google : OAuth verify

' --- Neon option ---
Uvicorn ..> NeonDB : DATABASE_URL\n(cloud dev/prod)

' --- Production ---
Browser ..> NextProd : HTTPS
NextProd ..> BackProd : HTTPS API
BackProd ..> NeonDB
BackProd ..> Groq
BackProd ..> SentryApp : erreurs

note right of Docker
  **8 services Docker Compose**
  frontend, backend, celery-worker,
  postgres, redis, minio, mailhog
  + volumes chroma_data, hf_cache
end note

@enduml\n`\n\n---\n\n## 18-etat-document.puml\n\n`plantuml\n@startuml sanad-etat-document
' ============================================================
' Sanad — Diagramme d'états : cycle de vie d'un document
' ============================================================

skinparam shadowing false

title Diagramme d'états — Cycle de vie d'un document

[*] --> PENDING : uploadDocument()\n[/api/documents/upload]

state PENDING : status = pending
state PROCESSING : status = processing
state INDEXED : status = indexed
state FAILED : status = failed

PENDING --> PROCESSING : CeleryWorker\nprend la tâche\nprocess_document()

PROCESSING --> INDEXED : extraction OK\n+ indexation ChromaDB OK
PROCESSING --> FAILED : erreur OCR\nou erreur indexation

INDEXED --> [*] : deleteDocument()\n[/api/documents/{id}]

FAILED --> PROCESSING : retry manuel\n(admin, futur)

state PROCESSING {
  state "Extraction texte" as Extract
  state "OCR (si image/scan)" as OCR
  state "Indexation BGE-M3" as Index

  [*] --> Extract
  Extract --> OCR : mime = image\nou PDF scanné
  Extract --> Index : texte natif\n(PDF/DOCX)
  OCR --> Index : ocr_score calculé
  Index --> [*]
}

note right of INDEXED
  Document prêt pour :
  - Synthèse automatique
  - Questions IA ciblées
  - Recherche vectorielle dossier
end note

note right of OCR
  Si ocr_score < 70 % :
  ocr_alert = true
  Alerte affichée à l'utilisateur
end note

@enduml\n`\n\n---\n\n## 19-activite-pipeline-ia.puml\n\n`plantuml\n@startuml sanad-activite-pipeline-ia
' ============================================================
' Sanad — Diagramme d'activité : Pipeline IA complet
' ============================================================

skinparam shadowing false

title Diagramme d'activité — Pipeline IA Sanad

start

:Utilisateur pose une question;

:Vérifier authentification JWT\n+ rôle (avocat/admin_cabinet);

if (document_id fourni ?) then (oui)
  :Recherche vectorielle\ndans le document;
  :source_type = "document";
elseif (case_id fourni ?) then (oui)
  :Recherche vectorielle\ndans les docs du dossier;
  :source_type = "document";
else (non)
  :Recherche corpus juridique\n(DOC, CPP, CPC) via ChromaDB;
  :source_type = "rag";
  if (Score RAG < seuil ?) then (oui)
    :Recherche web\n(Tavily / DuckDuckGo);
    :source_type = "rag+web";
  endif
endif

if (Sources trouvées ?) then (oui)
  :Construire prompt\navec extraits + citations;
  :Calculer score de confiance;
  if (Groq disponible ?) then (oui)
    :Générer réponse\n(Groq Llama 3.3 70B);
  else (non)
    :Fallback Ollama\n(mode dégradé local);
  endif
  :Streamer réponse SSE\nvers le frontend;
  if (confidence < 60 % ?) then (oui)
    :Afficher alerte\n"Score faible";
  endif
  :Ajouter disclaimer juridique;
  :Sauvegarder ChatMessage\nen base;
  :Journaliser dans audit_logs;
else (non)
  :Répondre "Aucune source pertinente trouvée";
  :confidence = 0;
endif

stop

@enduml\n`\n\n---\n\n## 20-architecture-principale.puml\n\n`plantuml\n@startuml sanad-architecture-principale
' ============================================================
' Sanad — Architecture principale (vue claire)
' Cœur produit : Plaidoirie (pas le chat)
' ============================================================

skinparam shadowing false
skinparam backgroundColor #F5F0E8
skinparam defaultFontName Arial
skinparam defaultFontSize 12
skinparam rectangle {
  BackgroundColor #FFFFFF
  BorderColor #0B1F4A
  RoundCorner 12
}
skinparam database {
  BackgroundColor #E8EEF7
  BorderColor #0B1F4A
}
skinparam actor {
  BackgroundColor #D2B589
  BorderColor #0B1F4A
}

title Sanad — Architecture principale

actor "Avocat" as Avocat
actor "Assistant\njuridique" as Assist
actor "Admin\ncabinet" as AdminC

rectangle "Navigateur Web\n(FR / AR / EN)" as Browser #0B1F4A

rectangle "Frontend\nNext.js · TypeScript · Tailwind\n:3000" as Front #FFFFFF

rectangle "Backend API\nFastAPI · JWT · Multi-tenant\n:8001" as API #0B1F4A

rectangle "Workers Celery\n(OCR / indexation)" as Celery #FFFFFF

database "PostgreSQL\nDonnées métier\n:5432" as PG
database "MinIO\nFichiers documents\n:9000" as MinIO
database "Redis\nCache / files\n:6379" as Redis
database "ChromaDB\nIndex sémantique" as Chroma

cloud "IA\nOllama (+ cloud fallback)\nCorrection / synthèse" as LLM

Avocat --> Browser
Assist --> Browser
AdminC --> Browser

Browser --> Front : HTTPS
Front --> API : REST + JWT Bearer

API --> PG : SQLAlchemy
API --> MinIO : upload / download
API --> Redis : tâches
API --> LLM : polish / compose\n(plaidoirie)
API --> Chroma : recherche\n(pièces / corpus)

Celery --> Redis
Celery --> MinIO
Celery --> Chroma
Celery --> PG

note right of API
  **Isolation multi-tenant**
  Filtrage par cabinet_id
  Rôles : avocat / assistant /
  admin_cabinet / admin_webvoice
end note

note bottom of Front
  **Cœur UI**
  Plaidoirie · Dossiers · Documents
  Planning · Équipe · Paramètres
  (Chat retiré du menu principal)
end note

@enduml\n`\n\n---\n\n## 21-stack-technologique.puml\n\n`plantuml\n@startuml sanad-stack-technologique-v2
' ============================================================
' Sanad — Stack technologique (par couches)
' Aligné Docker Compose + déploiement VPS
' ============================================================

skinparam shadowing false
skinparam backgroundColor #F5F0E8
skinparam defaultFontName Arial
skinparam defaultFontSize 11
skinparam package {
  BackgroundColor #FFFFFF
  BorderColor #0B1F4A
  FontColor #0B1F4A
  FontStyle bold
  RoundCorner 10
}
skinparam card {
  BackgroundColor #E8EEF7
  BorderColor #0B1F4A
}

title Sanad — Stack technologique

package "1. Présentation" as L1 {
  card "Next.js\n(App Router)" as next
  card "TypeScript" as ts
  card "Tailwind CSS" as tw
  card "Zustand\n(auth / locale)" as zu
  card "Framer Motion" as fm
  card "Playwright\n(maquettes)" as pw
}

package "2. API & métier" as L2 {
  card "Python 3\nFastAPI" as fastapi
  card "Pydantic" as pydantic
  card "SQLAlchemy 2\n+ Alembic" as sa
  card "JWT\n(python-jose)" as jwt
  card "Celery" as celery
  card "Dictation API\npolish / compose" as dict
}

package "3. Données & stockage" as L3 {
  card "PostgreSQL 16" as pg
  card "MinIO\n(S3)" as minio
  card "Redis 7" as redis
  card "ChromaDB" as chroma
}

package "4. Intelligence artificielle" as L4 {
  card "Ollama\n(modèle local)" as ollama
  card "LLM cloud\n(fallback)" as cloud
  card "OCR\n(Tesseract / PDF)" as ocr
  card "Embeddings\n(BGE-M3)" as emb
}

package "5. Infrastructure" as L5 {
  card "Docker\nCompose" as docker
  card "VPS Debian\n(cible prod)" as vps
  card "MailHog\n(dev SMTP)" as mail
  card "Git / GitHub" as git
}

L1 -[hidden]down-> L2
L2 -[hidden]down-> L3
L3 -[hidden]down-> L4
L4 -[hidden]down-> L5

note bottom of L2
  **Flux cœur produit**
  Dicter → Transcrire & corriger → Modifier
  → Exporter PDF / DOC → Classer dossier
end note

@enduml\n`\n\n---\n\n## 22-cas-utilisation-plaidoirie.puml\n\n`plantuml\n@startuml sanad-uc-plaidoirie
' ============================================================
' Sanad — Cas d'utilisation : Plaidoirie (cœur)
' ============================================================

skinparam shadowing false
skinparam backgroundColor #F5F0E8
skinparam actorStyle awesome
left to right direction

title Cas d'utilisation — Plaidoirie (cœur Sanad)

actor "Avocat" as Avocat
actor "Assistant\njuridique" as Assist
actor "Admin\ncabinet" as Admin

rectangle "Sanad — Module Plaidoirie" {
  usecase "Dicter la plaidoirie\n(micro AR / saisie)" as UC1
  usecase "Transcrire & corriger\nle texte (IA)" as UC2
  usecase "Modifier / vérifier\nle document" as UC3
  usecase "Exporter PDF\nou DOC" as UC4
  usecase "Classer dans\nun dossier" as UC5
  usecase "Consulter les\nplaidoiries archivées" as UC6
}

Avocat --> UC1
Avocat --> UC2
Avocat --> UC3
Avocat --> UC4
Avocat --> UC5

Admin --> UC1
Admin --> UC2
Admin --> UC3
Admin --> UC4
Admin --> UC5

Assist --> UC6
Assist --> UC4

UC1 ..> UC2 : <<include>>
UC2 ..> UC3 : <<include>>
UC3 ..> UC4 : <<extend>>
UC3 ..> UC5 : <<extend>>

note bottom of UC6
  L'assistant ne dicte pas.
  Il consulte et peut exporter.
end note

@enduml\n`\n\n---\n\n## 23-cas-utilisation-assistant.puml\n\n`plantuml\n@startuml sanad-uc-assistant
' ============================================================
' Sanad — Cas d'utilisation : Assistant juridique
' ============================================================

skinparam shadowing false
skinparam backgroundColor #F5F0E8
left to right direction

title Cas d'utilisation — Assistant juridique

actor "Assistant\njuridique" as A
actor "Avocat" as Avocat

rectangle "Espace Assistant — Sanad" {
  usecase "Consulter / préparer\nles dossiers" as UC1
  usecase "Uploader & classer\nles pièces" as UC2
  usecase "Suivre planning\n(audiences, tâches, notes)" as UC3
  usecase "Consulter les\nplaidoiries réalisées" as UC4
  usecase "Exporter plaidoirie\nPDF ou DOC" as UC5
}

rectangle "Réservé à l'avocat" as ZoneAvocat #FFE4E1 {
  usecase "Dicter / produire\nla plaidoirie" as UC_AV1
  usecase "Modifier le texte\ncorrigé" as UC_AV2
  usecase "Synthèse IA /\nanalyse dossier" as UC_AV3
}

A --> UC1
A --> UC2
A --> UC3
A --> UC4
A --> UC5

Avocat --> UC_AV1
Avocat --> UC_AV2
Avocat --> UC_AV3
Avocat --> UC1

note right of A
  **Rôle assistant**
  Préparer et organiser
  Pas de production de plaidoirie
end note

@enduml\n`\n\n---\n\n## 24-deploiement-docker.puml\n\n`plantuml\n@startuml sanad-deploiement-docker
' ============================================================
' Sanad — Déploiement Docker Compose (dev) → VPS
' ============================================================

skinparam shadowing false
skinparam backgroundColor #F5F0E8
skinparam node {
  BackgroundColor #FFFFFF
  BorderColor #0B1F4A
  RoundCorner 8
}

title Déploiement — Docker Compose / VPS Debian

node "Poste / VPS Linux Debian" {
  node "Docker Compose" {
    component "frontend\n:3000" as FE
    component "backend\n:8001" as BE
    component "celery-worker" as CW
    database "postgres\n:5432" as PG
    database "redis\n:6379" as RD
    database "minio\n:9000" as MN
    component "ollama\n:11434" as OL
  }
}

actor "Utilisateur\ncabinet" as U
U --> FE : navigateur
FE --> BE
BE --> PG
BE --> RD
BE --> MN
BE --> OL
CW --> RD
CW --> MN
CW --> PG

note bottom
  Dev : localhost
  Prod cible : VPS Debian (entreprise WebVoice)
end note

@enduml\n`\n\n---\n\n## 25-cas-utilisation-plateforme.puml\n\n`plantuml\n@startuml sanad-uc-plateforme-complet
left to right direction
skinparam shadowing false
skinparam backgroundColor #F5F0E8
skinparam packageStyle rectangle

title Cas d'utilisation GLOBAUX — Plateforme Sanad (complet)

actor "Avocat" as Av
actor "Assistant\njuridique" as As
actor "Admin\ncabinet" as Ac
actor "Admin\nWebVoice" as Aw
actor "Google\n<<system>>" as G
actor "SMTP\n<<system>>" as S
actor "LLM / Ollama\n<<system>>" as L

rectangle "Sanad" {

  package "1. Authentification" {
    usecase "S'inscrire (créer cabinet)" as UC01
    usecase "Vérifier email" as UC02
    usecase "Se connecter (JWT)" as UC03
    usecase "Connexion Google" as UC04
    usecase "Activer / utiliser 2FA" as UC05
    usecase "Mot de passe oublié" as UC06
    usecase "Réinitialiser mot de passe" as UC07
    usecase "Activer compte invitation" as UC08
    usecase "Se déconnecter" as UC09
  }

  package "2. Plaidoirie (cœur)" {
    usecase "Dicter (micro AR / saisie)" as UC10
    usecase "Corriger texte (IA)" as UC11
    usecase "Générer document officiel" as UC12
    usecase "Modifier titre / corps" as UC13
    usecase "Exporter PDF / Imprimer" as UC14
    usecase "Télécharger DOC" as UC15
    usecase "Classer dans un dossier" as UC16
    usecase "Consulter plaidoiries archivées" as UC17
  }

  package "3. Dossiers" {
    usecase "Créer dossier" as UC20
    usecase "Lister / rechercher dossiers" as UC21
    usecase "Filtrer par statut" as UC22
    usecase "Voir détail dossier" as UC23
    usecase "Modifier dossier" as UC24
    usecase "Voir activité dossier" as UC25
  }

  package "4. Documents" {
    usecase "Uploader pièce" as UC30
    usecase "Consulter liste documents" as UC31
    usecase "Voir texte extrait (OCR)" as UC32
    usecase "Télécharger fichier" as UC33
    usecase "Relancer extraction" as UC34
    usecase "Supprimer document" as UC35
    usecase "Obtenir synthèse (IA)" as UC36
  }

  package "5. Planning" {
    usecase "Gérer événements agenda" as UC40
    usecase "Gérer tâches" as UC41
    usecase "Gérer notes" as UC42
    usecase "Lier au dossier" as UC43
  }

  package "6. Équipe & paramètres" {
    usecase "Inviter collaborateur" as UC50
    usecase "Changer rôle membre" as UC51
    usecase "Configurer cabinet" as UC52
    usecase "Changer mot de passe" as UC53
    usecase "Configurer 2FA compte" as UC54
  }

  package "7. Admin plateforme" {
    usecase "Approuver cabinet" as UC60
    usecase "Suspendre / réactiver" as UC61
    usecase "Consulter métriques" as UC62
    usecase "Consulter audit logs" as UC63
  }

  package "8. Transversal" {
    usecase "Changer langue FR/AR/EN" as UC70
    usecase "Journaliser action (audit)" as UC71
  }
}

' Avocat
Av --> UC03
Av --> UC05
Av --> UC09
Av --> UC10
Av --> UC11
Av --> UC12
Av --> UC13
Av --> UC14
Av --> UC15
Av --> UC16
Av --> UC20
Av --> UC21
Av --> UC22
Av --> UC23
Av --> UC24
Av --> UC25
Av --> UC30
Av --> UC31
Av --> UC32
Av --> UC33
Av --> UC34
Av --> UC35
Av --> UC36
Av --> UC40
Av --> UC41
Av --> UC42
Av --> UC43
Av --> UC53
Av --> UC54
Av --> UC70

' Assistant
As --> UC03
As --> UC09
As --> UC17
As --> UC14
As --> UC15
As --> UC20
As --> UC21
As --> UC22
As --> UC23
As --> UC30
As --> UC31
As --> UC32
As --> UC33
As --> UC40
As --> UC41
As --> UC42
As --> UC43
As --> UC53
As --> UC70

' Admin cabinet
Ac --> UC01
Ac --> UC02
Ac --> UC03
Ac --> UC10
Ac --> UC11
Ac --> UC12
Ac --> UC13
Ac --> UC14
Ac --> UC15
Ac --> UC16
Ac --> UC20
Ac --> UC30
Ac --> UC35
Ac --> UC36
Ac --> UC50
Ac --> UC51
Ac --> UC52
Ac --> UC53
Ac --> UC54
Ac --> UC70

' WebVoice
Aw --> UC03
Aw --> UC60
Aw --> UC61
Aw --> UC62
Aw --> UC63

' Systèmes
G --> UC04
S --> UC02
S --> UC06
S --> UC50
L --> UC11
L --> UC12
L --> UC36

' Includes
UC01 ..> UC02 : <<include>>
UC10 ..> UC11 : <<include>>
UC11 ..> UC12 : <<include>>
UC12 ..> UC13 : <<include>>
UC03 <.. UC05 : <<extend>>
UC03 <.. UC04 : <<extend>>
UC40 ..> UC43 : <<extend>>
UC30 ..> UC71 : <<include>>
UC16 ..> UC30 : <<include>>

note bottom of UC17
  Assistant : lecture + export
  Pas de dictée / pas de compose
end note
@enduml\n`\n\n---\n\n## 26-sequence-plaidoirie.puml\n\n`plantuml\n@startuml sanad-sequence-plaidoirie
' ============================================================
' Sanad — Séquence : Parcours plaidoirie (cœur)
' ============================================================

skinparam shadowing false
skinparam backgroundColor #F5F0E8

title Séquence — Dicter → Corriger → Modifier → Exporter / Classer

actor "Avocat" as U
participant "Frontend\n/redaction" as FE
participant "API Dictation\n/api/dictation" as DICT
participant "Service IA\n(Ollama / LLM)" as IA
participant "API Documents\n/api/documents" as DOC
participant "MinIO" as S3
database "PostgreSQL" as DB

== 1. Dictée ==
U -> FE : Micro AR / saisie texte
FE -> FE : Afficher texte brut

== 2. Transcription & correction ==
U -> FE : Clic « Corriger »
FE -> DICT : POST /api/dictation/polish\n{ text }
DICT -> IA : Corriger (sans inventer)
IA --> DICT : texte corrigé
DICT --> FE : { polished, provider }
FE -> FE : Afficher texte éditable
U -> FE : Modifier / vérifier le texte

== 3. Document officiel ==
U -> FE : Clic « Générer le document »
FE -> DICT : POST /api/dictation/compose\n{ text, doc_type: plaidoirie }
DICT -> IA : Structurer titre + corps
IA --> DICT : { title, body }
DICT --> FE : document officiel
U -> FE : Modifier titre / corps librement

== 4a. Export local ==
U -> FE : PDF / Imprimer  ou  DOC
FE -> FE : Générer fichier côté client\n(export-official-doc)

== 4b. Classer dans un dossier ==
U -> FE : Choisir dossier + Enregistrer
FE -> DOC : POST /api/documents/upload\n(case_id + fichier)
DOC -> S3 : stocker {cabinet}/{case}/fichier
DOC -> DB : INSERT documents
DOC --> FE : DocumentItem
FE --> U : « Plaidoirie enregistrée »

@enduml\n`\n\n---\n\n## 27-sequence-login.puml\n\n`plantuml\n@startuml sanad-sequence-login
skinparam shadowing false
title Séquence — Connexion JWT

actor "Utilisateur" as U
participant "Frontend\n/login" as FE
participant "API Auth\n/api/auth" as API
database "PostgreSQL" as DB

U -> FE : email + mot de passe
FE -> API : POST /api/auth/login
API -> DB : SELECT user + cabinet
alt Identifiants OK + compte actif
  API -> API : Générer access_token\n+ refresh_token (JWT)
  API --> FE : tokens + user
  FE -> FE : localStorage + Zustand
  FE --> U : Redirection /dashboard
else Échec
  API --> FE : 401 / 403
  FE --> U : Message d'erreur
end

@enduml\n`\n\n---\n\n## 28-sequence-upload.puml\n\n`plantuml\n@startuml sanad-sequence-upload
skinparam shadowing false
title Séquence — Upload document (pièce dossier)

actor "Utilisateur\ncabinet" as U
participant "Frontend" as FE
participant "API Documents" as API
participant "MinIO" as S3
participant "Celery Worker" as W
database "PostgreSQL" as DB

U -> FE : Sélectionner fichier + dossier
FE -> API : POST /api/documents/upload
API -> API : Vérifier JWT + cabinet_id
API -> S3 : PUT {cabinet_id}/{case_id}/{file}
API -> DB : INSERT document\nstatus=pending
API --> FE : Document créé
API -> W : enqueue OCR / extraction
W -> S3 : lire fichier
W -> W : OCR / extract text
W -> DB : UPDATE extracted_text\nstatus=indexed
FE --> U : Statut mis à jour

@enduml\n`\n\n---\n\n## 29-sequence-invitation.puml\n\n`plantuml\n@startuml sanad-sequence-invitation
skinparam shadowing false
title Séquence — Invitation membre équipe

actor "Admin cabinet" as A
participant "Frontend\n/team" as FE
participant "API Team" as API
database "PostgreSQL" as DB
participant "SMTP" as Mail
actor "Nouveau membre" as M

A -> FE : email + rôle (avocat / assistant)
FE -> API : POST /api/team/invite
API -> DB : CREATE user (inactif)\n+ email_token (team_invite)
API -> Mail : Envoyer lien /activate?token=
API --> FE : Invitation créée
Mail --> M : Email d'invitation
M -> FE : Ouvrir /activate
FE -> API : Définir mot de passe
API -> DB : Activer user
API --> FE : OK → /login

@enduml\n`\n\n---\n\n## 30-sequence-inscription.puml\n\n`plantuml\n@startuml sanad-sequence-inscription
skinparam shadowing false
title Séquence — Inscription cabinet

actor "Futur admin" as U
participant "Frontend\n/register" as FE
participant "API Auth" as API
database "PostgreSQL" as DB
participant "SMTP" as Mail
actor "Admin WebVoice" as AW

U -> FE : Infos cabinet + compte
FE -> API : POST /api/auth/register
API -> DB : CREATE cabinet (pending)\n+ user admin_cabinet
API -> DB : CREATE email_token verify
API -> Mail : Email vérification
API --> FE : Compte créé (à vérifier)
U -> FE : Confirmer email
FE -> API : GET /api/auth/verify-email
API -> DB : is_verified = true
AW -> API : Approuver cabinet
API -> DB : cabinet.status = active\nuser.is_active = true
U -> FE : Se connecter → /dashboard

@enduml\n`\n\n---\n\n## 31-sequence-assistant-consultation.puml\n\n`plantuml\n@startuml sanad-sequence-assistant
skinparam shadowing false
title Séquence — Assistant : consulter / exporter une plaidoirie

actor "Assistant\njuridique" as A
participant "Frontend\n/redaction" as FE
participant "API Cases" as Cases
participant "API Documents" as Docs
database "PostgreSQL" as DB

A -> FE : Ouvrir Plaidoirie (mode lecture)
FE -> Cases : GET /api/cases
Cases -> DB : dossiers du cabinet
Cases --> FE : liste cases
loop pour chaque dossier
  FE -> Docs : GET /api/documents?case_id=
  Docs --> FE : documents
end
FE -> FE : Filtrer noms « plaidoirie… »
A -> FE : Voir une plaidoirie
FE -> Docs : GET /api/documents/{id}
Docs --> FE : extracted_text_preview
A -> FE : PDF / Imprimer  ou  DOC
FE -> FE : Export côté client\n(sans modifier le fichier serveur)

note right of A
  Pas d'appel /dictation/polish
  Pas d'upload de nouvelle plaidoirie
end note

@enduml\n`\n\n---\n\n## 32-cas-utilisation-dossiers-docs.puml\n\n`plantuml\n@startuml sanad-uc-dossiers-docs
left to right direction
skinparam shadowing false
title Cas d'utilisation — Dossiers & Documents

actor "Avocat" as Av
actor "Assistant" as As
actor "Admin cabinet" as Ac

rectangle "Dossiers" {
  usecase "Créer dossier" as C1
  usecase "Lister / rechercher\ndossiers" as C2
  usecase "Modifier dossier" as C3
  usecase "Voir détail dossier" as C4
  usecase "Filtrer par statut" as C5
}

rectangle "Documents" {
  usecase "Uploader pièce" as D1
  usecase "Télécharger pièce" as D2
  usecase "Voir texte OCR" as D3
  usecase "Relancer extraction" as D4
  usecase "Supprimer document" as D5
  usecase "Synthèse document (IA)" as D6
  usecase "Question sur document (IA)" as D7
}

Av --> C1
Av --> C2
Av --> C3
Av --> C4
Av --> C5
Av --> D1
Av --> D2
Av --> D3
Av --> D4
Av --> D5
Av --> D6
Av --> D7

As --> C1
As --> C2
As --> C4
As --> C5
As --> D1
As --> D2
As --> D3
' Pas D5 D6 D7 pour assistant

Ac --> C1
Ac --> C2
Ac --> C3
Ac --> D1
Ac --> D5
Ac --> D6

D1 ..> D3 : <<include>>
note right of D5
  Suppression interdite
  pour assistant_juridique
end note
@enduml\n`\n\n---\n\n## 33-cas-utilisation-planning.puml\n\n`plantuml\n@startuml sanad-uc-planning
left to right direction
skinparam shadowing false
title Cas d'utilisation — Planning (Agenda / Tâches / Notes)

actor "Avocat" as Av
actor "Assistant" as As
actor "Admin cabinet" as Ac

rectangle "Planning Sanad" {
  usecase "Créer événement\n(audience, délai, RDV)" as P1
  usecase "Modifier / supprimer\névénement" as P2
  usecase "Lier événement\nà un dossier" as P3
  usecase "Créer tâche" as P4
  usecase "Changer statut tâche\n(todo/doing/done)" as P5
  usecase "Créer note" as P6
  usecase "Consulter planning\ncabinet" as P7
}

Av --> P1
Av --> P2
Av --> P3
Av --> P4
Av --> P5
Av --> P6
Av --> P7

As --> P1
As --> P2
As --> P3
As --> P4
As --> P5
As --> P6
As --> P7

Ac --> P1
Ac --> P7

P1 ..> P3 : <<extend>>
P4 ..> P3 : <<extend>>
@enduml\n`\n\n---\n\n## 34-cas-utilisation-auth.puml\n\n`plantuml\n@startuml sanad-uc-auth-complet
left to right direction
skinparam shadowing false
title Cas d'utilisation — Authentification & comptes

actor "Visiteur" as V
actor "Membre cabinet" as M
actor "Admin cabinet" as Ac
actor "Google" as G
actor "SMTP" as S

rectangle "Auth Sanad" {
  usecase "S'inscrire" as U1
  usecase "Vérifier email" as U2
  usecase "Se connecter email/mdp" as U3
  usecase "Se connecter Google" as U4
  usecase "Saisir code 2FA" as U5
  usecase "Demander reset mdp" as U6
  usecase "Définir nouveau mdp" as U7
  usecase "Activer invitation" as U8
  usecase "Refresh token JWT" as U9
  usecase "Se déconnecter" as U10
  usecase "Configurer TOTP" as U11
}

V --> U1
V --> U3
V --> U4
V --> U6
Ac --> U1
M --> U3
M --> U5
M --> U7
M --> U8
M --> U9
M --> U10
M --> U11
G --> U4
S --> U2
S --> U6
S --> U8

U1 ..> U2 : <<include>>
U3 <.. U5 : <<extend>>
U6 ..> U7 : <<include>>
@enduml\n`\n\n---\n\n## 35-cas-utilisation-equipe-admin.puml\n\n`plantuml\n@startuml sanad-uc-equipe-admin
left to right direction
skinparam shadowing false
title Cas d'utilisation — Équipe & Admin plateforme

actor "Admin cabinet" as Ac
actor "Admin WebVoice" as Aw
actor "Nouveau membre" as N

rectangle "Équipe cabinet" {
  usecase "Inviter par email" as E1
  usecase "Générer lien invitation" as E2
  usecase "Changer rôle membre" as E3
  usecase "Lister membres" as E4
  usecase "Activer compte (invitation)" as E5
}

rectangle "Admin WebVoice" {
  usecase "Lister cabinets" as A1
  usecase "Approuver cabinet" as A2
  usecase "Suspendre cabinet" as A3
  usecase "Réactiver cabinet" as A4
  usecase "Voir métriques" as A5
  usecase "Voir audit logs" as A6
}

Ac --> E1
Ac --> E2
Ac --> E3
Ac --> E4
N --> E5
Aw --> A1
Aw --> A2
Aw --> A3
Aw --> A4
Aw --> A5
Aw --> A6
E1 ..> E5 : <<include>>
@enduml\n`\n\n---\n\n## 36-sequence-creer-dossier.puml\n\n`plantuml\n@startuml
title Séquence — Créer un dossier
actor "Utilisateur" as U
participant "Frontend /cases/new" as FE
participant "API Cases" as API
database "PostgreSQL" as DB

U -> FE : Formulaire (client, type, statut…)
FE -> API : POST /api/cases
API -> API : Vérifier JWT + cabinet_id
API -> DB : INSERT case\n(reference unique)
API --> FE : Case créé
FE --> U : Redirection détail / liste
@enduml\n`\n\n---\n\n## 37-sequence-2fa.puml\n\n`plantuml\n@startuml
title Séquence — Connexion avec 2FA
actor "Utilisateur" as U
participant "Frontend" as FE
participant "API Auth" as API
database "PostgreSQL" as DB

U -> FE : email + password
FE -> API : POST /api/auth/login
API -> DB : user (totp_enabled=true)
API --> FE : { needs_2fa: true }
U -> FE : code TOTP 6 chiffres
FE -> API : POST /api/auth/login\n+ totp_code
API -> API : Vérifier TOTP
API --> FE : tokens JWT
FE --> U : /dashboard
@enduml\n`\n\n---\n\n## 38-sequence-reset-password.puml\n\n`plantuml\n@startuml
title Séquence — Mot de passe oublié
actor "Utilisateur" as U
participant "Frontend" as FE
participant "API Auth" as API
database "PostgreSQL" as DB
participant "SMTP" as Mail

U -> FE : email
FE -> API : POST /api/auth/forgot-password
API -> DB : CREATE email_token\n(reset_password)
API -> Mail : lien /reset-password?token=
Mail --> U : email
U -> FE : nouveau mot de passe
FE -> API : POST /api/auth/reset-password
API -> DB : UPDATE hashed_password\n+ token used
API --> FE : OK → login
@enduml\n`\n\n---\n\n## 39-sequence-admin-approuver.puml\n\n`plantuml\n@startuml
title Séquence — Admin WebVoice approuve un cabinet
actor "Admin WebVoice" as AW
participant "Frontend /admin" as FE
participant "API Admin" as API
database "PostgreSQL" as DB

AW -> FE : Liste cabinets pending
FE -> API : GET /api/admin/cabinets
API --> FE : liste
AW -> FE : Approuver
FE -> API : PATCH .../approve
API -> DB : cabinet.status = active\nmembres vérifiés → is_active
API --> FE : OK
@enduml\n`\n\n---\n\n## 40-sequence-ocr-pipeline.puml\n\n`plantuml\n@startuml
title Séquence — Pipeline OCR / indexation (après upload)
participant "API Documents" as API
participant "Redis" as R
participant "Celery Worker" as W
participant "MinIO" as S3
participant "OCR / Extract" as OCR
participant "ChromaDB" as CH
database "PostgreSQL" as DB

API -> DB : document status=pending
API -> R : enqueue process_document(id)
W -> R : consume
W -> DB : status=processing
W -> S3 : lire fichier
W -> OCR : extraire texte
OCR --> W : text + ocr_score
W -> DB : extracted_text,\nstatus=indexed
W -> CH : index embeddings\n(case_{cabinet}_{case})
@enduml\n`\n\n---\n\n## 41-sequence-planning.puml\n\n`plantuml\n@startuml
title Séquence — Créer un événement planning
actor "Utilisateur" as U
participant "Frontend /agenda" as FE
participant "API Workspace" as API
database "PostgreSQL" as DB

U -> FE : Titre, type, dates, dossier?
FE -> API : POST /api/workspace/agenda
API -> DB : INSERT agenda_events\n(cabinet_id, case_id?)
API --> FE : événement créé
FE --> U : Affiché dans planning
@enduml\n`\n\n---\n\n## 42-sequence-synthese.puml\n\n`plantuml\n@startuml
title Séquence — Synthèse document (avocat / admin)
actor "Avocat" as U
participant "Frontend document" as FE
participant "API Documents" as API
participant "LLM" as IA
database "PostgreSQL" as DB

U -> FE : Demander synthèse
FE -> API : GET /api/documents/{id}/synthese
API -> DB : charger extracted_text\n+ vérifier rôle ≠ assistant
API -> IA : résumer pièce
IA --> API : synthèse
API --> FE : texte synthèse
FE --> U : Affichage
@enduml\n`\n\n---\n\n## 43-activite-plaidoirie.puml\n\n`plantuml\n@startuml
title Activité — Parcours plaidoirie avocat
start
:Ouvrir /redaction;
:Dicter ou saisir le texte;
if (Corriger ?) then (oui)
  :Appel API polish;
  :Afficher texte corrigé;
  :Avocat modifie le texte;
endif
:Générer document (compose);
:Avocat vérifie / modifie\ntitre et corps;
fork
  :Exporter PDF / Imprimer;
fork again
  :Télécharger DOC;
fork again
  if (Classer ?) then (oui)
    :Choisir dossier;
    :Upload document MinIO + DB;
  endif
end fork
stop
@enduml\n`\n\n---\n\n## 44-activite-inscription.puml\n\n`plantuml\n@startuml
title Activité — Inscription & activation cabinet
start
:Remplir formulaire /register;
:Créer cabinet (pending)\n+ admin_cabinet;
:Envoyer email vérification;
:Confirmer email;
if (WebVoice approuve ?) then (oui)
  :Cabinet active;\n:Compte is_active;
  :Connexion dashboard;
else (non / attente)
  :Cabinet reste pending;
endif
stop
@enduml\n`\n\n---\n\n## 45-etat-cabinet.puml\n\n`plantuml\n@startuml
title États — Cycle de vie d'un cabinet
[*] --> PENDING : register()
PENDING --> ACTIVE : approve()\n(Admin WebVoice)
ACTIVE --> SUSPENDED : suspend()
SUSPENDED --> ACTIVE : reactivate()
ACTIVE --> [*] : (fin logique)
note right of PENDING
  Membres non pleinement actifs
  jusqu'à approbation
end note
@enduml\n`\n\n---\n\n## 46-etat-dossier.puml\n\n`plantuml\n@startuml
title États — Statut d'un dossier (Case)
[*] --> EN_COURS : create()
EN_COURS --> URGENT : update(status)
URGENT --> EN_COURS : update(status)
EN_COURS --> CLOTURE : update(status)
URGENT --> CLOTURE : update(status)
CLOTURE --> EN_COURS : réouverture
CLOTURE --> [*]
@enduml\n`\n\n---\n\n## 47-mcd-entite-relation.puml\n\n`plantuml\n@startuml
title MCD / Modèle entité-relation — Sanad
skinparam linetype ortho

entity "cabinets" as C {
  * id : UUID <<PK>>
  --
  name
  city
  address
  barreau
  status
  created_at
}

entity "users" as U {
  * id : UUID <<PK>>
  --
  email <<unique>>
  hashed_password
  full_name
  role
  is_active
  is_verified
  * cabinet_id <<FK>>
}

entity "cases" as CA {
  * id : UUID <<PK>>
  --
  reference <<unique>>
  client_name
  case_type
  status
  * cabinet_id <<FK>>
  * responsible_id <<FK>>
}

entity "documents" as D {
  * id : UUID <<PK>>
  --
  filename
  original_name
  mime_type
  storage_path
  extracted_text
  status
  * case_id <<FK>>
  * cabinet_id <<FK>>
  * uploaded_by <<FK>>
}

entity "agenda_events" as A {
  * id : UUID <<PK>>
  --
  title
  event_type
  starts_at
  case_id <<FK>>
  * cabinet_id <<FK>>
}

entity "case_tasks" as T {
  * id : UUID <<PK>>
  --
  title
  status
  due_at
  case_id <<FK>>
  * cabinet_id <<FK>>
}

entity "case_notes" as N {
  * id : UUID <<PK>>
  --
  title
  body
  case_id <<FK>>
  * cabinet_id <<FK>>
}

entity "email_tokens" as E {
  * id : UUID <<PK>>
  --
  token_hash <<unique>>
  token_type
  expires_at
  * user_id <<FK>>
}

entity "audit_logs" as L {
  * id : UUID <<PK>>
  --
  action
  user_id
  cabinet_id
  ip_address
  created_at
}

C ||--o{ U
C ||--o{ CA
U ||--o{ CA : responsible
CA ||--o{ D
C ||--o{ D
CA ||--o{ A
CA ||--o{ T
CA ||--o{ N
U ||--o{ E
@enduml\n`\n\n---\n\n## 48-composants.puml\n\n`plantuml\n@startuml
title Diagramme de composants — Sanad
skinparam componentStyle rectangle

package "Frontend Next.js" {
  [Pages publiques] as Pub
  [Espace cabinet AppShell] as App
  [Module Plaidoirie] as Red
  [Module Dossiers] as Cases
  [Module Documents] as Docs
  [Module Planning] as Plan
  [Module Équipe] as Team
  [Admin WebVoice] as Adm
}

package "Backend FastAPI" {
  [Auth API] as Auth
  [Dictation API] as Dict
  [Cases API] as CApi
  [Documents API] as DApi
  [Workspace API] as WApi
  [Team API] as TApi
  [Admin API] as AApi
  [Celery Workers] as Cel
}

database "PostgreSQL" as PG
database "MinIO" as MN
database "Redis" as RD
database "ChromaDB" as CH
cloud "LLM / Ollama" as LLM

Pub --> Auth
App --> Auth
Red --> Dict
Red --> DApi
Cases --> CApi
Docs --> DApi
Plan --> WApi
Team --> TApi
Adm --> AApi

Dict --> LLM
DApi --> MN
DApi --> PG
DApi --> Cel
CApi --> PG
WApi --> PG
Auth --> PG
Cel --> RD
Cel --> MN
Cel --> CH
Cel --> PG
@enduml\n`\n\n---\n\n## 49-packages.puml\n\n`plantuml\n@startuml
title Diagramme de packages — Organisation code Sanad

package "frontend" {
  package "app" {
    [public pages]
    [cabinet pages]
    [admin pages]
  }
  package "components"
  package "lib/api"
  package "store"
  package "hooks"
}

package "backend" {
  package "api" {
    [auth]
    [dictation]
    [cases]
    [documents]
    [workspace]
    [team]
    [admin]
  }
  package "models"
  package "services" {
    [extraction OCR]
    [IA / LLM]
    [storage MinIO]
  }
  package "workers Celery"
}

frontend --> backend : HTTP/JWT
backend.models --> PostgreSQL
backend.services --> MinIO
backend.services --> Ollama
@enduml\n`\n\n---\n\n## 50-matrice-droits.puml\n\n`plantuml\n@startuml
title Matrice des droits (vue synthétique)
skinparam shadowing false

rectangle "Fonctionnalité" as F
rectangle "Avocat" as AV #0B1F4A
rectangle "Assistant" as AS #FFFFFF
rectangle "Admin cabinet" as AC #1a3a2a

note as N1
  | Fonction | Avocat | Assistant | Admin cab. |
  | Dicter plaidoirie | Oui | Non | Oui |
  | Corriger / modifier | Oui | Non | Oui |
  | Export PDF/DOC | Oui | Oui | Oui |
  | Classer plaidoirie | Oui | Non | Oui |
  | Gérer dossiers | Oui | Oui | Oui |
  | Upload pièces | Oui | Oui | Oui |
  | Supprimer document | Oui | Non | Oui |
  | Synthèse IA | Oui | Non | Oui |
  | Planning | Oui | Oui | Oui |
  | Inviter équipe | Non | Non | Oui |
  | Approuver cabinets | Non | Non | Non (WebVoice) |
end note
@enduml\n`\n\n---\n