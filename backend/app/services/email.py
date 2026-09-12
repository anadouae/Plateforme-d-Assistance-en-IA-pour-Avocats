"""Emails transactionnels LexHub — Resend (prioritaire) ou SMTP (fallback dev)."""

from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_BRAND = "LexHub"
_FROM = settings.EMAIL_FROM or settings.SMTP_FROM or "LexHub <noreply@lexhub.space>"


def email_configured() -> bool:
    if (settings.RESEND_API_KEY or "").strip():
        return True
    host = (settings.SMTP_HOST or "").strip().lower()
    return bool(host) and host not in {"mailhog", "localhost", "127.0.0.1", ""}


def _send_email(to: str, subject: str, html: str, text: str) -> bool:
    api_key = (settings.RESEND_API_KEY or "").strip()
    if api_key:
        try:
            r = httpx.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": _FROM,
                    "to": [to],
                    "reply_to": "contact@lexhub.space",
                    "subject": subject,
                    "html": html,
                    "text": text,
                },
                timeout=30.0,
            )
            if r.status_code in (200, 201):
                return True
            logger.error("Resend failed %s: %s", r.status_code, r.text[:500])
            return False
        except Exception as exc:
            logger.error("Resend error to %s: %s", to, exc)
            return False

    if not settings.SMTP_HOST:
        logger.warning("Email not configured — to %s: %s", to, subject)
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = _FROM
        msg["To"] = to
        msg.attach(MIMEText(text, "plain", "utf-8"))
        msg.attach(MIMEText(html, "html", "utf-8"))

        if settings.SMTP_TLS:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
            server.starttls()
        else:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)

        if settings.SMTP_USER:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(_FROM, [to], msg.as_string())
        server.quit()
        return True
    except Exception as exc:
        logger.error("SMTP send failed to %s: %s", to, exc)
        return False


def _btn(href: str, label: str) -> str:
    return f"""<a href="{href}" style="display:inline-block;margin-top:20px;background:#0B1F4A;color:#ffffff;
      padding:14px 28px;border-radius:10px;text-decoration:none;font-weight:600;font-size:15px">{label}</a>"""


def _code_box(code: str) -> str:
    return f"""<div style="margin:24px 0;padding:20px 24px;background:#F6EFDD;border-radius:12px;
      border:1px solid #E8DCC8;text-align:center">
      <p style="margin:0;font-size:32px;font-weight:700;letter-spacing:8px;color:#0B1F4A">{code}</p>
    </div>"""


def _email_shell(title: str, body_html: str, *, preheader: str = "") -> str:
    base = settings.FRONTEND_URL.rstrip("/")
    logo_url = f"{base}/logo-lexhub-cube.png"
    pre = (
        f'<span style="display:none;max-height:0;overflow:hidden">{preheader}</span>'
        if preheader
        else ""
    )
    return f"""<!DOCTYPE html>
<html lang="fr">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#F0EBE0;font-family:Inter,Arial,sans-serif;color:#2C3B5C">
{pre}
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#F0EBE0">
  <tr><td align="center" style="padding:40px 16px">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0"
      style="max-width:560px;background:#ffffff;border-radius:16px;overflow:hidden;
      border:1px solid #E8DCC8;box-shadow:0 8px 32px rgba(11,31,74,0.08)">
      <tr>
        <td style="background:linear-gradient(135deg,#0B1F4A 0%,#12307A 100%);padding:28px 32px;text-align:center">
          <img src="{logo_url}" alt="LexHub" width="56" height="56" style="display:block;margin:0 auto 10px" />
          <p style="margin:0;color:#ffffff;font-size:20px;font-weight:700;letter-spacing:0.5px">LexHub</p>
          <p style="margin:6px 0 0;color:rgba(255,255,255,0.75);font-size:12px">LegalTech pour cabinets marocains</p>
        </td>
      </tr>
      <tr>
        <td style="padding:32px 28px 28px">
          <h1 style="margin:0 0 16px;font-size:20px;line-height:1.35;color:#0B1F4A">{title}</h1>
          <div style="font-size:15px;line-height:1.65;color:#2C3B5C">{body_html}</div>
        </td>
      </tr>
      <tr>
        <td style="padding:16px 28px 24px;background:#FAF8F4;border-top:1px solid #EDE6D8;text-align:center">
          <p style="margin:0;font-size:11px;color:#8A96AB;line-height:1.5">
            {_BRAND} · <a href="{base}" style="color:#0B1F4A;text-decoration:none">lexhub.space</a><br/>
            Message automatique — merci de ne pas répondre directement.
          </p>
        </td>
      </tr>
    </table>
  </td></tr>
</table>
</body></html>"""


def send_password_reset_email(to: str, token: str) -> bool:
    url = f"{settings.FRONTEND_URL.rstrip('/')}/reset-password?token={token}"
    hours = settings.PASSWORD_RESET_EXPIRE_HOURS
    subject = f"{_BRAND} — Réinitialisation du mot de passe"
    text = f"Réinitialisez votre mot de passe LexHub (valable {hours}h) : {url}"
    html = _email_shell(
        "Réinitialisation du mot de passe",
        f"""<p>Vous avez demandé à réinitialiser votre mot de passe.</p>
        <p>Cliquez sur le bouton ci-dessous pour en définir un nouveau. Ce lien est valable
        <strong>{hours} heure{"s" if hours > 1 else ""}</strong>.</p>
        {_btn(url, "Réinitialiser mon mot de passe")}
        <p style="margin-top:24px;font-size:12px;color:#8A96AB">Si vous n'êtes pas à l'origine de cette demande,
        ignorez cet email. Votre mot de passe actuel reste inchangé.</p>""",
        preheader="Lien sécurisé pour définir un nouveau mot de passe.",
    )
    return _send_email(to, subject, html, text)


def send_otp_email(to: str, code: str, purpose_label: str) -> bool:
    subject = f"{_BRAND} — {purpose_label}"
    text = f"Votre code {_BRAND} : {code}\nValable 15 minutes."
    html = _email_shell(
        purpose_label,
        f"""<p>Voici votre code de vérification :</p>
        {_code_box(code)}
        <p style="font-size:13px;color:#8A96AB">Valable <strong>15 minutes</strong>.
        Ne le communiquez à personne — l'équipe LexHub ne vous le demandera jamais.</p>""",
        preheader=f"Votre code : {code}",
    )
    return _send_email(to, subject, html, text)


