import pandas as pd


def cargar_datos(ruta="results.csv"):
    """
    Carga los resultados guardados.
    Si no existe el archivo, devuelve un DataFrame vacío.
    """
    try:
        return pd.read_csv(ruta)
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame()


def resultados_grupo(ruta="results.csv", grupo=None):
    """
    Devuelve únicamente los resultados del grupo indicado.
    """
    df = cargar_datos(ruta)

    if df.empty or grupo is None:
        return df

    if "Grupo" not in df.columns:
        return pd.DataFrame()

    return df[df["Grupo"].astype(str).str.upper() == str(grupo).upper()]


def media_grupo(ruta="results.csv", grupo=None):
    """
    Calcula la media de la nota automática del grupo.
    """
    df = resultados_grupo(ruta, grupo)

    if df.empty or "Nota automática" not in df.columns:
        return 0.0

    return round(pd.to_numeric(df["Nota automática"], errors="coerce").mean(), 2)


def mejor_nota_grupo(ruta="results.csv", grupo=None):
    """
    Devuelve la mejor nota del grupo.
    """
    df = resultados_grupo(ruta, grupo)

    if df.empty or "Nota automática" not in df.columns:
        return 0.0

    return round(
        pd.to_numeric(df["Nota automática"], errors="coerce").max(),
        2
    )


def peor_nota_grupo(ruta="results.csv", grupo=None):
    """
    Devuelve la nota más baja del grupo.
    """
    df = resultados_grupo(ruta, grupo)

    if df.empty or "Nota automática" not in df.columns:
        return 0.0

    return round(
        pd.to_numeric(df["Nota automática"], errors="coerce").min(),
        2
    )


def numero_alumnos(ruta="results.csv", grupo=None):
    """
    Cuenta los alumnos que tienen resultados guardados.
    """
    df = resultados_grupo(ruta, grupo)

    if df.empty:
        return 0

    return len(df)


def estadisticas_grupo(ruta="results.csv", grupo=None):
    """
    Devuelve un resumen general del grupo.
    """
    df = resultados_grupo(ruta, grupo)

    if df.empty:
        return {
            "alumnos": 0,
            "media": 0.0,
            "mejor_nota": 0.0,
            "peor_nota": 0.0
        }

    return {
        "alumnos": numero_alumnos(ruta, grupo),
        "media": media_grupo(ruta, grupo),
        "mejor_nota": mejor_nota_grupo(ruta, grupo),
        "peor_nota": peor_nota_grupo(ruta, grupo)
    }


def comparativa_grupo(ruta="results.csv", grupo=None):
    """
    Prepara los datos para mostrar una comparativa anónima.

    Nunca devuelve los nombres reales de los alumnos.
    """
    df = resultados_grupo(ruta, grupo).copy()

    if df.empty:
        return pd.DataFrame()

    if "Nota automática" not in df.columns:
        return pd.DataFrame()

    df["Nota automática"] = pd.to_numeric(
        df["Nota automática"],
        errors="coerce"
    )

    df = df.sort_values(
        "Nota automática",
        ascending=False
    ).reset_index(drop=True)

    df["Alumno"] = [
        f"Alumno {i + 1}"
        for i in range(len(df))
    ]

    return df[["Alumno", "Nota automática"]]


def areas_disponibles(ruta="results.csv"):
    """
    Detecta las columnas de resultados por áreas.
    """
    df = cargar_datos(ruta)

    if df.empty:
        return []

    areas = [
        "Comprensión",
        "Morfología",
        "Semántica",
        "Textos",
        "Literatura",
        "Sintaxis",
        "Diálogo"
    ]

    return [
        area
        for area in areas
        if area in df.columns
    ]
