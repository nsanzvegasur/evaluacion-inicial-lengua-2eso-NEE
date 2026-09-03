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
    import plotly.graph_objects as go

    valores = [
        float(datos.get(c, 0) or 0)
        for c in COMPETENCIAS
    ]

    etiquetas = [
        NOMBRES_COMPETENCIAS[c]
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
            name="Alumno",
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


def comparativa(alumno, df):
    import pandas as pd
    import plotly.graph_objects as go

    if df is None or df.empty:
        return None

    nombres = []
    alumno_vals = []
    clase_vals = []

    for c in COMPETENCIAS:

        if c not in df.columns:
            continue

        nombres.append(
            NOMBRES_COMPETENCIAS[c]
        )

        valor_alumno = pd.to_numeric(
            pd.Series(
                [alumno.get(c, 0)]
            ),
            errors="coerce",
        ).fillna(0).iloc[0]

        valor_clase = pd.to_numeric(
            df[c],
            errors="coerce",
        ).mean()

        alumno_vals.append(
            float(valor_alumno)
        )

        clase_vals.append(
            float(
                0
                if pd.isna(valor_clase)
                else valor_clase
            )
        )

    if not nombres:
        return None

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=nombres,
            y=alumno_vals,
            name="Alumno",
        )
    )

    fig.add_trace(
        go.Bar(
            x=nombres,
            y=clase_vals,
            name="Media clase",
        )
    )

    fig.update_layout(
        title="Alumno vs. media de la clase",
        barmode="group",
        yaxis=dict(
            title="Nota sobre 10",
            range=[0, 10],
        ),
        margin=dict(
            l=40,
            r=40,
            t=60,
            b=80,
        ),
    )

    return fig


def generar_perfil(datos):

    resultado = []

    for c in COMPETENCIAS:

        nota = round(
            float(
                datos.get(c, 0) or 0
            ),
            2,
        )

        if nota < 5:

            nivel = "Necesita refuerzo"
            texto = (
                f"{NOMBRES_COMPETENCIAS[c]}: "
                "necesita refuerzo."
            )

        elif nota < 8:

            nivel = "Nivel adecuado"
            texto = (
                f"{NOMBRES_COMPETENCIAS[c]}: "
                "nivel adecuado."
            )

        else:

            nivel = "Fortaleza"
            texto = (
                f"{NOMBRES_COMPETENCIAS[c]}: "
                "fortaleza."
            )

        resultado.append(
            {
                "competencia": c,
                "nombre": NOMBRES_COMPETENCIAS[c],
                "nota": nota,
                "nivel": nivel,
                "texto": texto,
            }
        )

    return resultado

# =========================================================
# CONFIGURACIÓN
# =========================================================

st.set_page_config(
    page_title="Evaluación Inicial Lengua 2.º ESO",
    page_icon="📚",
    layout="centered",
)

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


def exacta(valor, *alternativas):
    v = normalizar(valor)

    if not v:
        return False

    return any(
        v == normalizar(x)
        for x in alternativas
    )


def contiene(valor, *alternativas):
    v = normalizar(valor)

    if not v:
        return False

    return any(
        normalizar(x) in v
        for x in alternativas
    )


# =========================================================
# CORRECCIÓN
# =========================================================