def send_lockout_email(to: str, minutes: int) -> bool:
    subject = f"{_BRAND} — Compte temporairement bloqué"
    text = f"Compte bloqué {minutes} min suite à échecs de connexion."
    html = _email_shell(
        "Compte temporairement bloqué",
        f"""<p>Suite à plusieurs tentatives de connexion infructueuses, l'accès à votre compte
        est suspendu environ <strong>{minutes} minutes</strong>.</p>
        <p style="font-size:13px;color:#8A96AB">Si ce n'était pas vous, nous vous recommandons
        de réinitialiser votre mot de passe dès que l'accès est rétabli.</p>""",
    )
    return _send_email(to, subject, html, text)


def send_cabinet_approved_email(to: str, *, cabinet_name: str, manager_name: str) -> bool:
    url = f"{settings.FRONTEND_URL.rstrip('/')}/login"
    subject = f"{_BRAND} — Cabinet activé ({cabinet_name})"
    text = f"Bonjour {manager_name}, votre cabinet {cabinet_name} est activé. Connectez-vous : {url}"
    html = _email_shell(
        "Votre cabinet est activé",
        f"""<p>Bonjour <strong>{manager_name}</strong>,</p>
        <p>Bonne nouvelle : votre cabinet <strong>{cabinet_name}</strong> est maintenant actif sur LexHub.
        Vous pouvez vous connecter et commencer à utiliser la plateforme.</p>
        {_btn(url, "Accéder à LexHub")}""",
        preheader=f"{cabinet_name} est prêt sur LexHub.",
    )
    return _send_email(to, subject, html, text)


def send_join_request_admin_email(
    to: str,
    *,
    cabinet_name: str,
    applicant_name: str,
    applicant_email: str,
) -> bool:
    url = f"{settings.FRONTEND_URL.rstrip('/')}/team#join-requests"
    subject = f"{_BRAND} — Nouvelle demande d'adhésion ({cabinet_name})"
    text = f"Demande de {applicant_name} ({applicant_email}) — {url}"
    html = _email_shell(
        "Nouvelle demande d'adhésion",
        f"""<p>Une personne souhaite rejoindre votre cabinet :</p>
        <p><strong>{applicant_name}</strong><br/>
        <span dir="ltr">{applicant_email}</span></p>
        <p>Cabinet : <strong>{cabinet_name}</strong></p>
        {_btn(url, "Examiner la demande")}""",
    )
    return _send_email(to, subject, html, text)


def send_join_approved_email(
    to: str,
    *,
    cabinet_name: str,
    applicant_name: str,
) -> bool:
    url = f"{settings.FRONTEND_URL.rstrip('/')}/login"
    subject = f"{_BRAND} — Accès approuvé ({cabinet_name})"
    text = f"Accès approuvé pour {cabinet_name}. Connectez-vous : {url}"
    html = _email_shell(
        "Accès approuvé",
        f"""<p>Bonjour <strong>{applicant_name}</strong>,</p>
        <p>Votre demande pour rejoindre <strong>{cabinet_name}</strong> a été acceptée.</p>
        {_btn(url, "Se connecter")}""",
    )
    return _send_email(to, subject, html, text)


def send_join_rejected_email(
    to: str,
    *,
    cabinet_name: str,
    applicant_name: str,
) -> bool:
    subject = f"{_BRAND} — Demande non retenue ({cabinet_name})"
    text = f"Demande non retenue pour {cabinet_name}."
    html = _email_shell(
        "Demande non retenue",
        f"""<p>Bonjour <strong>{applicant_name}</strong>,</p>
        <p>Votre demande pour rejoindre <strong>{cabinet_name}</strong> n'a pas été acceptée
        par l'administrateur du cabinet.</p>
        <p style="font-size:13px;color:#8A96AB">Pour toute question, contactez directement le cabinet concerné.</p>""",
    )
    return _send_email(to, subject, html, text)


def send_join_invite_email(
    to: str,
    *,
    cabinet_name: str,
    join_code: str,
    inviter_name: str,
    recipient_name: str | None = None,
    role: str = "avocat",
) -> bool:
    """Invitation admin : lien direct → création de compte immédiate."""
    base = settings.FRONTEND_URL.rstrip("/")
    from urllib.parse import quote

    accept_url = f"{base}/join/accept?code={quote(join_code, safe='')}"
    hello = recipient_name.strip() if recipient_name and recipient_name.strip() else "Bonjour"
    if recipient_name and recipient_name.strip():
        hello = f"Bonjour <strong>{recipient_name.strip()}</strong>"
    else:
        hello = "Bonjour"
    role_fr = {
        "avocat": "Avocat",
        "assistant_juridique": "Assistant juridique",
        "admin_cabinet": "Avocat admin (coordinateur)",
    }.get(role, "Avocat")
    subject = f"{_BRAND} — Invitation à rejoindre {cabinet_name}"
    text = (
        f"Invitation LexHub — cabinet {cabinet_name}\n"
        f"Rôle : {role_fr}\n"
        f"Activer mon compte : {accept_url}\n"
    )
    steps = """
        <ol style="margin:16px 0 8px;padding-left:20px;line-height:1.7;color:#2C3B5C">
          <li><strong>Ouvrir le lien</strong> ci-dessous (invitation personnelle).</li>
          <li><strong>Choisir votre mot de passe</strong> et confirmer votre nom.</li>
          <li><strong>Se connecter</strong> — accès immédiat, sans attente.</li>
        </ol>
        """
    html = _email_shell(
        f"Invitation — {cabinet_name}",
        f"""<p>{hello},</p>
        <p><strong>{inviter_name}</strong> vous invite à rejoindre le cabinet
        <strong>{cabinet_name}</strong> sur LexHub en tant que <strong>{role_fr}</strong>.</p>
        <p style="margin:18px 0 6px;font-size:13px;font-weight:600;color:#0B1F4A;text-transform:uppercase;letter-spacing:0.04em">
          Comment activer votre accès
        </p>
        {steps}
        {_btn(accept_url, "Activer mon compte")}
        <p style="margin-top:20px;font-size:12px;color:#8A96AB">
          Ce lien est personnel et expire automatiquement. Si vous n’attendiez pas cet email, ignorez-le.
        </p>""",
        preheader=f"Invitation LexHub — {cabinet_name}",
    )
    return _send_email(to, subject, html, text)


