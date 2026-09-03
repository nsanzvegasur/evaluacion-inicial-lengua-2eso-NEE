import csv
import io
import os
import re
import unicodedata
from datetime import datetime

import pandas as pd
import streamlit as st

from analytics import radar_chart, generar_perfil
from examen2ESO_NEE import EXAMEN


# ============================================================
# CONFIGURACIÓN
# ============================================================

st.set_page_config(
    page_title="Evaluación inicial de Lengua - 2.º ESO NEE",
    page_icon="📚",
    layout="centered",
)


CSV_FILE = "results.csv"

EXAM = EXAMEN["2ESO_NEE"]


# ============================================================
# PUNTUACIÓN
# ============================================================

PESOS = {
    "comprension": 2.0,
    "morfologia": 2.0,
    "determinantes": 0.5,
    "semantica": 1.0,
    "textos": 1.0,
    "literatura": 2.0,
    "sintaxis": 1.0,
    "dialogo": 0.5,
}


# ============================================================
# ESTILO
# ============================================================

st.markdown(
    """
    <style>

    @import url('https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Open Sans', Verdana, Arial, sans-serif !important;
    }

    .stApp {
        font-family: 'Open Sans', Verdana, Arial, sans-serif !important;
    }

    /* Texto general */
    .stMarkdown,
    .stText,
    p,
    li,
    label,
    .stCaption {
        font-family: 'Open Sans', Verdana, Arial, sans-serif !important;
        font-size: 16px !important;
        line-height: 1.65 !important;
    }

    /* Títulos de las preguntas */
    .pregunta {
        font-family: 'Open Sans', Verdana, Arial, sans-serif !important;
        font-size: 19px !important;
        font-weight: 600 !important;
        line-height: 1.55 !important;
        margin-top: 22px !important;
        margin-bottom: 10px !important;
    }

    /* Texto de los ejercicios */
    .ejercicio {
        font-family: 'Open Sans', Verdana, Arial, sans-serif !important;
        font-size: 18px !important;
        line-height: 1.7 !important;
        padding: 14px 18px !important;
        margin: 12px 0 18px 0 !important;
        border-radius: 8px;
        border: 1px solid rgba(128,128,128,0.25);
    }

    /* Enunciados de sección */
    .subtitulo {
        font-family: 'Open Sans', Verdana, Arial, sans-serif !important;
        font-size: 21px !important;
        font-weight: 700 !important;
        margin-top: 30px !important;
        margin-bottom: 18px !important;
    }

    /* Separación entre bloques */
    .bloque-examen {
        margin-top: 30px !important;
        margin-bottom: 35px !important;
        padding-bottom: 20px !important;
    }

    /* Campos de respuesta */
    .stTextInput input,
    .stTextArea textarea,
    .stSelectbox select {
        font-family: 'Open Sans', Verdana, Arial, sans-serif !important;
        font-size: 16px !important;
    }

    /* Opciones de los selectbox */
    div[data-baseweb="select"] {
        font-size: 16px !important;
    }

    /* Botones */
    .stButton button {
        font-family: 'Open Sans', Verdana, Arial, sans-serif !important;
        font-size: 17px !important;
        font-weight: 600 !important;
        padding: 10px 22px !important;
    }

    </style>
    """,
    unsafe_allow_html=True
)

# ============================================================
# NORMALIZACIÓN
# ============================================================

def normalizar(valor):

    if valor is None:
        return ""

    texto = str(valor).strip().lower()

    texto = unicodedata.normalize(
        "NFD",
        texto
    )

    texto = "".join(
        c for c in texto
        if unicodedata.category(c) != "Mn"
    )

    texto = texto.replace("º", "")
    texto = texto.replace("ª", "")

    texto = re.sub(
        r"\s+",
        " ",
        texto
    )

    return texto.strip()


def dividir_lista(valor):

    if valor is None:
        return []

    texto = str(valor).strip()

    if not texto:
        return []

    partes = re.split(
        r"[,;\n]+",
        texto
    )

    return [
        normalizar(p)
        for p in partes
        if normalizar(p)
    ]


def exacta(valor, *alternativas):

    v = normalizar(valor)

    if not v:
        return False

    return any(
        v == normalizar(a)
        for a in alternativas
    )


