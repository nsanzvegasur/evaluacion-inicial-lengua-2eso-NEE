import csv
import io
import os
import re
import unicodedata
from datetime import datetime

import pandas as pd
import streamlit as st

from examen2ESO_NEE import EXAMEN
COMPETENCIAS = [
    "comprension",
    "morfologia",
    "semantica",
    "textos",
    "literatura",
    "sintaxis",
]

NOMBRES_COMPETENCIAS = {
    "comprension": "Comprensión",
    "morfologia": "Morfología",
    "semantica": "Semántica",
    "textos": "Textos",
    "literatura": "Literatura",
    "sintaxis": "Sintaxis",
}


def radar_chart(datos, titulo="Perfil competencial"):
    valores = [
        float(datos.get(c, 0) or 0)
        for c in COMPETENCIAS
    ]
    etiquetas = [NOMBRES_COMPETENCIAS[c] for c in COMPETENCIAS]
    try:
        import plotly.graph_objects as go
        fig = go.Figure()
        fig.add_trace(
            go.Scatterpolar(
                r=valores + [valores[0]],
                theta=etiquetas + [etiquetas[0]],
                fill="toself",
                name="Resultado",
            )
        )
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
            title=titulo,
            showlegend=False,
        )
        return fig
    except Exception:
        return None


def nivel_competencia(nota):
    try:
        nota = float(nota)
    except (TypeError, ValueError):
        return "Sin datos"
    if nota >= 8:
        return "Alto"
    if nota >= 6:
        return "Medio"
    if nota >= 5:
        return "Básico"
    return "Inicial"


def comparativa(fila_alumno, df_anon):
    try:
        import plotly.graph_objects as go
        notas = []
        medias = []
        for c in COMPETENCIAS:
            col = f"nota_{c}"
            if col not in df_anon.columns:
                continue
            valor = float(fila_alumno.get(col, 0) or 0)
            serie = pd.to_numeric(df_anon[col], errors="coerce").dropna()
            if serie.empty:
                media = 0
            else:
                media = float(serie.mean())
            notas.append(valor)
            medias.append(media)
        if not notas:
            return None
        fig = go.Figure()
        fig.add_trace(go.Bar(name="Alumno", x=COMPETENCIAS[:len(notas)], y=notas))
        fig.add_trace(go.Bar(name="Media", x=COMPETENCIAS[:len(medias)], y=medias))
        fig.update_layout(barmode="group", yaxis=dict(range=[0, 10]))
        return fig
    except Exception:
        return None

# =========================================================
# CONFIGURACIÓN
# =========================================================

CSV_FILE = "results.csv"
EXAM = EXAMEN["2ESO_NEE"]


# =========================================================
# PUNTUACIÓN
# =========================================================

PESOS = {
    "comprension": 2.0,
    "morfologia": 2.5,
    "semantica": 1.0,
    "textos": 1.5,
    "literatura": 2.0,
    "sintaxis": 1.0,
}


NOMBRES = {
    "comprension": "Comprensión",
    "morfologia": "Morfología",
    "semantica": "Semántica",
    "textos": "Textos",
    "literatura": "Literatura",
    "sintaxis": "Sintaxis",
}


# =========================================================
# ESTILO
# =========================================================

st.markdown(
    """
    <style>
    html, body, [class*="css"] {
        font-family: "Open Sans", sans-serif;
    }

    .stApp {
        font-size: 1.08rem;
    }

    .titulo-principal {
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }

    .subtitulo {
        color: #666;
        margin-bottom: 1.4rem;
    }

    .bloque {
        padding: 0.5rem 0;
    }

    h1, h2, h3 {
        font-family: "Open Sans", sans-serif;
    }

    textarea, input {
        font-size: 1.05rem !important;
    }

    div[data-baseweb="select"] {
        font-size: 1.05rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# NORMALIZACIÓN
# =========================================================

def normalizar(valor):
    if valor is None:
        return ""

    texto = str(valor).strip().lower()

    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(
        c for c in texto
        if unicodedata.category(c) != "Mn"
    )

    texto = re.sub(r"\s+", " ", texto)

    return texto.strip()


def lista_normalizada(valor):
    if valor is None:
        return []

    texto = str(valor).strip()

    if not texto:
        return []

    return [
        normalizar(x)
        for x in re.split(r"[,;\n]+", texto)
        if normalizar(x)
    ]


# =========================================================
# LÓGICA ORIGINAL DEL EXAMEN
# =========================================================

"""
El resto del núcleo original permanece sin cambios.
"""