def send_plea_validated_email(
    to: str,
    *,
    assistant_name: str,
    lawyer_name: str,
    plea_title: str,
    cabinet_name: str,
) -> bool:
    url = f"{settings.FRONTEND_URL.rstrip('/')}/redaction"
    subject = f"{_BRAND} — Plaidoirie validée ({cabinet_name})"
    text = (
        f"{lawyer_name} a validé « {plea_title} ». "
        f"Ouvrez LexHub pour consulter / imprimer : {url}"
    )
    html = _email_shell(
        "Plaidoirie prête",
        f"""<p>Bonjour <strong>{assistant_name}</strong>,</p>
        <p><strong>{lawyer_name}</strong> a validé une plaidoirie dans
        <strong>{cabinet_name}</strong> :</p>
        <p style="margin:16px 0;padding:14px 16px;background:#F6EFDD;border-radius:10px;
          border:1px solid #E8DCC8;font-weight:600;color:#0B1F4A">{plea_title}</p>
        <p>Vous pouvez l’ouvrir, l’imprimer ou la télécharger (Word / PDF).</p>
        {_btn(url, "Ouvrir les plaidoiries validées")}""",
        preheader=f"Validée : {plea_title[:60]}",
    )
    return _send_email(to, subject, html, text)


def send_email_changed_notice(*, old_email: str, new_email: str, full_name: str) -> bool:
    """Prévenir l'ancienne ET la nouvelle adresse après changement d'email."""
    url = f"{settings.FRONTEND_URL.rstrip('/')}/login"
    subject = f"{_BRAND} — Adresse email modifiée"
    body_old = _email_shell(
        "Adresse email modifiée",
        f"""<p>Bonjour <strong>{full_name}</strong>,</p>
        <p>L'adresse de connexion de votre compte LexHub n'est plus <strong>{old_email}</strong>.</p>
        <p>La nouvelle adresse est <strong>{new_email}</strong>.</p>
        <p style="font-size:13px;color:#8A96AB">Si ce n'était <strong>pas vous</strong>,
        contactez <a href="mailto:contact@lexhub.space" style="color:#0B1F4A">contact@lexhub.space</a> immédiatement.</p>
        {_btn(url, "Se connecter")}""",
        preheader="Votre email LexHub a été modifié",
    )
    body_new = _email_shell(
        "Nouvelle adresse confirmée",
        f"""<p>Bonjour <strong>{full_name}</strong>,</p>
        <p>Cette adresse est désormais celle de votre compte LexHub.</p>
        {_btn(url, "Se connecter")}""",
        preheader="Email LexHub confirmé",
    )
    ok_old = _send_email(
        old_email,
        subject,
        body_old,
        f"Votre email LexHub a été changé vers {new_email}.",
    )
    ok_new = _send_email(
        new_email,
        f"{_BRAND} — Nouvelle adresse confirmée",
        body_new,
        f"Cette adresse est désormais votre identifiant LexHub.",
    )
    return bool(ok_old or ok_new)


def send_password_changed_email(to: str, *, full_name: str) -> bool:
    url = f"{settings.FRONTEND_URL.rstrip('/')}/login"
    subject = f"{_BRAND} — Mot de passe modifié"
    text = (
        f"Bonjour {full_name}, votre mot de passe LexHub a été modifié. "
        f"Si ce n’était pas vous : contact@lexhub.space"
    )
    html = _email_shell(
        "Mot de passe modifié",
        f"""<p>Bonjour <strong>{full_name}</strong>,</p>
        <p>Le mot de passe de votre compte LexHub vient d’être modifié.</p>
        <p>Si vous êtes à l’origine de cette action, aucune suite n’est nécessaire.</p>
        <p style="font-size:13px;color:#8A96AB">Si ce n’était <strong>pas vous</strong>,
        contactez <a href="mailto:contact@lexhub.space" style="color:#0B1F4A">contact@lexhub.space</a>.</p>
        {_btn(url, "Se connecter")}""",
        preheader="Confirmation de changement de mot de passe",
    )
    return _send_email(to, subject, html, text)


def send_digest_validated_pleas_email(
    to: str,
    *,
    assistant_name: str,
    pending_count: int,
    cabinet_name: str,
) -> bool:
    url = f"{settings.FRONTEND_URL.rstrip('/')}/redaction"
    subject = f"{_BRAND} — {pending_count} plaidoirie(s) validée(s) ({cabinet_name})"
    text = f"Il y a {pending_count} plaidoirie(s) validée(s) à consulter : {url}"
    html = _email_shell(
        "Résumé des plaidoiries validées",
        f"""<p>Bonjour <strong>{assistant_name}</strong>,</p>
        <p>Dans <strong>{cabinet_name}</strong>,
        <strong>{pending_count}</strong> plaidoirie(s) validée(s) sont disponibles.</p>
        {_btn(url, "Voir les plaidoiries")}""",
        preheader=f"{pending_count} plaidoirie(s) à traiter",
    )
    return _send_email(to, subject, html, text)

def send_account_deleted_email(to: str, *, full_name: str) -> bool:
    subject = f"{_BRAND} — Compte supprimé"
    text = (
        f"Bonjour {full_name}, votre compte LexHub a été définitivement désactivé. "
        f"Les données personnelles associées ont été anonymisées. Contact : contact@lexhub.space"
    )
    html = _email_shell(
        "Compte supprimé",
        f"""<p>Bonjour <strong>{full_name}</strong>,</p>
        <p>Votre compte LexHub a été <strong>supprimé</strong> à votre demande.</p>
        <p>Vos données personnelles ont été anonymisées. Les traces d’audit techniques
        peuvent être conservées sous forme non identifiante, conformément aux obligations légales.</p>
        <p style="font-size:13px;color:#8A96AB">Question : 
        <a href="mailto:contact@lexhub.space" style="color:#0B1F4A">contact@lexhub.space</a></p>""",
        preheader="Confirmation de suppression de compte",
    )
    return _send_email(to, subject, html, text)


