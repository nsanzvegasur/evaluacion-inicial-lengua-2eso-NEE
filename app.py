from pathlib import Path

import streamlit as st

# =========================================================
# CONFIGURACIÓN Y CAPA VISUAL NNEE
# =========================================================
# La configuración se hace aquí antes de ejecutar el núcleo.
# Así podemos mantener el núcleo de corrección intacto y aplicar
# la presentación accesible de forma estable.

st.set_page_config(
    page_title="Evaluación Inicial Lengua 2.º ESO — NNEE",
    page_icon="📚",
    layout="centered",
)

st.markdown(
    """
    <style>
    html, body, [class*="css"],
    [data-testid="stAppViewContainer"],
    [data-testid="stAppViewContainer"] * {
        font-family: "Trebuchet MS", Verdana, sans-serif !important;
    }

    [data-testid="stMainBlockContainer"] {
        max-width: 900px;
        padding-top: 2.2rem;
        padding-bottom: 4rem;
    }

    /* Título claramente diferenciado como versión NNEE */
    h1 {
        font-size: 2.15rem !important;
        line-height: 1.25 !important;
        margin-bottom: 1rem !important;
    }

    h1::after {
        content: "  ·  NNEE";
        font-size: 0.72em;
        font-weight: 700;
    }

    h2 {
        font-size: 1.75rem !important;
        line-height: 1.35 !important;
        letter-spacing: 0.01em;
        margin-top: 3.4rem !important;
        margin-bottom: 1.4rem !important;
        padding-top: 1.5rem !important;
        border-top: 3px solid #777 !important;
    }

    h3 {
        font-size: 1.45rem !important;
        line-height: 1.4 !important;
        margin-top: 1.4rem !important;
        margin-bottom: 1.2rem !important;
    }

    p, li, label {
        font-size: 1.12rem !important;
        line-height: 1.75 !important;
        letter-spacing: 0.01em;
    }

    [data-testid="stMarkdownContainer"] {
        font-size: 1.12rem !important;
        line-height: 1.8 !important;
    }

    /* Lo importante se identifica por color, no solo por negrita */
    strong, b {
        color: #b00020 !important;
        font-weight: 700 !important;
    }

    textarea, input,
    [data-baseweb="select"] {
        font-family: "Trebuchet MS", Verdana, sans-serif !important;
        font-size: 1.12rem !important;
        line-height: 1.6 !important;
    }

    input, textarea {
        min-height: 3.1rem !important;
        padding: 0.8rem 0.9rem !important;
    }

    textarea {
        min-height: 8rem !important;
    }

    [data-testid="stTextInput"],
    [data-testid="stTextArea"],
    [data-testid="stSelectbox"],
    [data-testid="stNumberInput"] {
        margin-bottom: 1.1rem !important;
    }

    button[kind="primary"] {
        font-size: 1.15rem !important;
        min-height: 3.6rem !important;
        margin-top: 2rem !important;
    }

    input:focus, textarea:focus,
    div[data-baseweb="select"]:focus-within {
        outline: 3px solid #555 !important;
        outline-offset: 2px !important;
    }

    /* No queremos una raya entre cada pregunta */
    hr {
        display: none !important;
    }

    /* Al imprimir: cada bloque principal comienza en una página nueva.
       En pantalla no cambia la navegación ni añade complejidad al formulario. */
    @media print {
        h2 {
            break-before: page;
            page-break-before: always;
        }

        h2:first-of-type {
            break-before: auto;
            page-break-before: auto;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# EJECUCIÓN DEL NÚCLEO ORIGINAL CON DOS AJUSTES DE EXAMEN
# =========================================================
# 1) El bloque de modalidad tiene ahora 3 preguntas (x4-x6).
# 2) Al quedar 6 preguntas de sintaxis, cada una vale 1/6 del punto.
# 3) La opción "exhortativa" se elimina del selector: se mantiene
#    únicamente "imperativa" como modalidad para ese tipo de oración.
#
# El núcleo sigue siendo el original; solo se neutralizan aquí las partes
# que dependen del número de preguntas y de las opciones mostradas.

core_path = Path(__file__).with_name("_app_core.py")
core_source = core_path.read_text(encoding="utf-8")

core_source = core_source.replace(
    '''st.set_page_config(\n    page_title="Evaluación Inicial Lengua 2.º ESO*",\n    page_icon="📚",\n    layout="centered",\n)\n''',
    "",
)

core_source = core_source.replace(
    "1.0 / 7",
    "1.0 / 6",
)

core_source = core_source.replace(
    '                    "exhortativa",\n',
    "",
)

core_namespace = {
    "__name__": "_app_core",
    "__file__": str(core_path),
}

exec(
    compile(core_source, str(core_path), "exec"),
    core_namespace,
)
