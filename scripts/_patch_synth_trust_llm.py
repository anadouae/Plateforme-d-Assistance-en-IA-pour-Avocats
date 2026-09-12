#!/usr/bin/env python3
"""Prefer LLM structured fields; don't fill with regex garbage."""
from pathlib import Path

p = Path(__file__).resolve().parents[1] / "backend/app/services/agent.py"
t = p.read_text(encoding="utf-8")
old = """            # Regex uniquement pour combler des listes vides — jamais pour remplacer le summary LLM
            parties = list(llm_data.get("parties") or []) or extract_parties(text)
            dates = list(llm_data.get("key_dates") or []) or extract_dates(text)
            amounts = list(llm_data.get("amounts") or []) or extract_amounts(text)
            risks = list(llm_data.get("risk_clauses") or [])
            if not risks and not scrambled:
                risks = extract_risk_clauses(text)"""
new = """            # Si le LLM a répondu : faire confiance à ses listes (même vides).
            # Le regex ne doit PAS remplir avec des n° de lois / phrases arabes inversées.
            parties = [x for x in (llm_data.get("parties") or []) if str(x).strip()]
            dates = [x for x in (llm_data.get("key_dates") or []) if str(x).strip()]
            amounts = [x for x in (llm_data.get("amounts") or []) if str(x).strip()]
            risks = [x for x in (llm_data.get("risk_clauses") or []) if str(x).strip()]
            dates = [d for d in dates if not __import__("re").fullmatch(r"\\d\\.\\d{2}\\.\\d{3}", str(d).replace("/", ".").replace("-", "."))]
            risks = [r for r in risks if len(str(r)) >= 20]
            # Regex seulement si le LLM n'a fourni AUCUNE structure utile
            if not parties and not dates and not amounts and not risks:
                parties = extract_parties(text)
                dates = extract_dates(text)
                amounts = extract_amounts(text)
                if not scrambled:
                    risks = extract_risk_clauses(text)"""
if old not in t:
    raise SystemExit("block not found")
p.write_text(t.replace(old, new), encoding="utf-8")
print("agent ok")