def send_agenda_reminder_email(
    to: str,
    *,
    full_name: str,
    event_title: str,
    starts_at_label: str,
    event_type_label: str,
    cabinet_name: str,
    case_reference: str | None = None,
    reminder_label: str | None = None,
) -> bool:
    url = f"{settings.FRONTEND_URL.rstrip('/')}/agenda"
    when_tag = reminder_label or "J-2"
    subject = f"{_BRAND} — Rappel agenda {when_tag} ({cabinet_name})"
    case_line = f" Dossier : {case_reference}." if case_reference else ""
    text = (
        f"Bonjour {full_name}, rappel : « {event_title} » ({event_type_label}) "
        f"le {starts_at_label}.{case_line} Ouvrir l’agenda : {url}"
    )
    case_html = (
        f'<p style="margin:8px 0 0;font-size:14px;color:#5A6A85">Dossier '
        f"<strong>{case_reference}</strong></p>"
        if case_reference
        else ""
    )
    html = _email_shell(
        f"Rappel agenda — {when_tag}",
        f"""<p>Bonjour <strong>{full_name}</strong>,</p>
        <p>Un événement approche dans <strong>{cabinet_name}</strong> :</p>
        <p style="margin:16px 0;padding:14px 16px;background:#F6EFDD;border-radius:10px;
          border:1px solid #E8DCC8">
          <span style="display:block;font-weight:600;color:#0B1F4A;margin-bottom:6px">{event_title}</span>
          <span style="font-size:14px;color:#2C3B5C">{event_type_label} · {starts_at_label}</span>
          {case_html}
        </p>
        <p>Pensez à préparer le dossier et à vérifier votre disponibilité.</p>
        {_btn(url, "Ouvrir l’agenda")}""",
        preheader=f"{event_type_label} le {starts_at_label} — {event_title[:50]}",
    )
    return _send_email(to, subject, html, text)


# ─── Lifecycle commercial (rétention type Cursor / Notion / Clio) ───────────


def send_welcome_free_email(
    to: str,
    *,
    full_name: str,
    cabinet_name: str,
) -> bool:
    """Bienvenue plan Découverte (gratuit) — modèle Coursera."""
    tarifs = f"{settings.FRONTEND_URL.rstrip('/')}/tarifs"
    dash = f"{settings.FRONTEND_URL.rstrip('/')}/dashboard"
    subject = f"{_BRAND} — Bienvenue · plan Découverte"
    text = (
        f"Bonjour {full_name}, bienvenue sur LexHub ({cabinet_name}). "
        f"Vous êtes sur Découverte (gratuit, quotas limités). Tarifs : {tarifs}"
    )
    html = _email_shell(
        "Bienvenue sur LexHub — plan Découverte",
        f"""<p>Bonjour <strong>{full_name}</strong>,</p>
        <p>Votre cabinet <strong>{cabinet_name}</strong> est prêt sur le plan
        <strong>Découverte</strong> (gratuit, quotas limités) — idéal pour tester
        la dictée et une première plaidoirie.</p>
        <p>Quand vous voudrez plus de sièges, de quotas ou OpenAI premium :
        choisissez Solo, Cabinet ou Entreprise sur la page tarifs
        (essai 30 jours avec carte, annulable).</p>
        {_btn(dash, "Ouvrir mon espace")}
        <p style="margin-top:16px;font-size:13px"><a href="{tarifs}" style="color:#0B1F4A">Voir les tarifs</a></p>""",
        preheader=f"Découverte gratuit — {cabinet_name}",
    )
    return _send_email(to, subject, html, text)


def send_welcome_trial_email(
    to: str,
    *,
    full_name: str,
    cabinet_name: str,
    trial_days: int = 14,
) -> bool:
    """Conservé pour essais payants démarrés après checkout carte."""
    url = f"{settings.FRONTEND_URL.rstrip('/')}/settings#abonnement"
    tarifs = f"{settings.FRONTEND_URL.rstrip('/')}/tarifs"
    subject = f"{_BRAND} — Essai {trial_days} jours démarré"
    text = (
        f"Bonjour {full_name}, essai LexHub ({cabinet_name}) : {trial_days} jours. "
        f"Sans résiliation avant la fin, le plan sera facturé. {url}"
    )
    html = _email_shell(
        f"Essai LexHub — {trial_days} jours",
        f"""<p>Bonjour <strong>{full_name}</strong>,</p>
        <p>Votre essai de <strong>{trial_days} jours</strong> pour
        <strong>{cabinet_name}</strong> a démarré. La carte enregistrée sera
        débitée automatiquement si vous ne résiliez pas avant la fin de l'essai.</p>
        {_btn(url, "Gérer mon abonnement")}
        <p style="margin-top:16px;font-size:13px"><a href="{tarifs}" style="color:#0B1F4A">Comparer les plans</a></p>""",
        preheader=f"Essai {trial_days} jours — {cabinet_name}",
    )
    return _send_email(to, subject, html, text)


def send_commercial_lead_email(
    *,
    kind: str,
    full_name: str,
    email: str,
    phone: str = "",
    cabinet_name: str = "",
    city: str = "",
    lawyers_count: int | None = None,
    message: str = "",
) -> bool:
    label = "Essai Entreprise" if kind == "enterprise_trial" else "Offre Sur mesure"
    dest = (getattr(settings, "SUPPORT_EMAIL", None) or "contact@lexhub.space").strip()
    subject = f"LexHub — {label} — {cabinet_name or full_name}"
    body = (
        f"{label}\nNom : {full_name}\nE-mail : {email}\nTéléphone : {phone}\n"
        f"Cabinet : {cabinet_name}\nVille : {city}\nAvocats : {lawyers_count or '—'}\n\n{message}"
    )
    html = _email_shell(
        label,
        f"""<p><strong>{label}</strong></p>
        <p>Nom : {full_name}<br/>E-mail : {email}<br/>Tél. : {phone or '—'}<br/>
        Cabinet : {cabinet_name or '—'}<br/>Ville : {city or '—'}<br/>
        Avocats : {lawyers_count if lawyers_count is not None else '—'}</p>
        <p>{(message or '').replace(chr(10), '<br/>')}</p>""",
        preheader=label,
    )
    ok = _send_email(dest, subject, html, body)
    _send_email(
        email,
        f"LexHub — nous avons bien reçu votre demande ({label})",
        _email_shell(
            "Demande reçue",
            f"""<p>Bonjour <strong>{full_name}</strong>,</p>
            <p>Votre demande <strong>{label}</strong> est bien arrivée.
            Un conseiller vous recontacte sous 24–48 h ouvrées.
            Solo et Cabinet restent disponibles en essai libre sur
            <a href="https://lexhub.space/tarifs">lexhub.space/tarifs</a>.</p>""",
            preheader="Demande reçue",
        ),
        f"Bonjour {full_name}, votre demande {label} est reçue. Réponse sous 24–48 h.",
    )
    return ok


