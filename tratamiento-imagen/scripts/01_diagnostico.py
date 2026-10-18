"""Diagnóstico de las cinco imágenes: métricas, tabla comparativa y figuras.

Uso:  python scripts/01_diagnostico.py
Salidas (carpeta resultados/): metricas.csv, metricas.json,
fig_conjunto.png, fig_histogramas.png, fig_nitidez_roi.png
"""
import json
import os

import cv2
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from config import ANCHO_COMUN, DIR_IMG, DIR_RES, ETIQUETAS, NOMBRES, ROI

plt.rcParams["font.family"] = ["Liberation Serif", "Times New Roman", "serif"]


def nitidez(gris):
    """Varianza del Laplaciano: más alta = más bordes definidos."""
    return float(cv2.Laplacian(gris, cv2.CV_64F).var())


def ruido_immerkaer(gris):
    """Estimación del ruido (sigma) con el método de Immerkaer (1996)."""
    h, w = gris.shape
    nucleo = np.array([[1, -2, 1], [-2, 4, -2], [1, -2, 1]], dtype=np.float64)
    conv = cv2.filter2D(gris.astype(np.float64), -1, nucleo)[1:-1, 1:-1]
    return float(np.sqrt(np.pi / 2) * np.abs(conv).sum() / (6.0 * (w - 2) * (h - 2)))


def recorte(img, caja):
    x0, y0, x1, y1 = caja
    return img[y0:y1, x0:x1]


def a_ancho_comun(gris):
    """Reescala a un ancho común (INTER_AREA) para que la nitidez sea comparable."""
    h, w = gris.shape
    if w == ANCHO_COMUN:
        return gris
    return cv2.resize(gris, (ANCHO_COMUN, round(h * ANCHO_COMUN / w)), interpolation=cv2.INTER_AREA)


def metricas(ruta, caja):
    img = cv2.imread(str(ruta))
    alto, ancho, canales = img.shape
    gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    g_norm = a_ancho_comun(gris)
    esc = ANCHO_COMUN / ancho
    caja_n = tuple(int(round(v * esc)) for v in caja)
    roi = recorte(g_norm, caja_n)
    return {
        "ancho": ancho,
        "alto": alto,
        "canales": canales,
        "megapixeles": round(ancho * alto / 1e6, 2),
        "tamano_kb": round(os.path.getsize(ruta) / 1024, 1),
        "brillo": round(float(gris.mean()), 2),
        "contraste": round(float(gris.std()), 2),
        "nitidez_global": round(nitidez(gris), 2),
        "nitidez_global_norm": round(nitidez(g_norm), 2),
        "nitidez_roi": round(nitidez(roi), 2),
        "brillo_roi": round(float(roi.mean()), 2),
        "p1": float(np.percentile(gris, 1)),
        "p99": float(np.percentile(gris, 99)),
        "rango_dinamico": float(np.percentile(gris, 99) - np.percentile(gris, 1)),
        "pct_pixeles_oscuros": round(float((gris < 50).mean() * 100), 1),
        "ruido": round(ruido_immerkaer(g_norm), 3),
    }


def main():
    res, imgs = {}, {}
    for n in NOMBRES:
        ruta = DIR_IMG / f"{n}.jpg"
        res[n] = metricas(ruta, ROI[n])
        imgs[n] = cv2.cvtColor(cv2.imread(str(ruta)), cv2.COLOR_BGR2RGB)
        print(n, res[n])

    (DIR_RES / "metricas.json").write_text(json.dumps(res, indent=2, ensure_ascii=False))
    with open(DIR_RES / "metricas.csv", "w", encoding="utf-8") as f:
        cols = list(res[NOMBRES[0]].keys())
        f.write("imagen," + ",".join(cols) + "\n")
        for n in NOMBRES:
            f.write(n + "," + ",".join(str(res[n][c]) for c in cols) + "\n")

    # Figura 1: conjunto de las cinco imágenes
    fig, ax = plt.subplots(2, 3, figsize=(10, 5.6))
    for a, n in zip(ax.ravel(), NOMBRES):
        a.imshow(imgs[n])
        a.set_title(f"{ETIQUETAS[n]} ({n}.jpg)", fontsize=13)
        a.axis("off")
    ax.ravel()[-1].axis("off")
    plt.tight_layout()
    plt.savefig(DIR_RES / "fig_conjunto.png", dpi=170)
    plt.close()

    # Figura 2: histogramas de gris de las cinco imágenes
    fig, ax = plt.subplots(2, 3, figsize=(10, 5.6), sharey=False)
    for a, n in zip(ax.ravel(), NOMBRES):
        g = cv2.cvtColor(imgs[n], cv2.COLOR_RGB2GRAY)
        a.hist(g.ravel(), bins=64, range=(0, 255), color="0.25")
        a.axvline(g.mean(), color="k", ls="--", lw=1)
        a.set_title(f"{ETIQUETAS[n]}  (media = {g.mean():.0f})", fontsize=13)
        a.set_xlim(0, 255)
        a.set_xlabel("Intensidad (0-255)", fontsize=12)
        a.set_ylabel("Píxeles", fontsize=12)
    ax.ravel()[-1].axis("off")
    plt.tight_layout()
    plt.savefig(DIR_RES / "fig_histogramas.png", dpi=170)
    plt.close()

    # Figura 3: recorte de la figura en referencia vs desenfocada + mapa del Laplaciano
    fig, ax = plt.subplots(2, 2, figsize=(8, 7.2))
    for j, n in enumerate(["referencia", "desenfocada"]):
        im = imgs[n]
        esc = ANCHO_COMUN / im.shape[1]
        im_n = cv2.resize(im, (ANCHO_COMUN, round(im.shape[0] * esc)), interpolation=cv2.INTER_AREA)
        caja_n = tuple(int(round(v * esc)) for v in ROI[n])
        rec = recorte(im_n, caja_n)
        lap = np.abs(cv2.Laplacian(cv2.cvtColor(rec, cv2.COLOR_RGB2GRAY), cv2.CV_64F))
        ax[0, j].imshow(rec)
        ax[0, j].set_title(f"{ETIQUETAS[n]}: recorte de la figura", fontsize=13)
        ax[1, j].imshow(np.clip(lap * 4, 0, 255), cmap="gray", vmin=0, vmax=255)
        ax[1, j].set_title(f"|Laplaciano|  (varianza = {res[n]['nitidez_roi']:.0f})", fontsize=13)
        for k in (0, 1):
            ax[k, j].axis("off")
    plt.tight_layout()
    plt.savefig(DIR_RES / "fig_nitidez_roi.png", dpi=170)
    plt.close()


if __name__ == "__main__":
    main()
