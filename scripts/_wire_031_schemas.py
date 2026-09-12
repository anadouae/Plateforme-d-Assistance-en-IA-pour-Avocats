# -*- coding: utf-8 -*-
"""Wire backend schemas/config for dossier judiciaire 031."""
from pathlib import Path

ROOT = Path(r"C:\Users\daurinia\Desktop\Avocat-AI-Assistance")


def write(rel: str, text: str):
    p = ROOT / rel
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    try:
        tmp.replace(p)
    except Exception:
        p.write_bytes(tmp.read_bytes())
        tmp.unlink(missing_ok=True)
    print("wrote", rel)


# —— config ——
cfg_path = ROOT / "backend/app/core/config.py"
cfg = cfg_path.read_text(encoding="utf-8")
if "CMI_MERCHANT_ID" not in cfg:
    cfg = cfg.replace(
        "    BACKUP_RETENTION_DAYS: int = 7\n",
        "    BACKUP_RETENTION_DAYS: int = 7\n\n"
        "    # Paiement Maroc — environnement CMI / PayZone / virement ICE\n"
        '    CMI_MERCHANT_ID: str = ""\n'
        '    CMI_STORE_KEY: str = ""\n'
        '    CMI_GATEWAY_URL: str = ""\n'
        "    CMI_ENABLED: bool = False\n"
        '    PAYZONE_MERCHANT_ID: str = ""\n'
        '    PAYZONE_API_KEY: str = ""\n'
        "    PAYZONE_ENABLED: bool = False\n"
        '    LEXHUB_BANK_RIB: str = ""\n'
        '    LEXHUB_BANK_NAME: str = "Attijariwafa Bank"\n'
        '    LEXHUB_BANK_BENEFICIARY: str = "WEBVOICE SARL"\n'
        '    LEXHUB_COMPANY_ICE: str = ""\n',
    )
    write("backend/app/core/config.py", cfg)
else:
    print("config already has CMI")

# —— billing ——
bill_path = ROOT / "backend/app/services/billing.py"
bill = bill_path.read_text(encoding="utf-8")
if '"id": "virement"' not in bill:
    old = '''MOROCCO_PAYMENT_METHODS = [
    {
        "id": "cmi",
        "name": "Carte bancaire (CMI)",
        "name_ar": "بطاقة بنكية (CMI)",
        "status": "coming_soon",
        "blurb": "Paiement sécurisé via le Centre Monétique Interbancaire.",
    },
    {
        "id": "payzone",
        "name": "PayZone",
        "name_ar": "PayZone",
        "status": "coming_soon",
        "blurb": "Paiement local multi-canaux (carte, mobile).",
    },
    {
        "id": "stripe",
        "name": "Carte internationale",
        "name_ar": "بطاقة دولية",
        "status": "coming_soon",
        "blurb": "Visa / Mastercard — cabinets multi-pays.",
    },
]'''
    new = '''MOROCCO_PAYMENT_METHODS = [
    {
        "id": "virement",
        "name": "Virement bancaire + facture ICE",
        "name_ar": "تحويل بنكي + فاتورة ICE",
        "status": "available",
        "blurb": "Référence LexHub + RIB — activation manuelle sous 24–48 h ouvrés jours.",
    },
    {
        "id": "cmi",
        "name": "Carte bancaire (CMI)",
        "name_ar": "بطاقة بنكية (CMI)",
        "status": "env_ready",
        "blurb": "Environnement prêt — activation opérateur CMI (merchant ID).",
    },
    {
        "id": "payzone",
        "name": "PayZone",
        "name_ar": "PayZone",
        "status": "env_ready",
        "blurb": "Environnement prêt — activation opérateur PayZone.",
    },
    {
        "id": "stripe",
        "name": "Carte internationale",
        "name_ar": "بطاقة دولية",
        "status": "coming_soon",
        "blurb": "Visa / Mastercard — cabinets multi-pays.",
    },
]'''
    if old not in bill:
        print("MISS morocco methods")
    else:
        write("backend/app/services/billing.py", bill.replace(old, new, 1))
else:
    print("billing virement already")

