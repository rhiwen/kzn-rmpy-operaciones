## Pryecto REDMINE -> Mails
* Por: Zeron
* Fecha: 20250421
___
Una solución automatizada basada en FastAPI para generar reportes de proyectos en Redmine y enviarlos por correo.

## 🚀 Características

- Conexión con Redmine vía API
- Procesamiento mensual de issues y tiempo invertido
- Exportación a CSV y XLSX
- Conversión a HTML para visualización rápida
- Envío por email con archivos adjuntos
- Documentado y extensible

## 📦 Requisitos

Instalar dependencias:

```bash
pip install -r requirements.txt
```

## ⚙️ Variables de Entorno

Puede usar un archivo `.env` o definir en su entorno:

```env
REDMINE_URL=https://proyectos.kaizen2b.net
REDMINE_API_KEY=API_KEY_AQUI
EMAIL_SENDER=noreplay@z3r0n.com
EMAIL_PASSWORD=CLAVE_CORREO
EMAIL_RECEIVERS=correo1@ejemplo.com,correo2@ejemplo.com
SMTP_SERVER=smtp.servidor.com
SMTP_PORT=465
```

## 🛠 Uso

Levantar el servidor:

```bash
uvicorn main:app --reload
```

Acceder a:
- `POST /generar-reporte`: Genera el reporte y lo envía por email (opcional)
- `GET /descargar/{filename}`: Descarga el archivo generado

### Ejemplo de request con `curl`:

```bash
curl -X POST http://localhost:8000/generar-reporte -H "Content-Type: application/json" -d '{"send_email": true}'
```

### ESTRUCTURA
```text
redmine_reporter_fastapi/
├── app/
│   ├── __init__.py
│   ├── schemas.py                 # Modelos Pydantic
│   ├── services/
│   │   └── report_service.py      # Lógica principal de reporte
│   ├── utils/
│   │   ├── redmine_client.py      # Acceso a Redmine
│   │   ├── file_manager.py        # Guardado CSV/XLSX/HTML
│   │   └── email_utils.py         # Envío de correo electrónico
├── data/                          # Reportes generados (.csv, .xlsx)
│   └── .gitkeep
├── logs/                          # (futuro uso para logs)
│   └── .gitkeep
├── main.py                        # FastAPI App y rutas
├── requirements.txt
├── README.md
```
## 📧 Envío de Correos

El sistema adjunta automáticamente los archivos generados y envía el reporte a los destinatarios definidos.

---

**Desarrollado por:** [Kaizen2B](https://kaizen2b.com)

### .env

* REPORT_TIME=10:00   # ← poné la hora deseada, formato 24 h