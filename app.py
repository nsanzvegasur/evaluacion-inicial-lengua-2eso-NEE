import streamlit as st

# La configuración de Streamlit la realiza el núcleo original.
# Evitamos una segunda llamada a set_page_config para que la app arranque
# de forma estable en Streamlit Cloud.
import _app_core  # noqa: E402,F401

# =========================================================
# CAPA VISUAL NNEE
# =========================================================
# Se aplica después del núcleo para no tocar la lógica de corrección.
# Los separadores internos se ocultan y cada h2 (sección principal)
# marca el comienzo de un bloque completo.

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
    </style>
    """,
    unsafe_allow_html=True,
)