# —— DocumentResponse ——
sch_path = ROOT / "backend/app/schemas/__init__.py"
sch = sch_path.read_text(encoding="utf-8")
marker = "kind: str = \"file\"\n    error_message: Optional[str] = None\n\n    class Config:\n        from_attributes = True\n\n\nclass DocumentDetailResponse"
if "inventory_number: Optional[int] = None\n    exhibit_type" not in sch:
    sch = sch.replace(
        marker,
        "kind: str = \"file\"\n"
        "    error_message: Optional[str] = None\n"
        "    inventory_number: Optional[int] = None\n"
        "    exhibit_type: Optional[str] = None\n"
        "    produced_by: Optional[str] = None\n"
        "    exhibit_version: Optional[str] = None\n"
        "    cited_in_plea: Optional[str] = None\n\n"
        "    class Config:\n"
        "        from_attributes = True\n\n\n"
        "class DocumentDetailResponse",
        1,
    )
    print("doc response fields")
else:
    print("doc response already")

# CaseTask assignee
if "assignee_id: Optional[str] = Field(None, max_length=36)" not in sch:
    sch = sch.replace(
        '    due_at: Optional[datetime] = None\n\n\nclass CaseTaskUpdate',
        '    due_at: Optional[datetime] = None\n'
        '    assignee_id: Optional[str] = Field(None, max_length=36)\n\n\nclass CaseTaskUpdate',
        1,
    )
    sch = sch.replace(
        '    due_at: Optional[datetime] = None\n\n\nclass CaseTaskResponse',
        '    due_at: Optional[datetime] = None\n'
        '    assignee_id: Optional[str] = Field(None, max_length=36)\n\n\nclass CaseTaskResponse',
        1,
    )
    sch = sch.replace(
        '    status: str\n    due_at: Optional[datetime] = None\n    created_at: datetime\n    updated_at: datetime\n\n    class Config:\n        from_attributes = True\n\n\nclass AgendaEventCreate',
        '    status: str\n    due_at: Optional[datetime] = None\n'
        '    assignee_id: Optional[str] = None\n'
        '    assignee_name: Optional[str] = None\n'
        '    created_at: datetime\n    updated_at: datetime\n\n'
        '    class Config:\n        from_attributes = True\n\n\nclass AgendaEventCreate',
        1,
    )
    print("task assignee")
else:
    print("task assignee already")

# Plaidoirie draft fields
if "trust_badge: str = \"a_relire\"" not in sch:
    sch = sch.replace(
        '    status: str = Field("draft", pattern="^(draft|validated)$")\n\n\nclass PlaidoirieDraftUpdate',
        '    status: str = Field("draft", pattern="^(draft|validated)$")\n'
        '    output_mode: Optional[str] = Field(None, pattern="^(orale|ecrite)$")\n'
        '    sources: list[dict] = Field(default_factory=list)\n\n\nclass PlaidoirieDraftUpdate',
        1,
    )
    sch = sch.replace(
        '    case_id: Optional[str] = None  # "" ou null = sans dossier\n\n\nclass PlaidoirieDraftResponse',
        '    case_id: Optional[str] = None  # "" ou null = sans dossier\n'
        '    title: Optional[str] = Field(None, min_length=1, max_length=512)\n'
        '    body: Optional[str] = None\n'
        '    output_mode: Optional[str] = Field(None, pattern="^(orale|ecrite)$")\n'
        '    sources: Optional[list[dict]] = None\n\n\nclass PlaidoirieDraftResponse',
        1,
    )
    sch = sch.replace(
        '    pinned: bool = False\n    created_at: datetime\n    updated_at: datetime\n\n    class Config:\n        from_attributes = True\n\n\nclass PlaidoirieAssignRequest',
        '    pinned: bool = False\n'
        '    output_mode: Optional[str] = None\n'
        '    citations: list[dict] = Field(default_factory=list)\n'
        '    sources: list[dict] = Field(default_factory=list)\n'
        '    validated_by: Optional[str] = None\n'
        '    validated_at: Optional[datetime] = None\n'
        '    trust_badge: str = "a_relire"\n'
        '    created_at: datetime\n    updated_at: datetime\n\n'
        '    class Config:\n        from_attributes = True\n\n\nclass PlaidoirieAssignRequest',
        1,
    )
    print("plea fields")
else:
    print("plea fields already")

write("backend/app/schemas/__init__.py", sch)
print("DONE schemas")
