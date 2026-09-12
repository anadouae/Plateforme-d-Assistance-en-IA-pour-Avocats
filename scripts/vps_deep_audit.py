#!/usr/bin/env python3
"""
Sanad / LexHub — audit profond (prod VPS).
Lance: python scripts/vps_deep_audit.py

Vérifie: stack, clés (présence), chiffrement, STT, OCR/PDF, LLM synthèse, doc cible.
N'affiche JAMAIS les secrets.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone

import paramiko

HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"
DOC_ID = "0566cb46-cb05-4b8f-b0ce-9b06300d07a0"
COMPOSE = "docker compose -f docker-compose.yml -f docker-compose.lexhub.yml"


def ssh_run(c: paramiko.SSHClient, cmd: str, timeout: int = 180) -> str:
    _, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode(errors="replace")
    err = e.read().decode(errors="replace")
    return (out + ("\n" + err if err.strip() else "")).strip()


def main() -> None:
    report: dict = {
        "when": datetime.now(timezone.utc).isoformat(),
        "host": HOST,
        "checks": {},
        "verdict": {},
    }

    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, username="root", password=PASSWORD, timeout=60, banner_timeout=120)

    # 1) Containers
    ps = ssh_run(c, f"cd {REMOTE} && {COMPOSE} ps --format '{{{{.Name}}}}|{{{{.Status}}}}'")
    services = {}
    for line in ps.splitlines():
        if "|" in line:
            name, st = line.split("|", 1)
            services[name.strip()] = st.strip()
    report["checks"]["containers"] = services
    need = ["backend", "celery-worker", "frontend", "postgres", "redis", "minio"]
    report["verdict"]["stack_up"] = all(
        any(n in k and "Up" in v for k, v in services.items()) for n in need
    )

    # 2) Env presence (no values)
    env_probe = ssh_run(
        c,
        f"""
cd {REMOTE}
{COMPOSE} exec -T backend python - <<'PY'
from app.core.config import settings
keys = [
  ("ENCRYPTION_KEY", bool(settings.ENCRYPTION_KEY)),
  ("GROQ_API_KEY", bool(settings.GROQ_API_KEY)),
  ("MISTRAL_API_KEY", bool(settings.MISTRAL_API_KEY)),
  ("GEMINI_API_KEY", bool(settings.GEMINI_API_KEY)),
  ("KIMI_API_KEY", bool(settings.KIMI_API_KEY)),
  ("DEEPSEEK_API_KEY", bool(settings.DEEPSEEK_API_KEY)),
  ("WHISPER_ENABLED", settings.WHISPER_ENABLED),
  ("DICTATION_STT_PREFER_GROQ", settings.DICTATION_STT_PREFER_GROQ),
  ("DICTATION_LOCAL_ONLY", settings.DICTATION_LOCAL_ONLY),
  ("DICTATION_POLISH_USE_LLM", settings.DICTATION_POLISH_USE_LLM),
  ("OCR_CLOUD_ENABLED", settings.OCR_CLOUD_ENABLED),
  ("LLM_USE_FREE_ROUTER", settings.LLM_USE_FREE_ROUTER),
  ("LLM_CHAT_USE_OLLAMA", settings.LLM_CHAT_USE_OLLAMA),
  ("GROQ_MODEL", settings.GROQ_MODEL),
  ("GROQ_WHISPER_MODEL", settings.GROQ_WHISPER_MODEL),
  ("GEMINI_MODEL", settings.GEMINI_MODEL),
  ("MISTRAL_MODEL", settings.MISTRAL_MODEL),
  ("WHISPER_MODEL", settings.WHISPER_MODEL),
]
for k,v in keys:
    print(f"{{k}}={{v}}")
PY
""",
        timeout=90,
    )
    flags = {}
    for line in env_probe.splitlines():
        if "=" in line and not line.startswith("warning"):
            k, v = line.split("=", 1)
            flags[k.strip()] = v.strip()
    report["checks"]["config"] = flags

    # 3) Encryption alignment backend vs worker
    enc = ssh_run(
        c,
        f"""
