"""Ops Coach LexHub — recommandations gains + brouillons email (admin)."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Cabinet, User, UserRole
from app.services.email import _btn, _email_shell, _send_email, email_configured


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
