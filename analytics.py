import pandas as pd
import plotly.graph_objects as go


COMPETENCIAS = [
    "comprension",
    "morfologia",
    "semantica",
    "textos",
    "literatura",
    "sintaxis",
]


NOMBRES = {
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

    etiquetas = [
        NOMBRES[c]
        for c in COMPETENCIAS
    ]

    valores.append(valores[0])
    etiquetas.append(etiquetas[0])

    fig = go.Figure()

    fig.add_trace(
        go.Scatterpolar(
            r=valores,
            theta=etiquetas,
            fill="toself",
            name="Resultado"
        )
    )

    fig.update_layout(
        title=titulo,
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10]
            )
        ),
        showlegend=False,
        margin=dict(
            l=40,
            r=40,
            t=60,
            b=40
        )
    )

    return fig


def generar_perfil(datos):

    resultado = []

    for c in COMPETENCIAS:

        nota = round(
            float(datos.get(c, 0) or 0),
            2
        )

        if nota < 5:
            nivel = "Necesita refuerzo"
            texto = f"{NOMBRES[c]}: necesita refuerzo."

        elif nota < 8:
            nivel = "Nivel adecuado"
            texto = f"{NOMBRES[c]}: nivel adecuado."

        else:
            nivel = "Fortaleza"
            texto = f"{NOMBRES[c]}: fortaleza."

        resultado.append(
            {
                "competencia": c,
                "nombre": NOMBRES[c],
                "nota": nota,
                "nivel": nivel,
                "texto": texto,
            }
        )

    return resultado