def contiene(valor, *alternativas):

    v = normalizar(valor)

    if not v:
        return False

    return any(
        normalizar(a) in v
        for a in alternativas
    )


# ============================================================
# MÉTRICA
# ============================================================

def normalizar_metrica(valor):

    if valor is None:
        return ""

    texto = str(valor).strip().upper()

    texto = re.sub(
        r"[;,/]+",
        " ",
        texto
    )

    texto = re.sub(
        r"\s+",
        " ",
        texto
    )

    return texto.strip()


def corregir_metrica(valor):

    normalizada = normalizar_metrica(valor)

    opciones = {
        "10A 10B 10A 10B",
    }

    return normalizada in opciones


# ============================================================
# CORRECCIÓN DE COMPRENSIÓN
# ============================================================

def corregir_comprension(respuestas):

    puntos = 0.0

    # c1: lugar
    if contiene(
        respuestas.get("c1", ""),
        "estacion",
        "estación",
        "tren",
        "vagon",
        "vagón"
    ):
        puntos += 0.5

    # c2: personajes
    personajes = dividir_lista(
        respuestas.get("c2", "")
    )

    tiene_hombre = any(
        "hombre" in x or
        "joven" in x
        for x in personajes
    )

    tiene_anciana = any(
        "anciana" in x
        for x in personajes
    )

    puntos += 0.5 * (
        (int(tiene_hombre) + int(tiene_anciana))
        / 2
    )

    # c3: cuándo
    if contiene(
        respuestas.get("c3", ""),
        "temprano",
        "madrugada",
        "amanecer"
    ):
        puntos += 0.5

    # c4: acciones
    acciones = dividir_lista(
        respuestas.get("c4", "")
    )

    criterios_acciones = [
        "llego",
        "llegó",
        "viajaban",
        "llevaba",
        "parecia",
        "parecía",
        "dormia",
        "dormía",
        "bajo",
        "bajó",
    ]

    encontradas = set()

    for accion in acciones:

        for criterio in criterios_acciones:

            if (
                accion == normalizar(criterio)
                or normalizar(criterio) in accion
            ):
                encontradas.add(
                    normalizar(criterio)
                )

    puntos += min(
        len(encontradas),
        3
    ) / 3 * 0.5

    return round(
        min(puntos, 2.0),
        2
    )


# ============================================================
# CORRECCIÓN DE MORFOLOGÍA
# ============================================================

def corregir_morfologia(respuestas):

    puntos = 0.0

    respuestas_correctas = {

        "m1": {
            "Lexema": ["silenci", "silenc"],
            "Morfemas": ["o"],
            "Estructura": ["simple"],
            "Categoría gramatical": ["sustantivo", "nombre"],
            "V/I": ["variable"],
        },

        "m2": {
            "Lexema": ["mochil"],
            "Morfemas": ["a", "s", "a-s", "as"],
            "Estructura": ["simple"],
            "Categoría gramatical": ["sustantivo", "nombre"],
            "V/I": ["variable"],
        },

        "m3": {
            "Lexema": ["conoc"],
            "Morfemas": ["des", "ido", "des-ido", "des ido"],
            "Estructura": ["derivada"],
            "Categoría gramatical": ["adjetivo"],
            "V/I": ["variable"],
        },
    }

    campos_por_palabra = 5

    for palabra_id, correctas in respuestas_correctas.items():

        datos = respuestas.get(
            palabra_id,
            {}
        )

        aciertos = 0

        for campo, alternativas in correctas.items():

            respuesta = datos.get(
                campo,
                ""
            )

            if exacta(
                respuesta,
                *alternativas
            ):
                aciertos += 1

        puntos += (
            aciertos / campos_por_palabra
        ) * (
            2.0 / 3
        )

    return round(
        min(puntos, 2.0),
        2
    )


# ============================================================
# DETERMINANTES Y PRONOMBRES
# ============================================================

def corregir_determinantes(respuestas):

    puntos = 0.0

    if exacta(
        respuestas.get("dp1", ""),
        "determinante"
    ):
        puntos += 0.25

    if exacta(
        respuestas.get("dp2", ""),
        "pronombre"
    ):
        puntos += 0.25

    return puntos


# ============================================================
# SEMÁNTICA
# ============================================================

