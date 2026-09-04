from pathlib import Path
import io
import re
import streamlit as st

st.set_page_config(page_title="Evaluación Inicial Lengua 2.º ESO — NNEE", page_icon="📚", layout="centered")

st.markdown("""
<style>
html,body,[class*="css"],[data-testid="stAppViewContainer"],[data-testid="stAppViewContainer"] *{font-family:"Trebuchet MS",Verdana,sans-serif!important}
[data-testid="stMainBlockContainer"]{max-width:900px;padding-top:2.2rem;padding-bottom:4rem}
h1{font-size:2.15rem!important;line-height:1.25!important} h1::after{content:"  ·  NNEE";font-size:.72em;font-weight:700}
h2{font-size:1.75rem!important;line-height:1.35!important;margin-top:3.4rem!important;padding-top:1.5rem!important;border-top:3px solid #777!important}
h3{font-size:1.45rem!important} p,li,label,[data-testid="stMarkdownContainer"]{font-size:1.12rem!important;line-height:1.75!important}
strong,b{color:inherit!important;font-weight:700!important}
.rojo{color:#b00020!important;font-weight:700!important;font-size:1.12rem!important;line-height:1.7!important}
.nota-9{text-align:center;margin:2.5rem 0 2rem}.nota-9 .titulo{font-size:1.65rem;font-weight:700;color:#444}.nota-9 .valor{font-size:4.2rem;font-weight:700;color:#b00020;line-height:1.05;margin-top:.4rem}
textarea,input,[data-baseweb="select"]{font-family:"Trebuchet MS",Verdana,sans-serif!important;font-size:1.12rem!important}input,textarea{min-height:3.1rem!important;padding:.8rem .9rem!important}textarea{min-height:8rem!important}
input:focus,textarea:focus,div[data-baseweb="select"]:focus-within{outline:3px solid #555!important;outline-offset:2px!important}
</style>
""", unsafe_allow_html=True)

core_path = Path(__file__).with_name("_app_core.py")
core_source = core_path.read_text(encoding="utf-8")

# Configuración y puntuación NNEE
core_source = core_source.replace('page_title="Evaluación Inicial Lengua 2.º ESO*",','page_title="Evaluación Inicial Lengua 2.º ESO — NNEE",')
core_source = core_source.replace('total = round(\n        sum(p.values()),\n        2\n    )','total = round(\n        sum(p.values()) * 0.9,\n        2\n    )')

# Ortografía: recuento separado de faltas y tildes; nunca resta puntos.
ini = core_source.index('def detectar_ortografia(respuestas):')
fin = core_source.index('# =========================================================\n# GUARDAR CSV', ini)
core_source = core_source[:ini] + '''def detectar_ortografia(respuestas):
    errores_ortografia = {"sustantibo","haver","hechar","aver","aora","havia","hamos","bamos","llendo","dijistes","hicistes","estava","tubieron","tubo"}
    errores_tilde = {"tambien":"también","ademas":"además","despues":"después","cuando":"cuándo","como":"cómo","quien":"quién","quienes":"quiénes","donde":"dónde","adonde":"adónde","que":"qué","dia":"día","dias":"días","esta":"está","estas":"estás","mas":"más","aun":"aún"}
    ortografia = set(); tildes = set()
    for respuesta in respuestas:
        if not respuesta: continue
        texto = str(respuesta).lower()
        for palabra in re.findall(r"\\b[\\wáéíóúüñ]+\\b", texto, flags=re.UNICODE):
            if palabra in errores_ortografia: ortografia.add(palabra)
            if palabra in errores_tilde and errores_tilde[palabra] not in texto: tildes.add(palabra)
    return len(ortografia), len(tildes)

''' + core_source[fin:]

