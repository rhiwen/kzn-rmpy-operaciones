import smtplib
import ssl
from email.message import EmailMessage

# Datos proporcionados
SMTP_SERVER = "k2b21525.ferozo.com"
SMTP_PORT = 465
EMAIL = "prueba123@kaizen2b.net"
PASSWORD = "cRv@4fL6xG"

# Construir mensaje de prueba
msg = EmailMessage()
msg["Subject"] = "✅ Prueba de SMTP exitosa"
msg["From"] = EMAIL
msg["To"] = ipedersen@kaizen2b.com #EMAIL  # Puedes enviarlo a ti mismo para testear #msg["To"] = ", ".join(["destino1@correo.com", "destino2@otro.com"])
msg.set_content("Este es un correo de prueba enviado desde Python.")

try:
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
        server.login(EMAIL, PASSWORD)
        server.send_message(msg)
        print("✅ Correo enviado correctamente.")
except Exception as e:
    print("❌ Error al enviar el correo:", e)