def corregir_semantica(respuestas):

    puntos = 0.0

    if exacta(
        respuestas.get("s1", ""),
        "antonimia"
    ):
        puntos += 1 / 3

    if exacta(
        respuestas.get("s2", ""),
        "campo semántico"
    ):
        puntos += 1 / 3

    if exacta(
        respuestas.get("s3", ""),
        "polisemia"
    ):
        puntos += 1 / 3

    return round(
        puntos,
        2
    )


# ============================================================
# TIPOS DE TEXTO
# ============================================================

def corregir_textos(respuestas):

    puntos = 0.0

    if exacta(
        respuestas.get("t1", ""),
        "instructivo"
    ):
        puntos += 0.5

    if exacta(
        respuestas.get("t2", ""),
        "expositivo"
    ):
        puntos += 0.5

    return puntos


# ============================================================
# LITERATURA
# ============================================================

def corregir_literatura(respuestas):

    puntos = 0.0

    # l1: versos
    if exacta(
        respuestas.get("l1", ""),
        "4"
    ):
        puntos += 0.25

    # l2: arte mayor
    if exacta(
        respuestas.get("l2", ""),
        "arte mayor"
    ):
        puntos += 0.25

    # l3: métrica
    if corregir_metrica(
        respuestas.get("l3", "")
    ):
        puntos += 0.35

    # l4: rima
    if exacta(
        respuestas.get("l4", ""),
        "consonante"
    ):
        puntos += 0.25

    # l5: sinalefa
    if contiene(
        respuestas.get("l5", ""),
        "sobre el",
        "mira el"
    ):
        puntos += 0.45

    # l6: personificación
    if contiene(
        respuestas.get("l6", ""),
        "viento susurra",
        "viento susurra cerca",
    ):
        puntos += 0.45

    return round(
        min(puntos, 2.0),
        2
    )


# ============================================================
# SINTAXIS
# ============================================================

def corregir_sintaxis(respuestas):

    puntos = 0.0

    # El examen actual contiene x1-x7.
    # Se corrigen únicamente los elementos existentes.

    correctas = {
        "x1": "frase",
        "x2": "oración",
        "x3": "oración",
        "x4": "interrogativa",
        "x5": "exclamativa",
        "x6": "enunciativa",
        "x7": "exhortativa",
    }

    if not correctas:
        return 0.0

    valor_por_pregunta = 1.0 / len(correctas)

    for pregunta_id, correcta in correctas.items():

        if pregunta_id not in respuestas:
            continue

        if exacta(
            respuestas.get(pregunta_id, ""),
            correcta
        ):
            puntos += valor_por_pregunta

    return round(
        puntos,
        2
    )


# ============================================================
# DIÁLOGO
# ============================================================

def corregir_estilo_indirecto(valor):

    texto = normalizar(valor)

    if not texto:
        return 0.0

    criterios = [
        "carlos" in texto,
        any(
            verbo in texto
            for verbo in [
                "dijo",
                "afirmo",
                "afirmó",
                "comento",
                "comentó",
                "respondio",
                "respondió",
            ]
        ),
        "que" in texto,
        "habia hecho" in texto,
        "lo habia hecho" in texto,
        "día anterior" in texto,
        "dia anterior" in texto,
    ]

    return sum(criterios) / len(criterios)


def corregir_dialogo(respuestas):

    puntos = 0.0

    interlocutores = dividir_lista(
        respuestas.get("d1", "")
    )

    tiene_lucia = any(
        "lucia" in x
        for x in interlocutores
    )

    tiene_carlos = any(
        "carlos" in x
        for x in interlocutores
    )

    puntos += 0.10 * (
        (int(tiene_lucia) + int(tiene_carlos))
        / 2
    )

    if exacta(
        respuestas.get("d2", ""),
        "6"
    ):
        puntos += 0.10

    puntos += (
        corregir_estilo_indirecto(
            respuestas.get("d3", "")
        )
        * 0.30
    )

    return round(
        min(puntos, 0.5),
        2
    )


# ============================================================
# CORRECCIÓN COMPLETA
# ============================================================