# Las faltas se contabilizan pero no descuentan.
old = '''    descuento = round(\n        min(\n            2.0,\n            faltas * 0.20\n            + faltas_tildes * 0.10,\n        ),\n        2,\n    )\n\n\n    nota_final = round(\n        max(\n            0.0,\n            nota_sin_faltas - descuento,\n        ),\n        2,\n    )'''
new = '''    descuento = 0.0\n\n    nota_final = round(nota_sin_faltas, 2)'''
if old not in core_source: raise RuntimeError("No se encontró el cálculo de descuento")
core_source = core_source.replace(old,new,1)

# Comprensión: solo Dónde, Quiénes, Cuándo y tres acciones en rojo.
old = '''        respuestas[pid] = st.text_input(\n            pregunta["enunciado"],\n            help=(\n                "Escribe una respuesta breve."\n                if pid != "c4"\n                else\n                "Escribe tres acciones separadas por comas."\n            ),\n            key=pid,\n        )'''
new = '''        if pid in ["c1", "c2", "c3"]:\n            palabra = {"c1":"Dónde", "c2":"Quiénes", "c3":"Cuándo"}[pid]\n            enunciado = pregunta["enunciado"].replace(palabra, f'<span class="rojo">{palabra}</span>')\n            st.markdown(enunciado, unsafe_allow_html=True)\n            respuestas[pid] = st.text_input("", help="Escribe una respuesta breve.", key=pid, label_visibility="collapsed")\n        else:\n            enunciado = pregunta["enunciado"].replace("**tres acciones**", '<span class="rojo">tres acciones</span>')\n            st.markdown(enunciado, unsafe_allow_html=True)\n            respuestas[pid] = st.text_input("", help="Escribe tres acciones separadas por comas.", key=pid, label_visibility="collapsed")'''
if old not in core_source: raise RuntimeError("No se encontró comprensión")
core_source=core_source.replace(old,new,1)

# Morfología: todos los rótulos solicitados en rojo y ayuda de morfemas.
old='''            if campo == "Estructura":\n\n                valor = st.selectbox(\n                    f"{palabra['palabra']} → {campo}",'''
new='''            if campo == "Estructura":\n                st.markdown(f'<div class="rojo">Escribe la estructura de {palabra["palabra"]}</div>', unsafe_allow_html=True)\n                valor = st.selectbox(\n                    "",'''
if old not in core_source: raise RuntimeError("No se encontró Estructura")
core_source=core_source.replace(old,new,1)
old='''            elif campo == "V/I":\n\n                valor = st.selectbox(\n                    f"{palabra['palabra']} → {campo}",'''
new='''            elif campo == "V/I":\n                st.markdown(f'<div class="rojo">Escribe si {palabra["palabra"]} es variable o invariable</div>', unsafe_allow_html=True)\n                valor = st.selectbox(\n                    "",'''
if old not in core_source: raise RuntimeError("No se encontró V/I")
core_source=core_source.replace(old,new,1)
old='''            elif campo == "Categoría gramatical":\n\n                valor = st.text_input(\n                    f"{palabra['palabra']} → {campo}",'''
new='''            elif campo == "Categoría gramatical":\n                st.markdown(f'<div class="rojo">Escribe la categoría gramatical de {palabra["palabra"]}</div>', unsafe_allow_html=True)\n                valor = st.text_input(\n                    "",'''
if old not in core_source: raise RuntimeError("No se encontró categoría")
core_source=core_source.replace(old,new,1)
old='''            else:\n\n                valor = st.text_input(\n                    f"{palabra['palabra']} → {campo}",\n                    key=key,\n                )'''
new='''            else:\n                if campo == "Lexema":\n                    etiqueta = f"Escribe el lexema de {palabra['palabra']}"; ayuda = None\n                elif campo == "Morfemas":\n                    etiqueta = f"Escribe los morfemas de {palabra['palabra']}"; ayuda = "Separa los distintos morfemas con comas y sin guion. Ejemplo: in, s"\n                else:\n                    etiqueta = f"{campo} de {palabra['palabra']}"; ayuda = None\n                st.markdown(f'<div class="rojo">{etiqueta}</div>', unsafe_allow_html=True)\n                valor = st.text_input("", help=ayuda, key=key, label_visibility="collapsed")'''
if old not in core_source: raise RuntimeError("No se encontró campos de morfología")
core_source=core_source.replace(old,new,1)