def corregir(res):
    p = {
        "comprension": 0.0,
        "morfologia": 0.0,
        "semantica": 0.0,
        "textos": 0.0,
        "literatura": 0.0,
        "sintaxis": 0.0,
    }

    # =====================================================
    # 1. COMPRENSIÓN = 2 PUNTOS
    # =====================================================

    # C1. Lugar
    if contiene(
        res.get("c1", ""),
        "tren",
        "estacion",
        "estación",
        "vagon",
        "vagón"
    ):
        p["comprension"] += 0.50

    # C2. Personajes
    personajes = lista_normalizada(res.get("c2", ""))

    tiene_hombre = any(
        "hombre" in x or
        "joven" in x
        for x in personajes
    )

    tiene_anciana = any(
        "anciana" in x
        for x in personajes
    )

    if tiene_hombre:
        p["comprension"] += 0.25

    if tiene_anciana:
        p["comprension"] += 0.25

    # C3. Cuándo
    if contiene(
        res.get("c3", ""),
        "temprano",
        "madrugada",
        "noche"
    ):
        p["comprension"] += 0.50

    # C4. Tres acciones
    acciones = [
        "llego",
        "llegó",
        "cubria",
        "cubría",
        "veia",
        "veía",
        "viajaban",
        "llevaba",
        "parecia",
        "parecía",
        "dormia",
        "dormía",
        "bajo",
        "bajó",
        "detuvo",
        "detenia",
        "detenía",
        "avanzar",
        "avanzaba"
    ]

    respuesta_acciones = normalizar(
        res.get("c4", "")
    )

    encontradas = set()

    for accion in acciones:
        if accion in respuesta_acciones:
            encontradas.add(accion)

    p["comprension"] += (
        min(len(encontradas), 3) / 3
    ) * 0.50

    p["comprension"] = min(
        p["comprension"],
        2.0
    )


    # =====================================================
    # 2. MORFOLOGÍA = 2,5 PUNTOS
    # =====================================================

    # Cada palabra:
    # Lexema 0,10
    # Morfemas 0,10
    # Estructura 0,10
    # Categoría 0,15
    # V/I 0,05
    #
    # 0,50 por palabra × 3 = 1,50
    #
    # Determinantes/pronombres = 1,00
    # Total = 2,50

    claves = {
        "m1": {
            "lexema": ("silenci", "silenc"),
            "morfemas": ("o",),
            "estructura": ("simple",),
            "categoria": (
                "sustantivo",
                "comun",
                "común",
                "abstracto",
                "masculino",
                "singular",
            ),
            "vi": ("variable", "v"),
        },

        "m2": {
            "lexema": ("mochil",),
            "morfemas": ("a", "s", "-a", "-s"),
            "estructura": ("simple",),
            "categoria": (
                "sustantivo",
                "comun",
                "común",
                "concreto",
                "femenino",
                "plural",
            ),
            "vi": ("variable", "v"),
        },

        "m3": {
            "lexema": ("conoc",),
            "morfemas": ("des", "ido", "-ido"),
            "estructura": (
                "derivada",
                "derivacion",
                "derivación",
            ),
            "categoria": (
                "adjetivo",
                "calificativo",
                "masculino",
                "singular",
            ),
            "vi": ("variable", "v"),
        },
    }

    campos_peso = {
        "lexema": 0.10,
        "morfemas": 0.10,
        "estructura": 0.10,
        "categoria": 0.15,
        "vi": 0.05,
    }

    for mid, campos in claves.items():

        for campo, alternativas in campos.items():

            valor = res.get(
                f"{mid}_{campo}",
                ""
            )

            v = normalizar(valor)

            ok = False

            if campo == "lexema":

                ok = any(
                    normalizar(a) in v
                    for a in alternativas
                )

            elif campo == "morfemas":

                partes = lista_normalizada(valor)

                if mid == "m1":
                    ok = (
                        "o" in partes
                        or "o" in v
                    )

                elif mid == "m2":
                    ok = (
                        "a" in partes
                        and "s" in partes
                    )

                elif mid == "m3":
                    ok = (
                        "des" in v
                        and "ido" in v
                    )

            elif campo == "categoria":

                if mid == "m1":
                    ok = (
                        "sustantivo" in v
                        and "masculino" in v
                        and "singular" in v
                    )

                elif mid == "m2":
                    ok = (
                        "sustantivo" in v
                        and "femenino" in v
                        and "plural" in v
                    )

                elif mid == "m3":
                    ok = (
                        "adjetivo" in v
                        and "masculino" in v
                        and "singular" in v
                    )

            else:

                ok = any(
                    v == normalizar(a)
                    for a in alternativas
                )

            if ok:
                p["morfologia"] += campos_peso[campo]

    # Determinantes y pronombres
    if exacta(
        res.get("dp1", ""),
        "determinante"
    ):
        p["morfologia"] += 0.50

    if exacta(
        res.get("dp2", ""),
        "pronombre"
    ):
        p["morfologia"] += 0.50

    p["morfologia"] = min(
        round(p["morfologia"], 4),
        2.5
    )


    # =====================================================
    # 3. SEMÁNTICA = 1 PUNTO
    # =====================================================

    sem_correctas = {
        "s1": ("antonimia",),
        "s2": (
            "campo semantico",
            "campo semántico",
        ),
        "s3": ("polisemia",),
    }

    for clave, alternativas in sem_correctas.items():

        if exacta(
            res.get(clave, ""),
            *alternativas
        ):
            p["semantica"] += 1 / 3

    p["semantica"] = min(
        round(p["semantica"], 4),
        1.0
    )


    # =====================================================
    # 4. TEXTOS = 1,5 PUNTOS
    # =====================================================

    # Texto A = instructivo
    if exacta(
        res.get("t1", ""),
        "instructivo",
        "instruccional"
    ):
        p["textos"] += 0.75

    # Texto B = expositivo
    if exacta(
        res.get("t2", ""),
        "expositivo"
    ):
        p["textos"] += 0.75

    p["textos"] = min(
        round(p["textos"], 4),
        1.5
    )


    # =====================================================
    # 5. LITERATURA = 2 PUNTOS
    # =====================================================

    # L1. Número de versos
    if exacta(
        res.get("l1", ""),
        "4"
    ):
        p["literatura"] += 0.30

    # L2. Arte mayor o menor
    if exacta(
        res.get("l2", ""),
        "arte mayor"
    ):
        p["literatura"] += 0.30

    # L3. Esquema métrico
    #
    # Se aceptan las formas:
    # 10A 11B 11B 10A
    # 10A, 11B, 11B, 10A
    # 10A / 11B / 11B / 10A
    #
    # También se acepta sin letras:
    # 10 11 11 10
    #
    met = normalizar(
        res.get("l3", "")
    )

    met_limpia = met.replace(",", " ")
    met_limpia = met_limpia.replace("/", " ")
    met_limpia = met_limpia.replace("-", " ")
    met_limpia = re.sub(
        r"\s+",
        " ",
        met_limpia
    ).strip()

    metricas_validas = {
        "10a 11b 11b 10a",
        "10 11 11 10",
    }

    if met_limpia in metricas_validas:
        p["literatura"] += 0.35

    # L4. Rima
    if exacta(
        res.get("l4", ""),
        "asonante",
        "rima asonante"
    ):
        p["literatura"] += 0.35

    # L5. Sinalefa
    #
    # En el poema aparecen:
    # "resplandece sobre"
    # "sobre el"
    # "brillan sobre"
    # "sobre el"
    # "susurra cerca"
    #
    # Aceptamos las parejas más claras.
    sinal = normalizar(
        res.get("l5", "")
    )

    parejas_sinalefa = [
        "sobre el",
        "brillan sobre",
        "susurra cerca",
        "cerca del",
        "mira el",
    ]

    if any(
        pareja in sinal
        for pareja in parejas_sinalefa
    ):
        p["literatura"] += 0.35

    # L6. Personificación
    #
    # "El viento susurra"
    # es la personificación clara del poema.
    pers = normalizar(
        res.get("l6", "")
    )

    if (
        "viento" in pers
        and "susurra" in pers
    ):
        p["literatura"] += 0.35

    p["literatura"] = min(
        round(p["literatura"], 4),
        2.0
    )


    # =====================================================
    # 6. SINTAXIS = 1 PUNTO
    # =====================================================

    correctas_sintaxis = {

        "x1": (
            "frase",
        ),

        "x2": (
            "oracion",
            "oración",
        ),

        "x3": (
            "oracion",
            "oración",
        ),

        "x4": (
            "interrogativa",
        ),

        "x5": (
            "exclamativa",
        ),

        "x6": (
            "enunciativa",
        ),

        "x7": (
            "exhortativa",
            "imperativa",
        ),
    }

    for clave, alternativas in correctas_sintaxis.items():

        if exacta(
            res.get(clave, ""),
            *alternativas
        ):
            p["sintaxis"] += (
                1.0 / 7
            )

    p["sintaxis"] = min(
        round(p["sintaxis"], 4),
        1.0
    )


    # =====================================================
    # TOTAL
    # =====================================================

    total = round(
        sum(p.values()),
        2
    )

    return p, total