cd {REMOTE}
B=$({COMPOSE} exec -T backend printenv ENCRYPTION_KEY | tr -d '\\r')
W=$({COMPOSE} exec -T celery-worker printenv ENCRYPTION_KEY | tr -d '\\r')
python3 - <<PY
b='''$B'''.strip(); w='''$W'''.strip()
print('same', b==w and len(b)>20)
print('b_len', len(b), 'w_len', len(w))
print('b_prefix', b[:4] if b else None, 'w_prefix', w[:4] if w else None)
PY
""",
    )
    report["checks"]["encryption_sync"] = enc
    report["verdict"]["encryption_ok"] = "same True" in enc

    # 4) Decrypt + open target PDF
    pdf = ssh_run(
        c,
        f"""
cd {REMOTE}
{COMPOSE} exec -T celery-worker python - <<'PY'
from app.core.database import SessionLocal
from app.models import Document
from app.services.object_storage import read_file
import fitz
db=SessionLocal()
doc=db.query(Document).filter(Document.id=='{DOC_ID}').first()
print('doc_status', getattr(doc.status,'value',doc.status) if doc else None)
print('ocr_score', doc.ocr_score if doc else None)
print('chars', len(doc.extracted_text or '') if doc else 0)
content=read_file(doc.storage_path)
print('magic', content[:8])
print('is_pdf', content[:5]==b'%PDF-')
print('is_fernet_raw', content[:6]==b'gAAAAA')
d=fitz.open(stream=content, filetype='pdf')
print('pages', len(d))
d.close()
db.close()
PY
""",
        timeout=90,
    )
    report["checks"]["target_pdf"] = pdf
    report["verdict"]["pdf_decrypt_ok"] = "is_pdf True" in pdf and "is_fernet_raw False" in pdf

    # 5) LLM router smoke (one short call)
    llm = ssh_run(
        c,
        f"""
cd {REMOTE}
{COMPOSE} exec -T backend python - <<'PY'
from app.services.free_llm_router import chat_free_tier
import time
t0=time.time()
try:
    text, provider = chat_free_tier(
        prompt="ping",
        system="Reply with one word only: OK",
        preferred="auto",
        allow_ollama=False,
    )
    print('ok', bool(text))
    print('provider', provider)
    print('reply', (text or '')[:40].replace('\\n',' '))
    print('ms', int((time.time()-t0)*1000))
except Exception as e:
    print('ok', False)
    print('error', type(e).__name__, str(e)[:200])
PY
""",
        timeout=120,
    )
    report["checks"]["llm_ping"] = llm
    report["verdict"]["llm_ok"] = "ok True" in llm

    # 6) Synthesis on target doc
    synth = ssh_run(
        c,
        f"""
cd {REMOTE}
{COMPOSE} exec -T backend python - <<'PY'
from app.core.database import SessionLocal
from app.models import Document
from app.services.agent import generate_synthesis
from app.services.extraction import _looks_like_broken_arabic_snippet
import time
db=SessionLocal()
doc=db.query(Document).filter(Document.id=='{DOC_ID}').first()
text=doc.extracted_text or ''
t0=time.time()
data=generate_synthesis(doc.original_name, text, language='ar')
ms=int((time.time()-t0)*1000)
summary=(data.get('summary') or '')
risks=data.get('risk_clauses') or []
dates=data.get('key_dates') or []
broken=sum(1 for r in risks if _looks_like_broken_arabic_snippet(str(r)))
print('summary_len', len(summary))
print('is_fallback', 'تعذر التلخيص' in summary or 'Synthèse indisponible' in summary)
print('risks', len(risks), 'broken_risks', broken)
print('dates', dates[:5])
print('ms', ms)
print('head', summary[:120].replace('\\n',' '))
db.close()
PY
""",
        timeout=180,
    )
    report["checks"]["synthesis"] = synth
    report["verdict"]["synth_ok"] = "is_fallback False" in synth and "summary_len" in synth

    # 7) STT status endpoint shape + groq whisper reachability (no audio required for status)
    stt = ssh_run(
        c,
        f"""
