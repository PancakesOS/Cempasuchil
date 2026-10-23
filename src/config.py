"""Rutas, URLs y constantes compartidas por scripts y notebooks."""

from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]

DIR_DATOS = RAIZ / "datos"
DIR_RAW = DIR_DATOS / "raw"
DIR_PROCESSED = DIR_DATOS / "processed"
DIR_MANUAL = DIR_DATOS / "manual"
DIR_FIGURAS = RAIZ / "outputs" / "figuras"
DIR_TABLAS = RAIZ / "outputs" / "tablas"

USER_AGENT = "SahuarisResearch/0.1 (investigacion cempasuchil Dia de Muertos)"

# Cierre de la Producción Agrícola del SIAP (DGSIAP, Agricultura). En 2026 el
# portal se mudó de infosiap.siap.gob.mx a nube.agricultura.gob.mx; las
# descargas se piden por un identificador de vista más el año.
URL_SIAP = "https://nube.agricultura.gob.mx/index.php"
VISTA_SIAP_MUNICIPAL = "10AE434F-A2158368-A120BC5A-EDF4AFAA"  # 2003-2025, nivel municipal
VISTA_SIAP_ESTATAL = "5F687BE6-1513BEE9-53E63085-9D3C988B"  # 1980-2002, nivel estatal
ANIOS_MUNICIPAL = range(2003, 2026)
ANIOS_ESTATAL = range(1980, 2003)
CODIFICACION_SIAP = "latin-1"

# El SIAP registra el cempasúchil como "Zempoalxochitl" en tres unidades:
# toneladas (flor de corte a granel), manojos y plantas en maceta.
PATRON_CEMPASUCHIL = r"zempoal|cempas|cempoal"

CVE_ENT_SONORA = 26

# Agrupación de estados para la serie larga. El noroeste y el Bajío fueron la
# zona de la flor para pigmento; el centro es la flor de altar.
REGIONES = {
    25: "Sinaloa y Sonora",
    26: "Sinaloa y Sonora",
    11: "Bajío (Gto., Mich., Qro.)",
    16: "Bajío (Gto., Mich., Qro.)",
    22: "Bajío (Gto., Mich., Qro.)",
    21: "Puebla",
    9: "CDMX y Edomex",
    15: "CDMX y Edomex",
}
REGION_RESTO = "Resto del país"
ORDEN_REGIONES = ["Sinaloa y Sonora", "Bajío (Gto., Mich., Qro.)", "Puebla", "CDMX y Edomex", REGION_RESTO]

# Destino de todas las rutas: el altar sonorense de referencia. Solo se trazan
# rutas desde los municipios que produjeron en los últimos cinco cierres.
DESTINO = ("Hermosillo", 29.0729, -110.9559)
ANIO_INICIO_RUTAS = 2021

URL_NOMINATIM = "https://nominatim.openstreetmap.org/search"
URL_OSRM = "https://router.project-osrm.org/route/v1/driving"
