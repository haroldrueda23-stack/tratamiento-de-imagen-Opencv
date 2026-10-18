"""Comparación JPG vs PNG sobre la imagen de referencia.

Uso:  python scripts/02_formatos.py
Salidas: resultados/comparacion.jpg, resultados/comparacion.png, resultados/formatos.json
"""
import json
import os

import cv2
import numpy as np

from config import DIR_IMG, DIR_RES

imagen = cv2.imread(str(DIR_IMG / "referencia.jpg"))
alto, ancho = imagen.shape[:2]

ruta_jpg = DIR_RES / "comparacion.jpg"
ruta_png = DIR_RES / "comparacion.png"
cv2.imwrite(str(ruta_jpg), imagen, [cv2.IMWRITE_JPEG_QUALITY, 90])
cv2.imwrite(str(ruta_png), imagen)

jpg = cv2.imread(str(ruta_jpg))
png = cv2.imread(str(ruta_png))

# PSNR: qué tanto se parece el archivo guardado a los píxeles de partida
psnr_jpg = cv2.PSNR(imagen, jpg)
dif_png = int(np.abs(imagen.astype(int) - png.astype(int)).max())

res = {
    "resolucion": [ancho, alto],
    "jpg_q90_kb": round(os.path.getsize(ruta_jpg) / 1024, 1),
    "png_kb": round(os.path.getsize(ruta_png) / 1024, 1),
    "original_kb": round(os.path.getsize(DIR_IMG / "referencia.jpg") / 1024, 1),
    "psnr_jpg_db": round(float(psnr_jpg), 2),
    "dif_max_png": dif_png,
}
res["razon_png_jpg"] = round(res["png_kb"] / res["jpg_q90_kb"], 2)
(DIR_RES / "formatos.json").write_text(json.dumps(res, indent=2))
print(res)
