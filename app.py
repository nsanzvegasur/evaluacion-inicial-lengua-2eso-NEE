import streamlit as st
import pandas as pd
import os
import re
import unicodedata
from datetime import datetime
from io import BytesIO

from examen2ESO_NEE import EXAMEN


# ============================================================
# CONFIGURACIÓN
# ============================================================

st.set_page_config(
    page_title="Evaluación inicial – 2.º ESO NEE",
    page_icon="📘",
    layout="wide",
    initial_sidebar_state="collapsed"
)

RESULTS_FILE = "results.csv"

EXAMEN_DATOS = EXAMEN["2ESO_NEE"]


# ============================================================
# ESTILO ACCESIBLE
# ============================================================

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:wght@400;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Atkinson Hyperlegible', Arial, sans-serif;
        font-size: 20px;
    }

    .stApp {
        max-width: 1200px;
        margin: auto;
    }

    h1 {
        font-size: 34px !important;
        line-height: 1.3 !important;
    }

    h2 {
        font-size: 29px !important;
        line-height: 1.4 !important;
        margin-top: 30px !important;
    }

    h3 {
        font-size: 25px !important;
        line-height: 1.4 !important;
    }

    .pregunta {
        font-size: 21px;
        line-height: 1.6;
        margin-top: 22px;
        margin-bottom: 8px;
        font-weight: 700;
    }

    .ayuda {
        font-size: 18px;
        line-height: 1.5;
        margin-bottom: 15px;
    }

    .aviso {
        padding: 15px;
        border-radius: 8px;
        margin: 15px 0;
        font-size: 20px;
    }

    textarea,
    input {
        font-size: 20px !important;
    }

    button {
        font-size: 21px !important;
        min-height: 50px !important;
    }

    .resultado {
        font-size: 26px;
        font-weight: 700;
        padding: 20px;
        margin-top: 20px;
    }

    .bloque {
        padding: 20px 0;
        margin-bottom: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# FUNCIONES GENERALES
# ============================================================

def normalizar(texto):
    """Pasa a minúsculas, elimina tildes y espacios sobrantes."""
    if texto is None:
        return ""

    texto = str(texto).strip().lower()

    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(
        c for c in texto
        if unicodedata.category(c) != "Mn"
    )

    texto = re.sub(r"\s+", " ", texto)

    return texto


def lista_normalizada(texto):
    """Divide respuestas separadas por coma, punto y coma o salto de línea."""
    if not texto:
        return []

    partes = re.split(r"[,;\n]+", str(texto))

    return [
        normalizar(p)
        for p in partes
        if normalizar(p)
    ]


def contiene_alguna(texto, opciones):
    texto_n = normalizar(texto)

    return any(
        normalizar(opcion) in texto_n
        for opcion in opciones
    )


def asegurar_csv():
    columnas = [
        "timestamp",
        "name",
        "group",
        "comprension",
        "morfologia",
        "determinantes_pronombres",
        "semantica",
        "textos",
        "literatura",
        "sintaxis",
        "dialogo",
        "nota_automatica",
        "produccion_escrita",
        "nota_final",
        "faltas"
    ]

    if not os.path.exists(RESULTS_FILE):
        pd.DataFrame(columns=columnas).to_csv(
            RESULTS_FILE,
            index=False,
            encoding="utf-8-sig"
        )


def cargar_resultados():
    asegurar_csv()

    try:
        return pd.read_csv(
            RESULTS_FILE,
            encoding="utf-8-sig"
        )
    except (pd.errors.EmptyDataError, FileNotFoundError):
        return pd.DataFrame()


def guardar_resultado(datos):
    asegurar_csv()

    df = cargar_resultados()

    nuevo = pd.DataFrame([datos])

    df = pd.concat(
        [df, nuevo],
        ignore_index=True
    )

    df.to_csv(
        RESULTS_FILE,
        index=False,
        encoding="utf-8-sig"
    )


# ============================================================
# DETECCIÓN DE FALTAS
# NO RESTA PUNTOS
# ============================================================

def detectar_faltas(texto):
    if not texto:
        return 0

    patrones = [
        r"\bxq\b",
        r"\bxk\b",
        r"\bq\b",
        r"\bke\b",
        r"\bporq\b",
        r"\bporqe\b",
        r"\bporquee\b"
    ]

    faltas = 0

    for patron in patrones:
        faltas += len(
            re.findall(
                patron,
                normalizar(texto)
            )
        )

    return faltas


# ============================================================
# COMPRENSIÓN
# MÁXIMO: 1,50
# ============================================================

def corregir_comprension(respuestas):

    puntos = 0.0

    # C1 - 0,35
    r1 = respuestas.get("c1", "")

    if contiene_alguna(
        r1,
        [
            "estacion",
            "en la estacion",
            "en el tren",
            "tren"
        ]
    ):
        puntos += 0.35

    # C2 - 0,35
    r2 = respuestas.get("c2", "")

    tiene_hombre = contiene_alguna(
        r2,
        ["hombre", "joven"]
    )

    tiene_anciana = contiene_alguna(
        r2,
        ["anciana", "vieja", "mujer"]
    )

    if tiene_hombre and tiene_anciana:
        puntos += 0.35
    elif tiene_hombre or tiene_anciana:
        puntos += 0.18

    # C3 - 0,30
    r3 = respuestas.get("c3", "")

    if contiene_alguna(
        r3,
        [
            "temprano",
            "muy temprano",
            "por la manana",
            "mañana temprano"
        ]
    ):
        puntos += 0.30

    # C4 - 0,50
    r4 = lista_normalizada(
        respuestas.get("c4", "")
    )

    acciones_validas = {
        "llego",
        "llegaron",
        "cubria",
        "se veia",
        "viajaban",
        "llevaba",
        "parecia",
        "dormia",
        "bajo"
    }

    acciones_encontradas = set()

    for respuesta in r4:
        for accion in acciones_validas:
            if accion in respuesta:
                acciones_encontradas.add(accion)

    numero_acciones = len(acciones_encontradas)

    if numero_acciones >= 3:
        puntos += 0.50
    elif numero_acciones == 2:
        puntos += 0.33
    elif numero_acciones == 1:
        puntos += 0.17

    return round(min(puntos, 1.50), 2)


# ============================================================
# MORFOLOGÍA
# MÁXIMO: 1,50
# ============================================================

def corregir_morfologia(respuestas):

    puntos = 0.0

    datos = EXAMEN_DATOS["morfologia"]

    for palabra in datos:

        pid = palabra["id"]

        campos = respuestas.get(pid, {})

        if pid == "m1":
            # silencio
            # lexema: silenci
            # sin morfemas flexivos
            # simple / sustantivo / variable

            if contiene_alguna(
                campos.get("Lexema", ""),
                ["silenci", "silencio"]
            ):
                puntos += 0.10

            morfemas = normalizar(
                campos.get("Morfemas", "")
            )

            if (
                morfemas == ""
                or contiene_alguna(
                    morfemas,
                    [
                        "ninguno",
                        "no tiene",
                        "sin morfemas",
                        "no hay"
                    ]
                )
            ):
                puntos += 0.10

            if contiene_alguna(
                campos.get("Estructura", ""),
                ["simple"]
            ):
                puntos += 0.10

            if contiene_alguna(
                campos.get("Categoría gramatical", ""),
                ["sustantivo", "nombre"]
            ):
                puntos += 0.10

            if contiene_alguna(
                campos.get("V/I", ""),
                ["variable"]
            ):
                puntos += 0.10

        elif pid == "m2":
            # mochilas
            # lexema: mochil
            # morfemas: a, s
            # simple / sustantivo / variable

            if contiene_alguna(
                campos.get("Lexema", ""),
                ["mochil", "mochila"]
            ):
                puntos += 0.10

            morfemas = lista_normalizada(
                campos.get("Morfemas", "")
            )

            tiene_a = any(
                "a" == m or m.endswith("a")
                for m in morfemas
            )

            tiene_s = any(
                m == "s" or m.endswith("s")
                for m in morfemas
            )

            if tiene_a and tiene_s:
                puntos += 0.10
            elif tiene_a or tiene_s:
                puntos += 0.05

            if contiene_alguna(
                campos.get("Estructura", ""),
                ["simple"]
            ):
                puntos += 0.10

            if contiene_alguna(
                campos.get("Categoría gramatical", ""),
                ["sustantivo", "nombre"]
            ):
                puntos += 0.10

            if contiene_alguna(
                campos.get("V/I", ""),
                ["variable"]
            ):
                puntos += 0.10

        elif pid == "m3":
            # desconocido
            # lexema: conoc
            # morfemas: des, ido
            # derivada / adjetivo / variable

            if contiene_alguna(
                campos.get("Lexema", ""),
                ["conoc"]
            ):
                puntos += 0.10

            morfemas = lista_normalizada(
                campos.get("Morfemas", "")
            )

            tiene_des = any(
                "des" == m or "des" in m
                for m in morfemas
            )

            tiene_ido = any(
                "ido" == m or "ido" in m
                for m in morfemas
            )

            if tiene_des and tiene_ido:
                puntos += 0.10
            elif tiene_des or tiene_ido:
                puntos += 0.05

            if contiene_alguna(
                campos.get("Estructura", ""),
                [
                    "derivada",
                    "derivado",
                    "prefijada",
                    "prefijado"
                ]
            ):
                puntos += 0.10

            if contiene_alguna(
                campos.get("Categoría gramatical", ""),
                ["adjetivo"]
            ):
                puntos += 0.10

            if contiene_alguna(
                campos.get("V/I", ""),
                ["variable"]
            ):
                puntos += 0.10

    return round(min(puntos, 1.50), 2)


# ============================================================
# DETERMINANTES Y PRONOMBRES
# MÁXIMO: 0,50
# ============================================================

def corregir_determinantes_pronombres(respuestas):

    puntos = 0.0

    # DP1 - Aquellos
    r1 = respuestas.get("dp1", "")

    if contiene_alguna(
        r1,
        [
            "demostrativo",
            "determinante demostrativo"
        ]
    ):
        puntos += 0.25

    # DP2 - Nadie
    r2 = respuestas.get("dp2", "")

    if contiene_alguna(
        r2,
        [
            "pronombre indefinido",
            "indefinido",
            "pronombre"
        ]
    ):
        puntos += 0.25

    return round(min(puntos, 0.50), 2)


# ============================================================
# SEMÁNTICA
# MÁXIMO: 0,75
# ============================================================

def corregir_semantica(respuestas):

    puntos = 0.0

    # S1 - antónimos
    if contiene_alguna(
        respuestas.get("s1", ""),
        ["antonimos", "antónimos", "antonimo", "opuestos"]
    ):
        puntos += 0.25

    # S2 - campo semántico
    if contiene_alguna(
        respuestas.get("s2", ""),
        [
            "campo semantico",
            "campo semántico"
        ]
    ):
        puntos += 0.25

    # S3 - polisemia
    if contiene_alguna(
        respuestas.get("s3", ""),
        [
            "polisemia",
            "polisemica",
            "polisémica"
        ]
    ):
        puntos += 0.25

    return round(min(puntos, 0.75), 2)


# ============================================================
# TIPOS DE TEXTO
# MÁXIMO: 0,75
# ============================================================

def corregir_textos(respuestas):

    puntos = 0.0

    # T1 - instructivo / prescriptivo
    if contiene_alguna(
        respuestas.get("t1", ""),
        [
            "instructivo",
            "prescriptivo",
            "prescriptivo"
        ]
    ):
        puntos += 0.375

    # T2 - expositivo
    if contiene_alguna(
        respuestas.get("t2", ""),
        [
            "expositivo",
            "expositiva"
        ]
    ):
        puntos += 0.375

    return round(min(puntos, 0.75), 2)


# ============================================================
# LITERATURA
# MÁXIMO: 1,50
# ============================================================

def corregir_literatura(respuestas):

    puntos = 0.0

    # L1 - 4 versos
    if contiene_alguna(
        respuestas.get("l1", ""),
        ["4", "cuatro"]
    ):
        puntos += 0.20

    # L2 - arte mayor
    if contiene_alguna(
        respuestas.get("l2", ""),
        [
            "arte mayor",
            "mayor"
        ]
    ):
        puntos += 0.20

    # L3 - 10A 10B 10A 10B
    #
    # Se aceptan espacios, comas y punto y coma.
    # Se exige A/B en mayúscula porque es arte mayor.

    respuesta_l3 = respuestas.get("l3", "").strip()

    respuesta_l3 = re.sub(
        r"[,;]+",
        " ",
        respuesta_l3
    )

    respuesta_l3 = re.sub(
        r"\s+",
        " ",
        respuesta_l3
    ).strip()

    if respuesta_l3 == "10A 10B 10A 10B":
        puntos += 0.30

    # L4 - rima consonante
    if contiene_alguna(
        respuestas.get("l4", ""),
        [
            "consonante",
            "rima consonante"
        ]
    ):
        puntos += 0.25

    # L5 - sinalefa
    #
    # Sinalefas reales del poema:
    # sobre el
    # viento susurra
    # mira el
    # También se acepta "sobre_el", etc.

    respuesta_l5 = normalizar(
        respuestas.get("l5", "")
    ).replace("_", " ")

    sinalefas_validas = [
        "sobre el",
        "viento susurra",
        "mira el"
    ]

    if any(
        sinalefa in respuesta_l5
        for sinalefa in sinalefas_validas
    ):
        puntos += 0.25

    # L6 - personificación
    #
    # "El viento susurra" es personificación.

    respuesta_l6 = normalizar(
        respuestas.get("l6", "")
    )

    if (
        "viento susurra" in respuesta_l6
        or "el viento susurra" in respuesta_l6
        or "viento" in respuesta_l6 and "susurra" in respuesta_l6
    ):
        puntos += 0.30

    return round(min(puntos, 1.50), 2)


# ============================================================
# SINTAXIS
# MÁXIMO: 1,50
# ============================================================

def corregir_sintaxis(respuestas):

    puntos = 0.0

    # --------------------------------------------------------
    # FRASE / ORACIÓN
    # 3 preguntas = 0,60
    # --------------------------------------------------------

    # X1 - Buenas tardes = frase
    if contiene_alguna(
        respuestas.get("x1", ""),
        ["frase"]
    ):
        puntos += 0.20

    # X2 - El perro ladra = oración
    if contiene_alguna(
        respuestas.get("x2", ""),
        ["oracion", "oración"]
    ):
        puntos += 0.20

    # X3 - Mi hermano estudia = oración
    if contiene_alguna(
        respuestas.get("x3", ""),
        ["oracion", "oración"]
    ):
        puntos += 0.20

    # --------------------------------------------------------
    # MODALIDAD ORACIONAL
    # 4 preguntas = 0,90
    # --------------------------------------------------------

    # X4 - interrogativa
    if contiene_alguna(
        respuestas.get("x4", ""),
        ["interrogativa", "interrogativo"]
    ):
        puntos += 0.225

    # X5 - exclamativa
    if contiene_alguna(
        respuestas.get("x5", ""),
        ["exclamativa", "exclamativo"]
    ):
        puntos += 0.225

    # X6 - enunciativa
    if contiene_alguna(
        respuestas.get("x6", ""),
        ["enunciativa", "enunciativo"]
    ):
        puntos += 0.225

    # X7 - exhortativa / imperativa
    if contiene_alguna(
        respuestas.get("x7", ""),
        [
            "exhortativa",
            "exhortativo",
            "imperativa",
            "imperativo"
        ]
    ):
        puntos += 0.225

    return round(min(puntos, 1.50), 2)


# ============================================================
# DIÁLOGO
# MÁXIMO: 1,00
# ============================================================

def corregir_dialogo(respuestas):

    puntos = 0.0

    # D1 - personajes
    personajes = lista_normalizada(
        respuestas.get("d1", "")
    )

    tiene_lucia = any(
        "lucia" in p
        for p in personajes
    )

    tiene_carlos = any(
        "carlos" in p
        for p in personajes
    )

    if tiene_lucia and tiene_carlos:
        puntos += 0.25
    elif tiene_lucia or tiene_carlos:
        puntos += 0.125

    # D2 - intervenciones
    if contiene_alguna(
        respuestas.get("d2", ""),
        ["6", "seis"]
    ):
        puntos += 0.25

    # D3 - estilo indirecto
    #
    # Se comprueban varios elementos:
    # - verbo introductorio
    # - que
    # - había hecho
    # - cambio temporal: el día anterior / el día antes
    #
    # Se permite también "ayer" porque es una adaptación NEE.

    r3 = normalizar(
        respuestas.get("d3", "")
    )

    if contiene_alguna(
        r3,
        [
            "dijo",
            "explico",
            "explico",
            "comento",
            "afirmo"
        ]
    ):
        puntos += 0.10

    if " que " in f" {r3} ":
        puntos += 0.10

    if contiene_alguna(
        r3,
        [
            "habia hecho",
            "había hecho"
        ]
    ):
        puntos += 0.20

    if contiene_alguna(
        r3,
        [
            "dia anterior",
            "día anterior",
            "dia antes",
            "día antes",
            "ayer"
        ]
    ):
        puntos += 0.10

    return round(min(puntos, 1.00), 2)


# ============================================================
# CORRECCIÓN COMPLETA
# TOTAL AUTOMÁTICO = 9 PUNTOS
# ============================================================

def corregir_examen(respuestas):

    resultados = {}

    resultados["comprension"] = corregir_comprension(
        respuestas["comprension"]
    )

    resultados["morfologia"] = corregir_morfologia(
        respuestas["morfologia"]
    )

    resultados["determinantes_pronombres"] = corregir_determinantes_pronombres(
        respuestas["determinantes_pronombres"]
    )

    resultados["semantica"] = corregir_semantica(
        respuestas["semantica"]
    )

    resultados["textos"] = corregir_textos(
        respuestas["textos"]
    )

    resultados["literatura"] = corregir_literatura(
        respuestas["literatura"]
    )

    resultados["sintaxis"] = corregir_sintaxis(
        respuestas["sintaxis"]
    )

    resultados["dialogo"] = corregir_dialogo(
        respuestas["dialogo"]
    )

    nota_automatica = round(
        sum(resultados.values()),
        2
    )

    return resultados, nota_automatica


# ============================================================
# PRODUCCIÓN ESCRITA
# MÁXIMO: 1,00
# ============================================================

def corregir_produccion(texto):

    texto_limpio = str(texto).strip()

    if not texto_limpio:
        return 0.0

    palabras = re.findall(
        r"\b\w+\b",
        texto_limpio,
        flags=re.UNICODE
    )

    numero_palabras = len(palabras)

    # Para la adaptación NEE:
    # - texto vacío = 0
    # - texto muy corto = 0,25
    # - texto con cierta elaboración = 0,50
    # - texto suficientemente desarrollado = 0,75
    # - texto desarrollado = 1,00

    if numero_palabras < 5:
        return 0.25

    if numero_palabras < 10:
        return 0.50

    if numero_palabras < 20:
        return 0.75

    return 1.00


# ============================================================
# EXCEL INDIVIDUAL
# ============================================================

def crear_excel_individual(
    nombre,
    grupo,
    resultados,
    nota_automatica,
    produccion,
    nota_final,
    faltas
):

    datos = {
        "Alumno": [nombre],
        "Grupo": [grupo],

        "Comprensión": [
            resultados["comprension"]
        ],

        "Morfología": [
            resultados["morfologia"]
        ],

        "Determinantes y pronombres": [
            resultados["determinantes_pronombres"]
        ],

        "Semántica": [
            resultados["semantica"]
        ],

        "Tipos de texto": [
            resultados["textos"]
        ],

        "Literatura": [
            resultados["literatura"]
        ],

        "Sintaxis": [
            resultados["sintaxis"]
        ],

        "Diálogo": [
            resultados["dialogo"]
        ],

        "Nota automática": [
            nota_automatica
        ],

        "Producción escrita": [
            produccion
        ],

        "Nota final": [
            nota_final
        ],

        "Faltas detectadas": [
            faltas
        ]
    }

    df = pd.DataFrame(datos)

    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        df.to_excel(
            writer,
            index=False,
            sheet_name="Resultado"
        )

    output.seek(0)

    return output


# ============================================================
# INICIO DE LA APP
# ============================================================

st.title("📘 Evaluación inicial – 2.º ESO NEE")

st.markdown(
    """
    ### Antes de empezar

    Lee las preguntas con calma.

    **Escribe tus respuestas de la forma más clara posible.**

    Las faltas de ortografía se pueden detectar, pero **no restan puntos**.
    """
)


# ============================================================
# DATOS DEL ALUMNO
# ============================================================

st.header("👤 Datos del alumno")

nombre = st.text_input(
    "Nombre y apellidos",
    key="nombre"
)

grupo = st.selectbox(
    "Grupo",
    ["A", "B", "C", "D", "E"],
    key="grupo"
)


# ============================================================
# COMPROBAR SI YA HA REALIZADO EL EXAMEN
# ============================================================

df_resultados = cargar_resultados()

ya_realizado = False

if nombre.strip() and not df_resultados.empty:

    if "name" in df_resultados.columns and "group" in df_resultados.columns:

        nombres_guardados = (
            df_resultados["name"]
            .fillna("")
            .astype(str)
            .map(normalizar)
        )

        grupos_guardados = (
            df_resultados["group"]
            .fillna("")
            .astype(str)
            .str.upper()
        )

        nombre_actual = normalizar(nombre)
        grupo_actual = grupo.upper()

        ya_realizado = (
            (nombres_guardados == nombre_actual)
            & (grupos_guardados == grupo_actual)
        ).any()


if ya_realizado:

    st.error(
        "Este alumno ya ha realizado la evaluación en este grupo."
    )

    st.stop()


# ============================================================
# FORMULARIO
# ============================================================

with st.form("examen_nee"):

    respuestas = {
        "comprension": {},
        "morfologia": {},
        "determinantes_pronombres": {},
        "semantica": {},
        "textos": {},
        "literatura": {},
        "sintaxis": {},
        "dialogo": {}
    }


    # ========================================================
    # 1. COMPRENSIÓN
    # ========================================================

    st.header("1. Comprensión lectora")

    st.markdown(
        f'<div class="bloque"><div class="pregunta">Lee el texto.</div>'
        f'<div class="ayuda">{EXAMEN_DATOS["comprension"]["texto"].replace(chr(10), "<br>")}</div></div>',
        unsafe_allow_html=True
    )

    for pregunta in EXAMEN_DATOS["comprension"]["preguntas"]:

        st.markdown(
            f'<div class="pregunta">{pregunta["enunciado"]}</div>',
            unsafe_allow_html=True
        )

        respuestas["comprension"][pregunta["id"]] = st.text_area(
            "",
            key=pregunta["id"],
            height=90
        )


    # ========================================================
    # 2. MORFOLOGÍA
    # ========================================================

    st.header("2. Morfología")

    st.markdown(
        "Completa los datos de cada palabra."
    )

    for palabra in EXAMEN_DATOS["morfologia"]:

        st.subheader(
            f"Palabra: {palabra['palabra']}"
        )

        respuestas["morfologia"][palabra["id"]] = {}

        for campo in palabra["campos"]:

            respuestas["morfologia"][palabra["id"]][campo] = st.text_input(
                campo,
                key=f'{palabra["id"]}_{campo}'
            )


    # ========================================================
    # 3. DETERMINANTES Y PRONOMBRES
    # ========================================================

    st.header("3. Determinantes y pronombres")

    for pregunta in EXAMEN_DATOS["determinantes_pronombres"]:

        st.markdown(
            f'<div class="pregunta">{pregunta["frase"]}</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            f'<div class="pregunta">{pregunta["enunciado"]}</div>',
            unsafe_allow_html=True
        )

        respuestas["determinantes_pronombres"][
            pregunta["id"]
        ] = st.text_input(
            "Respuesta",
            key=pregunta["id"]
        )


    # ========================================================
    # 4. SEMÁNTICA
    # ========================================================

    st.header("4. Semántica")

    for pregunta in EXAMEN_DATOS["semantica"]:

        st.markdown(
            f'<div class="pregunta">{pregunta["enunciado"]}</div>',
            unsafe_allow_html=True
        )

        respuestas["semantica"][
            pregunta["id"]
        ] = st.text_input(
            "Respuesta",
            key=pregunta["id"]
        )


    # ========================================================
    # 5. TIPOS DE TEXTO
    # ========================================================

    st.header("5. Tipos de texto")

    st.markdown(
        f'<div class="pregunta">{EXAMEN_DATOS["textos"]["enunciado"]}</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        f"""
        <div class="bloque">
        <strong>Texto A</strong><br>
        {EXAMEN_DATOS["textos"]["textos"]["A"]}
        <br><br>
        <strong>Texto B</strong><br>
        {EXAMEN_DATOS["textos"]["textos"]["B"]}
        </div>
        """,
        unsafe_allow_html=True
    )

    for pregunta in EXAMEN_DATOS["textos"]["preguntas"]:

        st.markdown(
            f'<div class="pregunta">{pregunta["enunciado"]}</div>',
            unsafe_allow_html=True
        )

        respuestas["textos"][
            pregunta["id"]
        ] = st.text_input(
            "Respuesta",
            key=pregunta["id"]
        )


    # ========================================================
    # 6. LITERATURA
    # ========================================================

    st.header("6. Literatura")

    st.markdown(
        f"""
        <div class="bloque">
        <strong>Lee el poema:</strong><br><br>
        {EXAMEN_DATOS["literatura"]["poema"].replace(chr(10), "<br>")}
        </div>
        """,
        unsafe_allow_html=True
    )

    for pregunta in EXAMEN_DATOS["literatura"]["preguntas"]:

        st.markdown(
            f'<div class="pregunta">{pregunta["enunciado"]}</div>',
            unsafe_allow_html=True
        )

        respuestas["literatura"][
            pregunta["id"]
        ] = st.text_area(
            "",
            key=pregunta["id"],
            height=80
        )


    # ========================================================
    # 7. SINTAXIS
    # ========================================================

    st.header("7. Sintaxis")

    for pregunta in EXAMEN_DATOS["sintaxis"]:

        st.markdown(
            f'<div class="pregunta">{pregunta["frase"]}</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            f'<div class="ayuda">{pregunta["enunciado"]}</div>',
            unsafe_allow_html=True
        )

        respuestas["sintaxis"][
            pregunta["id"]
        ] = st.text_input(
            "Respuesta",
            key=pregunta["id"]
        )


    # ========================================================
    # 8. DIÁLOGO
    # ========================================================

    st.header("8. Diálogo")

    st.markdown(
        f"""
        <div class="bloque">
        {EXAMEN_DATOS["dialogo"]["texto"].replace(chr(10), "<br>")}
        </div>
        """,
        unsafe_allow_html=True
    )

    for pregunta in EXAMEN_DATOS["dialogo"]["preguntas"]:

        st.markdown(
            f'<div class="pregunta">{pregunta["enunciado"]}</div>',
            unsafe_allow_html=True
        )

        respuestas["dialogo"][
            pregunta["id"]
        ] = st.text_area(
            "",
            key=pregunta["id"],
            height=100
        )


    # ========================================================
    # PRODUCCIÓN ESCRITA
    # ========================================================

    st.header("9. Producción escrita")

    st.markdown(
        """
        Escribe un pequeño texto relacionado con una experiencia,
        un viaje o un día especial.
        
        Intenta escribir **varias frases completas**.
        """
    )

    produccion_texto = st.text_area(
        "Escribe aquí tu texto:",
        height=220,
        key="produccion"
    )


    # ========================================================
    # BOTÓN
    # ========================================================

    enviado = st.form_submit_button(
        "✅ Terminar evaluación"
    )


# ============================================================
# CORREGIR Y GUARDAR
# ============================================================

if enviado:

    if not nombre.strip():

        st.error(
            "Escribe tu nombre y apellidos antes de terminar."
        )

        st.stop()

    resultados, nota_automatica = corregir_examen(
        respuestas
    )

    faltas = detectar_faltas(
        produccion_texto
    )

    produccion = corregir_produccion(
        produccion_texto
    )

    nota_final = round(
        min(
            nota_automatica + produccion,
            10.0
        ),
        2
    )

    datos_guardar = {
        "timestamp": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),

        "name": nombre.strip(),

        "group": grupo,

        "comprension": resultados["comprension"],

        "morfologia": resultados["morfologia"],

        "determinantes_pronombres": resultados[
            "determinantes_pronombres"
        ],

        "semantica": resultados["semantica"],

        "textos": resultados["textos"],

        "literatura": resultados["literatura"],

        "sintaxis": resultados["sintaxis"],

        "dialogo": resultados["dialogo"],

        "nota_automatica": nota_automatica,

        "produccion_escrita": produccion,

        "nota_final": nota_final,

        "faltas": faltas
    }

    guardar_resultado(
        datos_guardar
    )

    # Guardamos en sesión para mostrar el resultado
    st.session_state["resultado_guardado"] = True
    st.session_state["resultado_nombre"] = nombre.strip()
    st.session_state["resultado_grupo"] = grupo
    st.session_state["resultado"] = resultados
    st.session_state["nota_automatica"] = nota_automatica
    st.session_state["produccion"] = produccion
    st.session_state["nota_final"] = nota_final
    st.session_state["faltas"] = faltas

    st.rerun()


# ============================================================
# MOSTRAR RESULTADO
# ============================================================

if st.session_state.get("resultado_guardado", False):

    st.header("📊 Resultado")

    nota_automatica = st.session_state["nota_automatica"]
    produccion = st.session_state["produccion"]
    nota_final = st.session_state["nota_final"]
    faltas = st.session_state["faltas"]

    st.success(
        f"Evaluación terminada. Tu nota final es: **{nota_final:.2f} / 10**"
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Prueba automática",
            f"{nota_automatica:.2f} / 9"
        )

    with col2:
        st.metric(
            "Producción escrita",
            f"{produccion:.2f} / 1"
        )

    with col3:
        st.metric(
            "Nota final",
            f"{nota_final:.2f} / 10"
        )

    if faltas > 0:

        st.info(
            f"Se han detectado {faltas} posibles faltas o abreviaturas. "
            "Estas detecciones **no restan puntos**."
        )

    resultados = st.session_state["resultado"]

    st.subheader("Resultados por apartado")

    tabla = pd.DataFrame(
        {
            "Apartado": [
                "Comprensión",
                "Morfología",
                "Determinantes y pronombres",
                "Semántica",
                "Tipos de texto",
                "Literatura",
                "Sintaxis",
                "Diálogo"
            ],

            "Puntuación": [
                resultados["comprension"],
                resultados["morfologia"],
                resultados["determinantes_pronombres"],
                resultados["semantica"],
                resultados["textos"],
                resultados["literatura"],
                resultados["sintaxis"],
                resultados["dialogo"]
            ]
        }
    )

    st.dataframe(
        tabla,
        use_container_width=True,
        hide_index=True
    )

    # ========================================================
    # EXCEL INDIVIDUAL
    # ========================================================

    excel = crear_excel_individual(
        st.session_state["resultado_nombre"],
        st.session_state["resultado_grupo"],
        resultados,
        nota_automatica,
        produccion,
        nota_final,
        faltas
    )

    st.download_button(
        label="📥 Descargar resultado en Excel",
        data=excel,
        file_name=(
            f"resultado_"
            f"{st.session_state['resultado_nombre'].replace(' ', '_')}.xlsx"
        ),
        mime=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        )
    )


# ============================================================
# ESTADÍSTICAS DEL GRUPO
# ============================================================

st.header("📊 Estadísticas del grupo")

df = cargar_resultados()

if not df.empty and "group" in df.columns:

    grupo_actual = grupo

    df_grupo = df[
        df["group"]
        .fillna("")
        .astype(str)
        .str.upper()
        == grupo_actual.upper()
    ].copy()

    if not df_grupo.empty:

        if "nota_final" in df_grupo.columns:

            df_grupo["nota_final"] = pd.to_numeric(
                df_grupo["nota_final"],
                errors="coerce"
            )

            # Orden de realización, no por nota.
            # Así es más difícil identificar a un alumno
            # por su posición.
            df_grupo = df_grupo.reset_index(drop=True)

            df_comparativa = pd.DataFrame(
                {
                    "Alumno": [
                        f"Alumno {i + 1}"
                        for i in range(len(df_grupo))
                    ],
                    "Nota": df_grupo["nota_final"].round(2)
                }
            )

            st.write(
                f"Resultados guardados: **{len(df_grupo)}**"
            )

            st.dataframe(
                df_comparativa,
                use_container_width=True,
                hide_index=True
            )

            media = df_grupo["nota_final"].mean()

            st.metric(
                "Media del grupo",
                f"{media:.2f}"
            )

    else:

        st.info(
            "Todavía no hay resultados guardados en este grupo."
        )

else:

    st.info(
        "Todavía no hay resultados guardados."
    )