def send_trial_reminder_email(
    to: str,
    *,
    full_name: str,
    cabinet_name: str,
    days_left: int,
) -> bool:
    url = f"{settings.FRONTEND_URL.rstrip('/')}/settings#abonnement"
    if days_left <= 1:
        subject = f"{_BRAND} — Dernier jour d'essai"
        headline = "Votre essai se termine demain"
        body = (
            "Sans résiliation avant la fin, votre plan payant sera "
            "<strong>facturé automatiquement</strong> sur la carte enregistrée. "
            "Sinon, résiliez depuis Paramètres → Abonnement pour rester en Découverte."
        )
    elif days_left <= 3:
        subject = f"{_BRAND} — Plus que {days_left} jours d'essai"
        headline = f"Plus que {days_left} jours d'essai"
        body = (
            "Rappel : si vous ne résiliez pas avant la fin de l'essai, "
            "la facturation démarre automatiquement (comme Coursera). "
            "Sinon, votre espace bascule en Découverte."
        )
    else:
        subject = f"{_BRAND} — Il vous reste {days_left} jours d'essai"
        headline = f"{days_left} jours restants sur votre essai"
        body = (
            "Profitez de l'essai pour tester dictée, plaidoiries et équipe. "
            "Sans résiliation à la fin, le plan se paie automatiquement ; "
            "vous pouvez annuler à tout moment avant."
        )
    text = (
        f"Bonjour {full_name}, {days_left} j. d'essai restants ({cabinet_name}). "
        f"Sans résiliation → facturation auto. {url}"
    )
    html = _email_shell(
        headline,
        f"""<p>Bonjour <strong>{full_name}</strong>,</p>
        <p>Cabinet <strong>{cabinet_name}</strong> — {body}</p>
        {_btn(url, "Gérer l'abonnement")}""",
        preheader=f"Essai : {days_left} jour(s) restant(s)",
    )
    return _send_email(to, subject, html, text)


def send_trial_ended_email(
    to: str,
    *,
    full_name: str,
    cabinet_name: str,
) -> bool:
    url = f"{settings.FRONTEND_URL.rstrip('/')}/settings#abonnement"
    subject = f"{_BRAND} — Essai terminé · plan Découverte actif"
    text = (
        f"Bonjour {full_name}, l'essai de {cabinet_name} est terminé. "
        f"Vous êtes sur Découverte. Upgrade : {url}"
    )
    html = _email_shell(
        "Essai terminé — continuez avec Solo, Cabinet ou Entreprise",
        f"""<p>Bonjour <strong>{full_name}</strong>,</p>
        <p>L'essai pour <strong>{cabinet_name}</strong> est terminé
        (résiliation avant facturation, ou sans carte enregistrée).
        Votre espace reste accessible en <strong>Découverte</strong> (quotas limités).</p>
        <p>Passez à <strong>Solo</strong>, <strong>Cabinet</strong> ou <strong>Entreprise</strong>
        pour retrouver quotas, équipe et fonctions boostées (essai 30 j avec carte).</p>
        {_btn(url, "Voir les plans")}""",
        preheader="Essai terminé — Découverte actif.",
    )
    return _send_email(to, subject, html, text)


def send_trial_converted_email(
    to: str,
    *,
    full_name: str,
    cabinet_name: str,
    plan_name: str,
    billing_cycle: str,
) -> bool:
    """Coursera-like : essai non résilié → abonnement payant démarré."""
    url = f"{settings.FRONTEND_URL.rstrip('/')}/settings#abonnement"
    cycle = "annuel" if billing_cycle == "yearly" else "mensuel"
    subject = f"{_BRAND} — Abonnement {plan_name} activé"
    text = (
        f"Bonjour {full_name}, l'essai de {cabinet_name} est terminé. "
        f"Le plan {plan_name} ({cycle}) est maintenant facturé. {url}"
    )
    html = _email_shell(
        f"Abonnement {plan_name} activé",
        f"""<p>Bonjour <strong>{full_name}</strong>,</p>
        <p>L'essai de <strong>{cabinet_name}</strong> est terminé sans résiliation.
        Votre plan <strong>{plan_name}</strong> ({cycle}) est désormais actif
        et la carte enregistrée a été débitée (simulation CMI / PayZone).</p>
        <p>Vous pouvez gérer ou résilier votre abonnement à tout moment.</p>
        {_btn(url, "Gérer l'abonnement")}""",
        preheader=f"{plan_name} — facturation démarrée",
    )
    return _send_email(to, subject, html, text)


def send_plan_changed_email(
    to: str,
    *,
    full_name: str,
    cabinet_name: str,
    plan_name: str,
    billing_cycle: str,
) -> bool:
    url = f"{settings.FRONTEND_URL.rstrip('/')}/settings#abonnement"
    cycle = "annuel" if billing_cycle == "yearly" else "mensuel"
    subject = f"{_BRAND} — Plan {plan_name} activé"
    text = f"Bonjour {full_name}, plan {plan_name} ({cycle}) actif pour {cabinet_name}."
    html = _email_shell(
        f"Plan « {plan_name} » activé",
        f"""<p>Bonjour <strong>{full_name}</strong>,</p>
        <p>Le plan <strong>{plan_name}</strong> ({cycle}) est maintenant actif pour
        <strong>{cabinet_name}</strong>.</p>
        <p style="font-size:13px;color:#8A96AB">Paiement électronique (CMI / PayZone) en préparation —
        votre accès est déjà mis à jour.</p>
        {_btn(url, "Voir mon abonnement")}""",
        preheader=f"{plan_name} · {cycle}",
    )
    return _send_email(to, subject, html, text)