cd {REMOTE}
{COMPOSE} exec -T backend python - <<'PY'
from app.core.config import settings
from app.services import whisper_stt
print('prefer_groq', settings.DICTATION_STT_PREFER_GROQ)
print('local_only', settings.DICTATION_LOCAL_ONLY)
print('groq_key', bool(settings.GROQ_API_KEY))
print('whisper_enabled', settings.WHISPER_ENABLED)
print('whisper_model', settings.WHISPER_MODEL)
print('groq_whisper_model', settings.GROQ_WHISPER_MODEL)
# tiny wav silence probe if possible
import struct, io, wave
buf=io.BytesIO()
with wave.open(buf,'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(16000)
    w.writeframes(b'\\x00\\x00'*16000)  # 1s silence
raw=buf.getvalue()
try:
    text, provider = whisper_stt.transcribe_audio_bytes(raw, filename='probe.wav', language='ar')
    print('stt_provider', provider)
    print('stt_text_len', len(text or ''))
    print('stt_ok', True)
except Exception as e:
    print('stt_ok', False)
    print('stt_error', type(e).__name__, str(e)[:180])
PY
""",
        timeout=180,
    )
    report["checks"]["stt"] = stt
    report["verdict"]["stt_pipeline_reachable"] = "stt_ok True" in stt or "stt_provider" in stt

    # 8) HTTPS
    http = ssh_run(c, "curl -sf -o /dev/null -w '%{http_code}' https://lexhub.space/")
    report["checks"]["https"] = http
    report["verdict"]["site_200"] = http.strip() == "200"

    # 9) Recent celery/backend errors (last 15 min signal)
    logs = ssh_run(
        c,
        f"""
cd {REMOTE}
{COMPOSE} logs backend --since 30m 2>&1 | grep -iE '429|FileData|ENCRYPTION|failed permanently|model_not_found|Rate limit' | tail -20
echo '---'
{COMPOSE} logs celery-worker --since 30m 2>&1 | grep -iE '429|FileData|ENCRYPTION|failed permanently' | tail -15
""",
        timeout=60,
    )
    report["checks"]["recent_errors"] = logs[-4000:]

    c.close()

    # Scorecard
    v = report["verdict"]
    score = sum(1 for x in v.values() if x is True)
    total = len(v)
    report["scorecard"] = f"{score}/{total}"

    out_path = "docs/AUDIT_PROFOND_LEXHUB.json"
    # also human markdown
    md_lines = [
        f"# Audit profond LexHub — {report['when']}",
        "",
        f"**Score:** {report['scorecard']}",
        "",
        "## Verdicts",
    ]
    for k, val in v.items():
        md_lines.append(f"- {'OK' if val else 'FAIL'} — `{k}`")
    md_lines += ["", "## Lecture rapide", ""]
    md_lines.append(
        "- **IA saturée** = quotas free-tier (429) ou modèle HS : le routeur tourne Mistral→Groq→Gemini… ; "
        "si tous échouent, tu vois « تعذر التلخيص » même si le PDF est OK."
    )
    md_lines.append(
        "- **Voix** = Chrome Web Speech en live ; Whisper/Groq = chemin serveur (fichier / fallback)."
    )
    md_lines.append(
        "- **Whisper** = moteur speech→text (cloud Groq large-v3 prioritaire, sinon local `small` CPU)."
    )
    md_lines.append("")
    md_lines.append("## Détails bruts")
    md_lines.append("```")
    md_lines.append(json.dumps(report["verdict"], indent=2, ensure_ascii=False))
    md_lines.append("```")
    md_lines.append("")
    md_lines.append("### LLM ping")
    md_lines.append("```")
    md_lines.append(str(report["checks"].get("llm_ping", ""))[:800])
    md_lines.append("```")
    md_lines.append("")
    md_lines.append("### Synthèse doc cible")
    md_lines.append("```")
    md_lines.append(str(report["checks"].get("synthesis", ""))[:1200])
    md_lines.append("```")
    md_lines.append("")
    md_lines.append("### STT")
    md_lines.append("```")
    md_lines.append(str(report["checks"].get("stt", ""))[:800])
    md_lines.append("```")
    md_lines.append("")
    md_lines.append("### PDF cible + chiffrement")
    md_lines.append("```")
    md_lines.append(str(report["checks"].get("encryption_sync", "")))
    md_lines.append(str(report["checks"].get("target_pdf", ""))[:800])
    md_lines.append("```")
    md_lines.append("")
    md_lines.append("### Erreurs récentes (30 min)")
    md_lines.append("```")
    md_lines.append(str(report["checks"].get("recent_errors", ""))[:1500] or "(aucune)")
    md_lines.append("```")

    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    (root / "docs").mkdir(exist_ok=True)
    (root / out_path).write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path = root / "docs/AUDIT_PROFOND_LEXHUB.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")
    print(md_path.read_text(encoding="utf-8"))
    print("\nJSON:", out_path)


if __name__ == "__main__":
    main()
