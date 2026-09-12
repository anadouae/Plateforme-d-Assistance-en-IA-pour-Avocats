"""Extend schemas + cases response for dossier judiciaire vivant."""
from pathlib import Path

schemas = Path(r"C:\Users\daurinia\Desktop\Avocat-AI-Assistance\backend\app\schemas\__init__.py")
t = schemas.read_text(encoding="utf-8")

CASE_EXTRA = """
    court_file_number: Optional[str] = Field(None, max_length=80)
    judge_name: Optional[str] = Field(None, max_length=120)
    chamber: Optional[str] = Field(None, max_length=120)
    greffe: Optional[str] = Field(None, max_length=120)
    procedure_status: Optional[str] = Field(None, max_length=40)
    assistant_id: Optional[str] = Field(None, max_length=36)
    last_decision_type: Optional[str] = Field(None, max_length=80)
    last_decision_date: Optional[datetime] = None
    notification_date: Optional[datetime] = None
    appeal_deadline_at: Optional[datetime] = None
    appeal_deadline_days: Optional[int] = None
"""

if "court_file_number" not in t:
    # CaseCreate — after court_city
    t = t.replace(
        "    court_city: Optional[str] = Field(None, max_length=80)\n    client_role: Optional[str] = Field(None, max_length=40)",
        "    court_city: Optional[str] = Field(None, max_length=80)\n"
        + CASE_EXTRA
        + "    client_role: Optional[str] = Field(None, max_length=40)",
        1,
    )
    t = t.replace(
        "    court_city: Optional[str] = None\n    client_role: Optional[str] = None",
        "    court_city: Optional[str] = None\n"
        "    court_file_number: Optional[str] = None\n"
        "    judge_name: Optional[str] = None\n"
        "    chamber: Optional[str] = None\n"
        "    greffe: Optional[str] = None\n"
        "    procedure_status: Optional[str] = None\n"
        "    assistant_id: Optional[str] = None\n"
        "    last_decision_type: Optional[str] = None\n"
        "    last_decision_date: Optional[datetime] = None\n"
        "    notification_date: Optional[datetime] = None\n"
        "    appeal_deadline_at: Optional[datetime] = None\n"
        "    appeal_deadline_days: Optional[int] = None\n"
        "    client_role: Optional[str] = None",
        2,  # CaseUpdate + CaseResponse hopefully
    )

# Agenda event type pattern expand
t = t.replace(
    'pattern="^(audience|deadline|rdv|other)$"',
    'pattern="^(audience|deadline|rdv|notification|recours|expertise|mediation|other)$"',
)

# Document response extras — find DocumentResponse
if "inventory_number" not in t:
    # append near end before last classes or after DocumentResponse
    marker = "class DocumentResponse"
    idx = t.find(marker)
    if idx > 0:
        # find created_at in DocumentResponse
        sub = t[idx:idx+800]
        if "inventory_number" not in sub:
            t = t.replace(
                "class DocumentResponse(BaseModel):",
                "class DocumentResponse(BaseModel):",
                1,
            )
            # add fields before kind if present
            if "kind: Optional[str]" in t:
                t = t.replace(
                    "    kind: Optional[str] = None\n\n    class Config:",
                    "    kind: Optional[str] = None\n"
                    "    inventory_number: Optional[int] = None\n"
                    "    exhibit_type: Optional[str] = None\n"
                    "    produced_by: Optional[str] = None\n"
                    "    exhibit_version: Optional[str] = None\n"
                    "    cited_in_plea: Optional[str] = None\n\n"
                    "    class Config:",
                    1,
                )

# Document update schema
if "class DocumentMetaUpdate" not in t:
    t += '''


class DocumentMetaUpdate(BaseModel):
    inventory_number: Optional[int] = None
    exhibit_type: Optional[str] = Field(None, max_length=60)
    produced_by: Optional[str] = Field(None, max_length=40)
    exhibit_version: Optional[str] = Field(None, max_length=40)
    cited_in_plea: Optional[str] = Field(None, max_length=255)


class CaseCommentCreate(BaseModel):
    body: str = Field(..., min_length=1, max_length=4000)


class CaseCommentResponse(BaseModel):
    id: str
    case_id: str
    body: str
    author_name: str
    created_at: datetime

    class Config:
        from_attributes = True


class PaymentTransferCreate(BaseModel):
    plan_slug: str = Field(..., min_length=2, max_length=64)
    billing_cycle: str = Field("monthly", pattern="^(monthly|yearly)$")
    notes: Optional[str] = Field(None, max_length=1000)


class PaymentTransferResponse(BaseModel):
    id: str
    reference: str
    amount_mad: int
    plan_slug: str
    billing_cycle: str
    status: str
    ice: Optional[str] = None
    bank_rib: Optional[str] = None
    bank_name: Optional[str] = None
    beneficiary: Optional[str] = None
    instructions: str
    created_at: datetime
'''

tmp = schemas.with_suffix(".py.tmp")
tmp.write_text(t, encoding="utf-8")
tmp.replace(schemas)
print("schemas", "court_file_number" in t, "DocumentMetaUpdate" in t, "PaymentTransferCreate" in t)