# =========================================================
# ORTOGRAFÍA
# =========================================================

def detectar_ortografia(respuestas):
    """
    Detector conservador.
    No necesita dependencias externas.
    """

    errores = {
        "sustantibo",
        "haver",
        "hechar",
        "aver",
        "aora",
        "havia",
        "hamos",
        "bamos",
        "llendo",
        "dijistes",
        "hicistes",
        "estava",
        "tubieron",
        "tubo",
    }

    encontrados = set()

    for respuesta in respuestas:

        if not respuesta:
            continue

        palabras = re.findall(
            r"\b[\wáéíóúüñ]+\b",
            str(respuesta).lower(),
            flags=re.UNICODE,
        )

        for palabra in palabras:

            if palabra in errores:
                encontrados.add(palabra)

    return len(encontrados), 0


# =========================================================
# GUARDAR CSV
# =========================================================

def guardar_csv(fila):

    campos = [
        "name",
        "group",
        "date",
        "comprension",
        "morfologia",
        "semantica",
        "textos",
        "literatura",
        "sintaxis",
        "nota_sin_faltas",
        "faltas_ortografia",
        "faltas_tildes",
        "descuento_ortografia",
        "nota_final",
    ]

    if os.path.exists(CSV_FILE):

        try:
            df = pd.read_csv(
                CSV_FILE
            )

        except Exception:
            df = pd.DataFrame(
                columns=campos
            )

    else:
        df = pd.DataFrame(
            columns=campos
        )

    for campo in campos:

        if campo not in df.columns:
            df[campo] = ""

    nueva_fila = {
        campo: fila.get(
            campo,
            ""
        )
        for campo in campos
    }

    df = pd.concat(
        [
            df[campos],
            pd.DataFrame([nueva_fila]),
        ],
        ignore_index=True,
    )

    df.to_csv(
        CSV_FILE,
        index=False,
        encoding="utf-8-sig",
    )


