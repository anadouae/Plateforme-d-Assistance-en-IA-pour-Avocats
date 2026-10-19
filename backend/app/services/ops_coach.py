"""Ops Coach LexHub — signaux live + analyse IA + brouillons email (admin)."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Cabinet, User, UserRole
from app.services.email import _btn, _email_shell, _send_email, email_configured

logger = logging.getLogger(__name__)

OPS_AI_SYSTEM = (
    "Tu es l’Ops Coach LexHub : coach d’exploitation pour l’admin plateforme "
    "(pas pour l’avocat client). Tu analyses des métriques SaaS réelles "
    "(essais, impayés, usage IA, plaidoiries) et tu priorises qui contacter "
    "maintenant. Français pro, concret, actionnable. Pas de jargon inutile. "
    "Ne fabrique jamais de chiffres absents des données fournies."
)


PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def _contacts_for_cabinet(db: Session, cabinet_id: str) -> list[dict[str, str]]:
    users = (
        db.query(User)
        .filter(
            User.cabinet_id == cabinet_id,
            User.is_active.is_(True),
            ~User.email.like("%@deleted.lexhub.invalid"),
            User.role.in_([UserRole.ADMIN_CABINET, UserRole.AVOCAT]),
        )
        .order_by(User.role.asc(), User.created_at.asc())
        .all()
    )
    out: list[dict[str, str]] = []
    seen: set[str] = set()
    # Prefer admin_cabinet first
    ordered = sorted(
        users,
        key=lambda u: 0 if u.role == UserRole.ADMIN_CABINET else 1,
    )
    for u in ordered:
        email = (u.email or "").strip().lower()
        if not email or email in seen:
            continue
        seen.add(email)
        out.append(
            {
                "email": email,
                "name": (u.full_name or "").strip() or email.split("@")[0],
                "role": u.role.value,
            }
        )
        if len(out) >= 3:
            break
    return out


def _html_from_text(title: str, body_text: str, *, cta_url: str | None = None, cta_label: str = "Ouvrir LexHub") -> str:
    paragraphs = [p.strip() for p in body_text.replace("\r\n", "\n").split("\n\n") if p.strip()]
    parts = []
    for p in paragraphs:
        lines = "<br/>".join(line.strip() for line in p.split("\n") if line.strip())
        parts.append(f"<p style='margin:0 0 14px'>{lines}</p>")
    if cta_url:
        parts.append(_btn(cta_url, cta_label))
    return _email_shell(title, "".join(parts), preheader=title)


def build_email_draft(
    *,
    scenario: str,
    cabinet_name: str,
    contact_name: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, str]:
    """Templates V2 par scénario — ton LexHub, FR pro."""
    extra = extra or {}
    raw_name = (contact_name or "").strip()
    # Éviter « Bonjour Me, » si le prénom est juste le titre Me / Me.
    first = raw_name.split()[0] if raw_name else "Maître"
    if first.lower().rstrip(".") in {"me", "m", "mr", "mme", "dr", "maître", "maitre"}:
        rest = raw_name.split()[1:] if raw_name else []
        first = rest[0] if rest else "Maître"
    base = settings.FRONTEND_URL.rstrip("/")
    billing_url = f"{base}/settings?tab=billing"
    login_url = f"{base}/login"
    plan_label = extra.get("plan_label") or "Pro"
    delta = extra.get("delta_mad")
    days_left = extra.get("days_left")

    templates: dict[str, tuple[str, str, str, str]] = {
        "trial_convert": (
            f"LexHub — votre essai gratuit ({cabinet_name})",
            "Votre essai LexHub — et la suite ?",
            (
                f"Bonjour {first},\n\n"
                f"Vous utilisez actuellement LexHub en essai gratuit pour « {cabinet_name} ».\n\n"
                "Pourquoi ce message ? Pendant l’essai, vous testez la plateforme sans payer. "
                "Avant la fin de cette période, nous vous accompagnons pour :\n"
                "• essayer une plaidoirie assistée (le cœur de LexHub) ;\n"
                "• choisir ensuite un plan payant si LexHub vous convient.\n\n"
                "Sans action de votre part, l’essai s’arrête et l’accès se limite.\n\n"
                "Bien cordialement,\n"
                "L’équipe LexHub"
            ),
            billing_url,
        ),
        "trial_ending": (
            f"LexHub — fin d’essai proche ({cabinet_name})",
            "Votre essai LexHub se termine bientôt",
            (
                f"Bonjour {first},\n\n"
                f"L’essai gratuit de « {cabinet_name} »"
                + (f" se termine dans environ {days_left} jour(s)" if days_left is not None else " arrive bientôt à échéance")
                + ".\n\n"
                "Pourquoi vous écrire ? Pour éviter une coupure d’accès : "
                "activez un abonnement depuis LexHub (Paramètres → Facturation) "
                "si vous souhaitez continuer.\n\n"
                "Bien cordialement,\n"
                "L’équipe LexHub"
            ),
            billing_url,
        ),
        "past_due": (
            f"LexHub — règlement en attente ({cabinet_name})",
            "Règlement de votre abonnement LexHub",
            (
                f"Bonjour {first},\n\n"
                f"Le paiement de l’abonnement de « {cabinet_name} » n’a pas encore été reçu.\n\n"
                "Pourquoi ce message ? Sans règlement, le compte risque une limitation. "
                "Merci de régulariser dès que possible.\n\n"
                "Bien cordialement,\n"
                "L’équipe LexHub"
            ),
            billing_url,
        ),
        "cancel_retain": (
            f"LexHub — avant de nous quitter ({cabinet_name})",
            "Restons en contact — LexHub",
            (
                f"Bonjour {first},\n\n"
                f"Nous avons noté que « {cabinet_name} » a demandé l’arrêt de l’abonnement "
                "à la fin de la période en cours.\n\n"
                "Pourquoi ce message ? Avant de partir, nous pouvons adapter l’offre :\n"
                "• un plan plus petit ;\n"
                "• un pack de crédits IA ;\n"
                "• une courte session d’aide.\n\n"
                "Dites-nous ce qui vous aiderait.\n\n"
                "Bien cordialement,\n"
                "L’équipe LexHub"
            ),
            billing_url,
        ),
        "upsell_solo": (
            f"LexHub — plan {plan_label} pour {cabinet_name}",
            f"Passer au plan {plan_label} ?",
            (
                f"Bonjour {first},\n\n"
                f"« {cabinet_name} » est sur le plan Solo.\n\n"
                f"Pourquoi ce message ? Si votre équipe ou l’usage IA grandit, "
                f"le plan {plan_label} offre plus de capacité"
                + (f" (+{delta} MAD/mois)" if delta else "")
                + ".\n\n"
                "Vous pouvez changer de plan en quelques clics dans LexHub.\n\n"
                "Bien cordialement,\n"
                "L’équipe LexHub"
            ),
            billing_url,
        ),
        "heavy_usage": (
            f"LexHub — crédits IA ({cabinet_name})",
            "Votre usage IA LexHub",
            (
                f"Bonjour {first},\n\n"
                f"« {cabinet_name} » utilise déjà beaucoup l’IA LexHub ce mois-ci.\n\n"
                "Pourquoi ce message ? Pour éviter d’atteindre le plafond du plan actuel, "
                "un plan supérieur ou des crédits supplémentaires peuvent être utiles.\n\n"
                "Bien cordialement,\n"
                "L’équipe LexHub"
            ),
            billing_url,
        ),
        "activate_billing": (
            f"LexHub — activer un abonnement ({cabinet_name})",
            "Activer votre abonnement LexHub",
            (
                f"Bonjour {first},\n\n"
                f"« {cabinet_name} » est actif sur LexHub, mais sans abonnement payant pour l’instant "
                "(souvent encore en essai).\n\n"
                "Pourquoi ce message ? Pour sécuriser l’accès et les quotas, "
                "il suffit d’activer un plan dans LexHub.\n\n"
                "Bien cordialement,\n"
                "L’équipe LexHub"
            ),
            billing_url,
        ),
        "first_plea": (
            f"LexHub — première plaidoirie ({cabinet_name})",
            "Lancez votre première plaidoirie",
            (
                f"Bonjour {first},\n\n"
                f"Pour bien démarrer avec LexHub dans « {cabinet_name} », "
                "nous recommandons de lancer une première plaidoirie assistée "
                "(documents + dictée + rédaction).\n\n"
                "Pourquoi ce message ? C’est le meilleur moyen de voir la valeur de LexHub "
                "pendant votre période d’essai ou votre abonnement.\n\n"
                "Bien cordialement,\n"
                "L’équipe LexHub"
            ),
            login_url,
        ),
    }

    subject, title, body, cta = templates.get(
        scenario,
        (
            f"LexHub — {cabinet_name}",
            "Message LexHub",
            f"Bonjour {first},\n\nNous souhaitons échanger au sujet de LexHub.\n\nBien cordialement,\nL’équipe LexHub",
            login_url,
        ),
    )
    html = _html_from_text(title, body, cta_url=cta, cta_label="Ouvrir LexHub")
    return {
        "subject": subject,
        "body_text": body,
        "body_html": html,
        "cta_url": cta,
    }


def tip_card(
    *,
    tip_id: str,
    scenario: str,
    priority: str,
    action_type: str,
    titre: str,
    en_clair: str,
    action: str,
    why: list[str],
    sequence: list[str] | None = None,
    targets: list[dict[str, Any]] | None = None,
    internal_href: str | None = None,
    cta_label: str | None = None,
) -> dict[str, Any]:
    at = action_type
    label = cta_label
    if not label:
        label = {
            "email": "Préparer l’email",
            "call": "Voir contacts",
            "billing": "Ouvrir facturation",
            "ops": "Voir détails techniques",
            "watch": "Suivre",
        }.get(at, "Voir")
    return {
        "id": tip_id,
        "scenario": scenario,
        "priority": priority,
        "action_type": at,
        "titre": titre,
        "en_clair": en_clair,
        "action": action,
        "why": why,
        "sequence": sequence or [],
        "targets": targets or [],
        "internal_href": internal_href,
        "cta_label": label,
    }


def attach_targets_with_drafts(
    db: Session,
    *,
    scenario: str,
    cabinet_ids: list[str],
    extra_by_cab: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    extra_by_cab = extra_by_cab or {}
    targets: list[dict[str, Any]] = []
    for cid in cabinet_ids:
        cab = db.query(Cabinet).filter(Cabinet.id == cid).first()
        if not cab:
            continue
        contacts = _contacts_for_cabinet(db, cid)
        primary = contacts[0] if contacts else None
        draft = None
        if primary:
            draft = build_email_draft(
                scenario=scenario,
                cabinet_name=cab.name,
                contact_name=primary["name"],
                extra=extra_by_cab.get(cid, {}),
            )
        targets.append(
            {
                "cabinet_id": cab.id,
                "cabinet_name": cab.name,
                "city": cab.city or "",
                "contacts": contacts,
                "to_email": primary["email"] if primary else None,
                "to_name": primary["name"] if primary else None,
                "draft": draft,
                "cc_emails": [c["email"] for c in contacts[1:2]],
            }
        )
    return targets


def send_ops_email(
    *,
    to: str,
    subject: str,
    body_text: str,
    body_html: str | None = None,
    cc: list[str] | None = None,
) -> bool:
    """Envoi admin Ops Coach (validation humaine requise côté API)."""
    if not email_configured():
        return False
    html = body_html or _html_from_text(subject, body_text)
    # _send_email supports single to; send primary then optional cc as separate sends
    ok = _send_email(to.strip(), subject.strip(), html, body_text.strip())
    if not ok:
        return False
    for addr in cc or []:
        a = (addr or "").strip()
        if a and a.lower() != to.strip().lower():
            _send_email(a, subject.strip(), html, body_text.strip())
    return True


def sort_tips(tips: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(tips, key=lambda t: (PRIORITY_ORDER.get(t.get("priority", "low"), 9), t.get("titre", "")))


def _strip_json_fence(raw: str) -> str:
    text = (raw or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _parse_json_object(raw: str) -> dict[str, Any] | None:
    text = _strip_json_fence(raw)
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{[\s\S]*\}", text)
    if m:
        try:
            data = json.loads(m.group(0))
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass
    return None


def _compact_tips_for_ai(tips: list[dict[str, Any]], *, limit: int = 8) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for t in tips[:limit]:
        targets = t.get("targets") or []
        names = [x.get("cabinet_name") for x in targets[:4] if x.get("cabinet_name")]
        out.append(
            {
                "id": t.get("id"),
                "scenario": t.get("scenario"),
                "priority": t.get("priority"),
                "titre": t.get("titre"),
                "en_clair": t.get("en_clair"),
                "action": t.get("action"),
                "n_cibles": len(targets),
                "exemples_cabinets": names,
            }
        )
    return out


def enrich_ops_with_ai(
    *,
    metrics: dict[str, Any],
    facts: list[str],
    tips: list[dict[str, Any]],
    summary_fr: str,
) -> dict[str, Any]:
    """Analyse IA live sur les signaux détectés (fallback gracieux si LLM down)."""
    from app.services.local_llm import generate_with_prompt

    payload = {
        "fenetre": "rolling_30j + mois en cours usage",
        "resume_regles": summary_fr,
        "metriques": metrics,
        "faits": facts[:12],
        "cartes_action": _compact_tips_for_ai(tips),
    }
    prompt = (
        "Analyse LIVE des cabinets LexHub (données ci-dessous). "
        "Réponds UNIQUEMENT en JSON valide (pas de markdown) avec exactement :\n"
        "{\n"
        '  "brief_fr": "3-5 phrases : diagnostic opérationnel maintenant",\n'
        '  "priorites": ["1. action la plus urgente", "2. …", "3. …"],\n'
        '  "prochaine_heure": "ce que l’admin doit faire dans l’heure",\n'
        '  "risque_principal": "une phrase",\n'
        '  "opportunite": "une phrase"\n'
        "}\n\n"
        f"DONNÉES:\n{json.dumps(payload, ensure_ascii=False, default=str)[:6000]}"
    )
    try:
        raw = generate_with_prompt(prompt, system=OPS_AI_SYSTEM)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Ops Coach AI brief failed: %s", exc)
        raw = None

    parsed = _parse_json_object(raw or "") if raw else None
    if not parsed:
        return {
            "enabled": bool(raw),
            "status": "fallback" if not raw else "parse_error",
            "brief_fr": summary_fr,
            "priorites": [t.get("titre") for t in tips[:3] if t.get("titre")],
            "prochaine_heure": (
                tips[0].get("action") if tips else "Relancer Ops Coach après nouvelles connexions."
            ),
            "risque_principal": "",
            "opportunite": "",
            "method": "signals_sql + llm_brief",
        }

    priorites = parsed.get("priorites") or []
    if not isinstance(priorites, list):
        priorites = [str(priorites)]
    priorites = [str(p).strip() for p in priorites if str(p).strip()][:5]

    return {
        "enabled": True,
        "status": "ok",
        "brief_fr": str(parsed.get("brief_fr") or summary_fr).strip(),
        "priorites": priorites,
        "prochaine_heure": str(parsed.get("prochaine_heure") or "").strip(),
        "risque_principal": str(parsed.get("risque_principal") or "").strip(),
        "opportunite": str(parsed.get("opportunite") or "").strip(),
        "method": "signals_sql + llm_brief",
    }


def polish_tips_with_ai(tips: list[dict[str, Any]], *, ai_brief: dict[str, Any]) -> list[dict[str, Any]]:
    """Réécrit en_clair / action des 3 cartes les plus prioritaires via LLM."""
    if not tips or ai_brief.get("status") != "ok":
        return tips
    from app.services.local_llm import generate_with_prompt

    top = tips[:3]
    compact = _compact_tips_for_ai(top, limit=3)
    prompt = (
        "Réécris les cartes Ops Coach pour l’admin (plus percutant, toujours factuel). "
        "JSON uniquement :\n"
        '{"cartes":[{"id":"...","en_clair":"...","action":"..."}]}\n\n'
        f"BRIEF IA:\n{ai_brief.get('brief_fr','')}\n\n"
        f"CARTES:\n{json.dumps(compact, ensure_ascii=False)}"
    )
    try:
        raw = generate_with_prompt(prompt, system=OPS_AI_SYSTEM)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Ops Coach tip polish failed: %s", exc)
        return tips
    parsed = _parse_json_object(raw or "") if raw else None
    if not parsed:
        return tips
    cartes = parsed.get("cartes") or []
    if not isinstance(cartes, list):
        return tips
    by_id = {
        str(c.get("id")): c
        for c in cartes
        if isinstance(c, dict) and c.get("id")
    }
    out: list[dict[str, Any]] = []
    for t in tips:
        tid = str(t.get("id") or "")
        c = by_id.get(tid)
        if c:
            nt = dict(t)
            if c.get("en_clair"):
                nt["en_clair"] = str(c["en_clair"]).strip()
            if c.get("action"):
                nt["action"] = str(c["action"]).strip()
            nt["ai_polished"] = True
            out.append(nt)
        else:
            out.append(t)
    return out


def build_email_draft_ai(
    *,
    scenario: str,
    cabinet_name: str,
    contact_name: str,
    extra: dict[str, Any] | None = None,
    tip_context: str | None = None,
) -> dict[str, str]:
    """Brouillon email personnalisé par IA ; fallback templates figés."""
    base = build_email_draft(
        scenario=scenario,
        cabinet_name=cabinet_name,
        contact_name=contact_name,
        extra=extra,
    )
    from app.services.local_llm import generate_with_prompt

    extra = extra or {}
    prompt = (
        "Rédige un brouillon d’e-mail LexHub (admin plateforme → contact cabinet). "
        "Ton pro, court, humain. L’admin relira avant un envoi SMTP. "
        "JSON uniquement :\n"
        '{"subject":"...","body_text":"..."}\n\n'
        f"scénario={scenario}\n"
        f"cabinet={cabinet_name}\n"
        f"contact={contact_name}\n"
        f"extra={json.dumps(extra, ensure_ascii=False, default=str)}\n"
        f"contexte_carte={tip_context or ''}\n"
        f"modele_de_base_sujet={base['subject']}\n"
        f"modele_de_base_corps=\n{base['body_text']}\n"
        "Garde une signature « L’équipe LexHub ». "
        "Ne promets pas de réduction non demandée."
    )
    try:
        raw = generate_with_prompt(prompt, system=OPS_AI_SYSTEM)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Ops Coach AI draft failed: %s", exc)
        return {**base, "ai_generated": "false"}

    parsed = _parse_json_object(raw or "") if raw else None
    if not parsed or not parsed.get("subject") or not parsed.get("body_text"):
        return {**base, "ai_generated": "false"}

    subject = str(parsed["subject"]).strip()[:180]
    body = str(parsed["body_text"]).strip()
    if len(body) < 40:
        return {**base, "ai_generated": "false"}

    cta = base.get("cta_url") or f"{settings.FRONTEND_URL.rstrip('/')}/login"
    title = subject.split("—")[-1].strip() if "—" in subject else subject
    html = _html_from_text(title, body, cta_url=cta, cta_label="Ouvrir LexHub")
    return {
        "subject": subject,
        "body_text": body,
        "body_html": html,
        "cta_url": cta,
        "ai_generated": "true",
    }


def attach_targets_with_ai_drafts(
    db: Session,
    *,
    scenario: str,
    cabinet_ids: list[str],
    extra_by_cab: dict[str, dict[str, Any]] | None = None,
    tip_context: str | None = None,
    max_ai: int = 5,
) -> list[dict[str, Any]]:
    """Comme attach_targets_with_drafts mais brouillons IA (plafond pour latence)."""
    extra_by_cab = extra_by_cab or {}
    targets: list[dict[str, Any]] = []
    ai_left = max_ai
    for cid in cabinet_ids:
        cab = db.query(Cabinet).filter(Cabinet.id == cid).first()
        if not cab:
            continue
        contacts = _contacts_for_cabinet(db, cid)
        primary = contacts[0] if contacts else None
        draft = None
        if primary:
            if ai_left > 0:
                draft = build_email_draft_ai(
                    scenario=scenario,
                    cabinet_name=cab.name,
                    contact_name=primary["name"],
                    extra=extra_by_cab.get(cid, {}),
                    tip_context=tip_context,
                )
                ai_left -= 1
            else:
                draft = build_email_draft(
                    scenario=scenario,
                    cabinet_name=cab.name,
                    contact_name=primary["name"],
                    extra=extra_by_cab.get(cid, {}),
                )
        targets.append(
            {
                "cabinet_id": cab.id,
                "cabinet_name": cab.name,
                "city": cab.city or "",
                "contacts": contacts,
                "to_email": primary["email"] if primary else None,
                "to_name": primary["name"] if primary else None,
                "draft": draft,
                "cc_emails": [c["email"] for c in contacts[1:2]],
            }
        )
    return targets
