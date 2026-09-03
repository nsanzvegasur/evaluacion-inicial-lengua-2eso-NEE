import csv
import io
import os
import re
import unicodedata
from datetime import datetime

import pandas as pd
import streamlit as st

from examen2ESO_NEE import EXAMEN
import plotly.graph_objects as go


def radar_chart(datos, titulo="Perfil competencial"):
    competencias = [
        "comprension",
        "morfologia",
        "semantica",
        "textos",
        "literatura",
        "sintaxis",
    ]

    nombres = {
        "comprension": "Comprensión",
        "morfologia": "Morfología",
        "semantica": "Semántica",
        "textos": "Textos",
        "literatura": "Literatura",
        "sintaxis": "Sintaxis",
    }

    valores = [
        float(datos.get(c, 0) or 0)
        for c in competencias
    ]

    etiquetas = [
        nombres[c]
        for c in competencias
    ]

    valores.append(valores[0])
    etiquetas.append(etiquetas[0])

    fig = go.Figure()

    fig.add_trace(
        go.Scatterpolar(
            r=valores,
            theta=etiquetas,
            fill="toself",
            name="Resultado",
        )
    )

    fig.update_layout(
        title=titulo,
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10],
            )
        ),
        showlegend=False,
        margin=dict(
            l=40,
            r=40,
            t=60,
            b=40,
        ),
    )

    return fig


def generar_perfil(datos):

    competencias = {
        "comprension": "Comprensión",
        "morfologia": "Morfología",
        "semantica": "Semántica",
        "textos": "Textos",
        "literatura": "Literatura",
        "sintaxis": "Sintaxis",
    }

    resultado = []

    for clave, nombre in competencias.items():

        nota = round(
            float(
                datos.get(clave, 0) or 0
            ),
            2,
        )

        if nota < 5:
            nivel = "Necesita refuerzo"

        elif nota < 8:
            nivel = "Nivel adecuado"

        else:
            nivel = "Fortaleza"

        resultado.append(
            {
                "competencia": clave,
                "nombre": nombre,
                "nota": nota,
                "nivel": nivel,
            }
        )

    return resultado


# ==============================================================
# CONFIGURACIÓN
# ==============================================================

st.set_page_config(
    page_title="Evaluación inicial de Lengua - 2.º ESO NEE",
    page_icon="📚",
    layout="centered",
)

CSV_FILE = "results.csv"

EXAM = EXAMEN["2ESO_NEE"]


# ==============================================================
# PUNTUACIÓN
# ==============================================================

# Total exacto: 10 puntos
PESOS = {
    "comprension": 2.0,
    "morfologia": 2.5,
    "semantica": 1.0,
    "textos": 1.5,
    "literatura": 2.0,
    "sintaxis": 1.0,
}

NOMBRES = {
    "comprension": "Comprensión lectora",
    "morfologia": "Morfología",
    "semantica": "Semántica",
    "textos": "Textos y diálogo",
    "literatura": "Literatura",
    "sintaxis": "Sintaxis",
}


# ==============================================================
# ESTILO
# ==============================================================