# 2.2: solo Aquellos y Nadie en rojo; el resto de la frase queda normal.
old='''        st.write(\n            f"**{pregunta['frase']}**"\n        )\n\n        respuestas[\n            pregunta["id"]\n        ] = st.selectbox(\n\n            pregunta["enunciado"],'''
new='''        palabra_roja = "Aquellos" if pregunta["id"] == "dp1" else "Nadie"\n        frase = pregunta["frase"].replace(palabra_roja, f'<span class="rojo">{palabra_roja}</span>')\n        st.markdown(frase, unsafe_allow_html=True)\n        enunciado = pregunta["enunciado"].replace(f"**{palabra_roja}**", f'<span class="rojo">{palabra_roja}</span>')\n        st.markdown(enunciado, unsafe_allow_html=True)\n        respuestas[pregunta["id"]] = st.selectbox(\n            "",'''
if old not in core_source: raise RuntimeError("No se encontró 2.2")
core_source=core_source.replace(old,new,1)

# Semántica: cada ejemplo una sola vez; relación semántica en rojo.
old='''        st.write(\n            f"**{pregunta['elemento']}**"\n        )\n\n        respuestas[\n            pregunta["id"]\n        ] = st.selectbox(\n\n            pregunta["enunciado"],'''
new='''        if pregunta["id"] in ["s1", "s2"]:\n            texto_sem = f'<span class="rojo">{pregunta["elemento"]}</span> → ¿qué <span class="rojo">relación semántica</span> tienen?'\n        else:\n            texto_sem = '<span class="rojo">Hoja</span> (árbol / papel) → ¿qué fenómeno semántico aparece?'\n        st.markdown(texto_sem, unsafe_allow_html=True)\n        respuestas[pregunta["id"]] = st.selectbox(\n            "",'''
if old not in core_source: raise RuntimeError("No se encontró semántica")
core_source=core_source.replace(old,new,1)

# Tipos de texto: cada pregunta justo debajo de su texto, con tipo de texto en rojo.
old='''    for letra, texto in EXAM[\n        "textos"\n    ]["textos"].items():\n\n        st.markdown(\n            f"**Texto {letra}:** {texto}"\n        )\n\n    for pregunta in EXAM[\n        "textos"\n    ]["preguntas"]:\n\n        respuestas[\n            pregunta["id"]\n        ] = st.selectbox(\n\n            pregunta["enunciado"],'''
new='''    textos = EXAM["textos"]["textos"]\n    preguntas_textos = EXAM["textos"]["preguntas"]\n    for indice, (letra, texto) in enumerate(textos.items()):\n        st.markdown(f"**Texto {letra}:** {texto}")\n        if indice < len(preguntas_textos):\n            pregunta = preguntas_textos[indice]\n            enunciado = pregunta["enunciado"].replace("**tipo de texto**", '<span class="rojo">tipo de texto</span>')\n            st.markdown(enunciado, unsafe_allow_html=True)\n            respuestas[pregunta["id"]] = st.selectbox("", opciones_texto, key=pregunta["id"])'''
if old not in core_source: raise RuntimeError("No se encontró textos")
core_source=core_source.replace(old,new,1)

# Literatura: exactamente las palabras que ya estaban en negrita pasan a rojo.
for i,palabra in enumerate(["versos","arte mayor o menor","esquema métrico","rima","sinalefa","personificación"]):
    core_source=core_source.replace(f'preguntas_lit[{i}]["enunciado"]', f'preguntas_lit[{i}]["enunciado"].replace("**{palabra}**", \'<span class="rojo">{palabra}</span>\')')

# Sintaxis: las frases que estaban en negrita pasan a rojo, sin colorear el resto.
core_source=core_source.replace('''            st.write(\n                f"**{pregunta['frase']}**"\n            )''','''            st.markdown(f'<span class="rojo">{pregunta["frase"]}</span>', unsafe_allow_html=True)''')

