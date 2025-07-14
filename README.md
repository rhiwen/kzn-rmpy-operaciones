# Reportes RM-PY -> Operaciones - Avance por Versión

* Por: IP / RR
* Fecha: 2025/07/14
___

Sistema automatizado basado en FastAPI para generar reportes de avance de proyectos desde Redmine y enviarlos por email.

## 🚀 Características

- Conexión con Redmine vía API
- Procesamiento de issues agrupados por versión
- Cálculo de métricas de avance y tiempo invertido
- Generación de reportes HTML con formato optimizado para email
- Envío automático por correo electrónico
- Filtrado por equipos específicos (DATA, CONSULTORIA, DESARROLLO, TECNOLOGIA)
- Cache de time entries para optimizar rendimiento

## 📦 Requisitos

Instalar dependencias:
```bash
pip install -r requirements.txt
```

## ⚙️ Variables de Entorno

Configurar en archivo `.env`:
```env
# REDMINE
REDMINE_URL=https://proyectos.ejemplo.com
REDMINE_API_KEY=tu_api_key_aqui

# SMTP
EMAIL_SENDER=reportes@ejemplo.com
EMAIL_PASSWORD=tu_password_smtp
SMTP_SERVER=smtp.ejemplo.com
SMTP_PORT=465
SMTP_USE_STARTTLS=false
SMTP_SKIP_VERIFY=true

# DESTINATARIOS POR EQUIPO. Se admiten grupos: consultoria, desarrollo, tecnologia, data
EMAIL_CONSULTORIA=consultoria,user1@ejemplo.com
EMAIL_DESARROLLO=desarrollo,user1@ejemplo.com,user2@ejemplo.com
EMAIL_TECNOLOGIA=tecnologia,user1@ejemplo.com,user2@ejemplo.com
EMAIL_DATA=data,user1@ejemplo.com,user2@ejemplo.com

# Dominio para construir mails desde login
MAIL_DOMAIN=@ejemplo.com
```

## 🛠 Uso

Levantar el servidor:
```bash
uvicorn main:app --reload
```

Endpoints disponibles:
- `POST /generar-reporte`: Genera el reporte y lo envía por email
- `GET /descargar/{filename}`: Descarga archivo generado

### Ejemplo con `curl`:
```bash
curl -X POST http://localhost:8000/generar-reporte \
  -H "Content-Type: application/json" \
  -d '{"send_email": true}'
```

## 📊 Estructura del Reporte

El reporte incluye las siguientes columnas:
- **Proyecto y Versión**: Agrupados por fixed_version
- **Fechas**: Inicio y finalización calculadas por versión
- **Tareas**: Totales, abiertas, modificadas y cerradas (última semana y 30 días)
- **Progreso**: Porcentaje de completitud de tareas
- **Horas**: Estimadas, invertidas y porcentaje de consumo

### Lógica de Filtrado

- Solo proyectos activos (status=1)
- Equipos que contengan: DATA, CONSULTORIA, DESARROLLO, TECNOLOGIA
- Excluye proyectos padre (que tienen subproyectos)
- Agrupa por versión dentro de cada proyecto

### Períodos de Cálculo

- **Última semana**: Domingo a sábado anterior
- **Últimos 30 días**: Desde hace 30 días hasta hoy
- **Estados cerrados**: IDs 6, 5, 21, 9

## 📁 Estructura del Proyecto

```text
redmine_reporter_fastapi/
├── app/
│   ├── __init__.py
│   ├── schemas.py                 # Modelos Pydantic
│   ├── services/
│   │   └── report_service.py      # Lógica principal de reporte
│   ├── utils/
│   │   ├── redmine_client.py      # Procesamiento de proyectos Redmine
│   │   ├── file_manager.py        # Generación HTML y formateo
│   │   ├── email_utils.py         # Envío de correo electrónico
│   │   ├── cache_manager.py       # Cache de time entries
│   │   └── fecha.py               # Utilidades de fecha
├── data/                          # Reportes generados
│   └── .gitkeep
├── logs/                          # Logs del sistema
│   └── .gitkeep
├── main.py                        # FastAPI App y rutas
├── requirements.txt
├── README.md
└── .env.example
```

## 📧 Envío de Correos

El sistema genera reportes HTML optimizados para Gmail con:
- Estilos inline para compatibilidad
- Agrupación por equipo
- Líneas divisorias entre proyectos
- Formato tabular con anchos fijos

## 🔧 Configuración Adicional

### Cache de Time Entries
El sistema implementa cache para optimizar las consultas de tiempo invertido. Se puede configurar el período de cache modificando el parámetro `months` en `get_cached_time_entries()`.

### Personalización de Estados
Los estados de tareas cerradas se pueden modificar en la constante del archivo `redmine_client.py`:
```python
# Estados cerrados: (6, 5, 21, 9)
```

---

**Desarrollado por:** [Kaizen2B](https://kaizen2b.com)