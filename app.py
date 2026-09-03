import streamlit as st
import pandas as pd
import os
import re
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


# ============================================================
# ESTILO ACCESIBLE
# ============================================================

st.markdown(
    """
    <style>

    /* Fuente accesible */
    @import url('https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:wght@400;700&display=swap');

    html, body, [class*="css"] {
        font-family: "Atkinson Hyperlegible", "Lexend", Arial, sans-serif !important;
    }

    /* Texto general */
    .stApp {
        font-size: 20px;
    }

    p, li, label {
        font-size: 20px !important;
        line-height: 1.7 !important;
    }

    /* Títulos */
    h1 {
        font-size: 34px !important;
        line-height: 1.3 !important;
        margin-bottom: 25px !important;
    }

    h2 {
        font-size: 29px !important;
        line-height: 1.4 !important;
        margin-top: 35px !important;
        margin-bottom: 20px !important;
    }

    h3 {
        font-size: 25px !important;
        line-height: 1.4 !important;
    }

    /* Separación de bloques */
    .pregunta {
        padding: 18px 0 24px 0;
        margin-bottom: 15px;
    }

    /* Texto de ayuda */
    .ayuda {
        font-size: 18px;
        line-height: 1.6;
        margin-top: 5px;
        margin-bottom: 15px;
    }

    /* Inputs */
    input, textarea, select {
        font-size: 20px !important;
    }

    /* Botones */
    .stButton > button {
        font-size: 21px !important;
        padding: 12px 24px !important;
        min-height: 55px !important;
    }

    /* Avisos */
    .aviso {
        padding: 18px;
        border-radius: 10px;
        margin: 15px 0;
        line-height: 1.6;
    }

    /* Evitar demasiada anchura */
    .bloque-contenido {
        max-width: 1000px;
        margin: auto;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# FUNCIONES GENERALES
# ============================================================

def normalizar(texto):
    """Normaliza una respuesta para facilitar la corrección."""
    if texto is None:
        return ""

    texto = str(texto).strip().lower()

    reemplazos = {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "ü": "u",
    }

    for original, nuevo in reemplazos.items():
        texto = texto.replace(original, nuevo)

    texto = re.sub(r"\s+", " ", texto)

    return texto


def lista_normalizada(texto):
    """
    Permite separar respuestas mediante:
    - comas
    - punto y coma
    - saltos de línea
    """
    if not texto:
        return []

    partes = re.split(r"[,;\n]+", str(texto))

    return [
        normalizar(p)
        for p in partes
        if normalizar(p)
    ]


def contiene_alguna(respuesta, opciones):
    respuesta = normalizar(respuesta)

    return any(
        normalizar(opcion) in respuesta
        for opcion in opciones
    )


def asegurar_csv():
    """Crea results.csv si todavía no existe."""

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
        "faltas",
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
        df = pd.read_csv(
            RESULTS_FILE,
            encoding="utf-8-sig"
        )
    except Exception:
        return pd.DataFrame()

    return df


def guardar_resultado(resultado):
    asegurar_csv()

    df = cargar_resultados()

    nuevo = pd.DataFrame([resultado])

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
# DETECTOR DE ORTOGRAFÍA
# ============================================================

def detectar_faltas(texto):
    """
    Detector orientativo.
    
    IMPORTANTE:
    En la versión NEE las faltas se detectan,
    pero NO descuentan puntos.
    """

    if not texto:
        return 0

    texto = str(texto)

    faltas = 0

    patrones = [
        r"\bq\b",
        r"\bxq\b",
        r"\bke\b",
        r"\bporq\b",
        r"\bporquee\b",
    ]

    for patron in patrones:
        faltas += len(re.findall(patron, texto.lower()))

    return faltas


# ============================================================
# CORRECCIÓN
# ============================================================

def corregir_comprension(respuestas):

    puntos = 0.0

    # --------------------------------------------------------
    # C1 - Lugar
    # --------------------------------------------------------

    r = respuestas.get("c1", "")

    if contiene_alguna(
        r,
        [
            "estacion",
            "tren",
        ]
    ):
        puntos += 0.50

    # --------------------------------------------------------
    # C2 - Personajes
    # --------------------------------------------------------

    r = respuestas.get("c2", "")
    rn = normalizar(r)

    personajes = 0

    if "hombre" in rn:
        personajes += 1

    if "anciana" in rn or "mujer" in rn:
        personajes += 1

    if personajes >= 2:
        puntos += 0.50
    elif personajes == 1:
        puntos += 0.25

    # --------------------------------------------------------
    # C3 - Tiempo
    # --------------------------------------------------------

    r = respuestas.get("c3", "")

    if contiene_alguna(
        r,
        [
            "temprano",
            "madrugada",
            "por la manana",
            "mañana",
        ]
    ):
        puntos += 0.50

    # --------------------------------------------------------
    # C4 - Tres acciones
    # --------------------------------------------------------

    r = respuestas.get("c4", "")
    elementos = lista_normalizada(r)

    acciones_validas = [
        "llego",
        "llegar",
        "cubria",
        "cubrir",
        "viajaban",
        "viajar",
        "llevaba",
        "llevar",
        "parecia",
        "parecer",
        "dormia",
        "dormir",
        "llegaron",
        "bajo",
        "bajar",
        "era",
    ]

    aciertos = 0

    for elemento in elementos:

        if any(
            normalizar(accion) in elemento
            for accion in acciones_validas
        ):
            aciertos += 1

    aciertos = min(aciertos, 3)

    puntos += aciertos * (0.50 / 3)

    return round(puntos, 2)


def corregir_morfologia(respuestas):

    puntos = 0.0

    respuestas_correctas = {
        "m1": {
            "lexema": ["silenci"],
            "morfemas": [],
            "estructura": ["simple"],
            "categoria": ["sustantivo"],
            "tipo": ["invariable"],
        },

        "m2": {
            "lexema": ["mochil"],
            "morfemas": ["a", "s"],
            "estructura": ["simple"],
            "categoria": ["sustantivo"],
            "tipo": ["variable"],
        },

        "m3": {
            "lexema": ["conoc"],
            "morfemas": ["des", "ido"],
            "estructura": ["derivada"],
            "categoria": ["adjetivo"],
            "tipo": ["variable"],
        },
    }

    for pregunta_id, campos in respuestas_correctas.items():

        respuesta = respuestas.get(pregunta_id, {})

        if not isinstance(respuesta, dict):
            continue

        for campo, opciones in campos.items():

            valor = respuesta.get(campo, "")

            if contiene_alguna(valor, opciones):
                puntos += 0.20

    return round(min(puntos, 1.50), 2)


def corregir_determinantes_pronombres(respuestas):

    puntos = 0.0

    if contiene_alguna(
        respuestas.get("dp1", ""),
        [
            "determinante",
            "demostrativo",
        ]
    ):
        puntos += 0.25

    if contiene_alguna(
        respuestas.get("dp2", ""),
        [
            "pronombre",
            "indefinido",
        ]
    ):
        puntos += 0.25

    return round(puntos, 2)


def corregir_semantica(respuestas):

    puntos = 0.0

    if contiene_alguna(
        respuestas.get("s1", ""),
        [
            "antonimo",
            "antónimo",
            "opuestos",
            "contrarios",
        ]
    ):
        puntos += 0.25

    if contiene_alguna(
        respuestas.get("s2", ""),
        [
            "hiperonimo",
            "hiperónimo",
            "campo semantico",
            "campo semántico",
        ]
    ):
        puntos += 0.25

    if contiene_alguna(
        respuestas.get("s3", ""),
        [
            "polisemia",
            "polisemica",
            "polisémica",
        ]
    ):
        puntos += 0.25

    return round(puntos, 2)


def corregir_textos(respuestas):

    puntos = 0.0

    if contiene_alguna(
        respuestas.get("t1", ""),
        [
            "instructivo",
            "instruccion",
            "instrucción",
        ]
    ):
        puntos += 0.50

    if contiene_alguna(
        respuestas.get("t2", ""),
        [
            "expositivo",
            "explicativo",
        ]
    ):
        puntos += 0.50

    return round(puntos, 2)


def corregir_literatura(respuestas):

    puntos = 0.0

    # L1 - 4 versos
    if normalizar(respuestas.get("l1", "")) in [
        "4",
        "cuatro",
    ]:
        puntos += 0.25

    # L2 - arte mayor
    if contiene_alguna(
        respuestas.get("l2", ""),
        [
            "arte mayor",
            "mayor",
        ]
    ):
        puntos += 0.25

    # L3 - esquema métrico
    esquema = normalizar(
        respuestas.get("l3", "")
    )

    esquema = esquema.replace(",", " ")
    esquema = esquema.replace(";", " ")

    esquema = re.sub(
        r"\s+",
        " ",
        esquema
    ).strip()

    if esquema == "10a 10b 10a 10b":
        puntos += 0.50

    # L4 - rima
    if contiene_alguna(
        respuestas.get("l4", ""),
        [
            "consonante",
        ]
    ):
        puntos += 0.25

    # L5 - sinalefa
    r = normalizar(
        respuestas.get("l5", "")
    )

    if (
        "luna brilla" in r
        or "brilla sobre" in r
        or "sobre el" in r
        or "el gran" in r
    ):
        puntos += 0.25

    # L6 - personificación
    if contiene_alguna(
        respuestas.get("l6", ""),
        [
            "viento susurra",
            "viento",
            "susurra",
        ]
    ):
        puntos += 0.50

    return round(puntos, 2)


def corregir_sintaxis(respuestas):

    puntos = 0.0

    # --------------------------------------------------------
    # Frase / oración
    # Solo 3 preguntas en la adaptación NEE.
    # --------------------------------------------------------

    correctas = {
        "x1": ["frase"],
        "x2": ["oracion", "oración"],
        "x3": ["oracion", "oración"],
    }

    for pregunta, opciones in correctas.items():

        if contiene_alguna(
            respuestas.get(pregunta, ""),
            opciones
        ):
            puntos += 0.25

    # --------------------------------------------------------
    # Modalidad
    # --------------------------------------------------------

    modalidades = {
        "x4": ["interrogativa"],
        "x5": ["exclamativa"],
        "x6": ["enunciativa"],
        "x7": ["imperativa", "exhortativa"],
    }

    for pregunta, opciones in modalidades.items():

        if contiene_alguna(
            respuestas.get(pregunta, ""),
            opciones
        ):
            puntos += 0.25

    return round(puntos, 2)


def corregir_dialogo(respuestas):

    puntos = 0.0

    # D1 - personajes
    r = normalizar(
        respuestas.get("d1", "")
    )

    lucia = "lucia" in r
    carlos = "carlos" in r

    if lucia and carlos:
        puntos += 0.40
    elif lucia or carlos:
        puntos += 0.20

    # D2 - intervenciones
    if normalizar(
        respuestas.get("d2", "")
    ) in ["6", "seis"]:
        puntos += 0.30

    # D3 - estilo indirecto
    r = normalizar(
        respuestas.get("d3", "")
    )

    if "carlos dijo" in r or "carlos explico" in r:
        puntos += 0.10

    if "que" in r:
        puntos += 0.10

    if (
        "habia hecho" in r
        or "habia terminado" in r
        or "lo habia hecho" in r
    ):
        puntos += 0.10

    return round(min(puntos, 1.00), 2)


# ============================================================
# CORRECCIÓN COMPLETA
# ============================================================

def corregir_examen(respuestas):

    resultados = {}

    resultados["comprension"] = corregir_comprension(
        respuestas.get("comprension", {})
    )

    resultados["morfologia"] = corregir_morfologia(
        respuestas.get("morfologia", {})
    )

    resultados["determinantes_pronombres"] = corregir_determinantes_pronombres(
        respuestas.get("determinantes_pronombres", {})
    )

    resultados["semantica"] = corregir_semantica(
        respuestas.get("semantica", {})
    )

    resultados["textos"] = corregir_textos(
        respuestas.get("textos", {})
    )

    resultados["literatura"] = corregir_literatura(
        respuestas.get("literatura", {})
    )

    resultados["sintaxis"] = corregir_sintaxis(
        respuestas.get("sintaxis", {})
    )

    resultados["dialogo"] = corregir_dialogo(
        respuestas.get("dialogo", {})
    )

    # --------------------------------------------------------
    # IMPORTANTE:
    # En NEE las faltas NO descuentan nota.
    # --------------------------------------------------------

    nota_automatica = round(
        sum(resultados.values()),
        2
    )

    return resultados, nota_automatica


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
        "Comprensión": [resultados.get("comprension", 0)],
        "Morfología": [resultados.get("morfologia", 0)],
        "Determinantes y pronombres": [
            resultados.get(
                "determinantes_pronombres",
                0
            )
        ],
        "Semántica": [resultados.get("semantica", 0)],
        "Tipos de texto": [resultados.get("textos", 0)],
        "Literatura": [resultados.get("literatura", 0)],
        "Sintaxis": [resultados.get("sintaxis", 0)],
        "Diálogo": [resultados.get("dialogo", 0)],
        "Nota automática": [nota_automatica],
        "Producción escrita": [produccion],
        "Nota final": [nota_final],
        "Faltas detectadas": [faltas],
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
# INTERFAZ
# ============================================================

st.markdown(
    '<div class="bloque-contenido">',
    unsafe_allow_html=True
)

st.title("📘 Evaluación inicial de Lengua – 2.º ESO")

st.markdown(
    """
    ### Adaptación NEE

    Lee cada pregunta con calma.

    **No tengas prisa.**

    Escribe tus respuestas de la forma más clara posible.
    """
)

st.divider()


# ============================================================
# DATOS DEL ALUMNO
# ============================================================

st.header("👤 Tus datos")

nombre = st.text_input(
    "Escribe tu nombre y apellidos:",
    key="nombre"
)

grupo = st.selectbox(
    "Selecciona tu grupo:",
    [
        "A",
        "B",
        "C",
        "D",
        "E",
    ],
    key="grupo"
)


# ============================================================
# COMPROBAR REPETICIÓN
# ============================================================

df_existente = cargar_resultados()

ya_realizado = False

if nombre.strip() and not df_existente.empty:

    if "name" in df_existente.columns and "group" in df_existente.columns:

        coincidencias = df_existente[
            (
                df_existente["name"]
                .fillna("")
                .astype(str)
                .str.strip()
                .str.lower()
                ==
                nombre.strip().lower()
            )
            &
            (
                df_existente["group"]
                .fillna("")
                .astype(str)
                .str.strip()
                .str.upper()
                ==
                grupo.upper()
            )
        ]

        ya_realizado = not coincidencias.empty


if ya_realizado:

    st.error(
        "Este nombre ya tiene un examen registrado en este grupo."
    )

    st.stop()


# ============================================================
# FORMULARIO
# ============================================================

respuestas = {}

with st.form("examen_nee"):

    # ========================================================
    # COMPRENSIÓN
    # ========================================================

    st.header("1. Comprensión lectora")

    texto = EXAMEN["2ESO_NEE"]["comprension"]["texto"]

    st.markdown(
        f"""
        <div class="aviso">
        <strong>Lee este texto con atención:</strong>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(texto)

    respuestas["comprension"] = {}

    for pregunta in EXAMEN["2ESO_NEE"]["comprension"]["preguntas"]:

        pid = pregunta["id"]

        respuestas["comprension"][pid] = st.text_area(
            pregunta["enunciado"],
            key=pid,
            height=100
        )


    # ========================================================
    # MORFOLOGÍA
    # ========================================================

    st.header("2. Morfología")

    respuestas["morfologia"] = {}

    for pregunta in EXAMEN["2ESO_NEE"]["morfologia"]:

        pid = pregunta["id"]

        st.markdown(
            f"### Palabra: **{pregunta['palabra']}**"
        )

        respuestas["morfologia"][pid] = {}

        for campo in pregunta["campos"]:

            respuestas["morfologia"][pid][campo] = st.text_input(
                campo,
                key=f"{pid}_{campo}"
            )


    # ========================================================
    # DETERMINANTES Y PRONOMBRES
    # ========================================================

    st.header("3. Determinantes y pronombres")

    respuestas["determinantes_pronombres"] = {}

    for pregunta in EXAMEN["2ESO_NEE"]["determinantes_pronombres"]:

        pid = pregunta["id"]

        st.markdown(
            f"**{pregunta['frase']}**"
        )

        respuestas["determinantes_pronombres"][pid] = st.text_input(
            pregunta["enunciado"],
            key=pid
        )


    # ========================================================
    # SEMÁNTICA
    # ========================================================

    st.header("4. Semántica")

    respuestas["semantica"] = {}

    for pregunta in EXAMEN["2ESO_NEE"]["semantica"]:

        pid = pregunta["id"]

        st.markdown(
            pregunta["enunciado"]
        )

        respuestas["semantica"][pid] = st.text_input(
            "Respuesta:",
            key=pid
        )


    # ========================================================
    # TIPOS DE TEXTO
    # ========================================================

    st.header("5. Tipos de texto")

    st.markdown(
        EXAMEN["2ESO_NEE"]["textos"]["enunciado"]
    )

    respuestas["textos"] = {}

    for letra, texto in EXAMEN["2ESO_NEE"]["textos"]["textos"].items():

        st.markdown(
            f"""
            **Texto {letra}**

            {texto}
            """
        )

        pid = "t1" if letra == "A" else "t2"

        pregunta = next(
            p for p in EXAMEN["2ESO_NEE"]["textos"]["preguntas"]
            if p["id"] == pid
        )

        respuestas["textos"][pid] = st.text_input(
            pregunta["enunciado"],
            key=pid
        )


    # ========================================================
    # LITERATURA
    # ========================================================

    st.header("6. Literatura")

    st.markdown(
        """
        **Lee el poema:**
        """
    )

    st.markdown(
        EXAMEN["2ESO_NEE"]["literatura"]["poema"]
    )

    respuestas["literatura"] = {}

    for pregunta in EXAMEN["2ESO_NEE"]["literatura"]["preguntas"]:

        pid = pregunta["id"]

        if pid in ["l3", "l5", "l6"]:

            respuestas["literatura"][pid] = st.text_area(
                pregunta["enunciado"],
                key=pid,
                height=100
            )

        else:

            respuestas["literatura"][pid] = st.text_input(
                pregunta["enunciado"],
                key=pid
            )


    # ========================================================
    # SINTAXIS
    # ========================================================

    st.header("7. Sintaxis")

    respuestas["sintaxis"] = {}

    sintaxis = EXAMEN["2ESO_NEE"]["sintaxis"]

    for pregunta in sintaxis:

        pid = pregunta["id"]

        st.markdown(
            f"**{pregunta['frase']}**"
        )

        respuestas["sintaxis"][pid] = st.text_input(
            pregunta["enunciado"],
            key=pid
        )


    # ========================================================
    # DIÁLOGO
    # ========================================================

    st.header("8. Diálogo")

    st.markdown(
        """
        **Lee el diálogo:**
        """
    )

    st.markdown(
        EXAMEN["2ESO_NEE"]["dialogo"]["texto"]
    )

    respuestas["dialogo"] = {}

    for pregunta in EXAMEN["2ESO_NEE"]["dialogo"]["preguntas"]:

        pid = pregunta["id"]

        respuestas["dialogo"][pid] = st.text_area(
            pregunta["enunciado"],
            key=pid,
            height=110
        )


    # ========================================================
    # PRODUCCIÓN ESCRITA
    # ========================================================

    st.header("9. Producción escrita")

    produccion = st.text_area(
        "Escribe un pequeño texto contando un viaje o una experiencia que recuerdes.",
        height=220,
        key="produccion"
    )


    # ========================================================
    # ENVIAR
    # ========================================================

    enviar = st.form_submit_button(
        "✅ Terminar y corregir",
        use_container_width=True
    )


# ============================================================
# RESULTADOS
# ============================================================

if enviar:

    if not nombre.strip():

        st.error(
            "Antes de terminar, escribe tu nombre y apellidos."
        )

        st.stop()


    resultados, nota_automatica = corregir_examen(
        respuestas
    )


    # --------------------------------------------------------
    # ORTOGRAFÍA
    # --------------------------------------------------------

    texto_completo = " ".join(
        [
            str(respuestas.get("comprension", {})),
            str(respuestas.get("literatura", {})),
            str(respuestas.get("dialogo", {})),
            str(produccion),
        ]
    )

    faltas = detectar_faltas(
        texto_completo
    )


    # --------------------------------------------------------
    # PRODUCCIÓN ESCRITA
    # --------------------------------------------------------

    if produccion.strip():

        # De momento se registra como 1 punto disponible.
        # La corrección automática de producción escrita
        # se puede ajustar después con los criterios definitivos.

        nota_produccion = 1.0

    else:

        nota_produccion = 0.0


    # --------------------------------------------------------
    # NOTA FINAL
    # --------------------------------------------------------

    nota_final = round(
        nota_automatica + nota_produccion,
        2
    )

    nota_final = min(
        nota_final,
        10.0
    )


    # --------------------------------------------------------
    # GUARDAR
    # --------------------------------------------------------

    fila = {
        "timestamp": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),

        "name": nombre.strip(),

        "group": grupo,

        "comprension": resultados.get(
            "comprension",
            0
        ),

        "morfologia": resultados.get(
            "morfologia",
            0
        ),

        "determinantes_pronombres": resultados.get(
            "determinantes_pronombres",
            0
        ),

        "semantica": resultados.get(
            "semantica",
            0
        ),

        "textos": resultados.get(
            "textos",
            0
        ),

        "literatura": resultados.get(
            "literatura",
            0
        ),

        "sintaxis": resultados.get(
            "sintaxis",
            0
        ),

        "dialogo": resultados.get(
            "dialogo",
            0
        ),

        "nota_automatica": nota_automatica,

        "produccion_escrita": nota_produccion,

        "nota_final": nota_final,

        "faltas": faltas,
    }

    guardar_resultado(
        fila
    )


    # --------------------------------------------------------
    # MOSTRAR RESULTADO
    # --------------------------------------------------------

    st.success(
        "¡Examen terminado!"
    )

    st.header("📊 Tu resultado")

    st.metric(
        "Nota final",
        f"{nota_final:.2f} / 10"
    )

    st.info(
        f"Se han detectado {faltas} posibles faltas de ortografía. "
        "En esta adaptación NEE **no se descuentan puntos por ortografía**."
    )


    # --------------------------------------------------------
    # DESGLOSE
    # --------------------------------------------------------

    st.subheader(
        "Resultados por apartado"
    )

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
                "Diálogo",
            ],

            "Puntuación": [
                resultados["comprension"],
                resultados["morfologia"],
                resultados["determinantes_pronombres"],
                resultados["semantica"],
                resultados["textos"],
                resultados["literatura"],
                resultados["sintaxis"],
                resultados["dialogo"],
            ]
        }
    )

    st.dataframe(
        tabla,
        use_container_width=True,
        hide_index=True
    )


    # --------------------------------------------------------
    # EXCEL
    # --------------------------------------------------------

    excel = crear_excel_individual(
        nombre,
        grupo,
        resultados,
        nota_automatica,
        nota_produccion,
        nota_final,
        faltas
    )

    st.download_button(
        label="📥 Descargar mi resultado en Excel",
        data=excel,
        file_name=f"resultado_{nombre.replace(' ', '_')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )


# ============================================================
# ESTADÍSTICAS DEL GRUPO
# ============================================================

st.divider()

st.header("📊 Estadísticas del grupo")

df = cargar_resultados()

if df.empty:

    st.info(
        "Todavía no hay resultados guardados."
    )

else:

    st.write(
        f"Resultados guardados: **{len(df)}**"
    )

    grupo_actual = grupo

    df_grupo = df[
        df["group"]
        .fillna("")
        .astype(str)
        .str.upper()
        ==
        grupo_actual.upper()
    ].copy()

    if df_grupo.empty:

        st.info(
            "Todavía no hay resultados de este grupo."
        )

    else:

        # ----------------------------------------------------
        # IMPORTANTE:
        # NO se muestran nombres reales.
        # ----------------------------------------------------

        df_grupo = df_grupo.reset_index(drop=True)

        df_grupo["Alumno"] = [
            f"Alumno {i + 1}"
            for i in range(len(df_grupo))
        ]

        tabla_grupo = df_grupo[
            [
                "Alumno",
                "nota_final"
            ]
        ].copy()

        tabla_grupo.columns = [
            "Alumno",
            "Nota"
        ]

        st.dataframe(
            tabla_grupo,
            use_container_width=True,
            hide_index=True
        )

        st.metric(
            "Media del grupo",
            f"{df_grupo['nota_final'].mean():.2f}"
        )


st.markdown(
    "</div>",
    unsafe_allow_html=True
)
