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

exec(compile(source, str(core), "exec"), {"__name__": "__main__", "__file__": str(core)})
