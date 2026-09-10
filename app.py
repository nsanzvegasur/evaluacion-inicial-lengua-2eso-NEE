# Punto de entrada estable de la aplicación NNEE.
# Se ejecuta el núcleo directamente, aplicando únicamente los ajustes
# específicos de presentación de esta versión NNEE.
from pathlib import Path


core = Path(__file__).with_name("_app_core.py")
source = core.read_text(encoding="utf-8")

# El título del núcleo ya incluye NNEE; se mantiene una sola vez.
source = source.replace(
    "Evaluación inicial de Lengua — 2.º ESO · NNEE",
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
    "st.markdown(\"\"\"\n<style>\n/* Letra grande para toda la adaptación NNEE */\nhtml, body, [class*=\"css\"], .stApp { font-size: 1.35rem !important; }\np, li, label, .stMarkdown, .stTextInput, .stSelectbox, .stTextArea, .stNumberInput, .stCaption { font-size: 1.3rem !important; line-height: 1.65 !important; }\nh1 { font-size: 2.7rem !important; line-height: 1.25 !important; }\nh2 { font-size: 2.05rem !important; line-height: 1.3 !important; }\nh3 { font-size: 1.65rem !important; line-height: 1.35 !important; }\ninput, textarea, [data-baseweb=\"select\"], button { font-size: 1.3rem !important; line-height: 1.5 !important; }\n.stButton button, .stFormSubmitButton button { min-height: 3.2rem !important; }\n.descarga-excel { border: 3px solid #777; border-radius: 12px; padding: 1rem 1.1rem; margin: 1rem 0 .7rem; text-align: center; }\n.descarga-titulo { font-size: 1.35rem; font-weight: 700; }\n.descarga-texto { margin-top: .35rem; }\n.classroom-aviso { border: 3px solid #777; border-radius: 12px; padding: 1rem; margin: 1rem 0; text-align: center; font-size: 1.2rem; }\n.classroom-aviso b { font-size: 1.45rem; }\n"
)

# Excel: dos pestañas con la estructura del modelo aportado por la profesora.
# La primera contiene los resultados y la segunda todas las respuestas.
source = source.replace(
    'def excel_bytes(fila):\n    wb=Workbook(); ws=wb.active; ws.title="Resultado"\n    campos=list(fila); ws.append(campos); ws.append([fila[c] for c in campos]); ws.freeze_panes="A2"\n    for col in ws.columns: ws.column_dimensions[col[0].column_letter].width=max(14,min(34,max(len(str(x.value or "")) for x in col)+2))\n    out=io.BytesIO(); wb.save(out); return out.getvalue()',
    '''def excel_bytes(fila):
    wb=Workbook()
    ws=wb.active
    ws.title="Resultado"

    # Primera pestaña: resultados, siguiendo la estructura del Excel modelo.
    ws["A1"]="📚 Evaluación inicial de Lengua — 2.º ESO · NNEE"
    ws["A3"]="Alumno"; ws["B3"]=fila.get("name","")
    ws["A4"]="Grupo"; ws["B4"]=fila.get("group","")
    ws["A5"]="Fecha y hora"; ws["B5"]=fila.get("date","")
    ws["A7"]="NOTA DE ESTA PARTE (SOBRE 9)"; ws["B7"]=fila.get("nota_final_sobre_9",0)
    ws["A8"]="Nota antes del descuento por ortografía (sobre 9)"; ws["B8"]=fila.get("nota_final_sobre_9",0)
    ws["A9"]="Descuento por ortografía"; ws["B9"]=0
    ws["A10"]="Producción escrita"
    ws["A11"]="Nota producción escrita (hasta 1 punto)"
    ws["A12"]="NOTA FINAL (SOBRE 10)"
    ws["A14"]="RESULTADOS POR ÁREAS"
    maximos={"comprension":2,"morfologia":2.5,"semantica":1,"textos":1.5,"literatura":2,"sintaxis":1}
    nombres={"comprension":"Comprensión","morfologia":"Morfología","semantica":"Semántica","textos":"Textos","literatura":"Literatura","sintaxis":"Sintaxis"}
    for i,(clave,mx) in enumerate(maximos.items(),start=15):
        ws.cell(i,1,nombres[clave])
        ws.cell(i,2,round((fila.get(clave,0)/mx)*10,2) if mx else 0)
    ws["A22"]="PERFIL COMPETENCIAL"
    for i,(clave,mx) in enumerate(maximos.items(),start=23):
        porcentaje=(fila.get(clave,0)/mx) if mx else 0
        estado="consolidado" if porcentaje>=0.7 else "en proceso" if porcentaje>=0.5 else "necesita refuerzo"
        ws.cell(i,1,f"{nombres[clave]}: {estado}.")

    # Segunda pestaña: respuestas en el mismo formato del modelo.
    wr=wb.create_sheet("Respuestas")
    wr["A1"]="Pregunta"; wr["B1"]="Respuesta"
    respuestas=st.session_state.get("respuestas",{})
    for i,(pregunta,respuesta) in enumerate(respuestas.items(),start=2):
        wr.cell(i,1,pregunta)
        wr.cell(i,2,respuesta if respuesta is not None else "")
    wr.freeze_panes="A2"

    # Formato visual sencillo y legible, manteniendo la estructura del modelo.
    from openpyxl.styles import Font, Alignment, Border, Side
    borde=Side(style="thin", color="B7B7B7")
    for hoja in (ws,wr):
        for row in hoja.iter_rows():
            for cell in row:
                cell.alignment=Alignment(vertical="top", wrap_text=True)
                cell.border=Border(bottom=borde)
    ws["A1"].font=Font(bold=True,size=16)
    for r in (7,14,22): ws.cell(r,1).font=Font(bold=True)
    for c in range(1,3): wr.cell(1,c).font=Font(bold=True)
    ws.column_dimensions["A"].width=48
    ws.column_dimensions["B"].width=30
    wr.column_dimensions["A"].width=25
    wr.column_dimensions["B"].width=80

    out=io.BytesIO(); wb.save(out); return out.getvalue()'''
)