# Diálogo: las líneas que estaban en negrita pasan a rojo.
old='''    st.markdown(\n        EXAM["dialogo"]["texto"].replace(\n            "\\n",\n            "  \\n"\n        )\n    )'''
new='''    for linea in EXAM["dialogo"]["texto"].splitlines():\n        st.markdown(f'<span class="rojo">{linea}</span>', unsafe_allow_html=True)'''
core_source=core_source.replace(old,new,1)

# Instrucción inicial sobre la ayuda.
marker='''    st.header(\n        "1. Comprensión lectora — 2 puntos"\n    )'''
core_source=core_source.replace(marker,'''    st.info("Durante el examen tienes disponible el botón de ayuda en las preguntas que lo necesitan. Puedes mantenerlo pulsado para consultar cómo introducir la respuesta.")\n\n    st.header(\n        "1. Comprensión lectora — 2 puntos"\n    )''',1)

# Exportación Excel con la misma estructura de resultado del examen ordinario.
excel_fn='''\n\ndef excel_individual(fila, respuestas, perfil):\n    from openpyxl import Workbook\n    from openpyxl.styles import Font, Alignment\n    wb = Workbook()\n    ws = wb.active; ws.title = "Resultado"\n    ws["A1"] = "📚 Evaluación inicial de Lengua — 2.º ESO"; ws["A1"].font = Font(bold=True,size=16)\n    ws["A3"] = "Alumno"; ws["B3"] = fila["name"]\n    ws["A4"] = "Grupo"; ws["B4"] = fila["group"]\n    ws["A5"] = "Fecha y hora"; ws["B5"] = fila["date"]\n    ws["A7"] = "NOTA DE ESTA PARTE · SOBRE 9"; ws["B7"] = fila["nota_examen_9"]\n    ws["A8"] = "Nota antes del descuento por ortografía (sobre 9)"; ws["B8"] = fila["nota_sin_faltas"]\n    ws["A9"] = "Faltas de ortografía"; ws["B9"] = fila["faltas_ortografia"]\n    ws["A10"] = "Faltas de tildes"; ws["B10"] = fila["faltas_tildes"]\n    ws["A11"] = "Descuento por faltas"; ws["B11"] = "0 — las faltas se contabilizan, pero no restan"\n    ws["A12"] = "Producción escrita"; ws["B12"] = "PENDIENTE — debe realizarse a mano (hasta 1 punto adicional)"\n    ws["A13"] = "Nota producción escrita (hasta 1 punto)"; ws["B13"] = fila["nota_produccion_escrita"]\n    ws["A14"] = "NOTA FINAL (SOBRE 10)"; ws["B14"] = fila["nota_final_10"]\n    ws["A16"] = "RESULTADOS POR ÁREAS"; ws["A16"].font = Font(bold=True)\n    r=17\n    for clave,nombre_area in NOMBRES.items(): ws.cell(r,1).value=nombre_area; ws.cell(r,2).value=fila[clave]; r+=1\n    ws[f"A{r+1}"]="PERFIL COMPETENCIAL"; ws[f"A{r+1}"].font=Font(bold=True)\n    r+=2\n    for item in perfil: ws.cell(r,1).value=item["texto"]; ws.cell(r,1).alignment=Alignment(wrap_text=True,vertical="top"); r+=1\n    ws.column_dimensions["A"].width=55; ws.column_dimensions["B"].width=35\n    ws2=wb.create_sheet("Respuestas"); ws2["A1"]="Pregunta"; ws2["B1"]="Respuesta"\n    for c in (ws2["A1"],ws2["B1"]): c.font=Font(bold=True)\n    for r,(pregunta,respuesta) in enumerate(respuestas.items(),2): ws2.cell(r,1).value=pregunta; ws2.cell(r,2).value=str(respuesta); ws2.cell(r,2).alignment=Alignment(wrap_text=True,vertical="top")\n    ws2.column_dimensions["A"].width=25; ws2.column_dimensions["B"].width=80\n    salida=io.BytesIO(); wb.save(salida); salida.seek(0); return salida.getvalue()\n'''
core_source=core_source.replace('\n\ndef safe_read_results():',excel_fn+'\n\ndef safe_read_results():',1)

