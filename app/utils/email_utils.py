# app/utils/email_utils.py
"""
Envío de correos HTML con soporte:
  • SSL directo o STARTTLS
  • Validación opcional de certificado
  • Expansión de alias mediante gestor_mails (get_destinatarios)
  • Compatibilidad retro (send_report_email = send_html_email)
"""

from __future__ import annotations
import os
import ssl
import smtplib
import logging
from email.message import EmailMessage
from typing import List, Sequence, Union, Optional

from app.utils.gestor_mails import get_destinatarios

# ───────────── Config .env ─────────────
EMAIL_SENDER   = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SMTP_SERVER    = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT      = int(os.getenv("SMTP_PORT", 465))
USE_STARTTLS   = os.getenv("SMTP_USE_STARTTLS", "false").lower() == "true"
SKIP_VERIFY    = os.getenv("SMTP_SKIP_VERIFY", "false").lower() == "true"

# ───────────────────────────────────────
def _ssl_context() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    if SKIP_VERIFY:
        logging.warning("⚠️  SSL verification desactivada")
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _normalize_recip(to: Union[str, Sequence[str]]) -> List[str]:
    """
    • str  → cadena 'alias,mail' → get_destinatarios()
    • list → se asume lista de mails finales
    """
    if isinstance(to, str):
        recip = get_destinatarios(to)
    else:
        recip = list(to)
    # Deduplicar y limpiar
    limpios, seen = [], set()
    for m in recip:
        m = m.strip()
        if m and m not in seen:
            seen.add(m)
            limpios.append(m)
    return limpios


# ───────────────────────────────────────
def send_html_email(
    subject: str,
    html_content: str,
    recipients: Union[str, Sequence[str]],
    attachments: Optional[Sequence[str]] = None,
) -> None:
    """Envío principal: admite alias o lista de correos en `recipients`."""
    recip = _normalize_recip(recipients)
    if not recip:
        logging.info("⏭ Sin destinatarios — no se envía correo")
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = EMAIL_SENDER
    msg["To"] = ", ".join(recip)

    msg.set_content("Este correo contiene un reporte en formato HTML.")
    msg.add_alternative(html_content, subtype="html")

    # Adjuntos binarios opcionales
    if attachments:
        for path in attachments:
            try:
                with open(path, "rb") as f:
                    data = f.read()
                msg.add_attachment(
                    data,
                    maintype="application",
                    subtype="octet-stream",
                    filename=os.path.basename(path),
                )
            except Exception as exc:
                logging.warning("⚠️  No se pudo adjuntar %s: %s", path, exc)

    ctx = _ssl_context()
    logging.info("📧 Enviando correo a %s…", ", ".join(recip))

    if USE_STARTTLS:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=60) as server:
            server.starttls(context=ctx)
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
    else:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=ctx, timeout=60) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)

    logging.info("✅ Correo enviado correctamente")


# ────────── Compatibilidad retro ──────────
def send_report_email(
    subject: str,
    html_body: str,
    attachments: Optional[Sequence[str]] = None,
    to: Optional[Union[str, Sequence[str]]] = None,
) -> None:
    """
    Alias para código antiguo que aún invoque send_report_email.
    Si `to` es None intentará leer EMAIL_RECEIVERS del .env.
    """
    if to is None:
        raw = os.getenv("EMAIL_RECEIVERS", "").strip()
        if not raw:
            raise RuntimeError("No hay destinatarios configurados (EMAIL_RECEIVERS vacío) y `to` es None.")
        to = raw
    send_html_email(subject, html_body, to, attachments)