def send_cancel_requested_email(
    to: str,
    *,
    full_name: str,
    cabinet_name: str,
    reason_label: str,
) -> bool:
    url = f"{settings.FRONTEND_URL.rstrip('/')}/settings#abonnement"
    subject = f"{_BRAND} — Demande de résiliation enregistrée"
    text = (
        f"Bonjour {full_name}, résiliation demandée pour {cabinet_name} "
        f"(motif : {reason_label}). Accès jusqu'à fin de période. {url}"
    )
    html = _email_shell(
        "Résiliation enregistrée",
        f"""<p>Bonjour <strong>{full_name}</strong>,</p>
        <p>Nous avons bien reçu votre demande de résiliation pour
        <strong>{cabinet_name}</strong>.</p>
        <p>Motif : <strong>{reason_label}</strong></p>
        <p>Votre accès reste actif jusqu'à la fin de la période en cours.
        Vous pouvez annuler cette demande à tout moment.</p>
        {_btn(url, "Gérer mon abonnement")}
        <p style="margin-top:20px;font-size:13px;color:#8A96AB">On regrette de vous voir partir —
        contact@lexhub.space</p>""",
        preheader="Votre accès reste actif jusqu'à la fin de période.",
    )
    return _send_email(to, subject, html, text)


def send_cancel_undone_email(
    to: str,
    *,
    full_name: str,
    cabinet_name: str,
) -> bool:
    url = f"{settings.FRONTEND_URL.rstrip('/')}/dashboard"
    subject = f"{_BRAND} — Résiliation annulée · abonnement maintenu"
    text = f"Bonjour {full_name}, la résiliation de {cabinet_name} est annulée."
    html = _email_shell(
        "Content de vous garder",
        f"""<p>Bonjour <strong>{full_name}</strong>,</p>
        <p>La demande de résiliation pour <strong>{cabinet_name}</strong> a été annulée.
        Votre abonnement se poursuit normalement.</p>
        {_btn(url, "Retour au tableau de bord")}""",
        preheader="Abonnement maintenu — merci de rester avec LexHub.",
    )
    return _send_email(to, subject, html, text)


def send_invoice_ready_email(
    to: str,
    *,
    full_name: str,
    invoice_number: str,
    amount_mad: int,
    plan_name: str,
) -> bool:
    url = f"{settings.FRONTEND_URL.rstrip('/')}/settings#abonnement"
    subject = f"{_BRAND} — Facture {invoice_number}"
    text = (
        f"Bonjour {full_name}, facture {invoice_number} — {plan_name} — {amount_mad} MAD. {url}"
    )
    html = _email_shell(
        f"Facture {invoice_number}",
        f"""<p>Bonjour <strong>{full_name}</strong>,</p>
        <p>Votre facture LexHub est disponible :</p>
        <p style="padding:14px 16px;background:#F6EFDD;border-radius:10px;border:1px solid #E8DCC8">
          <strong>{invoice_number}</strong><br/>
          {plan_name} · <strong>{amount_mad} MAD</strong>
        </p>
        <p style="font-size:13px;color:#8A96AB">Document provisoire tant que le paiement CMI/PayZone
        n'est pas activé.</p>
        {_btn(url, "Ouvrir l'abonnement")}""",
        preheader=f"{invoice_number} · {amount_mad} MAD",
    )
    return _send_email(to, subject, html, text)


def send_quota_warning_email(
    to: str,
    *,
    full_name: str,
    cabinet_name: str,
    used: int,
    limit: int,
) -> bool:
    url = f"{settings.FRONTEND_URL.rstrip('/')}/settings#abonnement"
    pct = int(100 * used / max(limit, 1))
    subject = f"{_BRAND} — {pct}% du quota plaidoiries utilisé"
    text = f"Bonjour {full_name}, {used}/{limit} plaidoiries ce mois ({cabinet_name}). {url}"
    html = _email_shell(
        "Quota plaidoiries bientôt atteint",
        f"""<p>Bonjour <strong>{full_name}</strong>,</p>
        <p>Le cabinet <strong>{cabinet_name}</strong> a utilisé
        <strong>{used}/{limit}</strong> plaidoiries ce mois ({pct}%).</p>
        <p>Passez au plan supérieur pour éviter une interruption en pleine audience.</p>
        {_btn(url, "Augmenter mon plan")}""",
        preheader=f"{used}/{limit} plaidoiries — {pct}%",
    )
    return _send_email(to, subject, html, text)


def send_invite_accepted_admin_email(
    to: str,
    *,
    admin_name: str,
    member_name: str,
    member_email: str,
    cabinet_name: str,
    role_label: str,
) -> bool:
    url = f"{settings.FRONTEND_URL.rstrip('/')}/team"
    subject = f"{_BRAND} — {member_name} a rejoint {cabinet_name}"
    text = f"{member_name} ({member_email}) a accepté l'invitation ({role_label})."
    html = _email_shell(
        "Nouveau membre dans l'équipe",
        f"""<p>Bonjour <strong>{admin_name}</strong>,</p>
        <p><strong>{member_name}</strong> (<span dir="ltr">{member_email}</span>) a accepté
        l'invitation et a rejoint <strong>{cabinet_name}</strong> en tant que
        <strong>{role_label}</strong>.</p>
        {_btn(url, "Voir l'équipe")}""",
        preheader=f"{member_name} a rejoint le cabinet",
    )
    return _send_email(to, subject, html, text)