# =========================================================
# CSV INDIVIDUAL
# =========================================================

def csv_individual(fila):

    salida = io.StringIO()

    campos = list(
        fila.keys()
    )

    writer = csv.DictWriter(
        salida,
        fieldnames=campos,
    )

    writer.writeheader()
    writer.writerow(fila)

    return salida.getvalue().encode(
        "utf-8-sig"
    )


# =========================================================
# LEER RESULTADOS
# =========================================================

def safe_read_results():

    if not os.path.exists(
        CSV_FILE
    ):

        return pd.DataFrame(
            columns=[
                "name",
                "group",
                "date",
                "comprension",
                "morfologia",
                "semantica",
                "textos",
                "literatura",
                "sintaxis",
                "nota_sin_faltas",
                "faltas_ortografia",
                "faltas_tildes",
                "descuento_ortografia",
                "nota_final",
            ]
        )

    try:

        return pd.read_csv(
            CSV_FILE
        )

    except Exception:

        return pd.DataFrame()


# =========================================================
# CABECERA
# =========================================================

st.title(
    "📚 Evaluación inicial de Lengua — 2.º ESO"
)

st.caption(
    "Lengua Castellana y Literatura · Curso 2026-2027"
)


# =========================================================
# RESULTADO DEL ALUMNO
# =========================================================