def corregir_examen(respuestas):

    puntos = {}

    puntos["comprension"] = corregir_comprension(
        respuestas
    )

    puntos["morfologia"] = corregir_morfologia(
        respuestas.get("morfologia", {})
    )

    puntos["determinantes"] = corregir_determinantes(
        respuestas
    )

    puntos["semantica"] = corregir_semantica(
        respuestas
    )

    puntos["textos"] = corregir_textos(
        respuestas
    )

    puntos["literatura"] = corregir_literatura(
        respuestas
    )

    puntos["sintaxis"] = corregir_sintaxis(
        respuestas
    )

    puntos["dialogo"] = corregir_dialogo(
        respuestas
    )

    nota = sum(
        puntos.values()
    )

    return puntos, round(
        min(nota, 10.0),
        2
    )


# ============================================================
# CSV
# ============================================================

def cargar_resultados():

    columnas = [
        "name",
        "group",
        "date",
        "comprension",
        "morfologia",
        "determinantes",
        "semantica",
        "textos",
        "literatura",
        "sintaxis",
        "dialogo",
        "total",
    ]

    if not os.path.exists(CSV_FILE):
        return pd.DataFrame(
            columns=columnas
        )

    try:
        df = pd.read_csv(
            CSV_FILE
        )

        return df

    except Exception:
        return pd.DataFrame(
            columns=columnas
        )


def guardar_resultado(fila):

    df = cargar_resultados()

    df = pd.concat(
        [
            df,
            pd.DataFrame([fila])
        ],
        ignore_index=True
    )

    df.to_csv(
        CSV_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    return df


def csv_individual(fila):

    salida = io.StringIO()

    writer = csv.DictWriter(
        salida,
        fieldnames=list(fila.keys())
    )

    writer.writeheader()
    writer.writerow(fila)

    return salida.getvalue().encode(
        "utf-8-sig"
    )


# ============================================================
# COMPARATIVA ANÓNIMA
# ============================================================

def grafico_comparativa_anónima(
    puntos,
    df
):

    competencias = [
        "comprension",
        "morfologia",
        "semantica",
        "textos",
        "literatura",
        "sintaxis",
    ]

    nombres = [
        "Comprensión",
        "Morfología",
        "Semántica",
        "Textos",
        "Literatura",
        "Sintaxis",
    ]

    alumno = [
        float(
            puntos.get(c, 0)
        )
        for c in competencias
    ]

    medias = []

    for c in competencias:

        if (
            df.empty
            or c not in df.columns
        ):
            medias.append(0)
            continue

        serie = pd.to_numeric(
            df[c],
            errors="coerce"
        )

        medias.append(
            float(
                serie.mean()
            )
            if not serie.dropna().empty
            else 0
        )

    import plotly.graph_objects as go

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=nombres,
            y=alumno,
            name="Tu resultado"
        )
    )

    fig.add_trace(
        go.Bar(
            x=nombres,
            y=medias,
            name="Media del grupo"
        )
    )

    fig.update_layout(
        title="Resultado y media del grupo",
        barmode="group",
        yaxis=dict(
            title="Puntuación",
            range=[0, 2.5]
        ),
        margin=dict(
            l=40,
            r=40,
            t=60,
            b=80
        ),
    )

    return fig


# ============================================================
# PANTALLA DE RESULTADOS
# ============================================================

