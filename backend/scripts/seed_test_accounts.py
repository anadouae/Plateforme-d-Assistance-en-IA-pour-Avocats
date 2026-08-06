#!/usr/bin/env python3
"""
Comptes de test Sanad — prêts à l'emploi (actifs, vérifiés).

Usage :
  cd backend
  python scripts/seed_test_accounts.py

Avec Docker :
  docker compose exec backend python scripts/seed_test_accounts.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models import (
    Cabinet,
    CabinetStatus,
    Case,
    Document,
    DocumentStatus,
    User,
    UserRole,
)

# ─── Comptes créés ───────────────────────────────────────────────
# Tous : mot de passe indiqué · is_active=True · is_verified=True
ACCOUNTS = [
    {
        "email": "demo@sanad.ma",
        "password": "Sanad2026!",
        "full_name": "Me Douae El Assal",
        "role": UserRole.ADMIN_CABINET,
        "cabinet_key": "atlas",
        "phone": "+212600000001",
    },
    {
        "email": "avocat@sanad.ma",
        "password": "Sanad2026!",
        "full_name": "Me Youssef Alami",
        "role": UserRole.AVOCAT,
        "cabinet_key": "atlas",
        "phone": "+212600000002",
    },
    {
        "email": "assistant@sanad.ma",
        "password": "Sanad2026!",
        "full_name": "Sara Bennani",
        "role": UserRole.ASSISTANT,
        "cabinet_key": "atlas",
        "phone": "+212600000003",
    },
    {
        "email": "test@cabinet-rabat.ma",
        "password": "Test2026!",
        "full_name": "Me Karim Idrissi",
        "role": UserRole.ADMIN_CABINET,
        "cabinet_key": "rabat",
        "phone": "+212600000004",
    },
    {
        "email": "admin@webvoice.ma",
        "password": "WebVoice2026!",
        "full_name": "Admin WebVoice",
        "role": UserRole.ADMIN_WEBVOICE,
        "cabinet_key": "webvoice",
        "phone": "+212600000099",
    },
]

CABINETS = {
    "atlas": {
        "name": "Cabinet Démo Atlas",
        "city": "Casablanca",
        "address": "123 Bd Mohammed V, Casablanca",
        "barreau": "Casablanca",
    },
    "rabat": {
        "name": "Cabinet Test Rabat",
        "city": "Rabat",
        "address": "45 Av. Hassan II, Rabat",
        "barreau": "Rabat",
    },
    "webvoice": {
        "name": "WebVoice Platform",
        "city": "Casablanca",
        "address": "WebVoice HQ",
        "barreau": "N/A",
    },
}

DEMO_BAIL_TEXT = """
CONTRAT DE BAIL COMMERCIAL
Entre la Société ATLAS SARL, représentée par M. Hassan TAZI, et Monsieur Ahmed BENALI.
Article 2 — Durée : trois (3) années, du 01/07/2026 au 01/07/2029.
Article 3 — Loyer : 12 000 MAD par mois, payable d'avance.
Article 4 — Résiliation anticipée : indemnité de 3 mois de loyer.
Article 5 — Arbitrage : tout litige sera soumis à l'arbitrage de la Chambre de commerce.
"""

DEMO_MISE_EN_DEMEURE = """
MISE EN DEMEURE
Casablanca, le 15/06/2026
Monsieur Ahmed BENALI
Objet : Impayé de loyer — 36 000 MAD
Vous disposez d'un délai de quinze (15) jours pour régulariser la situation,
sous peine de résiliation du bail et de poursuites judiciaires.
Société ATLAS SARL
"""

DEMO_ARABIC_TEXT = """
عقد كراء تجاري
بين شركة أطلس ش.م.م و السيد أحمد بنعلي
المدة: ثلاث سنوات من 01/07/2026 إلى 01/07/2029
الأجرة الشهرية: 12000 درهم
"""


def _get_or_create_cabinet(db, key: str) -> Cabinet:
    info = CABINETS[key]
    cabinet = db.query(Cabinet).filter(Cabinet.name == info["name"]).first()
    if cabinet:
        cabinet.status = CabinetStatus.ACTIVE
        return cabinet
    cabinet = Cabinet(
        name=info["name"],
        city=info["city"],
        address=info["address"],
        barreau=info["barreau"],
        status=CabinetStatus.ACTIVE,
    )
    db.add(cabinet)
    db.flush()
    print(f"  + Cabinet : {cabinet.name}")
    return cabinet


# Secret TOTP de démo (admin plateforme) — Google Authenticator / Authy
# Code à 6 chiffres généré avec ce secret (pas un « RSA » hardware).
DEMO_ADMIN_TOTP_SECRET = "JBSWY3DPEHPK3PXP"


def _get_or_create_user(db, account: dict, cabinet: Cabinet) -> User:
    user = db.query(User).filter(User.email == account["email"]).first()
    if user:
        user.is_active = True
        user.is_verified = True
        user.hashed_password = hash_password(account["password"])
        user.role = account["role"]
        user.cabinet_id = cabinet.id
        print(f"  ~ Mis à jour : {account['email']}")
    else:
        user = User(
            email=account["email"],
            hashed_password=hash_password(account["password"]),
            full_name=account["full_name"],
            phone=account.get("phone"),
            role=account["role"],
            is_active=True,
            is_verified=True,
            cabinet_id=cabinet.id,
        )
        db.add(user)
        db.flush()
        print(f"  + Créé : {account['email']} / {account['password']} ({account['role'].value})")

    # Admin plateforme : Magic Link / email (pas de TOTP téléphone obligatoire)
    if account["role"] == UserRole.ADMIN_WEBVOICE:
        user.totp_secret = None
        user.totp_enabled = False
        print("  ! Admin : connexion Magic Link (email) ou mot de passe — sans 2FA téléphone")
    return user


def _seed_demo_cases(db, cabinet: Cabinet, admin: User) -> None:
    if db.query(Case).filter(Case.reference == "WV-2026-0001", Case.cabinet_id == cabinet.id).first():
        return

    case1 = Case(
        reference="WV-2026-0001",
        client_name="Ahmed BENALI",
        case_type="Bail commercial",
        status="En cours",
        description="Litige relatif aux impayés de loyer et résiliation anticipée",
        cabinet_id=cabinet.id,
        responsible_id=admin.id,
    )
    db.add(case1)
    db.flush()

    docs = [
        ("bail_commercial.pdf", DEMO_BAIL_TEXT.strip(), 96),
        ("mise_en_demeure.pdf", DEMO_MISE_EN_DEMEURE.strip(), 94),
        ("contrat_arabe.pdf", DEMO_ARABIC_TEXT.strip(), 88),
    ]
    for i, (name, text, score) in enumerate(docs):
        db.add(
            Document(
                filename=f"demo-{i}.txt",
                original_name=name,
                mime_type="application/pdf",
                file_size=len(text.encode()),
                storage_path=f"./uploads/demo/{name}",
                extracted_text=text,
                ocr_score=score,
                status=DocumentStatus.INDEXED,
                case_id=case1.id,
                cabinet_id=cabinet.id,
                uploaded_by=admin.id,
            )
        )
    print("  + Dossier WV-2026-0001 avec 3 documents de test")

    case2 = Case(
        reference="WV-2026-0002",
        client_name="Société MAROC EXPORT",
        case_type="Droit commercial",
        status="Ouvert",
        description="Contentieux contractuel — livraison marchandises",
        cabinet_id=cabinet.id,
        responsible_id=admin.id,
    )
    db.add(case2)
    db.flush()
    print("  + Dossier WV-2026-0002 (vide — pour tester upload)")


def seed():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--with-demo-data", action="store_true")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        print("\n=== Sanad — création des comptes de test ===\n")
        cabinets: dict[str, Cabinet] = {}
        for key in CABINETS:
            cabinets[key] = _get_or_create_cabinet(db, key)

        users: dict[str, User] = {}
        for account in ACCOUNTS:
            cabinet = cabinets[account["cabinet_key"]]
            users[account["email"]] = _get_or_create_user(db, account, cabinet)

        if args.with_demo_data:
            _seed_demo_cases(db, cabinets["atlas"], users["demo@sanad.ma"])

        db.commit()
        print("\n=== Comptes prêts — connectez-vous sur http://localhost:3000/login ===\n")
        print("| Email                  | Mot de passe    | Rôle              |")
        print("|------------------------|-----------------|-------------------|")
        for a in ACCOUNTS:
            print(f"| {a['email']:<22} | {a['password']:<15} | {a['role'].value:<17} |")
        print()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
