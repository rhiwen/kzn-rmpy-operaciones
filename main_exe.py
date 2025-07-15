from pathlib import Path
from dotenv import load_dotenv
from os import getenv
import logging
import sys
import smtplib
from redminelib.exceptions import ForbiddenError, AuthError, ServerError

# Definimos BASE_DIR compatible con PyInstaller:
# Si corre como EXE toma el directorio del ejecutable, sino el del script.
if getattr(sys, 'frozen', False):
    # sys.executable → ruta al ejecutable dentro del bundle (temporal)
    # exe "onefile": sys.argv[0] es la ruta al EXE real
    BASE_DIR = Path(sys.argv[0]).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent

# debug: por que no lee env?
print("BASE_DIR =", BASE_DIR)
print(".env exists?", (BASE_DIR / ".env").is_file())

# Cargamos las variables de entorno desde el .env en BASE_DIR
env_file = BASE_DIR / ".env"
load_dotenv(env_file)

# debug para ver si lee el env
print("REDMINE_URL:", getenv("REDMINE_URL"))
print("API_KEY:", getenv("API_KEY"))

# Ruta al log de errores (solo se generará si ocurre un error)
log_path = BASE_DIR / "error.log"

# Elimina cualquier log previo al iniciar la ejecución (opcional)
if log_path.exists():
    log_path.unlink()

def main():
    try:
        # Importamos el servicio principal de reporte
        from app.services.report_service import generate_report

        # Ejecutamos el reporte (el envío de mail está embebido en esta función)
        html_content = generate_report(send_email=True)

        # Si no ocurre excepción, simplemente termina sin generar log.
        pass

    # ------------------- CLASIFICACIÓN DE ERRORES -------------------

    # Redmine - error de credenciales, API inválida, falta de permisos
    except (ForbiddenError, AuthError) as e:
        _log("❌ Error de Redmine (credenciales o permisos):", e)
        sys.exit(1)

    # Redmine - servidor no responde o error del backend de Redmine
    except ServerError as e:
        _log("❌ Error de Redmine (servidor Redmine no responde):", e)
        sys.exit(1)

    # SMTP - error de autenticación con el servidor de correo
    except smtplib.SMTPAuthenticationError as e:
        _log("❌ Error SMTP (credenciales email incorrectas):", e)
        sys.exit(1)

    # SMTP - error de conexión al servidor de correo
    except smtplib.SMTPConnectError as e:
        _log("❌ Error SMTP (no se pudo conectar al servidor SMTP):", e)
        sys.exit(1)

    # Sistema operativo - error de permisos de escritura o acceso
    except PermissionError as e:
        _log("❌ Error de permisos de sistema (problema al ejecutar o escribir archivos):", e)
        sys.exit(1)

    # Sistema operativo - archivo faltante
    except FileNotFoundError as e:
        _log("❌ Error de archivo no encontrado:", e)
        sys.exit(1)

    # Captura general - cualquier otro error inesperado
    except Exception as e:
        _log("💥 Error inesperado:", e)
        sys.exit(1)

# ------------------- FUNCIÓN AUXILIAR DE LOG -------------------

def _log(mensaje, exception_obj):
    """
    Configura el logger solo si ocurre un error,
    y registra el mensaje con el detalle de la excepción.
    """
    logging.basicConfig(
        level=logging.ERROR,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(log_path, encoding='utf-8')]
    )
    logging.error(mensaje)
    logging.exception(exception_obj)

# ------------------- PUNTO DE ENTRADA -------------------

if __name__ == "__main__":
    main()