def send_payment_failed_email(
    to: str,
    *,
    full_name: str,
    cabinet_name: str,
    plan_name: str,
    amount_mad: int | None = None,
) -> bool:
    url = f"{settings.FRONTEND_URL.rstrip('/')}/settings#abonnement"
    amt = f" ({amount_mad} MAD)" if amount_mad else ""
    subject = f"{_BRAND} — Paiement non abouti · action requise"
    text = (
        f"Bonjour {full_name}, le paiement pour {cabinet_name} ({plan_name}{amt}) "
        f"n'a pas abouti. Mettez à jour le moyen de paiement : {url}"
    )
    html = _email_shell(
        "Paiement non abouti",
        f"""<p>Bonjour <strong>{full_name}</strong>,</p>
        <p>Le renouvellement de <strong>{cabinet_name}</strong> ({plan_name}{amt})
        n'a pas pu être débité.</p>
        <p>Sans régularisation, l'accès peut basculer en mode restreint.
        Mettez à jour votre moyen de paiement (CMI / PayZone / virement).</p>
        {_btn(url, "Régulariser mon abonnement")}""",
        preheader="Action requise pour garder votre accès LexHub.",
    )
    return _send_email(to, subject, html, text)


def send_renewal_reminder_email(
    to: str,
    *,
    full_name: str,
    cabinet_name: str,
    plan_name: str,
    days_left: int,
    amount_mad: int,
    period_end_label: str,
) -> bool:
    url = f"{settings.FRONTEND_URL.rstrip('/')}/settings#abonnement"
    if days_left <= 1:
        subject = f"{_BRAND} — Renouvellement demain · {plan_name}"
        headline = "Renouvellement demain"
    else:
        subject = f"{_BRAND} — Renouvellement dans {days_left} jours"
        headline = f"Renouvellement dans {days_left} jours"
    text = (
        f"Bonjour {full_name}, renouvellement {plan_name} le {period_end_label} "
        f"({amount_mad} MAD) pour {cabinet_name}. {url}"
    )
    html = _email_shell(
        headline,
        f"""<p>Bonjour <strong>{full_name}</strong>,</p>
        <p>L'abonnement <strong>{plan_name}</strong> de <strong>{cabinet_name}</strong>
        se renouvelle le <strong>{period_end_label}</strong> — montant prévu
        <strong>{amount_mad} MAD</strong>.</p>
        <p style="font-size:13px;color:#8A96AB">Vous pouvez changer de plan ou annuler
        avant cette date depuis vos paramètres.</p>
        {_btn(url, "Gérer le renouvellement")}""",
        preheader=f"{plan_name} · {period_end_label} · {amount_mad} MAD",
    )
    return _send_email(to, subject, html, text)


def send_payment_receipt_email(
    to: str,
    *,
    full_name: str,
    cabinet_name: str,
    invoice_number: str,
    amount_mad: int,
    plan_name: str,
    paid: bool = False,
) -> bool:
    """Reçu / facture (provisoire tant que CMI n'est pas live ; fiscal-ready)."""
    url = f"{settings.FRONTEND_URL.rstrip('/')}/settings#abonnement"
    stamp = "Payé" if paid else "Émise (paiement électronique bientôt)"
    subject = f"{_BRAND} — {'Reçu' if paid else 'Facture'} {invoice_number}"
    text = (
        f"Bonjour {full_name}, {stamp} {invoice_number} — {plan_name} — "
        f"{amount_mad} MAD — {cabinet_name}. {url}"
    )
    html = _email_shell(
        f"{'Reçu de paiement' if paid else 'Facture'} {invoice_number}",
        f"""<p>Bonjour <strong>{full_name}</strong>,</p>
        <p>Document pour <strong>{cabinet_name}</strong> :</p>
        <p style="padding:14px 16px;background:#F6EFDD;border-radius:10px;border:1px solid #E8DCC8">
          <strong>{invoice_number}</strong><br/>
          {plan_name} · <strong>{amount_mad} MAD</strong><br/>
          Statut : <strong>{stamp}</strong>
        </p>
        <p style="font-size:13px;color:#8A96AB">Structure prête pour facture fiscale marocaine
        (ICE, TVA) dès activation CMI / PayZone.</p>
        {_btn(url, "Voir l'abonnement")}""",
        preheader=f"{invoice_number} · {amount_mad} MAD",
    )
    return _send_email(to, subject, html, text)


def send_onboarding_tip_email(
    to: str,
    *,
    full_name: str,
    cabinet_name: str,
    day: int,
) -> bool:
    """Tips J+1 / J+2 — activation produit (1ʳᵉ plaidoirie)."""
    base = settings.FRONTEND_URL.rstrip("/")
    if day <= 1:
        subject = f"{_BRAND} — Conseil du jour : dictez votre 1ʳᵉ plaidoirie"
        headline = "Activez LexHub en 5 minutes"
        body = (
            "Le cœur du produit, c'est la dictée arabe → fusḥā → structure → export Word. "
            "Créez une plaidoirie de démo dès aujourd'hui — même 2 minutes suffisent."
        )
        cta_url = f"{base}/plaidoirie"
        cta = "Ouvrir l'atelier plaidoirie"
    else:
        subject = f"{_BRAND} — Invitez un collègue ou liez un dossier"
        headline = "Passez en mode cabinet"
        body = (
            "Après la première dictée : liez la plaidoirie à un dossier, uploadez une pièce, "
            "ou invitez un assistant pour la mise en forme. L'équipe multiplie la valeur LexHub."
        )
        cta_url = f"{base}/team"
        cta = "Inviter un collègue"
    text = f"Bonjour {full_name} ({cabinet_name}). {body} {cta_url}"
    html = _email_shell(
        headline,
        f"""<p>Bonjour <strong>{full_name}</strong>,</p>
        <p>Cabinet <strong>{cabinet_name}</strong> — jour {day} sur LexHub.</p>
        <p>{body}</p>
        {_btn(cta_url, cta)}""",
        preheader=f"Tip J+{day} — activation cabinet",
    )
    return _send_email(to, subject, html, text)


def send_inactivity_winback_email(
    to: str,
    *,
    full_name: str,
    cabinet_name: str,
    days_inactive: int = 14,
) -> bool:
    url = f"{settings.FRONTEND_URL.rstrip('/')}/dashboard"
    subject = f"{_BRAND} — On vous attend · {cabinet_name}"
    text = (
        f"Bonjour {full_name}, aucune activité depuis {days_inactive} j. "
        f"Revenez dicter une plaidoirie : {url}"
    )
    html = _email_shell(
        "Votre cabinet LexHub vous attend",
        f"""<p>Bonjour <strong>{full_name}</strong>,</p>
        <p>Cela fait environ <strong>{days_inactive} jours</strong> que
        <strong>{cabinet_name}</strong> n'a pas utilisé LexHub.</p>
        <p>Une audience approche ? Relancez en dictant 3 minutes — la plaidoirie
        se structure toute seule.</p>
        {_btn(url, "Revenir au tableau de bord")}
        <p style="margin-top:16px;font-size:13px;color:#8A96AB">
        Besoin d'aide ? contact@lexhub.space</p>""",
        preheader="Revenez en 3 minutes — une plaidoirie suffit.",
    )
    return _send_email(to, subject, html, text)