if st.session_state.get(
    "examen_enviado",
    False
):

    puntos = st.session_state[
        "puntos"
    ]

    nota_final = st.session_state[
        "nota_final"
    ]

    fila = st.session_state[
        "fila"
    ]

    st.markdown(
        '<div class="titulo-principal">📊 Resultado de la evaluación</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        f'<div class="resultado-final">Nota final: {nota_final:.2f} / 10</div>',
        unsafe_allow_html=True
    )

    st.success(
        "El examen se ha entregado correctamente."
    )

    st.divider()

    st.subheader(
        "Resultados por bloques"
    )

    nombres_bloques = [
        ("comprension", "Comprensión lectora"),
        ("morfologia", "Morfología"),
        ("determinantes", "Determinantes y pronombres"),
        ("semantica", "Semántica"),
        ("textos", "Tipos de texto"),
        ("literatura", "Literatura"),
        ("sintaxis", "Sintaxis"),
        ("dialogo", "Diálogo"),
    ]

    columnas = st.columns(4)

    for i, (
        clave,
        nombre
    ) in enumerate(nombres_bloques):

        columnas[
            i % 4
        ].metric(
            nombre,
            f"{puntos.get(clave, 0):.2f}"
        )

    st.divider()

    # --------------------------------------------------------
    # RADAR
    # --------------------------------------------------------

    st.subheader(
        "Perfil competencial"
    )

    datos_radar = {
        "comprension": (
            puntos.get("comprension", 0)
            / PESOS["comprension"]
            * 10
        ),
        "morfologia": (
            puntos.get("morfologia", 0)
            / PESOS["morfologia"]
            * 10
        ),
        "semantica": (
            puntos.get("semantica", 0)
            / PESOS["semantica"]
            * 10
        ),
        "textos": (
            puntos.get("textos", 0)
            / PESOS["textos"]
            * 10
        ),
        "literatura": (
            puntos.get("literatura", 0)
            / PESOS["literatura"]
            * 10
        ),
        "sintaxis": (
            puntos.get("sintaxis", 0)
            / PESOS["sintaxis"]
            * 10
        ),
    }

    fig_radar = radar_chart(
        datos_radar,
        "Perfil competencial"
    )

    st.plotly_chart(
        fig_radar,
        use_container_width=True
    )

    # --------------------------------------------------------
    # PERFIL
    # --------------------------------------------------------

    perfil = generar_perfil(
        datos_radar
    )

    st.subheader(
        "🧠 Perfil"
    )

    for elemento in perfil:

        st.write(
            f"**{elemento['nombre']}**: "
            f"{elemento['nivel']}."
        )

    # --------------------------------------------------------
    # COMPARATIVA ANÓNIMA
    # --------------------------------------------------------

    df_resultados = cargar_resultados()

    if (
        not df_resultados.empty
        and len(df_resultados) > 1
    ):

        st.divider()

        st.subheader(
            "📊 Comparativa con el grupo"
        )

        st.caption(
            "La comparativa es anónima: "
            "no se muestran nombres de alumnos."
        )

        figura = grafico_comparativa_anónima(
            puntos,
            df_resultados
        )

        st.plotly_chart(
            figura,
            use_container_width=True
        )

    # --------------------------------------------------------
    # DESCARGA CSV
    # --------------------------------------------------------

    st.divider()

    st.subheader(
        "📥 Descargar resultado"
    )

    st.download_button(
        "⬇️ Descargar mi resultado CSV",
        data=csv_individual(fila),
        file_name="resultado_2ESO_NEE.csv",
        mime="text/csv",
        use_container_width=True,
    )

    # --------------------------------------------------------
    # DESCARGA EXCEL
    # --------------------------------------------------------

    try:

        salida_excel = io.BytesIO()

        with pd.ExcelWriter(
            salida_excel,
            engine="openpyxl"
        ) as writer:

            pd.DataFrame(
                [fila]
            ).to_excel(
                writer,
                index=False,
                sheet_name="Resultado"
            )

        salida_excel.seek(0)

        st.download_button(
            "📊 Descargar resultado Excel",
            data=salida_excel,
            file_name="resultado_2ESO_NEE.xlsx",
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            use_container_width=True,
        )

    except Exception:
        pass

    st.stop()


# ============================================================
# CABECERA
# ============================================================