# Guardar las respuestas para poder incluirlas en la segunda pestaña del Excel.
source = source.replace(
    'st.session_state.update(enviado=True,fila=fila,puntos=puntos,nota9=nota9,faltas=faltas,tildes=tildes)',
    'st.session_state.update(enviado=True,fila=fila,puntos=puntos,nota9=nota9,faltas=faltas,tildes=tildes,respuestas=respuestas)'
)

# En resultados solo se ofrece Excel, con nombre de archivo basado en el alumno.
source = source.replace(
    'st.markdown("### Descargar resultados")\n    st.download_button("Descargar resultado CSV",csv_bytes(fila),file_name="Resultado_2ESO_NEE.csv",mime="text/csv",use_container_width=True)\n    st.download_button("Descargar resultado Excel",excel_bytes(fila),file_name="Resultado_2ESO_NEE.xlsx",mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",use_container_width=True)\n    st.markdown("Esta evaluación está lista para descargar y entregar en Classroom.")',
    'st.markdown("### Descargar resultados")\n    st.markdown(\'<div class="descarga-excel"><div class="descarga-titulo">Resultado preparado para guardar</div><div class="descarga-texto">Descarga el archivo Excel para conservar los resultados de esta evaluación.</div></div>\', unsafe_allow_html=True)\n    nombre_archivo=re.sub(r"[^A-Za-z0-9ÁÉÍÓÚáéíóúÑñÜüÇç _-]", "", fila.get("name", "alumno")).strip() or "alumno"\n    nombre_archivo=re.sub(r"\s+", "_", nombre_archivo)\n    st.download_button("DESCARGAR RESULTADO EN EXCEL",excel_bytes(fila),file_name=f"{nombre_archivo}_NNEE_2ESO.xlsx",mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",use_container_width=True)\n    st.markdown(\'<div class="classroom-aviso"><b>CLASSROOM</b><br>Cuando hayas descargado el Excel, puedes entregarlo en Classroom.</div>\', unsafe_allow_html=True)'
)

exec(compile(source, str(core), "exec"), {"__name__": "__main__", "__file__": str(core)})