if st.session_state.get(
    "enviado",
    False
):

    nombre_resultado = st.session_state[
        "nombre"
    ]

    grupo_resultado = st.session_state[
        "grupo"
    ]

    puntos = st.session_state[
        "puntos"
    ]

    nota_sin_faltas = st.session_state[
        "nota_sin_faltas"
    ]

    descuento = st.session_state[
        "descuento"
    ]

    nota_final = st.session_state[
        "nota_final"
    ]

    faltas = st.session_state[
        "faltas"
    ]

    faltas_tildes = st.session_state[
        "faltas_tildes"
    ]

    fila = st.session_state[
        "fila"
    ]

    scores = {
        "comprension": round(
            puntos["comprension"]
            / 2.0
            * 10,
            2,
        ),

        "morfologia": round(
            puntos["morfologia"]
            / 2.5
            * 10,
            2,
        ),

        "semantica": round(
            puntos["semantica"]
            / 1.0
            * 10,
            2,
        ),

        "textos": round(
            puntos["textos"]
            / 1.5
            * 10,
            2,
        ),

        "literatura": round(
            puntos["literatura"]
            / 2.0
            * 10,
            2,
        ),

        "sintaxis": round(
            puntos["sintaxis"]
            / 1.0
            * 10,
            2,
        ),
    }

    st.success(
        "✅ Examen corregido y guardado correctamente."
    )

    st.metric(
        "NOTA FINAL",
        f"{nota_final:.2f}/10",
    )

    st.write(
        f"**Nota sin faltas de ortografía:** "
        f"{nota_sin_faltas:.2f}/10"
    )

    st.write(
        f"**Descuento por faltas:** "
        f"-{descuento:.2f}"
    )

    st.write(
        f"**Faltas de ortografía detectadas:** "
        f"{faltas}"
    )

    st.write(
        f"**Faltas de tilde detectadas:** "
        f"{faltas_tildes}"
    )


    # =====================================================
    # RESULTADO POR ÁREAS
    # =====================================================

    st.subheader(
        "Resultado por áreas"
    )

    cols = st.columns(3)

    for i, clave in enumerate(
        [
            "comprension",
            "morfologia",
            "semantica",
            "textos",
            "literatura",
            "sintaxis",
        ]
    ):

        cols[i % 3].metric(
            NOMBRES[clave],
            f"{scores[clave]:.2f}/10",
        )


    # =====================================================
    # PERFIL
    # =====================================================

    st.subheader(
        "🧠 Perfil competencial"
    )

    for item in generar_perfil(
        scores
    ):

        st.write(
            item["texto"]
        )


    # =====================================================
    # RADAR
    # =====================================================

    figura_radar = radar_chart(
        scores,
        "Perfil competencial",
    )

    if figura_radar is not None:

        st.plotly_chart(
            figura_radar,
            use_container_width=True,
        )


    # =====================================================
    # DESCARGA INDIVIDUAL
    # =====================================================

    st.subheader(
        "📥 Descargar resultado"
    )

    st.download_button(
        "⬇️ Descargar mi resultado CSV",

        data=csv_individual(
            fila
        ),

        file_name=(
            "Resultado_2ESO_NEE_"
            + re.sub(
                r"[^A-Za-z0-9_-]+",
                "_",
                nombre_resultado,
            )
            + ".csv"
        ),

        mime="text/csv",

        use_container_width=True,
    )


    # =====================================================
    # ESTADÍSTICAS DEL GRUPO
    # =====================================================

    st.divider()

    with st.expander(
        "📊 Estadísticas del grupo"
    ):

        df = safe_read_results()

        if df.empty:

            st.info(
                "Todavía no hay resultados guardados."
            )

        else:

            st.write(
                f"Resultados guardados: "
                f"**{len(df)}**"
            )

            medias = {}

            for clave in NOMBRES:

                if clave in df.columns:

                    medias[clave] = pd.to_numeric(
                        df[clave],
                        errors="coerce",
                    ).mean()

            if medias:

                st.dataframe(
                    pd.DataFrame(
                        [medias]
                    ).rename(
                        columns=NOMBRES
                    ),
                    use_container_width=True,
                )

            # Solo alumnos del mismo grupo
            if "group" in df.columns:

                df_clase = df[
                    df["group"]
                    == grupo_resultado
                ].copy()

            else:

                df_clase = df.copy()

            if not df_clase.empty:

                # No mostramos nombres
                df_anon = df_clase.copy()

                df_anon["name"] = [
                    f"Alumno {i + 1}"
                    for i in range(
                        len(df_anon)
                    )
                ]

                # El alumno actual es la última fila
                fila_alumno = df_anon.iloc[-1]

                try:

                    figura = comparativa(
                        fila_alumno,
                        df_anon,
                    )

                    if figura is not None:

                        st.plotly_chart(
                            figura,
                            use_container_width=True,
                        )

                except Exception:

                    st.info(
                        "La comparativa no está disponible en este momento."
                    )


    # =====================================================
    # VOLVER AL INICIO
    # =====================================================

    if st.button(
        "🔄 Volver al inicio",
        use_container_width=True,
    ):

        st.session_state.clear()

        st.rerun()

    st.stop()


