import csv
import io
import os
import re
import unicodedata
from datetime import datetime

import pandas as pd
import streamlit as st
from openpyxl import Workbook

from examen2ESO_NEE import EXAMEN

st.set_page_config(page_title="Evaluación inicial Lengua 2.º ESO NNEE", page_icon="📚", layout="centered")
CSV_FILE = "results.csv"
EXAM = EXAMEN["2ESO_NEE"]

st.markdown("""
<style>
html, body, [class*="css"], .stApp, input, textarea, button, select, div[data-baseweb="select"] {
    font-family: "Trebuchet MS", Verdana, sans-serif !important;
}
.stApp { font-size: 1.12rem; }
h1 { font-size: 2.25rem !important; }
h2 { font-size: 1.75rem !important; }
h3 { font-size: 1.4rem !important; }
.titulo { font-size: 2.45rem; font-weight: 700; line-height: 1.2; margin: .2rem 0 .4rem; }
.subtitulo { font-size: 1.2rem; margin-bottom: 1rem; }
.bloque { border: 2px solid #777; border-radius: 10px; padding: 1rem 1.1rem; margin: 1rem 0; }
.separador { border-top: 3px solid #777; margin: 1.3rem 0; }
.rojo { color: #c00000; font-weight: 700; }
.ayuda { border-left: 5px solid #777; padding: .75rem 1rem; margin: .8rem 0 1.2rem; font-size: 1.05rem; }
.nota9 { text-align:center; font-size: 2.5rem; font-weight: 800; margin: 1rem 0; }
.aviso { border: 2px solid #777; border-radius: 10px; padding: 1rem; font-size: 1.12rem; }
.poema-titulo { text-align: center; color: #c00000; font-weight: 700; font-size: 1.35rem; margin: .5rem 0 1rem; }
textarea, input { font-size: 1.08rem !important; }
</style>
""", unsafe_allow_html=True)

def normalizar(v):
    if v is None: return ""
    s = str(v).strip().lower()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s).strip()

def lista(v):
    return [normalizar(x) for x in re.split(r"[,;\n]+", str(v or "")) if normalizar(x)]

def exacta(v, *ops):
    n = normalizar(v)
    return bool(n) and any(n == normalizar(x) for x in ops)

def contiene(v, *ops):
    n = normalizar(v)
    return bool(n) and any(normalizar(x) in n for x in ops)

def rojo_marcadores(texto):
    texto = str(texto)
    partes = re.split(r"(\*\*.*?\*\*)", texto, flags=re.S)
    salida = []
    for p in partes:
        if p.startswith("**") and p.endswith("**"):
            salida.append('<span class="rojo">' + p[2:-2] + '</span>')
        else:
            salida.append(p.replace("\n", "<br>"))
    return "".join(salida)

def bloque_html(contenido):
    st.markdown(f'<div class="bloque">{contenido}</div>', unsafe_allow_html=True)

def detectar_ortografia(respuestas):
    faltas = {"sustantibo", "haver", "hechar", "aver", "aora", "havia", "hamos", "bamos", "llendo", "dijistes", "hicistes", "estava", "tubieron", "tubo"}
    tildes = {"donde":"dónde", "quienes":"quiénes", "cuando":"cuándo", "como":"cómo", "que":"qué", "quien":"quién", "cuanto":"cuánto", "tambien":"también", "despues":"después", "mas":"más", "dia":"día", "llego":"llegó", "parecia":"parecía", "dormia":"dormía", "bajo":"bajó", "cubria":"cubría", "veia":"veía"}
    nf = nt = 0
    for respuesta in respuestas:
        if not respuesta: continue
        palabras = re.findall(r"\b[\wáéíóúüñ]+\b", str(respuesta).lower(), flags=re.UNICODE)
        nf += sum(p in faltas for p in palabras)
        nt += sum(p in tildes for p in palabras)
    return nf, nt

