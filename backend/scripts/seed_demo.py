#!/usr/bin/env python3
"""Optional demo seed — run manually: python -m scripts.seed_demo"""
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

DEMO_BAIL_TEXT = """
CONTRAT DE BAIL COMMERCIAL
Entre la Société ATLAS SARL et Monsieur Ahmed BENALI.
Article 2 — Durée : trois (3) années, du 01/07/2026 au 01/07/2029.
Article 3 — Loyer : 12 000 MAD par mois.
Article 4 — Résiliation anticipée : indemnité de 3 mois de loyer.
"""


def seed():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "demo@sanad.ma").first()
        if not user:
            cabinet = Cabinet(
                name="Cabinet Démo Atlas",
                city="Casablanca",
                address="123 Bd Mohammed V",
                barreau="Casablanca",
                status=CabinetStatus.ACTIVE,
            )
            db.add(cabinet)
            db.flush()
            user = User(
                email="demo@sanad.ma",
                hashed_password=hash_password("Sanad2026!"),
                full_name="Me Douae El Assal",
                phone="+212600000000",
                role=UserRole.ADMIN_CABINET,
                is_active=True,
                is_verified=True,
                cabinet_id=cabinet.id,
            )
            db.add(user)
            db.flush()
            print("Created demo@sanad.ma / Sanad2026!")

        if not db.query(Case).filter(Case.reference == "WV-2026-0001").first():
            case = Case(
                reference="WV-2026-0001",
                client_name="Ahmed B.",
                case_type="Bail commercial",
                status="En cours",
                description="Litige relatif aux obligations locatives",
                cabinet_id=user.cabinet_id,
                responsible_id=user.id,
            )
            db.add(case)
            db.flush()
            db.add(
                Document(
                    filename="demo-bail.txt",
                    original_name="bail_commercial.pdf",
                    mime_type="application/pdf",
                    file_size=4096,
                    storage_path="./uploads/demo/placeholder",
                    extracted_text=DEMO_BAIL_TEXT.strip(),
                    ocr_score=96,
                    status=DocumentStatus.INDEXED,
                    case_id=case.id,
                    cabinet_id=user.cabinet_id,
                    uploaded_by=user.id,
                )
            )
            print("Created demo case WV-2026-0001")

        if not db.query(User).filter(User.email == "admin@webvoice.ma").first():
            platform = db.query(Cabinet).filter(Cabinet.name == "WebVoice Platform").first()
            if not platform:
                platform = Cabinet(
                    name="WebVoice Platform",
                    city="Casablanca",
                    address="WebVoice HQ",
                    barreau="N/A",
                    status=CabinetStatus.ACTIVE,
                )
                db.add(platform)
                db.flush()
            db.add(
                User(
                    email="admin@webvoice.ma",
                    hashed_password=hash_password("WebVoice2026!"),
                    full_name="Admin WebVoice",
                    role=UserRole.ADMIN_WEBVOICE,
                    is_active=True,
                    is_verified=True,
                    cabinet_id=platform.id,
                )
            )
            print("Created admin@webvoice.ma / WebVoice2026!")

        db.commit()
        print("Demo seed complete.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
