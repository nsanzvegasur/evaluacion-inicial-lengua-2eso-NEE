# Punto de entrada estable de la aplicación NNEE.
# Se ejecuta el núcleo directamente, aplicando únicamente los ajustes
# específicos de presentación de esta versión NNEE.
from pathlib import Path


core = Path(__file__).with_name("_app_core.py")
source = core.read_text(encoding="utf-8")

# Título específico de la adaptación NNEE.
source = source.replace(
    "Evaluación inicial de Lengua — 2.º ESO",
    "Evaluación inicial de Lengua — 2.º ESO · NNEE"
)

# Se elimina el aviso/botón de ayuda general del principio.
source = source.replace(
    "st.markdown('<div class=\"ayuda\"><b>AYUDA DURANTE EL EXAMEN:</b> puedes pulsar el botón de ayuda de cada pregunta para ver cómo debes introducir la respuesta.</div>', unsafe_allow_html=True)\n",
    ""
)

# En semántica se resaltan en rojo las palabras o grupos de palabras,
# no la indicación "relación semántica".
source = source.replace(
    "st.markdown(f\"<span>{q['elemento']}</span> — <span class='rojo'>relación semántica</span>\",unsafe_allow_html=True)",
    "st.markdown(f\"<span class='rojo'>{q['elemento']}</span>\",unsafe_allow_html=True)"
)

# El poema queda centrado y con una separación visual clara antes de la primera pregunta.
source = source.replace(
    "st.markdown(EXAM[\"literatura\"][\"poema\"].replace(\"\\n\",\"<br>\"), unsafe_allow_html=True)",
    "st.markdown('<div style=\"text-align:center; line-height:1.9; margin-bottom:2.5rem;\">' + EXAM[\"literatura\"][\"poema\"].replace(\"\\n\",\"<br>\") + '</div>', unsafe_allow_html=True)"
)

# En diálogo, el primer ejercicio incluye el aviso para separar los interlocutores por comas.
source = source.replace(
    "for q in EXAM[\"dialogo\"][\"preguntas\"]:\n        st.markdown(rojo_marcadores(q[\"enunciado\"]),unsafe_allow_html=True)",
    "for q in EXAM[\"dialogo\"][\"preguntas\"]:\n        st.markdown(rojo_marcadores(q[\"enunciado\"]),unsafe_allow_html=True)\n        if q[\"id\"] == \"d1\":\n            st.markdown('<div class=\"ayuda\"><b>Aviso:</b> separa las respuestas por comas.</div>', unsafe_allow_html=True)"
)

# Adaptación de accesibilidad: letra grande en toda la prueba, incluidos
# enunciados, textos, selectores, campos de respuesta, botones y resultados.
source = source.replace(
    "st.markdown(\"\"\"\n<style>",
    "st.markdown(\"\"\"\n<style>\n/* Letra grande para toda la adaptación NNEE */\nhtml, body, [class*=\"css\"], .stApp { font-size: 1.35rem !important; }\np, li, label, .stMarkdown, .stTextInput, .stSelectbox, .stTextArea, .stNumberInput, .stCaption { font-size: 1.3rem !important; line-height: 1.65 !important; }\nh1 { font-size: 2.7rem !important; line-height: 1.25 !important; }\nh2 { font-size: 2.05rem !important; line-height: 1.3 !important; }\nh3 { font-size: 1.65rem !important; line-height: 1.35 !important; }\ninput, textarea, [data-baseweb=\"select\"], button { font-size: 1.3rem !important; line-height: 1.5 !important; }\n.stButton button, .stFormSubmitButton button { min-height: 3.2rem !important; }\n")
)

exec(compile(source, str(core), "exec"), {"__name__": "__main__", "__file__": str(core)})