def send_upgrade_checklist_email(
    to: str,
    *,
    full_name: str,
    cabinet_name: str,
    plan_name: str,
) -> bool:
    base = settings.FRONTEND_URL.rstrip("/")
    subject = f"{_BRAND} — Checklist {plan_name} · 4 actions utiles"
    text = (
        f"Bonjour {full_name}, plan {plan_name} actif pour {cabinet_name}. "
        f"Checklist : équipe, 2FA, plaidoirie, branding. {base}/settings#abonnement"
    )
    html = _email_shell(
        f"Bienvenue sur {plan_name} — checklist",
        f"""<p>Bonjour <strong>{full_name}</strong>,</p>
        <p><strong>{cabinet_name}</strong> est sur <strong>{plan_name}</strong>.
        Pour en tirer le maximum :</p>
        <ol style="padding-left:18px;line-height:1.7">
          <li>Inviter un collègue (Équipe)</li>
          <li>Activer la 2FA (Paramètres → Sécurité)</li>
          <li>Dicter / valider une plaidoirie</li>
          <li>Personnaliser le branding cabinet</li>
        </ol>
        {_btn(f"{base}/team", "Ouvrir l'équipe")}
        <p style="margin-top:12px;font-size:13px">
          <a href="{base}/settings#abonnement" style="color:#0B1F4A">Voir l'abonnement</a>
        </p>""",
        preheader=f"4 actions pour maximiser {plan_name}",
    )
    return _send_email(to, subject, html, text)


def send_weekly_cabinet_digest_email(
    to: str,
    *,
    full_name: str,
    cabinet_name: str,
    cases_n: int,
    pleas_n: int,
    docs_n: int,
    events_n: int,
) -> bool:
    url = f"{settings.FRONTEND_URL.rstrip('/')}/dashboard"
    subject = f"{_BRAND} — Semaine LexHub · {cabinet_name}"
    text = (
        f"Bonjour {full_name}, semaine : {cases_n} dossiers, {pleas_n} plaidoiries, "
        f"{docs_n} docs, {events_n} événements. {url}"
    )
    html = _email_shell(
        "Votre semaine LexHub",
        f"""<p>Bonjour <strong>{full_name}</strong>,</p>
        <p>Activité de <strong>{cabinet_name}</strong> (7 derniers jours) :</p>
        <ul style="line-height:1.8">
          <li><strong>{cases_n}</strong> dossier(s) créé(s) / touché(s)</li>
          <li><strong>{pleas_n}</strong> plaidoirie(s)</li>
          <li><strong>{docs_n}</strong> document(s)</li>
          <li><strong>{events_n}</strong> événement(s) agenda</li>
        </ul>
        {_btn(url, "Ouvrir le tableau de bord")}""",
        preheader=f"{pleas_n} plaidoiries · {cases_n} dossiers",
    )
    return _send_email(to, subject, html, text)


def send_changelog_soft_email(
    to: str,
    *,
    full_name: str,
    items: list[str],
) -> bool:
    url = f"{settings.FRONTEND_URL.rstrip('/')}/dashboard"
    bullets = "".join(f"<li>{it}</li>" for it in items[:6])
    subject = f"{_BRAND} — Nouveautés utiles pour votre cabinet"
    text = f"Bonjour {full_name}. Nouveautés : " + " · ".join(items[:4])
    html = _email_shell(
        "Ce qui change sur LexHub",
        f"""<p>Bonjour <strong>{full_name}</strong>,</p>
        <p>Quelques améliorations récentes (sans spam) :</p>
        <ul style="line-height:1.7">{bullets}</ul>
        {_btn(url, "Essayer maintenant")}""",
        preheader="Mises à jour produit — courtes et utiles.",
    )
    return _send_email(to, subject, html, text)


def send_seats_almost_full_email(
    to: str,
    *,
    full_name: str,
    cabinet_name: str,
    role_label: str,
    used: int,
    limit: int,
) -> bool:
    url = f"{settings.FRONTEND_URL.rstrip('/')}/settings#abonnement"
    subject = f"{_BRAND} — Sièges {role_label} presque pleins"
    text = (
        f"Bonjour {full_name}, {used}/{limit} sièges {role_label} sur {cabinet_name}. {url}"
    )
    html = _email_shell(
        f"Sièges {role_label} bientôt saturés",
        f"""<p>Bonjour <strong>{full_name}</strong>,</p>
        <p><strong>{cabinet_name}</strong> utilise <strong>{used}/{limit}</strong>
        sièges <strong>{role_label}</strong>.</p>
        <p>Passez au plan supérieur avant de bloquer une invitation urgente.</p>
        {_btn(url, "Augmenter les sièges")}""",
        preheader=f"{used}/{limit} {role_label}",
    )
    return _send_email(to, subject, html, text)


def send_twofa_nudge_email(
    to: str,
    *,
    full_name: str,
) -> bool:
    url = f"{settings.FRONTEND_URL.rstrip('/')}/settings#securite"
    subject = f"{_BRAND} — Sécurisez votre compte (2FA)"
    text = f"Bonjour {full_name}, activez la double authentification : {url}"
    html = _email_shell(
        "Activez la double authentification",
        f"""<p>Bonjour <strong>{full_name}</strong>,</p>
        <p>Votre compte admin cabinet n'a pas encore la <strong>2FA</strong>.
        En 2 minutes, vous protégez dossiers et plaidoiries même si le mot de passe fuit.</p>
        {_btn(url, "Activer la 2FA")}""",
        preheader="2 minutes pour sécuriser le cabinet.",
    )
    return _send_email(to, subject, html, text)
