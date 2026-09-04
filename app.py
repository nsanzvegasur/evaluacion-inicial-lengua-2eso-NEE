import streamlit as st

# =========================================================
# CONFIGURACIÓN DE LA INTERFAZ ADAPTADA
# =========================================================
# El núcleo del examen se conserva íntegramente en _app_core.py.
# Este archivo añade únicamente la capa visual accesible.

st.set_page_config(
    page_title="Evaluación Inicial Lengua 2.º ESO",
    page_icon="📚",
    layout="centered",
)

# El núcleo ya contiene su propia llamada a set_page_config.
# La anulamos al importarlo para evitar una segunda configuración.
st.set_page_config = lambda *args, **kwargs: None


# ---------------------------------------------------------
# Adaptador de secciones
# ---------------------------------------------------------
# No queremos una raya antes de cada pregunta. El examen se presenta
# por bloques completos: Comprensión, Morfología, Semántica, etc.
# Solo se marca visualmente el comienzo de cada bloque.

_original_header = st.header
_original_divider = st.divider


def _inicio_bloque():
    st.markdown(
        '<div class="bloque" aria-hidden="true"></div>',
        unsafe_allow_html=True,
    )


def _header(*args, **kwargs):
    _inicio_bloque()
    return _original_header(*args, **kwargs)


def _divider(*args, **kwargs):
    # Los separadores internos dejan de generar líneas adicionales.
    # El comienzo de cada bloque ya queda marcado por .bloque.
    return None


st.header = _header
st.divider = _divider


# Ejecutamos el examen original.
import _app_core  # noqa: E402,F401


# ---------------------------------------------------------
# Capa visual: se aplica DESPUÉS del núcleo para que prevalezca.
# ---------------------------------------------------------
st.markdown(
    """
    <style>
    html, body, [class*="css"],
    [data-testid="stAppViewContainer"],
    [data-testid="stAppViewContainer"] * {
        font-family: "Trebuchet MS", Verdana, sans-serif !important;
    }

    [data-testid="stAppViewContainer"] {
        font-size: 20px !important;
    }

    [data-testid="stMainBlockContainer"] {
        max-width: 900px;
        padding-top: 2.2rem;
        padding-bottom: 4rem;
    }

    .titulo-principal {
        font-size: 2.15rem !important;
        line-height: 1.25 !important;
        font-weight: 700 !important;
        margin-bottom: 1rem !important;
    }

    .subtitulo {
        font-size: 1.2rem !important;
        line-height: 1.65 !important;
        margin-bottom: 2rem !important;
    }

    /*
       Un bloque corresponde a una sección completa del examen.
       Hay una sola separación visible entre secciones, no entre preguntas.
    */
    .bloque {
        display: block;
        width: 100%;
        height: 0;
        margin: 3.2rem 0 2rem 0;
        border-top: 3px solid #777;
    }

    h1, h2, h3, h4 {
        font-family: "Trebuchet MS", Verdana, sans-serif !important;
        line-height: 1.35 !important;
        letter-spacing: 0.01em;
    }

    h1 {
        font-size: 2.15rem !important;
        margin-top: 1.2rem !important;
        margin-bottom: 1.5rem !important;
    }

    h2 {
        font-size: 1.75rem !important;
        margin-top: 1.5rem !important;
        margin-bottom: 1.4rem !important;
    }

    h3 {
        font-size: 1.45rem !important;
        margin-top: 1.3rem !important;
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
    </style>
    """,
    unsafe_allow_html=True,
)
