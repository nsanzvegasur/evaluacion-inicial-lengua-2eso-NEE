import streamlit as st

# =========================================================
# CONFIGURACIÓN DE LA INTERFAZ ADAPTADA
# =========================================================
# El núcleo del examen se conserva íntegramente en _app_core.py.
# Este archivo añade únicamente la capa visual accesible.

st.set_page_config(
    page_title="Evaluación Inicial Lengua 2.º ESO * ",
    page_icon="📚",
    layout="centered",
)

# El núcleo ya contiene su propia llamada a set_page_config.
# La anulamos al importarlo para evitar una segunda configuración.
st.set_page_config = lambda *args, **kwargs: None


# ---------------------------------------------------------
# Capa visual: tipografía local y lectura fácil
# ---------------------------------------------------------
# No depende de Google Fonts ni de ninguna fuente externa.
# Trebuchet MS suele estar disponible en Windows y tiene formas
# de letras diferenciadas y una apariencia más humanista que Arial.
# Se deja Verdana como respaldo local.

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
       .bloque es el espacio visual que separa cada pregunta.
       Se inserta antes de cada campo de respuesta mediante el
       pequeño adaptador de abajo. La línea superior ayuda a que
       cada ejercicio se perciba como una unidad independiente.
    */
    .bloque {
        display: block;
        width: 100%;
        min-height: 28px;
        margin: 2rem 0 1.4rem 0;
        border-top: 2px solid #b8b8b8;
    }

    /* Separadores de sección del examen */
    [data-testid="stMarkdownContainer"] hr,
    [data-testid="stDivider"] {
        border: 0 !important;
        border-top: 3px solid #777 !important;
        margin: 3rem 0 !important;
        opacity: 1 !important;
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

    /* Texto de los enunciados y fragmentos del examen */
    [data-testid="stMarkdownContainer"] {
        font-size: 1.12rem !important;
        line-height: 1.8 !important;
    }

    /* Campos de respuesta grandes y cómodos para escribir */
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

    /* Más espacio alrededor de cada widget de respuesta */
    [data-testid="stTextInput"],
    [data-testid="stTextArea"],
    [data-testid="stSelectbox"],
    [data-testid="stNumberInput"] {
        margin-bottom: 1.1rem !important;
    }

    /* Botón final claramente identificable */
    button[kind="primary"] {
        font-size: 1.15rem !important;
        min-height: 3.6rem !important;
        margin-top: 2rem !important;
    }

    /* El foco del teclado queda muy visible */
    input:focus, textarea:focus,
    div[data-baseweb="select"]:focus-within {
        outline: 3px solid #555 !important;
        outline-offset: 2px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# Adaptadores de los campos de respuesta
# ---------------------------------------------------------
# Antes de cada respuesta insertamos .bloque. Así no hay que tocar
# la lógica de corrección ni las claves de las respuestas del examen.

_original_text_input = st.text_input
_original_text_area = st.text_area
_original_selectbox = st.selectbox
_original_number_input = st.number_input
_original_divider = st.divider


def _bloque():
    st.markdown(
        '<div class="bloque" aria-hidden="true"></div>',
        unsafe_allow_html=True,
    )


def _text_input(*args, **kwargs):
    _bloque()
    return _original_text_input(*args, **kwargs)


def _text_area(*args, **kwargs):
    _bloque()
    return _original_text_area(*args, **kwargs)


def _selectbox(*args, **kwargs):
    _bloque()
    return _original_selectbox(*args, **kwargs)


def _number_input(*args, **kwargs):
    _bloque()
    return _original_number_input(*args, **kwargs)


def _divider(*args, **kwargs):
    # Conservamos st.divider(), pero hacemos que el separador sea
    # mucho más visible en la versión adaptada.
    return _original_divider(*args, **kwargs)


st.text_input = _text_input
st.text_area = _text_area
st.selectbox = _selectbox
st.number_input = _number_input
st.divider = _divider


# Ejecutamos el examen original sin modificar su corrección.
import _app_core  # noqa: E402,F401