st.markdown(
    """
    <style>
    html, body, [class*="css"] {
        font-family: "Open Sans", sans-serif;
    }

    .titulo-principal {
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0.15rem;
    }

    .subtitulo {
        color: #666;
        margin-bottom: 1.4rem;
    }

    .texto-ejercicio {
        margin-top: 0.4rem;
        margin-bottom: 0.2rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ==============================================================
# NORMALIZACIÓN
# ==============================================================

def normalizar(valor):
    """
    Normaliza para corregir respuestas.

    IMPORTANTE:
    Esto se usa solo para comparar respuestas.
    No se utiliza para detectar faltas de tildes.
    """

    if valor is None:
        return ""

    texto = str(valor).strip().lower()

    texto = unicodedata.normalize("NFD", texto)

    texto = "".join(
        c
        for c in texto
        if unicodedata.category(c) != "Mn"
    )

    texto = re.sub(r"\s+", " ", texto)

    return texto.strip()


def dividir_lista(valor):
    """
    Acepta respuestas separadas por:
    - comas
    - punto y coma
    - saltos de línea
    """

    if valor is None:
        return []

    texto = str(valor).strip()

    if not texto:
        return []

    partes = re.split(r"[,;\n]+", texto)

    return [
        normalizar(parte)
        for parte in partes
        if normalizar(parte)
    ]


def exacta(valor, *alternativas):
    texto = normalizar(valor)

    if not texto:
        return False

    return any(
        texto == normalizar(alternativa)
        for alternativa in alternativas
    )


def contiene(valor, *criterios):
    texto = normalizar(valor)

    if not texto:
        return False

    return any(
        normalizar(criterio) in texto
        for criterio in criterios
    )


# ==============================================================
# CORRECCIÓN DE COMPRENSIÓN
# ==============================================================

def corregir_comprension(respuestas):

    puntos = 0.0

    # ----------------------------------------------------------
    # c1 - lugar = 0,50
    # ----------------------------------------------------------

    if contiene(
        respuestas.get("c1", ""),
        "tren",
        "estacion",
        "vagon",
    ):
        puntos += 0.50

    # ----------------------------------------------------------
    # c2 - personajes = 0,50
    # ----------------------------------------------------------

    personajes = dividir_lista(
        respuestas.get("c2", "")
    )

    tiene_hombre = any(
        "hombre" in x or "joven" in x
        for x in personajes
    )

    tiene_anciana = any(
        "anciana" in x
        for x in personajes
    )

    if tiene_hombre and tiene_anciana:
        puntos += 0.50
    elif tiene_hombre or tiene_anciana:
        puntos += 0.25

    # ----------------------------------------------------------
    # c3 - cuándo = 0,40
    # ----------------------------------------------------------

    if contiene(
        respuestas.get("c3", ""),
        "temprano",
        "madrugada",
        "amanecer",
    ):
        puntos += 0.40

    # ----------------------------------------------------------
    # c4 - tres acciones = 0,60
    # ----------------------------------------------------------

    texto = normalizar(
        respuestas.get("c4", "")
    )

    acciones = [
        ("llegar", ["llegar", "llego", "llegó"]),
        ("cubrir", ["cubrir", "cubria", "cubría"]),
        ("viajar", ["viajar", "viajaban"]),
        ("llevar", ["llevar", "llevaba"]),
        ("parecer", ["parecer", "parecia", "parecía"]),
        ("dormir", ["dormir", "dormia", "dormía"]),
        ("bajar", ["bajar", "bajo", "bajó"]),
        ("ver", ["ver", "veia", "veía"]),
    ]

    encontradas = set()

    for nombre, formas in acciones:

        if any(
            normalizar(forma) in texto
            for forma in formas
        ):
            encontradas.add(nombre)

    puntos += min(
        len(encontradas),
        3
    ) * 0.20

    return min(puntos, 2.0)


# ==============================================================
# CORRECCIÓN DE MORFOLOGÍA
# ==============================================================

def corregir_morfologia(respuestas):

    puntos = 0.0

    # Cada palabra vale 2/3.
    # Total de las tres palabras = 2 puntos.

    correctas = {

        "m1": {
            "lexema": ["silenci", "silenc"],
            "morfemas": ["o"],
            "estructura": ["simple"],
            "categoria": ["sustantivo"],
            "vi": ["variable"],
        },

        "m2": {
            "lexema": ["mochil"],
            "morfemas": ["a", "s"],
            "estructura": ["simple"],
            "categoria": ["sustantivo"],
            "vi": ["variable"],
        },

        "m3": {
            "lexema": ["conoc"],
            "morfemas": ["des", "ido", "id", "o"],
            "estructura": ["derivada"],
            "categoria": ["adjetivo"],
            "vi": ["variable"],
        },
    }

    for mid, datos in correctas.items():

        # ------------------------------------------------------
        # Lexema = 0,13
        # ------------------------------------------------------

        lexema = normalizar(
            respuestas.get(f"{mid}_Lexema", "")
        )

        if lexema in [
            normalizar(x)
            for x in datos["lexema"]
        ]:
            puntos += 0.13

        # ------------------------------------------------------
        # Morfemas = 0,13
        # ------------------------------------------------------

        morfemas = normalizar(
            respuestas.get(f"{mid}_Morfemas", "")
        )

        if mid == "m1":

            ok = "o" in morfemas

        elif mid == "m2":

            partes = dividir_lista(morfemas)

            ok = (
                "a" in partes
                and "s" in partes
            )

        else:

            ok = (
                "des" in morfemas
                and (
                    "ido" in morfemas
                    or "id" in morfemas
                )
            )

        if ok:
            puntos += 0.13

        # ------------------------------------------------------
        # Estructura = 0,13
        # ------------------------------------------------------

        estructura = normalizar(
            respuestas.get(f"{mid}_Estructura", "")
        )

        if estructura in [
            normalizar(x)
            for x in datos["estructura"]
        ]:
            puntos += 0.13

        # ------------------------------------------------------
        # Categoría = 0,20
        # ------------------------------------------------------

        categoria = normalizar(
            respuestas.get(f"{mid}_Categoría gramatical", "")
        )

        if categoria in [
            normalizar(x)
            for x in datos["categoria"]
        ]:
            puntos += 0.20

        # ------------------------------------------------------
        # V/I = 0,07
        # ------------------------------------------------------

        vi = normalizar(
            respuestas.get(f"{mid}_V/I", "")
        )

        if vi in [
            normalizar(x)
            for x in datos["vi"]
        ]:
            puntos += 0.07

    # ----------------------------------------------------------
    # Determinantes y pronombres = 0,50
    # ----------------------------------------------------------

    if exacta(
        respuestas.get("dp1", ""),
        "determinante",
    ):
        puntos += 0.25

    if exacta(
        respuestas.get("dp2", ""),
        "pronombre",
    ):
        puntos += 0.25

    return min(puntos, 2.5)


# ==============================================================
# CORRECCIÓN DE SEMÁNTICA
# ==============================================================

def corregir_semantica(respuestas):

    puntos = 0.0

    if exacta(
        respuestas.get("s1", ""),
        "antonimia",
    ):
        puntos += 1 / 3

    if exacta(
        respuestas.get("s2", ""),
        "campo semántico",
    ):
        puntos += 1 / 3

    if exacta(
        respuestas.get("s3", ""),
        "polisemia",
    ):
        puntos += 1 / 3

    return min(puntos, 1.0)


# ==============================================================
# CORRECCIÓN DE TEXTOS Y DIÁLOGO
# ==============================================================

def corregir_textos_dialogo(respuestas):

    puntos = 0.0

    # ----------------------------------------------------------
    # Tipos de texto = 0,60
    # ----------------------------------------------------------

    if exacta(
        respuestas.get("t1", ""),
        "instructivo",
    ):
        puntos += 0.30

    if exacta(
        respuestas.get("t2", ""),
        "expositivo",
    ):
        puntos += 0.30

    # ----------------------------------------------------------
    # d1 - interlocutores = 0,30
    # ----------------------------------------------------------

    interlocutores = dividir_lista(
        respuestas.get("d1", "")
    )

    lucia = any(
        "lucia" in x
        for x in interlocutores
    )

    carlos = any(
        "carlos" in x
        for x in interlocutores
    )

    if lucia and carlos:
        puntos += 0.30
    elif lucia or carlos:
        puntos += 0.15

    # ----------------------------------------------------------
    # d2 - intervenciones = 0,30
    # ----------------------------------------------------------

    if exacta(
        respuestas.get("d2", ""),
        "6",
        "seis",
        "6 intervenciones",
        "seis intervenciones",
    ):
        puntos += 0.30

    # ----------------------------------------------------------
    # d3 - estilo indirecto = 0,30
    # ----------------------------------------------------------

    indirecto = normalizar(
        respuestas.get("d3", "")
    )

    tiene_carlos = "carlos" in indirecto

    tiene_verbo = any(
        verbo in indirecto
        for verbo in [
            "dijo",
            "comento",
            "comentó",
            "afirmo",
            "afirmó",
        ]
    )

    tiene_que = "que" in indirecto

    tiene_habia_hecho = (
        "habia hecho" in indirecto
    )

    tiene_dia_anterior = (
        "dia anterior" in indirecto
        or "dia antes" in indirecto
    )

    if (
        tiene_carlos
        and tiene_verbo
        and tiene_que
        and tiene_habia_hecho
        and tiene_dia_anterior
    ):
        puntos += 0.30

    return min(puntos, 1.5)


# ==============================================================
# CORRECCIÓN DE LITERATURA
# ==============================================================

def corregir_literatura(respuestas):

    puntos = 0.0

    # ----------------------------------------------------------
    # l1 - versos = 0,30
    # ----------------------------------------------------------

    if exacta(
        respuestas.get("l1", ""),
        "4",
    ):
        puntos += 0.30

    # ----------------------------------------------------------
    # l2 - arte mayor = 0,30
    # ----------------------------------------------------------

    if exacta(
        respuestas.get("l2", ""),
        "arte mayor",
    ):
        puntos += 0.30

    # ----------------------------------------------------------
    # l3 - métrica = 0,35
    # ----------------------------------------------------------

    metrica = normalizar(
        respuestas.get("l3", "")
    )

    # Se eliminan únicamente separadores.
    # Se mantienen A/B como letras.

    metrica = re.sub(
        r"[,;]+",
        " ",
        metrica,
    )

    metrica = re.sub(
        r"\s+",
        " ",
        metrica,
    ).strip()

    patron = (
        r"^10a\s+10b\s+10a\s+10b$"
    )

    if re.fullmatch(
        patron,
        metrica,
    ):
        puntos += 0.35

    # ----------------------------------------------------------
    # l4 - rima = 0,35
    # ----------------------------------------------------------

    if exacta(
        respuestas.get("l4", ""),
        "consonante",
        "rima consonante",
    ):
        puntos += 0.35

    # ----------------------------------------------------------
    # l5 - sinalefa = 0,35
    # ----------------------------------------------------------

    sinalefa = normalizar(
        respuestas.get("l5", "")
    )

    if (
        "sobre el" in sinalefa
        or "mira el" in sinalefa
    ):
        puntos += 0.35

    # ----------------------------------------------------------
    # l6 - personificación = 0,35
    # ----------------------------------------------------------

    personificacion = normalizar(
        respuestas.get("l6", "")
    )

    if (
        "viento susurra" in personificacion
        or (
            "viento" in personificacion
            and "susurra" in personificacion
        )
    ):
        puntos += 0.35

    return min(puntos, 2.0)


# ==============================================================
# CORRECCIÓN DE SINTAXIS
# ==============================================================

def corregir_sintaxis(respuestas):

    puntos = 0.0

    correctas = {
        "x1": ["frase"],
        "x2": ["oracion"],
        "x3": ["oracion"],
        "x4": ["interrogativa"],
        "x5": ["exclamativa"],
        "x6": ["enunciativa"],
        "x7": ["exhortativa", "imperativa"],
        "x8": ["desiderativa"],
        "x9": ["exhortativa", "imperativa"],
    }

    ids_presentes = [
        p["id"]
        for p in EXAM.get("sintaxis", [])
    ]

    if not ids_presentes:
        return 0.0

    valor = 1.0 / len(ids_presentes)

    for pid in ids_presentes:

        if exacta(
            respuestas.get(pid, ""),
            *correctas.get(pid, []),
        ):
            puntos += valor

    return min(puntos, 1.0)


# ==============================================================
# CORRECCIÓN GENERAL
# ==============================================================

def corregir_examen(respuestas):

    puntos = {
        "comprension": corregir_comprension(
            respuestas
        ),

        "morfologia": corregir_morfologia(
            respuestas
        ),

        "semantica": corregir_semantica(
            respuestas
        ),

        "textos": corregir_textos_dialogo(
            respuestas
        ),

        "literatura": corregir_literatura(
            respuestas
        ),

        "sintaxis": corregir_sintaxis(
            respuestas
        ),
    }

    for clave in puntos:
        puntos[clave] = round(
            min(
                puntos[clave],
                PESOS[clave],
            ),
            2,
        )

    nota = round(
        sum(puntos.values()),
        2,
    )

    return puntos, nota


# ==============================================================
# ORTOGRAFÍA
# ==============================================================

# MUY IMPORTANTE:
# No se normalizan tildes para detectar faltas.
# Por tanto "había" NO se considera "havia".
#
# La normalización anterior solo se usa para comparar respuestas.

ERRORES_ORTOGRAFICOS = {
    "haver": "haber",
    "aver": "a ver",
    "hechar": "echar",
    "ahi": "ahí",
    "ai": "ahí",
}


def detectar_ortografia(textos):

    faltas = 0

    for texto in textos:

        if not texto:
            continue

        texto_original = str(texto).lower()

        for incorrecta in ERRORES_ORTOGRAFICOS:

            if re.search(
                rf"\b{re.escape(incorrecta)}\b",
                texto_original,
            ):
                faltas += 1

    descuento = min(
        faltas * 0.20,
        2.0,
    )

    return faltas, round(descuento, 2)


# ==============================================================
# GUARDAR RESULTADOS
# ==============================================================

def guardar_resultado(
    nombre,
    grupo,
    puntos,
    nota_inicial,
    faltas,
    descuento,
    nota_final,
):

    fila = {
        "fecha": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),

        "nombre": nombre,
        "grupo": grupo,

        "comprension": puntos["comprension"],
        "morfologia": puntos["morfologia"],
        "semantica": puntos["semantica"],
        "textos": puntos["textos"],
        "literatura": puntos["literatura"],
        "sintaxis": puntos["sintaxis"],

        "nota_sin_faltas": nota_inicial,
        "faltas_ortografia": faltas,
        "descuento_ortografia": descuento,
        "nota_final": nota_final,
    }

    columnas = list(fila.keys())

    nuevo = pd.DataFrame(
        [fila],
        columns=columnas,
    )

    try:

        if os.path.exists(CSV_FILE):

            antiguo = pd.read_csv(
                CSV_FILE
            )

            for columna in columnas:

                if columna not in antiguo.columns:
                    antiguo[columna] = ""

            antiguo = antiguo[columnas]

            final = pd.concat(
                [
                    antiguo,
                    nuevo,
                ],
                ignore_index=True,
            )

        else:

            final = nuevo

        final.to_csv(
            CSV_FILE,
            index=False,
            encoding="utf-8-sig",
        )

        return True

    except Exception as error:

        st.error(
            "No se pudo guardar el resultado."
        )

        st.exception(error)

        return False


# ==============================================================
# CSV INDIVIDUAL
# ==============================================================

def csv_individual(fila):

    salida = io.StringIO()

    writer = csv.DictWriter(
        salida,
        fieldnames=fila.keys(),
    )

    writer.writeheader()
    writer.writerow(fila)

    return salida.getvalue().encode(
        "utf-8-sig"
    )


# ==============================================================
# EXCEL
# ==============================================================

def excel_individual(fila):

    salida = io.BytesIO()

    df = pd.DataFrame([fila])

    with pd.ExcelWriter(
        salida,
        engine="openpyxl",
    ) as writer:

        df.to_excel(
            writer,
            index=False,
            sheet_name="Resultado",
        )

    salida.seek(0)

    return salida.getvalue()


# ==============================================================
# CARGAR RESULTADOS
# ==============================================================

def cargar_resultados():

    if not os.path.exists(CSV_FILE):
        return pd.DataFrame()

    try:
        return pd.read_csv(
            CSV_FILE
        )

    except Exception:
        return pd.DataFrame()


# ==============================================================
# CABECERA
# ==============================================================

st.markdown(
    '<div class="titulo-principal">📚 Evaluación inicial de Lengua</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitulo">2.º ESO · Lengua Castellana y Literatura · Curso 2026-2027</div>',
    unsafe_allow_html=True,
)


# ==============================================================
# PANTALLA DE RESULTADOS
# ==============================================================

if st.session_state.get(
    "examen_enviado",
    False,
):

    nombre = st.session_state["nombre"]
    grupo = st.session_state["grupo"]

    puntos = st.session_state["puntos"]
    nota_inicial = st.session_state["nota_inicial"]

    faltas = st.session_state["faltas"]
    descuento = st.session_state["descuento"]
    nota_final = st.session_state["nota_final"]

    fila = st.session_state["fila"]

    st.success(
        "✅ Examen enviado correctamente."
    )

    st.metric(
        "NOTA FINAL",
        f"{nota_final:.2f} / 10",
    )

    st.write(
        f"**Nota sin faltas de ortografía:** "
        f"{nota_inicial:.2f}/10"
    )

    st.write(
        f"**Descuento por faltas:** "
        f"-{descuento:.2f}"
    )

    st.divider()

    # ----------------------------------------------------------
    # RESULTADOS
    # ----------------------------------------------------------

    st.subheader(
        "Resultado por apartados"
    )

    columnas = st.columns(3)

    for i, clave in enumerate(PESOS):

        columnas[i % 3].metric(
            NOMBRES[clave],
            f"{puntos[clave]:.2f}/{PESOS[clave]:.1f}",
        )

    # ----------------------------------------------------------
    # PERFIL
    # ----------------------------------------------------------

    st.divider()

    st.subheader(
        "🧠 Perfil competencial"
    )

    perfil = generar_perfil(
        puntos
    )

    # analytics.py puede devolver lista o diccionario
    if isinstance(perfil, dict):

        for clave, info in perfil.items():

            st.write(
                f"**{info['nombre']}**: "
                f"{info['nota']:.2f}/10 — "
                f"{info['nivel']}"
            )

    else:

        for info in perfil:

            st.write(
                f"**{info['nombre']}**: "
                f"{info['nota']:.2f}/10 — "
                f"{info['nivel']}"
            )

    # ----------------------------------------------------------
    # RADAR
    # ----------------------------------------------------------

    try:

        fig = radar_chart(
            puntos,
            "Perfil competencial",
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

    except Exception:
        pass

    # ----------------------------------------------------------
    # DESCARGAS
    # ----------------------------------------------------------

    st.divider()

    st.subheader(
        "📥 Descargar resultado"
    )

    st.download_button(
        "⬇️ Descargar resultado CSV",
        data=csv_individual(fila),
        file_name="resultado_2ESO_NEE.csv",
        mime="text/csv",
        use_container_width=True,
    )

    st.download_button(
        "📊 Descargar resultado Excel",
        data=excel_individual(fila),
        file_name="resultado_2ESO_NEE.xlsx",
        mime=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        use_container_width=True,
    )

    # ----------------------------------------------------------
    # VOLVER
    # ----------------------------------------------------------

    if st.button(
        "🔄 Volver al inicio",
        use_container_width=True,
    ):

        st.session_state.clear()

        st.rerun()

    # MUY IMPORTANTE:
    # Aquí se detiene la aplicación.
    # Por tanto, el formulario NO vuelve a aparecer.
    st.stop()


# ==============================================================
# DATOS DEL ALUMNO
# ==============================================================

st.subheader(
    "Datos del alumno"
)

nombre = st.text_input(
    "Nombre y apellidos",
    placeholder="Escribe tu nombre y apellidos",
)

grupo = st.selectbox(
    "Grupo",
    [
        "",
        "2º A",
        "2º B",
        "2º C",
        "2º D",
    ],
)

if not nombre.strip():

    st.info(
        "Escribe tu nombre y apellidos para comenzar."
    )

    st.stop()

if not grupo:

    st.info(
        "Selecciona tu grupo."
    )

    st.stop()


# ==============================================================
# FORMULARIO
# ==============================================================

with st.form(
    "examen_2eso_nee"
):

    respuestas = {}

    # ==========================================================
    # 1. COMPRENSIÓN
    # ==========================================================

    st.header(
        "1. Comprensión lectora — 2 puntos"
    )

    st.write(
        EXAM["comprension"]["texto"]
    )

    for pregunta in EXAM["comprension"]["preguntas"]:

        pid = pregunta["id"]

        # Markdown para que SOLO aparezcan en negrita
        # las palabras marcadas con **...**
        st.markdown(
            pregunta["enunciado"]
        )

        if pid == "c4":

            respuestas[pid] = st.text_input(
                "Respuesta",
                help=(
                    "Escribe tres acciones que aparezcan "
                    "en el texto. Puedes separarlas con comas."
                ),
                key=pid,
            )

        elif pid == "c2":

            respuestas[pid] = st.text_input(
                "Respuesta",
                help=(
                    "Escribe los interlocutores/personajes "
                    "separados por comas."
                ),
                key=pid,
            )

        else:

            respuestas[pid] = st.text_input(
                "Respuesta",
                key=pid,
            )

    # ==========================================================
    # 2. MORFOLOGÍA
    # ==========================================================

    st.header(
        "2. Morfología — 2,5 puntos"
    )

    for palabra in EXAM["morfologia"]:

        st.subheader(
            palabra["palabra"]
        )

        for campo in palabra["campos"]:

            clave = (
                f"{palabra['id']}_{campo}"
            )

            if campo == "Estructura":

                respuestas[clave] = st.selectbox(
                    campo,
                    [
                        "",
                        "simple",
                        "compuesta",
                        "derivada",
                        "parasintética",
                    ],
                    key=clave,
                )

            elif campo == "V/I":

                respuestas[clave] = st.selectbox(
                    campo,
                    [
                        "",
                        "variable",
                        "invariable",
                    ],
                    key=clave,
                )

            elif campo == "Categoría gramatical":

                respuestas[clave] = st.text_input(
                    campo,
                    help=(
                        "Escribe la categoría gramatical "
                        "de la palabra."
                    ),
                    key=clave,
                )

            elif campo == "Morfemas":

                respuestas[clave] = st.text_input(
                    campo,
                    help=(
                        "Puedes separar los morfemas "
                        "con comas."
                    ),
                    key=clave,
                )

            else:

                respuestas[clave] = st.text_input(
                    campo,
                    help=(
                        "Escribe el lexema de la palabra."
                    ),
                    key=clave,
                )

        st.divider()

    # ==========================================================
    # 3. DETERMINANTES Y PRONOMBRES
    # ==========================================================

    st.header(
        "3. Determinantes y pronombres"
    )

    for pregunta in EXAM[
        "determinantes_pronombres"
    ]:

        pid = pregunta["id"]

        st.markdown(
            pregunta["frase"]
        )

        respuestas[pid] = st.selectbox(
            pregunta["enunciado"],
            [
                "",
                "determinante",
                "pronombre",
            ],
            key=pid,
        )

    # ==========================================================
    # 4. SEMÁNTICA
    # ==========================================================

    st.header(
        "4. Semántica — 1 punto"
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

    for pregunta in EXAM["semantica"]:

        st.markdown(
            f"**{pregunta['elemento']}**"
        )

        respuestas[
            pregunta["id"]
        ] = st.selectbox(
            pregunta["enunciado"],
            opciones_semantica,
            key=pregunta["id"],
        )

    # ==========================================================
    # 5. TIPOS DE TEXTO
    # ==========================================================

    st.header(
        "5. Tipos de texto"
    )

    st.markdown(
        EXAM["textos"]["enunciado"]
    )

    opciones_textos = [
        "",
        "narrativo",
        "descriptivo",
        "expositivo",
        "argumentativo",
        "instructivo",
        "dialogado",
    ]

    # Cada texto y JUSTO DEBAJO su selector.
    for letra, texto in EXAM[
        "textos"
    ]["textos"].items():

        st.markdown(
            f"**Texto {letra}:** {texto}"
        )

        pregunta = next(
            p
            for p in EXAM[
                "textos"
            ]["preguntas"]
            if p["id"] == f"t{letra}"
        )

        respuestas[
            pregunta["id"]
        ] = st.selectbox(
            pregunta["enunciado"],
            opciones_textos,
            key=pregunta["id"],
        )

    # ==========================================================
    # 6. LITERATURA
    # ==========================================================

    st.header(
        "6. Literatura — 2 puntos"
    )

    st.markdown(
        EXAM["literatura"]["poema"].replace(
            "\n",
            "  \n"
        )
    )

    # Número de versos
    respuestas["l1"] = st.selectbox(
        "1. ¿Cuántos **versos** tiene el poema?",
        [
            "",
            "2",
            "3",
            "4",
            "5",
            "6",
            "7",
            "8",
        ],
        key="l1",
    )

    # Arte mayor / menor
    respuestas["l2"] = st.selectbox(
        "2. ¿Es de **arte mayor o menor**?",
        [
            "",
            "arte menor",
            "arte mayor",
        ],
        key="l2",
    )

    # Esquema métrico
    respuestas["l3"] = st.text_input(
        "3. Escribe el **esquema métrico**.",
        help=(
            "Puedes escribirlo con espacios, comas "
            "o puntos y coma. Ejemplo: "
            "10A 10B 10A 10B"
        ),
        key="l3",
    )

    # Rima
    respuestas["l4"] = st.selectbox(
        "4. ¿Qué tipo de **rima** tiene?",
        [
            "",
            "asonante",
            "consonante",
        ],
        key="l4",
    )

    # Sinalefa
    respuestas["l5"] = st.text_input(
        "5. Busca una **sinalefa** y escribe las palabras.",
        help=(
            "Puedes escribir, por ejemplo, "
            "sobre el o mira el."
        ),
        key="l5",
    )

    # Personificación
    respuestas["l6"] = st.text_input(
        "6. Busca una **personificación**.",
        help=(
            "Una respuesta posible aparece en "
            "El viento susurra."
        ),
        key="l6",
    )

    # ==========================================================
    # 6.1 / 6.2 SINTAXIS
    # ==========================================================

    st.header(
        "7. Sintaxis — 1 punto"
    )

    sintaxis = EXAM["sintaxis"]

    # Con el examen que acabamos de fijar:
    # x1, x2, x3 = frase u oración
    # x4, x5, x6, x7 = modalidad.
    #
    # Si en tu versión definitiva cambias los IDs a
    # x1, x2, x5 / x6, x8, x9, este código los
    # clasifica automáticamente por esos IDs.

    ids_frase = {
        "x1",
        "x2",
        "x3",
        "x5",
    }

    ids_modalidad = {
        "x4",
        "x6",
        "x7",
        "x8",
        "x9",
    }

    st.subheader(
        "7.1. Frase u oración"
    )

    for pregunta in sintaxis:

        pid = pregunta["id"]

        if pid not in ids_frase:
            continue

        st.markdown(
            f"**{pregunta['frase']}**"
        )

        respuestas[pid] = st.selectbox(
            pregunta["enunciado"],
            [
                "",
                "frase",
                "oración",
            ],
            key=pid,
        )

    st.subheader(
        "7.2. Modalidad oracional"
    )

    opciones_modalidad = [
        "",
        "enunciativa",
        "interrogativa",
        "exclamativa",
        "desiderativa",
        "exhortativa",
    ]

    for pregunta in sintaxis:

        pid = pregunta["id"]

        if pid not in ids_modalidad:
            continue

        st.markdown(
            f"**{pregunta['frase']}**"
        )

        respuestas[pid] = st.selectbox(
            pregunta["enunciado"],
            opciones_modalidad,
            key=pid,
        )

    # ==========================================================
    # 8. DIÁLOGO
    # ==========================================================

    st.header(
        "8. Diálogo"
    )

    st.markdown(
        EXAM["dialogo"]["texto"].replace(
            "\n",
            "  \n"
        )
    )

    for pregunta in EXAM[
        "dialogo"
    ]["preguntas"]:

        pid = pregunta["id"]

        st.markdown(
            pregunta["enunciado"]
        )

        if pid == "d3":

            respuestas[pid] = st.text_area(
                "Respuesta",
                help=(
                    "Escribe una oración completa "
                    "en estilo indirecto."
                ),
                key=pid,
                height=90,
            )

        elif pid == "d1":

            respuestas[pid] = st.text_input(
                "Respuesta",
                help=(
                    "Escribe los interlocutores "
                    "separados por comas."
                ),
                key=pid,
            )

        else:

            respuestas[pid] = st.text_input(
                "Respuesta",
                key=pid,
            )

    # ==========================================================
    # ENVIAR
    # ==========================================================

    st.divider()

    enviar = st.form_submit_button(
        "📤 ENTREGAR",
        use_container_width=True,
    )


# ==============================================================
# PROCESAR ENTREGA
# ==============================================================

if enviar:

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

    # ----------------------------------------------------------
    # CORRECCIÓN
    # ----------------------------------------------------------

    puntos, nota_inicial = corregir_examen(
        respuestas
    )

    # ----------------------------------------------------------
    # ORTOGRAFÍA
    # ----------------------------------------------------------

    textos_para_ortografia = [
        valor
        for valor in respuestas.values()
        if isinstance(valor, str)
    ]

    faltas, descuento = detectar_ortografia(
        textos_para_ortografia
    )

    nota_final = round(
        max(
            0.0,
            nota_inicial - descuento,
        ),
        2,
    )

    # ----------------------------------------------------------
    # GUARDAR
    # ----------------------------------------------------------

    guardado = guardar_resultado(
        nombre=nombre.strip(),
        grupo=grupo,
        puntos=puntos,
        nota_inicial=nota_inicial,
        faltas=faltas,
        descuento=descuento,
        nota_final=nota_final,
    )

    if not guardado:
        st.stop()

    # ----------------------------------------------------------
    # SESIÓN
    # ----------------------------------------------------------

    fila = {
        "fecha": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        "nombre": nombre.strip(),
        "grupo": grupo,
        "comprension": puntos["comprension"],
        "morfologia": puntos["morfologia"],
        "semantica": puntos["semantica"],
        "textos": puntos["textos"],
        "literatura": puntos["literatura"],
        "sintaxis": puntos["sintaxis"],
        "nota_sin_faltas": nota_inicial,
        "faltas_ortografia": faltas,
        "descuento_ortografia": descuento,
        "nota_final": nota_final,
    }

    st.session_state[
        "examen_enviado"
    ] = True

    st.session_state[
        "nombre"
    ] = nombre.strip()

    st.session_state[
        "grupo"
    ] = grupo

    st.session_state[
        "puntos"
    ] = puntos

    st.session_state[
        "nota_inicial"
    ] = nota_inicial

    st.session_state[
        "faltas"
    ] = faltas

    st.session_state[
        "descuento"
    ] = descuento

    st.session_state[
        "nota_final"
    ] = nota_final

    st.session_state[
        "fila"
    ] = fila

    st.rerun()


# ==============================================================
# ESTADÍSTICAS ANÓNIMAS
# ==============================================================

# Solo aparecen mientras se está haciendo el examen.
# Después de entregar se ejecuta st.stop() en la pantalla
# de resultados y no se muestra esta parte.

with st.expander(
    "📊 Estadísticas del grupo"
):

    df = cargar_resultados()

    if df.empty:

        st.info(
            "Todavía no hay resultados guardados."
        )

    else:

        st.write(
            f"Resultados guardados: **{len(df)}**"
        )

        # ------------------------------------------------------
        # Comparativa ANÓNIMA
        # ------------------------------------------------------
        #
        # No se muestran nombres.
        # Solo medias por grupo y por competencia.
        # ------------------------------------------------------

        columnas_competencias = [
            "comprension",
            "morfologia",
            "semantica",
            "textos",
            "literatura",
            "sintaxis",
        ]

        disponibles = [
            c
            for c in columnas_competencias
            if c in df.columns
        ]

        if disponibles:

            tabla = df[
                disponibles
            ].apply(
                pd.to_numeric,
                errors="coerce",
            )

            medias = tabla.mean()

            st.subheader(
                "Media de la clase"
            )

            for clave in disponibles:

                st.write(
                    f"**{NOMBRES[clave]}:** "
                    f"{medias[clave]:.2f}/10"
                )

        # ------------------------------------------------------
        # Nunca se muestra el listado de alumnos.
        # ------------------------------------------------------

        st.caption(
            "Las estadísticas de grupo son anónimas."
        )
