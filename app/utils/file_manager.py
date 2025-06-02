from typing import List, Dict, Any
import pandas as pd
import re

# Definición de la función principal que transforma datos en HTML
def data_to_html(rows: List[Dict[str, Any]]) -> str:

    # Si no hay datos, devuelve un mensaje informativo
    if not rows:
        return "<p>No se encontraron proyectos relevantes.</p>"

    # Convierte la lista de diccionarios en un dataframe de pandas
    df = pd.DataFrame(rows)

    # Verifica que exista la columna 'Equipo' (clave para la agrupación)
    if "Equipo" not in df.columns:
        return "<p>Error: Falta la columna 'Equipo'.</p>"

    # Define el orden de columnas que se utilizarán en la tabla final
    columnas_ordenadas = [
        "Proyecto Padre", "Proyecto", "Fecha de inicio", "Fecha finalización",
        "Tareas totales", "Tareas abiertas", "Tareas modificadas última semana",
        "Tareas cerradas última semana", "Tareas modificadas últimos 30 días",
        "Tareas cerradas últimos 30 días", "Horas estimadas", "Horas insumidas",
        "Progreso tareas", "Horas consumidas"
    ]

    # Inicia el HTML con encabezado general del reporte
    html = """
    <div style='font-family: Arial, sans-serif; font-size: 13px;'>
    <h2 style='margin-bottom: 8px;'>Reporte de proyectos</h2>
    """

    # Agrupa el dataframe por 'Equipo' para generar un bloque por equipo
    for equipo, grupo in df.groupby("Equipo"):
        # Elimina la columna de agrupación y reordena las columnas según la lista definida
        grupo = grupo.drop(columns=["Equipo"])
        grupo = grupo[columnas_ordenadas]

        # Agrega un título por cada equipo
        html += f"<h3 style='margin-top: 20px; margin-bottom: 6px; font-size: 14px;'>{equipo}</h3>"

        # Comienza la tabla HTML para el equipo actual
        html += """
        <table style='border-collapse: collapse; width: 100%; table-layout: fixed;'>
        <thead><tr>
        """

        # Define anchos fijos por columna para alinear bien el contenido
        anchos = {
            "Proyecto Padre": "180px",
            "Proyecto": "180px",
            "Fecha de inicio": "90px",
            "Fecha finalización": "90px",
            "Tareas totales": "70px",
            "Tareas abiertas": "70px",
            "Tareas modificadas última semana": "70px",
            "Tareas cerradas última semana": "70px",
            "Tareas modificadas últimos 30 días": "70px",
            "Tareas cerradas últimos 30 días": "70px",
            "Horas estimadas": "90px",
            "Horas insumidas": "90px",
            "Progreso tareas": "90px",
            "Horas consumidas": "90px"
        }

        # Construye el encabezado de la tabla con los nombres de columnas
        for col in columnas_ordenadas:
            html += (
                f"<th style='border: 1px solid #ccc; padding: 4px; "
                f"background-color: #f2f2f2; text-align: left; vertical-align: middle; "
                f"width: {anchos[col]};'>{col}</th>"
            )
        html += "</tr></thead><tbody>"

        # Itera por cada fila del grupo actual (equipo)
        for _, row in grupo.iterrows():
            html += "<tr>"
            for col in columnas_ordenadas:
                cell = row[col]
                valor = cell if cell is not None else ""

                # Para columnas Proyecto y Proyecto Padre aplica partición si hay separadores ( - – — )
                if col in ["Proyecto", "Proyecto Padre"] and isinstance(valor, str):
                    match = re.search(r"\s*[-–—]\s*", valor)
                    if match:
                        idx = match.start()
                        parte1 = valor[:idx].strip()
                        parte2 = valor[idx + len(match.group()):].strip()
                        valor = (
                            f"{parte1}<br>"
                            f"<span style='font-size:12px;color:#555;'>{parte2}</span>"
                        )

                # Genera la celda de la tabla HTML, permitiendo saltos de línea para textos largos
                html += (
                    f"<td style='border: 1px solid #ccc; padding: 2px 4px; "
                    f"text-align: left; vertical-align: middle; white-space: normal; overflow-wrap: break-word;'>"
                    f"{valor}</td>"
                )
            html += "</tr>"

        # Cierra el bloque de tabla para el equipo actual
        html += "</tbody></table>"

    # Cierra el div principal
    html += "</div>"
    return html