st.markdown(
    '<div class="titulo-principal">📚 Evaluación inicial de Lengua — 2.º ESO</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitulo-principal">'
    'Lengua Castellana y Literatura · Prueba adaptada NEE'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# DATOS DEL ALUMNO
# ============================================================

nombre = st.text_input(
    "Nombre y apellidos",
    help="Escribe tu nombre y apellidos."
)

grupo = st.selectbox(
    "Grupo",
    [
        "",
        "2.º A",
        "2.º B",
        "2.º C",
        "2.º D",
    ],
    help="Selecciona tu grupo."
)


# ============================================================
# RESPUESTAS
# ============================================================

respuestas = {}


# ============================================================
# 1. COMPRENSIÓN
# ============================================================

st.header(
    "1. Comprensión lectora"
)

st.markdown(
    f'<div class="texto-examen">{EXAM["comprension"]["texto"].replace(chr(10), "<br>")}</div>',
    unsafe_allow_html=True
)

for p in EXAM["comprension"]["preguntas"]:

    st.markdown(
        f'<div class="pregunta">{p["enunciado"]}</div>',
        unsafe_allow_html=True
    )

    respuestas[p["id"]] = st.text_input(
        "",
        key=f"comp_{p['id']}",
        label_visibility="collapsed",
        help=(
            "Escribe una respuesta breve."
            if p["id"] != "c4"
            else "Escribe tres acciones separadas por comas. "
                 "Ejemplo: miraba, bajó, caminó."
        )
    )

    st.markdown(
        '<div class="separador-pregunta"></div>',
        unsafe_allow_html=True
    )


st.divider()


# ============================================================
# 2. MORFOLOGÍA
# ============================================================

st.header(
    "2. Morfología"
)

for palabra in EXAM["morfologia"]:

    st.markdown(
        f'<div class="elemento-pregunta">Palabra: <strong>{palabra["palabra"]}</strong></div>',
        unsafe_allow_html=True
    )

    datos_palabra = {}

    for campo in palabra["campos"]:

        clave = (
            f"{palabra['id']}_{campo}"
        )

        if campo == "Estructura":

            valor = st.selectbox(
                "Estructura",
                [
                    "",
                    "simple",
                    "derivada",
                    "compuesta",
                    "parasintética",
                ],
                key=clave,
                help="Indica cómo está formada la palabra."
            )

        elif campo == "V/I":

            valor = st.selectbox(
                "V/I",
                [
                    "",
                    "variable",
                    "invariable",
                ],
                key=clave,
                help="Indica si la palabra es variable o invariable."
            )

        else:

            valor = st.text_input(
                campo,
                key=clave,
                help=(
                    "Escribe la respuesta."
                    if campo != "Morfemas"
                    else "Escribe los morfemas de la palabra."
                )
            )

        datos_palabra[campo] = valor

    respuestas[
        palabra["id"]
    ] = datos_palabra

    st.markdown(
        '<div class="separador-pregunta"></div>',
        unsafe_allow_html=True
    )


st.divider()


# ============================================================
# 3. DETERMINANTES Y PRONOMBRES
# ============================================================

st.header(
    "3. Determinantes y pronombres"
)

for p in EXAM["determinantes_pronombres"]:

    st.markdown(
        f'<div class="elemento-pregunta">{p["frase"]}</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        f'<div class="pregunta">{p["enunciado"]}</div>',
        unsafe_allow_html=True
    )

    respuestas[p["id"]] = st.selectbox(
        "",
        [
            "",
            "determinante",
            "pronombre",
        ],
        key=f"dp_{p['id']}",
        label_visibility="collapsed",
        help="Selecciona una opción."
    )

    st.markdown(
        '<div class="separador-pregunta"></div>',
        unsafe_allow_html=True
    )


st.divider()


# ============================================================
# 4. SEMÁNTICA
# ============================================================

st.header(
    "4. Semántica"
)

opciones_semantica = [
    "",
    "antonimia",
    "sinonimia",
    "campo semántico",
    "polisemia",
    "homonimia",
    "meronimia",
    "hipónimos",
    "hiperónimo",
]


for p in EXAM["semantica"]:

    st.markdown(
        f'<div class="elemento-pregunta">{p["elemento"]}</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        f'<div class="pregunta">{p["enunciado"]}</div>',
        unsafe_allow_html=True
    )

    respuestas[p["id"]] = st.selectbox(
        "",
        opciones_semantica,
        key=f"sem_{p['id']}",
        label_visibility="collapsed",
        help="Selecciona la relación semántica correcta."
    )

    st.markdown(
        '<div class="separador-pregunta"></div>',
        unsafe_allow_html=True
    )


st.divider()


# ============================================================
# 5. TIPOS DE TEXTO
# ============================================================

st.header(
    "5. Tipos de texto"
)

st.markdown(
    f'<div class="enunciado-grande">{EXAM["textos"]["enunciado"]}</div>',
    unsafe_allow_html=True
)


opciones_texto = [
    "",
    "narrativo",
    "descriptivo",
    "expositivo",
    "argumentativo",
    "instructivo",
    "dialogado",
]


# IMPORTANTE:
# No usamos next().
# Se utilizan directamente los textos A y B del examen.

textos_definidos = EXAM["textos"]["textos"]
preguntas_textos = {
    p["id"]: p
    for p in EXAM["textos"]["preguntas"]
}


for letra, texto in textos_definidos.items():

    st.markdown(
        f'<div class="elemento-pregunta"><strong>Texto {letra}:</strong></div>',
        unsafe_allow_html=True
    )

    st.markdown(
        f'<div class="texto-examen">{texto}</div>',
        unsafe_allow_html=True
    )

    pregunta = preguntas_textos.get(
        f"t{letra}"
    )

    if pregunta:

        st.markdown(
            f'<div class="pregunta">{pregunta["enunciado"]}</div>',
            unsafe_allow_html=True
        )

        respuestas[
            pregunta["id"]
        ] = st.selectbox(
            "",
            opciones_texto,
            key=f"texto_{pregunta['id']}",
            label_visibility="collapsed",
            help="Selecciona el tipo de texto."
        )

    st.markdown(
        '<div class="separador-pregunta"></div>',
        unsafe_allow_html=True
    )


st.divider()


# ============================================================
# 6. LITERATURA
# ============================================================

st.header(
    "6. Literatura"
)

st.markdown(
    f'<div class="texto-examen">'
    f'{EXAM["literatura"]["poema"].replace(chr(10), "<br>")}'
    f'</div>',
    unsafe_allow_html=True
)


literatura = {
    p["id"]: p
    for p in EXAM["literatura"]["preguntas"]
}


# Número de versos

st.markdown(
    '<div class="pregunta">1. ¿Cuántos <strong>versos</strong> tiene el poema?</div>',
    unsafe_allow_html=True
)

respuestas["l1"] = st.selectbox(
    "",
    [
        "",
        "1",
        "2",
        "3",
        "4",
        "5",
        "6",
    ],
    key="literatura_l1",
    label_visibility="collapsed",
    help="Cuenta los versos del poema."
)


# Arte mayor / menor

st.markdown(
    '<div class="pregunta">2. ¿Es de <strong>arte mayor o menor</strong>?</div>',
    unsafe_allow_html=True
)

respuestas["l2"] = st.selectbox(
    "",
    [
        "",
        "arte menor",
        "arte mayor",
    ],
    key="literatura_l2",
    label_visibility="collapsed",
    help="Recuerda que el arte mayor tiene 9 sílabas métricas o más."
)


# Esquema métrico

st.markdown(
    '<div class="pregunta">3. Escribe el <strong>esquema métrico</strong>.</div>',
    unsafe_allow_html=True
)

respuestas["l3"] = st.text_input(
    "",
    key="literatura_l3",
    label_visibility="collapsed",
    help=(
        "Escribe, por ejemplo: 10A 10B 10A 10B. "
        "También puedes separar los elementos con comas o punto y coma."
    )
)


# Rima

st.markdown(
    '<div class="pregunta">4. ¿Qué tipo de <strong>rima</strong> tiene?</div>',
    unsafe_allow_html=True
)

respuestas["l4"] = st.selectbox(
    "",
    [
        "",
        "asonante",
        "consonante",
    ],
    key="literatura_l4",
    label_visibility="collapsed",
    help="Selecciona el tipo de rima."
)


# Sinalefa

st.markdown(
    '<div class="pregunta">5. Busca una <strong>sinalefa</strong> y escribe las palabras.</div>',
    unsafe_allow_html=True
)

respuestas["l5"] = st.text_input(
    "",
    key="literatura_l5",
    label_visibility="collapsed",
    help=(
        "Escribe las dos palabras que forman la sinalefa. "
        "Ejemplo: sobre el."
    )
)


# Personificación

st.markdown(
    '<div class="pregunta">6. Busca una <strong>personificación</strong>.</div>',
    unsafe_allow_html=True
)

respuestas["l6"] = st.text_input(
    "",
    key="literatura_l6",
    label_visibility="collapsed",
    help=(
        "Escribe las palabras exactas que forman la personificación."
    )
)


st.divider()


# ============================================================
# 7. SINTAXIS
# ============================================================

st.header(
    "7. Sintaxis"
)


# ------------------------------------------------------------
# 7.1 FRASE U ORACIÓN
# ------------------------------------------------------------

st.subheader(
    "7.1. Frase u oración"
)

ids_frase = {
    "x1",
    "x2",
    "x3",
    "x5",
}


for p in EXAM["sintaxis"]:

    if p["id"] not in ids_frase:
        continue

    st.markdown(
        f'<div class="elemento-pregunta">{p["frase"]}</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        f'<div class="pregunta">{p["enunciado"]}</div>',
        unsafe_allow_html=True
    )

    respuestas[p["id"]] = st.selectbox(
        "",
        [
            "",
            "frase",
            "oración",
        ],
        key=f"sintaxis_{p['id']}",
        label_visibility="collapsed",
        help="Selecciona si es una frase o una oración."
    )


# ------------------------------------------------------------
# 7.2 MODALIDAD ORACIONAL
# ------------------------------------------------------------

st.subheader(
    "7.2. Modalidad oracional"
)

ids_modalidad = {
    "x4",
    "x5",
    "x6",
    "x7",
    "x8",
    "x9",
}


opciones_modalidad = [
    "",
    "enunciativa",
    "interrogativa",
    "exclamativa",
    "desiderativa",
    "exhortativa",
]


for p in EXAM["sintaxis"]:

    if p["id"] not in ids_modalidad:
        continue

    # Si el elemento ya se ha mostrado arriba como frase/oración,
    # no volver a mostrarlo allí.

    if p["id"] in ids_frase:
        continue

    st.markdown(
        f'<div class="elemento-pregunta">{p["frase"]}</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        f'<div class="pregunta">{p["enunciado"]}</div>',
        unsafe_allow_html=True
    )

    respuestas[p["id"]] = st.selectbox(
        "",
        opciones_modalidad,
        key=f"sintaxis_{p['id']}",
        label_visibility="collapsed",
        help="Selecciona la modalidad oracional."
    )


st.divider()


# ============================================================
# 8. DIÁLOGO
# ============================================================

st.header(
    "8. Diálogo"
)

st.markdown(
    f'<div class="texto-examen">'
    f'{EXAM["dialogo"]["texto"].replace(chr(10), "<br>")}'
    f'</div>',
    unsafe_allow_html=True
)


for p in EXAM["dialogo"]["preguntas"]:

    st.markdown(
        f'<div class="pregunta">{p["enunciado"]}</div>',
        unsafe_allow_html=True
    )

    if p["id"] == "d3":

        respuestas[p["id"]] = st.text_area(
            "",
            key="dialogo_d3",
            label_visibility="collapsed",
            height=100,
            help=(
                "Transforma la intervención a estilo indirecto."
            )
        )

    else:

        respuestas[p["id"]] = st.text_input(
            "",
            key=f"dialogo_{p['id']}",
            label_visibility="collapsed",
            help=(
                "Para los interlocutores, escribe los nombres "
                "separados por comas. Ejemplo: Lucía, Carlos."
                if p["id"] == "d1"
                else "Escribe la respuesta."
            )
        )


st.divider()


# ============================================================
# ENTREGAR
# ============================================================

if st.button(
    "✅ ENTREGAR EXAMEN",
    use_container_width=True
):

    if not nombre.strip():

        st.error(
            "Escribe tu nombre y apellidos."
        )

        st.stop()


    if not grupo:

        st.error(
            "Selecciona tu grupo."
        )

        st.stop()


    # --------------------------------------------------------
    # CORRECCIÓN
    # --------------------------------------------------------

    puntos, nota_final = corregir_examen(
        respuestas
    )


    # --------------------------------------------------------
    # GUARDAR RESULTADO
    # --------------------------------------------------------

    fila = {
        "name": nombre.strip(),
        "group": grupo,
        "date": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),

        "comprension": puntos["comprension"],
        "morfologia": puntos["morfologia"],
        "determinantes": puntos["determinantes"],
        "semantica": puntos["semantica"],
        "textos": puntos["textos"],
        "literatura": puntos["literatura"],
        "sintaxis": puntos["sintaxis"],
        "dialogo": puntos["dialogo"],

        "total": nota_final,
    }


    guardar_resultado(
        fila
    )


    # --------------------------------------------------------
    # ESTADO DE SESIÓN
    # Esto hace que el formulario desaparezca después de enviar.
    # --------------------------------------------------------

    st.session_state[
        "examen_enviado"
    ] = True

    st.session_state[
        "puntos"
    ] = puntos

    st.session_state[
        "nota_final"
    ] = nota_final

    st.session_state[
        "fila"
    ] = fila

    st.rerun()