# CSV: misma información explícita sobre 9 y producción escrita.
old='''        "descuento_ortografia",\n        "nota_final",\n    ]'''
new='''        "descuento_ortografia",\n        "nota_examen_9",\n        "produccion_escrita",\n        "nota_produccion_escrita",\n        "nota_final_10",\n        "nota_final",\n    ]'''
if old not in core_source: raise RuntimeError("No se encontró cabecera CSV")
core_source=core_source.replace(old,new,1)
old='''        "descuento_ortografia":\n            descuento,\n\n        "nota_final":\n            nota_final,\n    }'''
new='''        "descuento_ortografia": descuento,\n        "nota_examen_9": nota_final,\n        "produccion_escrita": "PENDIENTE — debe realizarse a mano (hasta 1 punto adicional)",\n        "nota_produccion_escrita": "",\n        "nota_final_10": "",\n        "nota_final": nota_final,\n    }'''
if old not in core_source: raise RuntimeError("No se encontró fila CSV")
core_source=core_source.replace(old,new,1)

# Resultado: nota grande centrada y texto explícito.
old='''    st.metric(\n        "NOTA FINAL",\n        f"{nota_final:.2f}/10",\n    )'''
new='''    st.markdown(f'<div class="nota-9"><div class="titulo">NOTA DE ESTA PARTE · SOBRE 9</div><div class="valor">{nota_final:.2f} / 9</div></div>', unsafe_allow_html=True)'''
if old not in core_source: raise RuntimeError("No se encontró métrica final")
core_source=core_source.replace(old,new,1)
old='''    st.write(\n        f"**Nota sin faltas de ortografía:** "\n        f"{nota_sin_faltas:.2f}/10"\n    )\n\n    st.write(\n        f"**Descuento por faltas:** "\n        f"-{descuento:.2f}"\n    )'''
new='''    st.write(f"**Nota de la prueba automática (sobre 9):** {nota_sin_faltas:.2f}/9")\n    st.write(f"**Faltas de ortografía detectadas:** {faltas}")\n    st.write(f"**Faltas de tilde detectadas:** {faltas_tildes}")\n    st.write("**Las faltas se contabilizan, pero no restan puntos en esta adaptación NNEE.**")\n    st.info("**Producción escrita pendiente:** esta parte todavía debe realizarse a mano y se corregirá aparte. Puede aportar **hasta 1 punto adicional** para completar la nota sobre 10.")'''
if old not in core_source: raise RuntimeError("No se encontró texto de resultados")
core_source=core_source.replace(old,new,1)

# Guardar respuestas y ofrecer Excel junto al CSV.
core_source=core_source.replace('''    st.session_state[\n        "fila"\n    ] = fila\n\n    st.rerun()''','''    st.session_state["fila"] = fila\n    st.session_state["respuestas"] = respuestas\n\n    st.rerun()''',1)
marker='''        use_container_width=True,\n    )\n\n\n    # =====================================================\n    # ESTADÍSTICAS DEL GRUPO'''
replacement='''        use_container_width=True,\n    )\n\n    st.download_button(\n        "📊 Descargar Excel",\n        data=excel_individual(fila, st.session_state.get("respuestas", {}), generar_perfil(scores)),\n        file_name="Resultado_2ESO_NEE_" + re.sub(r"[^A-Za-z0-9_-]+", "_", nombre_resultado) + ".xlsx",\n        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",\n        use_container_width=True,\n    )\n\n\n    # =====================================================\n    # ESTADÍSTICAS DEL GRUPO'''
if marker not in core_source: raise RuntimeError("No se encontró zona de descargas")
core_source=core_source.replace(marker,replacement,1)

exec(compile(core_source, str(core_path), "exec"), {"__name__":"_app_core","__file__":str(core_path)})
