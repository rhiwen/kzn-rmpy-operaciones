from typing import List, Dict, Any
import pandas as pd
import re
from app.utils.fecha import generar_fecha_reporte

def data_to_html(rows: List[Dict[str, Any]]) -> str:
    """
    Genera el HTML del reporte de proyectos con corte por VERSION,
    alineando a la izquierda las columnas Proyecto y Version.
    """
    if not rows:
        return "<p>No se encontraron proyectos relevantes.</p>"

    df = pd.DataFrame(rows)
    if "Equipo" not in df.columns:
        return "<p>Error: Falta la columna 'Equipo'.</p>"

    columnas_ordenadas = [
        "Proyecto", "Version", "Fecha de inicio", "Fecha finalización",
        "Tareas abiertas", "Tareas totales", "Progreso tareas", 
        "Tareas modificadas última semana", "Tareas cerradas última semana",
        "Tareas modificadas últimos 30 días", "Tareas cerradas últimos 30 días",
        "Horas estimadas", "Horas insumidas", "Horas consumidas"
    ]

    fecha_reporte = generar_fecha_reporte()
    html = f"""
    <div style='font-family: Arial, sans-serif; font-size: 13px;'>
    <h2 style='margin-bottom: 8px;'>
        KZN - Reporte de Avance: Proyectos y Versiones al {fecha_reporte}
    </h2>
    """

    # Anchos de columna (opcional)
    anchos = {
    "Proyecto": "150px", "Version": "180px", "Fecha de inicio": "90px",
    "Fecha finalización": "90px", "Tareas totales": "70px", "Tareas abiertas": "70px",
    "Tareas modificadas última semana": "70px", "Tareas cerradas última semana": "70px",
    "Tareas modificadas últimos 30 días": "70px", "Tareas cerradas últimos 30 días": "70px",
    "Horas estimadas": "90px", "Horas insumidas": "90px",
    "Progreso tareas": "90px", "Horas consumidas": "90px"
    }

    for equipo, grupo in df.groupby("Equipo"):
        grupo = grupo.drop(columns=["Equipo"])[columnas_ordenadas]

        html += f"<h3 style='margin-top: 20px; margin-bottom: 6px; font-size: 14px;'>{equipo}</h3>"
        html += """
        <table style='border-collapse: collapse; width: 100%; table-layout: fixed;'>
        <thead><tr>
        """
        # Encabezados
        for col in columnas_ordenadas:
            # Si es Proyecto o Version alineamos a la izquierda
            align = "left" if col in ("Proyecto", "Version") else "center"
            html += (
            f"<th style='border: 1px solid #ccc; padding: 4px;"
            f"background-color: #f2f2f2; text-align: {align};"
            f"vertical-align: middle; width: {anchos[col]};'>{col}</th>"
            )
        html += "</tr></thead><tbody>"
        # Línea gruesa debajo del header
        html += (
        "<tr><td colspan='14' style='border: none;"
        "border-bottom: 3px solid #333; padding: 0; height: 1px;'></td></tr>"
        )

        # Orden y sort
        grupo['orden_version'] = grupo.apply(lambda row: (
            0 if row["Version"] == "Sin versión"
            else 1 if row["Fecha de inicio"] is not None
            else 2
        ), axis=1)
        grupo['fecha_sort'] = grupo.apply(lambda row: (
            "" if row["Version"] == "Sin versión"
            else row["Fecha de inicio"] if row["Fecha de inicio"] is not None
            else "9999-12-31"
        ), axis=1)
        grupo_sorted = grupo.sort_values(['Proyecto', 'orden_version', 'fecha_sort'])
        grupo_sorted = grupo_sorted.drop(['orden_version', 'fecha_sort'], axis=1)

        # Filas
        proyecto_actual = None
        for _, row in grupo_sorted.iterrows():
            if proyecto_actual and proyecto_actual != row["Proyecto"]:
                # Línea gruesa entre proyectos
                html += (
                "<tr><td colspan='14' style='border: none;"
                "border-bottom: 3px solid #333; padding: 0; height: 1px;'></td></tr>"
                )
            proyecto_actual = row["Proyecto"]

            html += "<tr>"
            for col in columnas_ordenadas:
                cell = row[col] if row[col] is not None else ""

                # Formateos puntuales
                if col in ("Horas estimadas", "Horas insumidas") and isinstance(cell, (int, float)):
                    cell = f"{cell:.2f}"
                elif col in ("Progreso tareas", "Horas consumidas") and isinstance(cell, str) and "%" in cell:
                    cell = cell.split(".")[0] + "%"

                # Separador Proyecto/Version con salto de línea
                if col in ("Proyecto", "Version") and isinstance(cell, str):
                    m = re.search(r"\s*[-–—]\s*", cell)
                    if m:
                        idx = m.start()
                        parte1 = cell[:idx].strip()
                        parte2 = cell[idx + len(m.group()):].strip()
                        cell = (
                        f"{parte1}<br>"
                        f"<span style='font-size:12px;color:#555;'>{parte2}</span>"
                        )

                # Determinar alineación según columna
                align = "left" if col in ("Proyecto", "Version") else "center"
                html += (
                f"<td style='border: 1px solid #ccc; padding: 2px 4px;"
                f"text-align: {align}; vertical-align: middle;"
                "white-space: normal; overflow-wrap: break-word;'>"
                f"{cell}</td>"
                )
            html += "</tr>"

        # Línea gruesa al final del equipo
        html += (
        "<tr><td colspan='14' style='border: none;"
        "border-bottom: 3px solid #333; padding: 0; height: 1px;'></td></tr>"
        )
        html += "</tbody></table>"

    html += "</div>"
    return html
