import logging
import os
import smtplib
import ssl
from email.message import EmailMessage
from typing import Sequence, Optional
from app.utils.fecha import generar_fecha_reporte

# Configuración por variables de entorno 
EMAIL_SENDER    = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD  = os.getenv("EMAIL_PASSWORD")
EMAIL_RECEIVERS = os.getenv("EMAIL_RECEIVERS", "").split(",")
SMTP_SERVER     = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT       = int(os.getenv("SMTP_PORT", 465))
USE_STARTTLS    = os.getenv("SMTP_USE_STARTTLS", "false").lower() == "true"
SKIP_VERIFY     = os.getenv("SMTP_SKIP_VERIFY", "false").lower() == "true"

def generar_subject() -> str:
    fecha_reporte = generar_fecha_reporte()
    return f"KZN-REDMINE - Reporte de Avance Proyectos y Tareas al {fecha_reporte}"

def send_report_email(
    subject: str,
    html_body: str,
    attachments: Optional[Sequence[str]] = None,
    to: Optional[Sequence[str]] = None,
) -> None:
    recipients = list(to or EMAIL_RECEIVERS)
    recipients = [r.strip() for r in recipients if r.strip()]
    if not recipients:
        raise RuntimeError("No hay destinatarios configurados (EMAIL_RECEIVERS)")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = EMAIL_SENDER
    msg["To"] = ", ".join(recipients)

    msg.set_content("Este mensaje contiene el reporte en formato HTML.")
    msg.add_alternative(html_body, subtype="html")

    if attachments:
        for path in attachments:
            try:
                with open(path, "rb") as fp:
                    data = fp.read()
                msg.add_attachment(
                    data,
                    maintype="application",
                    subtype="octet-stream",
                    filename=os.path.basename(path),
                )
            except Exception as exc:
                logging.warning("⚠️  No se pudo adjuntar %s: %s", path, exc)

    logging.info("✉️  Enviando correo a %s…", ", ".join(recipients))

    context = ssl._create_unverified_context() if SKIP_VERIFY else ssl.create_default_context()

    try:
        if USE_STARTTLS:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=60) as server:
                server.starttls(context=context)
                server.login(EMAIL_SENDER, EMAIL_PASSWORD)
                server.send_message(msg)
        else:
            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context, timeout=60) as server:
                server.login(EMAIL_SENDER, EMAIL_PASSWORD)
                server.send_message(msg)
    except smtplib.SMTPException as exc:
        logging.exception("❌ Error al enviar correo: %s", exc)
        raise

    logging.info("✅ Correo enviado correctamente")
