# Punto de entrada estable de la aplicación NNEE.
# Ejecuta directamente el núcleo de la evaluación adaptada.
from pathlib import Path

core = Path(__file__).with_name("_app_core.py")
source = core.read_text(encoding="utf-8")

# Elimina cualquier resto del monitor de pestañas y deja la aplicación
# funcionando como antes de esa modificación.
source = source.replace('import streamlit.components.v1 as components\n', '')
source = source.replace('from pathlib import Path\n', '')
source = source.replace('TAB_MONITOR = components.declare_component("tab_monitor", path=str(Path(__file__).parent / "tab_monitor"))\n', '')
source = source.replace('if "cambios_pestana" not in st.session_state:\n    st.session_state.cambios_pestana = 0\n', '')
source = source.replace('evento_pestana = TAB_MONITOR(key="monitor_pestana")\nif isinstance(evento_pestana, dict):\n    nuevo = int(evento_pestana.get("count", 0) or 0)\n    if nuevo > st.session_state.cambios_pestana:\n        st.session_state.cambios_pestana = nuevo\nif not st.session_state.get("enviado") and st.session_state.cambios_pestana > 0:\n    if st.session_state.cambios_pestana >= 3:\n        st.error("Se han detectado 3 cambios de pestaña o salida de la ventana. El examen se enviará automáticamente.")\n    else:\n        restante = 3 - st.session_state.cambios_pestana\n        st.warning(f"Cambio de pestaña detectado ({st.session_state.cambios_pestana}). Evita salir del examen. Tras {restante} cambio(s) más, el examen se enviará automáticamente.")\n', '')
source = source.replace('evento_pestana = TAB_MONITOR(key="monitor_pestana")\nif isinstance(evento_pestana, dict):\n    try:\n        nuevo = int(evento_pestana.get("count", 0))\n        if nuevo > st.session_state.cambios_pestana:\n            st.session_state.cambios_pestana = nuevo\n    except (TypeError, ValueError):\n        pass\n\nif not st.session_state.get("enviado") and st.session_state.cambios_pestana > 0:\n    if st.session_state.cambios_pestana >= 3:\n        st.error("Se han detectado 3 cambios de pestaña o salida de la ventana. El examen se enviará automáticamente.")\n    else:\n        restante = 3 - st.session_state.cambios_pestana\n        st.warning(f"Cambio de pestaña detectado ({st.session_state.cambios_pestana}). Evita salir del examen. Tras {restante} cambio(s) más, el examen se enviará automáticamente.")\n\n', '')
source = source.replace('    if int(fila.get("cambios_pestana", 0) or 0) > 0:\n        cambios=int(fila.get("cambios_pestana", 0) or 0)\n        st.warning(f"Durante el examen se detectaron {cambios} cambios de pestaña o salida de la ventana.")\n', '')
source = source.replace('    if int(fila.get("cambios_pestana", 0) or 0) > 0:\n        cambios = int(fila.get("cambios_pestana", 0) or 0)\n        st.warning(f"Durante el examen se detectaron {cambios} cambios de pestaña o salida de la ventana.")\n', '')
source = source.replace(',"cambios_pestana":st.session_state.cambios_pestana', '')
source = source.replace(',"cambios_pestana": st.session_state.cambios_pestana', '')
source = source.replace('    "cambios_pestana": st.session_state.cambios_pestana,\n', '')
source = source.replace(', cambios_pestana=st.session_state.cambios_pestana', '')
source = source.replace(',st.session_state.cambios_pestana', '')
source = source.replace('"cambios_pestana"', '"__eliminado_cambios_pestana__"')
source = source.replace('excel_bytes(fila,st.session_state.cambios_pestana)', 'excel_bytes(fila)')
source = source.replace('if enviar or st.session_state.cambios_pestana >= 3:', 'if enviar:')

exec(compile(source, str(core), "exec"), {"__name__": "__main__", "__file__": str(core)})
