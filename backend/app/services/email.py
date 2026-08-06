import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings

logger = logging.getLogger(__name__)


def _send_smtp(to: str, subject: str, html: str, text: str) -> bool:
    if not settings.SMTP_HOST:
        logger.warning("SMTP not configured — email to %s: %s", to, subject)
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_FROM
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
        server.sendmail(settings.SMTP_FROM, [to], msg.as_string())
        server.quit()
        return True
    except Exception as exc:
        logger.error("Email send failed to %s: %s", to, exc)
        return False


def send_verification_email(to: str, token: str) -> bool:
    url = f"{settings.FRONTEND_URL}/confirm-email?token={token}"
    subject = "Sanad — Vérifiez votre adresse email"
    text = f"Vérifiez votre email en cliquant sur : {url}\nLien valable {settings.EMAIL_VERIFY_EXPIRE_HOURS}h."
    html = f"""
    <div style="font-family:Inter,sans-serif;max-width:560px;margin:0 auto">
      <h2 style="color:#006233">Sanad — Avocat AI Assistance</h2>
      <p>Vérifiez votre adresse email professionnelle pour activer votre compte.</p>
      <a href="{url}" style="display:inline-block;background:#006233;color:#fff;padding:12px 24px;
         border-radius:8px;text-decoration:none;font-weight:600">Vérifier mon email</a>
      <p style="color:#666;font-size:12px;margin-top:24px">Lien valable {settings.EMAIL_VERIFY_EXPIRE_HOURS} heures.</p>
    </div>
    """
    return _send_smtp(to, subject, html, text)


def send_password_reset_email(to: str, token: str) -> bool:
    url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    subject = "Sanad — Réinitialisation du mot de passe"
    text = f"Réinitialisez votre mot de passe : {url}\nLien valable {settings.PASSWORD_RESET_EXPIRE_HOURS}h."
    html = f"""
    <div style="font-family:Inter,sans-serif;max-width:560px;margin:0 auto">
      <h2 style="color:#006233">Réinitialisation du mot de passe</h2>
      <p>Cliquez sur le bouton ci-dessous pour définir un nouveau mot de passe.</p>
      <a href="{url}" style="display:inline-block;background:#006233;color:#fff;padding:12px 24px;
         border-radius:8px;text-decoration:none">Réinitialiser</a>
      <p style="color:#666;font-size:12px">Si vous n'avez pas demandé ce lien, ignorez cet email.</p>
    </div>
    """
    return _send_smtp(to, subject, html, text)


def send_otp_email(to: str, code: str, purpose_label: str) -> bool:
    subject = f"Sanad — {purpose_label}"
    text = (
        f"Votre code Sanad : {code}\n"
        f"Valable 15 minutes. Ne le partagez avec personne."
    )
    html = f"""
    <div style="font-family:Inter,sans-serif;max-width:560px;margin:0 auto">
      <h2 style="color:#0B1F4A">Sanad — {purpose_label}</h2>
      <p>Voici votre code de vérification :</p>
      <p style="font-size:28px;font-weight:700;letter-spacing:6px;color:#0B1F4A">{code}</p>
      <p style="color:#666;font-size:12px">Valable 15 minutes. Si vous n'êtes pas à l'origine de cette demande, ignorez cet email.</p>
    </div>
    """
    return _send_smtp(to, subject, html, text)


def send_magic_link_email(to: str, token: str) -> bool:
    url = f"{settings.FRONTEND_URL.rstrip('/')}/magic-login?token={token}"
    subject = "Sanad — Lien de connexion sécurisé"
    text = f"Connectez-vous à Sanad (lien valable 15 min) :\n{url}"
    html = f"""
    <div style="font-family:Inter,sans-serif;max-width:560px;margin:0 auto">
      <h2 style="color:#0B1F4A">Connexion Sanad</h2>
      <p>Cliquez pour vous connecter — aucun mot de passe requis.</p>
      <a href="{url}" style="display:inline-block;background:#0B1F4A;color:#fff;padding:12px 24px;
         border-radius:8px;text-decoration:none;font-weight:600">Se connecter</a>
      <p style="color:#666;font-size:12px;margin-top:24px">Lien à usage unique, valable 15 minutes.</p>
    </div>
    """
    return _send_smtp(to, subject, html, text)


def send_lockout_email(to: str, minutes: int) -> bool:
    subject = "Sanad — Compte temporairement bloqué"
    text = (
        f"Votre compte Sanad a été temporairement bloqué suite à plusieurs tentatives "
        f"de connexion échouées. Réessayez dans environ {minutes} minutes.\n"
        "Si ce n'était pas vous, réinitialisez votre mot de passe immédiatement."
    )
    html = f"""
    <div style="font-family:Inter,sans-serif;max-width:560px;margin:0 auto">
      <h2 style="color:#0B1F4A">Compte temporairement bloqué</h2>
      <p>Plusieurs tentatives de connexion ont échoué. Pour votre sécurité, l'accès est
      suspendu environ <strong>{minutes} minutes</strong>.</p>
      <p style="color:#666;font-size:13px">Si vous n'êtes pas à l'origine de ces tentatives,
      changez votre mot de passe dès que possible.</p>
    </div>
    """
    return _send_smtp(to, subject, html, text)


def send_team_invite_email(to: str, token: str, cabinet_name: str, inviter: str) -> bool:
    url = f"{settings.FRONTEND_URL.rstrip('/')}/activate?token={token}"
    subject = f"Sanad — Invitation à rejoindre {cabinet_name}"
    text = (
        f"{inviter} vous invite à rejoindre {cabinet_name} sur Sanad.\n"
        f"Activez votre compte et choisissez votre mot de passe : {url}"
    )
    html = f"""
    <div style="font-family:Inter,sans-serif;max-width:560px;margin:0 auto">
      <h2 style="color:#006233">Invitation Sanad</h2>
      <p><strong>{inviter}</strong> vous invite à rejoindre le cabinet <strong>{cabinet_name}</strong>.</p>
      <p>Cliquez ci-dessous pour <strong>activer votre compte</strong> et définir votre mot de passe.</p>
      <a href="{url}" style="display:inline-block;background:#C89B3C;color:#0a1612;padding:12px 24px;
         border-radius:8px;text-decoration:none;font-weight:600">Activer mon compte</a>
    </div>
    """
    return _send_smtp(to, subject, html, text)
