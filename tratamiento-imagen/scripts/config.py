"""Configuración común de los scripts del informe de tratamiento de imagen."""
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DIR_IMG = RAIZ / "imagenes"
DIR_RES = RAIZ / "resultados"
DIR_RES.mkdir(exist_ok=True)

# Orden fijo de las cinco condiciones de captura (guía R2-A2-S8)
NOMBRES = ["referencia", "oscura", "desenfocada", "fondo", "angulo"]

ETIQUETAS = {
    "referencia": "Referencia",
    "oscura": "Baja iluminación",
    "desenfocada": "Desenfocada",
    "fondo": "Fondo complejo",
    "angulo": "Otra perspectiva",
}

# Región de interés (x0, y0, x1, y1) en píxeles de cada imagen original:
# rectángulo que encierra la figura y su base. Se definió observando cada foto.
ROI = {
    "referencia": (660, 10, 1350, 1480),
    "oscura": (760, 340, 1440, 1320),
    "desenfocada": (40, 570, 600, 1430),
    "fondo": (700, 460, 1075, 1040),
    "angulo": (925, 410, 1490, 1440),
}

# Ancho común para comparar nitidez entre imágenes de distinta resolución
ANCHO_COMUN = 2016
