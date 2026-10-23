"""Descarga de todas las fuentes externas del proyecto a datos/raw/.

Cada fuente es reanudable: si el archivo destino ya existe, se omite (usa
--forzar para volver a bajarla). Uso:

    uv run python -m src.descarga                 # todas las fuentes
    uv run python -m src.descarga --solo siap
    uv run python -m src.descarga --forzar --solo rutas

Fuentes:
    siap   Cierre de la Producción Agrícola (SIAP): municipal 2003-2025 y estatal 1980-2002
    rutas  Coordenadas (Nominatim) y distancia por carretera a Hermosillo (OSRM) de cada
           municipio productor; requiere datos/processed/cempasuchil_municipal.csv
"""

import argparse
import json
import logging
import time
from pathlib import Path

import requests

from src import config

log = logging.getLogger("descarga")

SESION = requests.Session()
SESION.headers.update({"User-Agent": config.USER_AGENT})


def _get(url: str, intentos: int = 4, **kwargs) -> requests.Response:
    """GET con reintentos y espera exponencial para errores de red o 5xx/429."""
    for intento in range(1, intentos + 1):
        try:
            resp = SESION.get(url, timeout=kwargs.pop("timeout", 180), **kwargs)
            if resp.status_code in (429, 500, 502, 503, 504):
                raise requests.HTTPError(f"HTTP {resp.status_code}")
            return resp
        except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as err:
            if intento == intentos:
                raise
            espera = 2**intento
            log.warning("  %s (intento %d/%d), reintento en %ds", err, intento, intentos, espera)
            time.sleep(espera)
    raise RuntimeError("inalcanzable")


def _descargar_archivo(url: str, destino: Path, forzar: bool, **kwargs) -> Path:
    if destino.exists() and not forzar:
        log.info("  ya existe %s", destino.relative_to(config.RAIZ))
        return destino
    destino.parent.mkdir(parents=True, exist_ok=True)
    resp = _get(url, stream=True, **kwargs)
    resp.raise_for_status()
    tmp = destino.with_suffix(destino.suffix + ".part")
    with tmp.open("wb") as f:
        for bloque in resp.iter_content(chunk_size=1 << 20):
            f.write(bloque)
    tmp.rename(destino)
    log.info("  %s (%.1f MB)", destino.relative_to(config.RAIZ), destino.stat().st_size / 1e6)
    return destino


def descargar_siap(forzar: bool) -> None:
    for anio in config.ANIOS_MUNICIPAL:
        log.info("SIAP municipal %d", anio)
        params = {"view": config.VISTA_SIAP_MUNICIPAL, "ANIO": anio}
        destino = config.DIR_RAW / "siap" / "municipal" / f"Cierre_agricola_mun_{anio}.csv"
        _descargar_archivo(config.URL_SIAP, destino, forzar, params=params)
    for anio in config.ANIOS_ESTATAL:
        log.info("SIAP estatal %d", anio)
        params = {"view": config.VISTA_SIAP_ESTATAL, "ANIO": anio}
        destino = config.DIR_RAW / "siap" / "estatal" / f"Cierre_agricola_{anio}.csv"
        _descargar_archivo(config.URL_SIAP, destino, forzar, params=params)


def _geocodificar(municipio: str, estado: str) -> tuple[float, float] | None:
    params = {"q": f"{municipio}, {estado}, México", "format": "json", "limit": 1, "countrycodes": "mx"}
    resp = _get(config.URL_NOMINATIM, params=params, timeout=60)
    resp.raise_for_status()
    time.sleep(1.1)  # política de uso de Nominatim: una petición por segundo
    resultados = resp.json()
    if not resultados:
        return None
    return float(resultados[0]["lat"]), float(resultados[0]["lon"])


def descargar_rutas(forzar: bool) -> None:
    """Una ruta por municipio productor; el resultado se guarda como JSON por municipio."""
    import pandas as pd

    origenes = pd.read_csv(config.DIR_PROCESSED / "cempasuchil_municipal.csv")
    origenes = origenes[origenes["anio"] >= config.ANIO_INICIO_RUTAS]
    origenes = origenes[["idestado", "nomestado", "idmunicipio", "nommunicipio"]].drop_duplicates()
    dir_rutas = config.DIR_RAW / "rutas"
    dir_rutas.mkdir(parents=True, exist_ok=True)
    nombre_destino, lat_d, lon_d = config.DESTINO
    for fila in origenes.itertuples():
        destino = dir_rutas / f"{fila.idestado:02d}{fila.idmunicipio:03d}.json"
        if destino.exists() and not forzar:
            continue
        log.info("Ruta %s, %s -> %s", fila.nommunicipio, fila.nomestado, nombre_destino)
        coords = _geocodificar(fila.nommunicipio, fila.nomestado)
        registro = {
            "idestado": fila.idestado,
            "nomestado": fila.nomestado,
            "idmunicipio": fila.idmunicipio,
            "nommunicipio": fila.nommunicipio,
            "lat": None,
            "lon": None,
            "distancia_km": None,
            "duracion_h": None,
        }
        if coords:
            registro["lat"], registro["lon"] = coords
            url = f"{config.URL_OSRM}/{coords[1]},{coords[0]};{lon_d},{lat_d}"
            resp = _get(url, params={"overview": "false"}, timeout=60)
            if resp.ok and resp.json().get("routes"):
                ruta = resp.json()["routes"][0]
                registro["distancia_km"] = round(ruta["distance"] / 1000, 1)
                registro["duracion_h"] = round(ruta["duration"] / 3600, 2)
        destino.write_text(json.dumps(registro, ensure_ascii=False, indent=2), encoding="utf-8")


FUENTES = {
    "siap": descargar_siap,
    "rutas": descargar_rutas,
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--solo", nargs="+", choices=FUENTES, help="fuentes a descargar")
    parser.add_argument("--forzar", action="store_true", help="volver a descargar aunque exista")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    for nombre in args.solo or FUENTES:
        FUENTES[nombre](forzar=args.forzar)


if __name__ == "__main__":
    main()