# =========================================================
# DATOS DEL ALUMNO
# =========================================================

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


# =========================================================
# FORMULARIO
# =========================================================

with st.form(
    "examen_2eso_nee"
):

    respuestas = {}


    # =====================================================
    # 1. COMPRENSIÓN
    # =====================================================

    st.header(
        "1. Comprensión lectora — 2 puntos"
    )

    st.write(
        EXAM["comprension"]["texto"]
    )

    for pregunta in EXAM[
        "comprension"
    ]["preguntas"]:

        pid = pregunta["id"]

        respuestas[pid] = st.text_input(
            pregunta["enunciado"],
            help=(
                "Escribe una respuesta breve."
                if pid != "c4"
                else
                "Escribe tres acciones separadas por comas."
            ),
            key=pid,
        )


    st.divider()


    # =====================================================
    # 2. MORFOLOGÍA
    # =====================================================

    st.header(
        "2. Morfología — 2,5 puntos"
    )

    for palabra in EXAM[
        "morfologia"
    ]:

        st.subheader(
            palabra["palabra"]
        )

        for campo in palabra[
            "campos"
        ]:

            clave_campo = normalizar(
                campo
            ).replace(
                " ",
                "_"
            ).replace(
                "/",
                "_"
            )

            key = (
                f"{palabra['id']}_"
                f"{clave_campo}"
            )

            if campo == "Estructura":

                valor = st.selectbox(
                    f"{palabra['palabra']} → {campo}",

                    [
                        "",
                        "simple",
                        "derivada",
                        "compuesta",
                        "parasintética",
                    ],

                    key=key,
                )

            elif campo == "V/I":

                valor = st.selectbox(
                    f"{palabra['palabra']} → {campo}",

                    [
                        "",
                        "variable",
                        "invariable",
                    ],

                    key=key,
                )

            elif campo == "Categoría gramatical":

                valor = st.text_input(
                    f"{palabra['palabra']} → {campo}",

                    help=(
                        "Indica la categoría "
                        "gramatical y sus rasgos "
                        "principales."
                    ),

                    key=key,
                )

            else:

                valor = st.text_input(
                    f"{palabra['palabra']} → {campo}",
                    key=key,
                )

            respuestas[
                f"{palabra['id']}_{clave_campo}"
            ] = valor


    # =====================================================
    # 2.2 DETERMINANTES Y PRONOMBRES
    # =====================================================

    st.subheader(
        "2.2. Determinantes y pronombres"
    )

    for pregunta in EXAM[
        "determinantes_pronombres"
    ]:

        st.write(
            f"**{pregunta['frase']}**"
        )

        respuestas[
            pregunta["id"]
        ] = st.selectbox(

            pregunta["enunciado"],

            [
                "",
                "determinante",
                "pronombre",
            ],

            key=pregunta["id"],
        )


    st.divider()


    # =====================================================
    # 3. SEMÁNTICA
    # =====================================================

    st.header(
        "3. Semántica — 1 punto"
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

    for pregunta in EXAM[
        "semantica"
    ]:

        st.write(
            f"**{pregunta['elemento']}**"
        )

        respuestas[
            pregunta["id"]
        ] = st.selectbox(

            pregunta["enunciado"],

            opciones_semantica,

            key=pregunta["id"],
        )


    st.divider()


    # =====================================================
    # 4. TIPOS DE TEXTO
    # =====================================================

    st.header(
        "4. Tipos de texto — 1,5 puntos"
    )

    st.write(
        EXAM["textos"]["enunciado"]
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

    for letra, texto in EXAM[
        "textos"
    ]["textos"].items():

        st.markdown(
            f"**Texto {letra}:** {texto}"
        )

    for pregunta in EXAM[
        "textos"
    ]["preguntas"]:

        respuestas[
            pregunta["id"]
        ] = st.selectbox(

            pregunta["enunciado"],

            opciones_texto,

            key=pregunta["id"],
        )


    st.divider()


    # =====================================================
    # 5. LITERATURA
    # =====================================================

    st.header(
        "5. Literatura — 2 puntos"
    )

    st.markdown(
        EXAM["literatura"]["poema"].replace(
            "\n",
            "  \n"
        )
    )

    preguntas_lit = EXAM[
        "literatura"
    ]["preguntas"]


    # L1
    respuestas["l1"] = st.selectbox(
        preguntas_lit[0]["enunciado"],

        [
            "",
            "1",
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


    # L2
    respuestas["l2"] = st.selectbox(
        preguntas_lit[1]["enunciado"],

        [
            "",
            "arte menor",
            "arte mayor",
        ],

        key="l2",
    )


    # L3
    respuestas["l3"] = st.text_input(
        preguntas_lit[2]["enunciado"],

        help=(
            "Puedes escribir, por ejemplo: "
            "10A 11B 11B 10A. "
            "También puedes separar los datos "
            "con comas."
        ),

        key="l3",
    )


    # L4
    respuestas["l4"] = st.selectbox(
        preguntas_lit[3]["enunciado"],

        [
            "",
            "asonante",
            "consonante",
        ],

        key="l4",
    )


    # L5
    respuestas["l5"] = st.text_input(
        preguntas_lit[4]["enunciado"],

        help=(
            "Escribe las dos palabras "
            "que forman la sinalefa."
        ),

        key="l5",
    )


    # L6
    respuestas["l6"] = st.text_input(
        preguntas_lit[5]["enunciado"],

        help=(
            "Escribe las palabras que forman "
            "la personificación."
        ),

        key="l6",
    )


    st.divider()


    # =====================================================
    # 6. SINTAXIS
    # =====================================================

    st.header(
        "6. Sintaxis — 1 punto"
    )

    st.subheader(
        "6.1. Frase u oración"
    )

    for pregunta in EXAM[
        "sintaxis"
    ]:

        pid = pregunta["id"]

        if pid in [
            "x1",
            "x2",
            "x3",
        ]:

            st.write(
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
        "6.2. Modalidad oracional"
    )

    for pregunta in EXAM[
        "sintaxis"
    ]:

        pid = pregunta["id"]

        if pid in [
            "x4",
            "x5",
            "x6",
            "x7",
        ]:

            st.write(
                f"**{pregunta['frase']}**"
            )

            respuestas[pid] = st.selectbox(

                pregunta["enunciado"],

                [
                    "",
                    "enunciativa",
                    "interrogativa",
                    "exclamativa",
                    "desiderativa",
                    "exhortativa",
                    "imperativa",
                ],

                key=pid,
            )


    st.divider()


    # =====================================================
    # 7. DIÁLOGO
    # =====================================================

    st.header(
        "7. Diálogo"
    )

    st.markdown(
        EXAM["dialogo"]["texto"].replace(
            "\n",
            "  \n"
        )
    )

    preguntas_dialogo = EXAM[
        "dialogo"
    ]["preguntas"]


    # D1
    respuestas["d1"] = st.text_input(
        preguntas_dialogo[0]["enunciado"],

        help=(
            "Escribe los dos interlocutores "
            "separados por comas."
        ),

        key="d1",
    )


    # D2
    respuestas["d2"] = st.number_input(
        preguntas_dialogo[1]["enunciado"],

        min_value=0,
        max_value=20,
        value=0,
        step=1,

        key="d2",
    )

    respuestas["d2"] = str(
        int(respuestas["d2"])
    )


    # D3
    respuestas["d3"] = st.text_area(
        preguntas_dialogo[2]["enunciado"],

        help=(
            "Transforma el diálogo a estilo "
            "indirecto manteniendo el sentido."
        ),

        key="d3",
        height=100,
    )


    # =====================================================
    # ENVIAR
    # =====================================================

    enviar = st.form_submit_button(
        "📤 ENVIAR EXAMEN",
        use_container_width=True,
    )


# =========================================================
# CORREGIR Y GUARDAR
# =========================================================

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


    puntos, nota_sin_faltas = corregir(
        respuestas
    )


    todas_respuestas = [
        v
        for v in respuestas.values()
        if isinstance(v, str)
    ]


    faltas, faltas_tildes = detectar_ortografia(
        todas_respuestas
    )


    descuento = round(
        min(
            2.0,
            faltas * 0.20
            + faltas_tildes * 0.10,
        ),
        2,
    )


    nota_final = round(
        max(
            0.0,
            nota_sin_faltas - descuento,
        ),
        2,
    )


    # =====================================================
    # SCORES SOBRE 10
    # =====================================================

    scores = {

        "comprension": round(
            puntos["comprension"]
            / 2.0
            * 10,
            2,
        ),

        "morfologia": round(
            puntos["morfologia"]
            / 2.5
            * 10,
            2,
        ),

        "semantica": round(
            puntos["semantica"]
            / 1.0
            * 10,
            2,
        ),

        "textos": round(
            puntos["textos"]
            / 1.5
            * 10,
            2,
        ),

        "literatura": round(
            puntos["literatura"]
            / 2.0
            * 10,
            2,
        ),

        "sintaxis": round(
            puntos["sintaxis"]
            / 1.0
            * 10,
            2,
        ),
    }


    # =====================================================
    # FILA CSV
    # =====================================================

    fila = {

        "name": nombre.strip(),

        "group": grupo,

        "date": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),

        **scores,

        "nota_sin_faltas":
            nota_sin_faltas,

        "faltas_ortografia":
            faltas,

        "faltas_tildes":
            faltas_tildes,

        "descuento_ortografia":
            descuento,

        "nota_final":
            nota_final,
    }


    try:

        guardar_csv(
            fila
        )

    except Exception as e:

        st.error(
            "No se pudo guardar el resultado."
        )

        st.exception(e)

        st.stop()


    # =====================================================
    # GUARDAR EN SESSION STATE
    # =====================================================

    st.session_state[
        "enviado"
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
        "nota_sin_faltas"
    ] = nota_sin_faltas

    st.session_state[
        "descuento"
    ] = descuento

    st.session_state[
        "nota_final"
    ] = nota_final

    st.session_state[
        "faltas"
    ] = faltas

    st.session_state[
        "faltas_tildes"
    ] = faltas_tildes

    st.session_state[
        "fila"
    ] = fila

    st.rerun()
