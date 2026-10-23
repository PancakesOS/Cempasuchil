"""Lectura y homologación del Cierre Agrícola del SIAP para el cempasúchil.

    uv run python -m src.procesamiento

Produce en datos/processed/:
    cempasuchil_municipal.csv  filas de cempasúchil 2003-2025 (municipio x ciclo x modalidad)
    cempasuchil_estatal.csv    filas de cempasúchil 1980-2025 a nivel estado (1980-2002 tal cual;
                               2003-2025 sumado desde el municipal)
    rutas_hermosillo.csv       distancia por carretera de cada municipio productor a Hermosillo
"""

import json

import pandas as pd

from src import config

COLUMNAS_NUMERICAS = ["sembrada", "cosechada", "siniestrada", "volumenproduccion", "rendimiento", "precio", "valorproduccion"]

# Presentación del producto según el nombre del cultivo y la unidad en el SIAP.
# "Forrajero" es la flor sembrada para alimento animal (pigmento de yema y piel
# de pollo). La flor "a granel" en toneladas no declara uso: en los años 80 y 90
# era sobre todo materia prima para pigmento; desde 2000, flor de corte.
# Las plantas en maceta aparecen como "Zempoalxochitl" con unidad Planta de 2005
# a 2019 y como "Zempoalxochitl (planta)" desde 2022.
PRESENTACIONES = ["Flor a granel (t)", "Forrajero (t)", "Flor en manojo", "Planta en maceta"]


def _presentacion(cultivo: str, unidad: str) -> str:
    if "forrajero" in cultivo.lower():
        return "Forrajero (t)"
    if unidad == "Planta":
        return "Planta en maceta"
    if unidad in ("Manojo", "Gruesa"):
        return "Flor en manojo"
    return "Flor a granel (t)"


def leer_cierre(ruta) -> pd.DataFrame:
    """Lee un CSV del SIAP y homologa los nombres de columna entre años.

    2018 nombra al cultivo "Nomcultivo Sin Um" y desde 2024 el precio se llama
    "Preciomediorural"; algunos años traen comas de miles en los números.
    """
    df = pd.read_csv(ruta, encoding=config.CODIFICACION_SIAP, dtype=str)
    df.columns = [c.strip().lower().replace(" sin um", "") for c in df.columns]
    df = df.rename(columns={"preciomediorural": "precio"})
    return df


def _filtrar_cempasuchil(df: pd.DataFrame) -> pd.DataFrame:
    df = df[df["nomcultivo"].str.contains(config.PATRON_CEMPASUCHIL, case=False, na=False)].copy()
    for col in df.columns:
        df[col] = df[col].str.strip()
    for col in COLUMNAS_NUMERICAS:
        df[col] = pd.to_numeric(df[col].str.replace(",", "", regex=False), errors="coerce")
    for col in ["anio", "idestado", "idmunicipio", "idunidadmedida", "idcultivo"]:
        if col in df:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    df["presentacion"] = [_presentacion(c, u) for c, u in zip(df["nomcultivo"], df["nomunidad"])]
    return df


def cempasuchil_municipal() -> pd.DataFrame:
    rutas = sorted((config.DIR_RAW / "siap" / "municipal").glob("Cierre_agricola_mun_*.csv"))
    return pd.concat([_filtrar_cempasuchil(leer_cierre(r)) for r in rutas], ignore_index=True)


def cempasuchil_estatal(municipal: pd.DataFrame) -> pd.DataFrame:
    rutas = sorted((config.DIR_RAW / "siap" / "estatal").glob("Cierre_agricola_*.csv"))
    historico = pd.concat([_filtrar_cempasuchil(leer_cierre(r)) for r in rutas], ignore_index=True)
    claves = ["anio", "idestado", "nomestado", "nomcultivo", "presentacion", "nomunidad"]
    reciente = (
        municipal.groupby(claves, as_index=False)[["sembrada", "cosechada", "siniestrada", "volumenproduccion", "valorproduccion"]]
        .sum()
    )
    historico = historico.groupby(claves, as_index=False)[["sembrada", "cosechada", "siniestrada", "volumenproduccion", "valorproduccion"]].sum()
    estatal = pd.concat([historico, reciente], ignore_index=True)
    estatal["precio"] = estatal["valorproduccion"] / estatal["volumenproduccion"]
    return estatal.sort_values(["anio", "idestado", "nomcultivo"]).reset_index(drop=True)


def rutas_hermosillo() -> pd.DataFrame:
    archivos = sorted((config.DIR_RAW / "rutas").glob("*.json"))
    return pd.DataFrame([json.loads(a.read_text(encoding="utf-8")) for a in archivos])


def construir_tablas() -> None:
    config.DIR_PROCESSED.mkdir(parents=True, exist_ok=True)
    municipal = cempasuchil_municipal()
    municipal.to_csv(config.DIR_PROCESSED / "cempasuchil_municipal.csv", index=False)
    estatal = cempasuchil_estatal(municipal)
    estatal.to_csv(config.DIR_PROCESSED / "cempasuchil_estatal.csv", index=False)
    print(f"  cempasuchil_municipal.csv ({len(municipal):,} filas)")
    print(f"  cempasuchil_estatal.csv ({len(estatal):,} filas)")
    if (config.DIR_RAW / "rutas").exists():
        rutas = rutas_hermosillo()
        rutas.to_csv(config.DIR_PROCESSED / "rutas_hermosillo.csv", index=False)
        print(f"  rutas_hermosillo.csv ({len(rutas):,} municipios)")


if __name__ == "__main__":
    construir_tablas()