def corregir(res):
    p = {"comprension":0.0,"morfologia":0.0,"semantica":0.0,"textos":0.0,"literatura":0.0,"sintaxis":0.0}
    if contiene(res.get("c1"), "tren", "estacion", "vagon"): p["comprension"] += .50
    pers = lista(res.get("c2"))
    p["comprension"] += .25 * int(any("hombre" in x or "joven" in x for x in pers))
    p["comprension"] += .25 * int(any("anciana" in x for x in pers))
    if contiene(res.get("c3"), "temprano", "madrugada", "noche"): p["comprension"] += .50
    acciones = {"llego","cubria","veia","viajaban","llevaba","parecia","dormia","bajo"}
    halladas = {a for a in acciones if a in normalizar(res.get("c4"))}
    p["comprension"] += min(3,len(halladas))/3*.50
    claves = {
      "m1": {"lexema":"niñ","morfemas":["o","s"],"estructura":"simple","categoria":["sustantivo","masculino","plural"],"vi":"variable"},
      "m2": {"lexema":"mochil","morfemas":["a","s"],"estructura":"simple","categoria":["sustantivo","femenino","plural"],"vi":"variable"},
      "m3": {"lexema":"conoc","morfemas":["des","ido"],"estructura":"derivada","categoria":["adjetivo","masculino","singular"],"vi":"variable"}}
    pesos = {"lexema":.10,"morfemas":.10,"estructura":.10,"categoria":.15,"vi":.05}
    for mid, cs in claves.items():
        for campo, correcta in cs.items():
            v = normalizar(res.get(f"{mid}_{campo}"))
            ok = False
            if campo == "lexema": ok = normalizar(correcta) in v
            elif campo == "morfemas": ok = all(normalizar(x) in v for x in (correcta if isinstance(correcta,list) else [correcta]))
            elif campo == "categoria": ok = all(x in v for x in correcta)
            else: ok = v == normalizar(correcta)
            if ok: p["morfologia"] += pesos[campo]
    if exacta(res.get("dp1"),"determinante"): p["morfologia"] += .50
    if exacta(res.get("dp2"),"pronombre"): p["morfologia"] += .50
    for k, ok in {"s1":"antonimia","s2":"campo semantico","s3":"polisemia"}.items():
        if exacta(res.get(k), ok): p["semantica"] += 1/3
    if exacta(res.get("t1"),"instructivo","instruccional"): p["textos"] += .75
    if exacta(res.get("t2"),"expositivo"): p["textos"] += .75
    if exacta(res.get("l1"),"4"): p["literatura"] += .30
    if exacta(res.get("l2"),"arte mayor"): p["literatura"] += .30
    m = normalizar(res.get("l3")).replace(","," ").replace("/"," ").replace("-"," ")
    if m in {"10a 11b 11b 10a","10 11 11 10"}: p["literatura"] += .35
    if exacta(res.get("l4"),"asonante","rima asonante"): p["literatura"] += .35
    if contiene(res.get("l5"),"sobre el","brillan sobre","susurra cerca","mira el"): p["literatura"] += .35
    if contiene(res.get("l6"),"viento") and contiene(res.get("l6"),"susurra"): p["literatura"] += .35
    correctas = {"x1":"frase","x2":"oracion","x3":"oracion","x4":"interrogativa","x5":"exclamativa","x6":"enunciativa"}
    for k,v in correctas.items():
        if exacta(res.get(k),v): p["sintaxis"] += 1/6
    return p, round(sum(p.values()),2)

def csv_bytes(fila):
    out=io.StringIO(); w=csv.DictWriter(out,fieldnames=list(fila)); w.writeheader(); w.writerow(fila); return out.getvalue().encode("utf-8-sig")

def excel_bytes(fila):
    wb=Workbook(); ws=wb.active; ws.title="Resultado"
    campos=list(fila); ws.append(campos); ws.append([fila[c] for c in campos]); ws.freeze_panes="A2"
    for col in ws.columns: ws.column_dimensions[col[0].column_letter].width=max(14,min(34,max(len(str(x.value or "")) for x in col)+2))
    out=io.BytesIO(); wb.save(out); return out.getvalue()

def guardar_csv(fila):
    campos=list(fila)
    if os.path.exists(CSV_FILE):
        try: df=pd.read_csv(CSV_FILE)
        except Exception: df=pd.DataFrame(columns=campos)
    else: df=pd.DataFrame(columns=campos)
    for c in campos:
        if c not in df.columns: df[c]=""
    df=pd.concat([df[campos],pd.DataFrame([fila])],ignore_index=True)
    df.to_csv(CSV_FILE,index=False,encoding="utf-8-sig")

st.markdown('<div class="titulo">Evaluación inicial de Lengua — 2.º ESO · NNEE</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitulo">Lengua Castellana y Literatura · Curso 2026-2027</div>', unsafe_allow_html=True)

