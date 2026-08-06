# Codes PlantUML — Sanad (à copier / prévisualiser)

Ouvre chaque fichier `.puml` dans Cursor (extension PlantUML)  
ou colle le code sur https://www.plantuml.com/plantuml/uml

| Fichier | Diagramme |
|---------|-----------|
| `20-architecture-principale.puml` | Architecture principale |
| `21-stack-technologique.puml` | Stack technologique |
| `22-cas-utilisation-plaidoirie.puml` | UC Plaidoirie (cœur) |
| `23-cas-utilisation-assistant.puml` | UC Assistant juridique |
| `24-deploiement-docker.puml` | Déploiement Docker / VPS |

Les anciens fichiers `14-` à `19-` restent disponibles ; **préférer 20–24** (alignés produit actuel : plaidoirie, sans chat au centre).

---

## 1. Architecture principale

```plantuml
@startuml sanad-architecture-principale
skinparam shadowing false
skinparam backgroundColor #F5F0E8

title Sanad — Architecture principale

actor "Avocat" as Avocat
actor "Assistant\njuridique" as Assist
actor "Admin\ncabinet" as AdminC

rectangle "Navigateur Web\n(FR / AR / EN)" as Browser #0B1F4A
rectangle "Frontend\nNext.js · TypeScript · Tailwind\n:3000" as Front
rectangle "Backend API\nFastAPI · JWT · Multi-tenant\n:8001" as API #0B1F4A
rectangle "Workers Celery\n(OCR / indexation)" as Celery

database "PostgreSQL\n:5432" as PG
database "MinIO\n:9000" as MinIO
database "Redis\n:6379" as Redis
database "ChromaDB" as Chroma
cloud "IA\nOllama (+ cloud)\nCorrection plaidoirie" as LLM

Avocat --> Browser
Assist --> Browser
AdminC --> Browser
Browser --> Front : HTTPS
Front --> API : REST + JWT
API --> PG
API --> MinIO
API --> Redis
API --> LLM
API --> Chroma
Celery --> Redis
Celery --> MinIO
Celery --> Chroma

note bottom of Front
  Cœur UI : Plaidoirie · Dossiers · Documents
  Planning · Équipe · Paramètres
  Chat retiré du menu principal
end note
@enduml
```

---

## 2. Stack technologique

```plantuml
@startuml sanad-stack-technologique-v2
skinparam shadowing false
title Sanad — Stack technologique

package "Présentation" {
  card "Next.js" as next
  card "TypeScript" as ts
  card "Tailwind CSS" as tw
  card "Zustand" as zu
}

package "API & métier" {
  card "FastAPI" as fastapi
  card "SQLAlchemy + Alembic" as sa
  card "JWT" as jwt
  card "Celery" as celery
  card "Dictation polish/compose" as dict
}

package "Données" {
  card "PostgreSQL 16" as pg
  card "MinIO" as minio
  card "Redis 7" as redis
  card "ChromaDB" as chroma
}

package "IA" {
  card "Ollama" as ollama
  card "LLM cloud (fallback)" as cloud
  card "OCR" as ocr
}

package "Infrastructure" {
  card "Docker Compose" as docker
  card "VPS Debian" as vps
}

@enduml
```

---

## 3. Cas d’utilisation — Plaidoirie

```plantuml
@startuml
left to right direction
title UC — Plaidoirie

actor Avocat
actor "Assistant juridique" as Assist

rectangle Sanad {
  usecase "Dicter" as UC1
  usecase "Transcrire & corriger" as UC2
  usecase "Modifier" as UC3
  usecase "Exporter PDF/DOC" as UC4
  usecase "Classer dossier" as UC5
  usecase "Consulter plaidoiries" as UC6
}

Avocat --> UC1
Avocat --> UC2
Avocat --> UC3
Avocat --> UC4
Avocat --> UC5
Assist --> UC6
Assist --> UC4
@enduml
```

---

## 4. Cas d’utilisation — Assistant

```plantuml
@startuml
left to right direction
title UC — Assistant juridique

actor "Assistant juridique" as A

rectangle "Peut faire" {
  usecase "Préparer dossiers" as U1
  usecase "Uploader pièces" as U2
  usecase "Suivre planning" as U3
  usecase "Consulter plaidoiries" as U4
  usecase "Exporter PDF/DOC" as U5
}

rectangle "Ne fait pas" #FFE4E1 {
  usecase "Dicter la plaidoirie" as N1
  usecase "Modifier le texte avocat" as N2
}

A --> U1
A --> U2
A --> U3
A --> U4
A --> U5
@enduml
```