if st.session_state.get("enviado"):
    fila=st.session_state["fila"]; puntos=st.session_state["puntos"]; nota9=st.session_state["nota9"]
    faltas=st.session_state["faltas"]; tildes=st.session_state["tildes"]
    st.success("Examen corregido y guardado correctamente.")
    st.markdown(f'<div class="nota9">NOTA DE ESTA PARTE · SOBRE 9<br>{nota9:.2f} / 9</div>',unsafe_allow_html=True)
    st.markdown('<div class="aviso"><b>IMPORTANTE:</b> esta nota automática es sobre 9. Queda por realizar la producción escrita a mano, que puede aportar hasta 1 punto adicional.</div>',unsafe_allow_html=True)
    st.write(f"Faltas de ortografía detectadas: {faltas}")
    st.write(f"Faltas de tilde detectadas: {tildes}")
    st.caption("Los errores ortográficos y de tilde se cuentan como información de seguimiento, pero no restan puntos de la nota.")
    st.subheader("Resultado por áreas")
    for c,mx in [("comprension",2),("morfologia",2.5),("semantica",1),("textos",1.5),("literatura",2),("sintaxis",1)]: st.write(f"{c.capitalize()}: {puntos[c]/mx*10:.2f}/10")
    st.download_button("Descargar resultado CSV",csv_bytes(fila),file_name="Resultado_2ESO_NEE.csv",mime="text/csv",use_container_width=True)
    st.download_button("Descargar resultado Excel",excel_bytes(fila),file_name="Resultado_2ESO_NEE.xlsx",mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",use_container_width=True)
    if st.button("Volver al inicio",use_container_width=True): st.session_state.clear(); st.rerun()
    st.stop()

nombre=st.text_input("Nombre y apellidos",placeholder="Escribe tu nombre y apellidos")
grupo=st.selectbox("Grupo",["","2º A","2º B","2º C","2º D"])

with st.form("examen_2eso_nee"):
    respuestas={}
    bloque_html("<h2>1. Comprensión lectora — 2 puntos</h2>" + EXAM["comprension"]["texto"].replace("\n","<br>"))
    for q in EXAM["comprension"]["preguntas"]:
        texto=rojo_marcadores(q["enunciado"])
        ayuda="Escribe una respuesta breve." if q["id"]!="c4" else "Escribe tres acciones separadas por comas."
        respuestas[q["id"]]=st.text_input("",help=ayuda,key=q["id"],label_visibility="collapsed")
        st.markdown(texto,unsafe_allow_html=True)
    st.markdown('<div class="separador"></div>',unsafe_allow_html=True)

    bloque_html("<h2>2. Morfología — 2,5 puntos</h2><div class='ayuda'><b>Cómo responder:</b> separa los diferentes morfemas mediante comas y sin guion.</div>")
    etiquetas={"Lexema":"lexema","Morfemas":"morfemas","Estructura":"estructura","Categoría gramatical":"categoría gramatical","V/I":"variable o invariable"}
    for palabra in EXAM["morfologia"]:
        st.markdown(f"<h3>{palabra['palabra']}</h3>",unsafe_allow_html=True)
        for campo in palabra["campos"]:
            if campo == "V/I": continue
            visible=etiquetas.get(campo,campo)
            st.markdown(f'<span class="rojo">{visible}</span>',unsafe_allow_html=True)
            key=f"{palabra['id']}_{normalizar(campo).replace(' ','_').replace('/','_')}"
            if campo=="Estructura": val=st.selectbox("",["","simple","derivada","compuesta","parasintética"],key=key,label_visibility="collapsed")
            else: val=st.text_input("",key=key,label_visibility="collapsed")
            respuestas[key]=val
    st.markdown('<div class="separador"></div>',unsafe_allow_html=True)

    bloque_html("<h2>2.2. Determinantes y pronombres</h2>")
    for q in EXAM["determinantes_pronombres"]:
        frase=q["frase"].replace("**Aquellos**","<span class='rojo'>Aquellos</span>").replace("**Nadie**","<span class='rojo'>Nadie</span>")
        st.markdown(frase,unsafe_allow_html=True)
        en=q["enunciado"].replace("**Aquellos**","<span class='rojo'>Aquellos</span>").replace("**Nadie**","<span class='rojo'>Nadie</span>")
        st.markdown(en,unsafe_allow_html=True)
        respuestas[q["id"]]=st.selectbox("",["","determinante","pronombre"],key=q["id"],label_visibility="collapsed")
    st.markdown('<div class="separador"></div>',unsafe_allow_html=True)

    bloque_html("<h2>3. Semántica — 1 punto</h2>")
    opciones=["","antonimia","sinonimia","campo semántico","polisemia","homonimia","meronimia","hipónimos","hiperónimo"]
    for q in EXAM["semantica"]:
        st.markdown(f"<span class='rojo'>{q['elemento']}</span>",unsafe_allow_html=True)
        respuestas[q["id"]]=st.selectbox("",opciones,key=q["id"],label_visibility="collapsed")
    st.markdown('<div class="separador"></div>',unsafe_allow_html=True)

    bloque_html("<h2>4. Tipos de texto — 1,5 puntos</h2><p>Lee cada texto y escribe el <span class='rojo'>tipo de texto</span>.</p>")
    opciones_t=["","narrativo","descriptivo","expositivo","argumentativo","instructivo","dialogado"]
    for letra in ["A","B"]:
        texto=EXAM["textos"]["textos"][letra]
        q=next(x for x in EXAM["textos"]["preguntas"] if x["id"]==f"t{1 if letra=='A' else 2}")
        st.markdown(f"<p><span class='rojo'><b>Texto {letra}:</b></span> {texto}</p>",unsafe_allow_html=True)
        respuestas[q["id"]]=st.selectbox("",opciones_t,key=q["id"],label_visibility="collapsed")
    st.markdown('<div class="separador"></div>',unsafe_allow_html=True)

    bloque_html("<h2>5. Literatura — 2 puntos</h2>")
    st.markdown('<div class="poema-titulo">POEMA</div>', unsafe_allow_html=True)
    st.markdown(EXAM["literatura"]["poema"].replace("\n","<br>"), unsafe_allow_html=True)
    for q, opciones in zip(EXAM["literatura"]["preguntas"],[ ["","1","2","3","4","5","6","7","8"],["","arte menor","arte mayor"],None,["","asonante","consonante"],None,None ]):
        st.markdown(rojo_marcadores(q["enunciado"]),unsafe_allow_html=True)
        if q["id"]=="l3": val=st.text_input("",help="Puedes escribir el esquema métrico.",key=q["id"],label_visibility="collapsed")
        elif q["id"] in ("l5","l6"): val=st.text_input("",key=q["id"],label_visibility="collapsed")
        else: val=st.selectbox("",opciones,key=q["id"],label_visibility="collapsed")
        respuestas[q["id"]]=val
    st.markdown('<div class="separador"></div>',unsafe_allow_html=True)

    bloque_html("<h2>6. Sintaxis — 1 punto</h2>")
    st.markdown('<div class="poema-titulo">1. DISTINGUIR FRASE U ORACIÓN</div>',unsafe_allow_html=True)
    for q in EXAM["sintaxis"][:3]:
        st.markdown(f"<span class='rojo'>{q['frase']}</span>",unsafe_allow_html=True)
        if q["id"] in ("x1","x2","x3"): ops=["","frase","oración"]
        else: ops=["","enunciativa","interrogativa","exclamativa","desiderativa","exhortativa","imperativa"]
        respuestas[q["id"]]=st.selectbox("",ops,key=q["id"],label_visibility="collapsed")
    st.markdown('<div class="separador"></div>',unsafe_allow_html=True)
    st.markdown('<div class="poema-titulo">2. MODALIDAD ORACIONAL</div>',unsafe_allow_html=True)
    for q in EXAM["sintaxis"][3:]:
        st.markdown(f"<span class='rojo'>{q['frase']}</span>",unsafe_allow_html=True)
        ops=["","enunciativa","interrogativa","exclamativa","desiderativa","exhortativa","imperativa"]
        respuestas[q["id"]]=st.selectbox("",ops,key=q["id"],label_visibility="collapsed")
    st.markdown('<div class="separador"></div>',unsafe_allow_html=True)

    bloque_html("<h2>7. Diálogo</h2>" + EXAM["dialogo"]["texto"].replace("\n","<br>"))
    for q in EXAM["dialogo"]["preguntas"]:
        st.markdown(rojo_marcadores(q["enunciado"]),unsafe_allow_html=True)
        if q["id"]=="d2": val=st.number_input("",min_value=0,max_value=20,value=0,step=1,key="d2",label_visibility="collapsed")
        elif q["id"]=="d3": val=st.text_area("",height=100,key="d3",label_visibility="collapsed")
        else: val=st.text_input("",help="Escribe los dos interlocutores separados por comas.",key="d1",label_visibility="collapsed")
        respuestas[q["id"]]=str(int(val)) if q["id"]=="d2" else val
    enviar=st.form_submit_button("ENVIAR EXAMEN",use_container_width=True)

if enviar:
    if not nombre.strip(): st.error("Escribe tu nombre y apellidos."); st.stop()
    if not grupo: st.error("Selecciona tu grupo."); st.stop()
    puntos,total10=corregir(respuestas)
    faltas,tildes=detectar_ortografia([v for v in respuestas.values() if isinstance(v,str)])
    nota9=round(total10*0.9,2)
    fila={"name":nombre.strip(),"group":grupo,"date":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),**{k:round(v,2) for k,v in puntos.items()},"nota_sobre_9":nota9,"faltas_ortografia":faltas,"faltas_tildes":tildes,"produccion_escrita_pendiente":"Sí · hasta +1 punto"}
    try: guardar_csv(fila)
    except Exception as e: st.error("No se pudo guardar el resultado."); st.exception(e); st.stop()
    st.session_state.update(enviado=True,fila=fila,puntos=puntos,nota9=nota9,faltas=faltas,tildes=tildes)
    st.rerun()