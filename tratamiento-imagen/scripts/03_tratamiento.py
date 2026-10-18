"""Tratamiento de la imagen problemática (oscura.jpg) y evaluación antes/después.

Problema identificado: subexposición (brillo bajo, histograma comprimido hacia 0).
Tratamiento elegido: corrección gamma sobre el canal V (HSV), con gamma calculada
para llevar el brillo medio a un valor objetivo. Se comparan, solo como contraste
de la decisión, otras tres alternativas habituales para subexposición.

Uso:  python scripts/03_tratamiento.py
Salidas: resultados/oscura_tratada.png, resultados/alternativas.png,
         resultados/fig_antes_despues.png, resultados/fig_hist_tratamiento.png,
         resultados/tratamiento.json
"""
import json

import cv2
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from config import DIR_IMG, DIR_RES, ROI

plt.rcParams["font.family"] = ["Liberation Serif", "serif"]

BRILLO_OBJETIVO = 110  # media de gris deseada (la referencia tiene ~157; 110 evita sobreexponer)


def nitidez(gris):
    return float(cv2.Laplacian(gris, cv2.CV_64F).var())


def ruido_immerkaer(gris):
    h, w = gris.shape
    nucleo = np.array([[1, -2, 1], [-2, 4, -2], [1, -2, 1]], dtype=np.float64)
    conv = cv2.filter2D(gris.astype(np.float64), -1, nucleo)[1:-1, 1:-1]
    return float(np.sqrt(np.pi / 2) * np.abs(conv).sum() / (6.0 * (w - 2) * (h - 2)))


def medir(bgr, caja):
    gris = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    x0, y0, x1, y1 = caja
    roi = gris[y0:y1, x0:x1]
    return {
        "ancho": bgr.shape[1],
        "alto": bgr.shape[0],
        "brillo": round(float(gris.mean()), 2),
        "contraste": round(float(gris.std()), 2),
        "nitidez": round(nitidez(gris), 2),
        "nitidez_roi": round(nitidez(roi), 2),
        "brillo_roi": round(float(roi.mean()), 2),
        "contraste_roi": round(float(roi.std()), 2),
        "rango_dinamico": float(np.percentile(gris, 99) - np.percentile(gris, 1)),
        "pct_oscuros": round(float((gris < 50).mean() * 100), 1),
        "pct_saturados": round(float((gris > 250).mean() * 100), 2),
        "ruido": round(ruido_immerkaer(gris), 3),
    }


def gamma_v(bgr, gamma):
    """Corrección gamma solo sobre el canal V para no alterar el tono (H) ni la saturación (S)."""
    lut = np.array([255 * (i / 255.0) ** gamma for i in range(256)]).clip(0, 255).astype(np.uint8)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    hsv[:, :, 2] = cv2.LUT(hsv[:, :, 2], lut)
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)


def gamma_para_objetivo(bgr, objetivo):
    """Calcula gamma tal que (media/255)^gamma = objetivo/255 (aproximación de primer orden)."""
    media = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY).mean()
    return float(np.log(objetivo / 255.0) / np.log(media / 255.0))


def lineal(bgr):
    """Alternativa 1: ajuste lineal alpha*x + beta (el ejemplo de la guía)."""
    return cv2.convertScaleAbs(bgr, alpha=2.0, beta=40)


def ecualizar_v(bgr):
    """Alternativa 2: ecualización global del histograma sobre el canal V."""
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    hsv[:, :, 2] = cv2.equalizeHist(hsv[:, :, 2])
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)


def clahe_l(bgr):
    """Alternativa 3: CLAHE sobre el canal L de LAB."""
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    lab[:, :, 0] = clahe.apply(lab[:, :, 0])
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)


def main():
    original = cv2.imread(str(DIR_IMG / "oscura.jpg"))
    caja = ROI["oscura"]

    gamma = gamma_para_objetivo(original, BRILLO_OBJETIVO)
    tratada = gamma_v(original, gamma)
    cv2.imwrite(str(DIR_RES / "oscura_tratada.png"), tratada)

    candidatas = {
        "Original": original,
        f"Gamma {gamma:.2f} (elegida)": tratada,
        "Lineal (a=2, b=40)": lineal(original),
        "Ecualización (V)": ecualizar_v(original),
        "CLAHE (L)": clahe_l(original),
    }
    res = {"gamma": round(gamma, 3), "objetivo": BRILLO_OBJETIVO, "metricas": {}}
    for nombre, im in candidatas.items():
        res["metricas"][nombre] = medir(im, caja)
        print(nombre, res["metricas"][nombre])
    (DIR_RES / "tratamiento.json").write_text(json.dumps(res, indent=2, ensure_ascii=False))

    # Figura: antes vs después (imagen completa + recorte de la figura)
    x0, y0, x1, y1 = caja
    fig, ax = plt.subplots(2, 2, figsize=(9, 7.4), gridspec_kw={"height_ratios": [1, 1.5]})
    for j, (t, im) in enumerate([("Antes (oscura.jpg)", original), (f"Después (gamma = {gamma:.2f})", tratada)]):
        rgb = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
        ax[0, j].imshow(rgb)
        ax[0, j].set_title(t, fontsize=13)
        ax[0, j].axis("off")
        ax[1, j].imshow(rgb[y0:y1, x0:x1])
        ax[1, j].set_title("Detalle de la figura", fontsize=13)
        ax[1, j].axis("off")
    plt.tight_layout()
    plt.savefig(DIR_RES / "fig_antes_despues.png", dpi=170)
    plt.close()

    # Figura: histogramas antes/después + referencia
    ref = cv2.imread(str(DIR_IMG / "referencia.jpg"))
    fig, ax = plt.subplots(1, 3, figsize=(10, 3.2), sharey=True)
    for a, (t, im) in zip(ax, [("Oscura (antes)", original), ("Oscura tratada (después)", tratada), ("Referencia", ref)]):
        g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
        a.hist(g.ravel(), bins=64, range=(0, 255), color="0.25")
        a.axvline(g.mean(), color="k", ls="--", lw=1)
        a.set_title(f"{t}\nmedia = {g.mean():.0f}, desv. = {g.std():.0f}", fontsize=13)
        a.set_xlim(0, 255)
        a.set_xlabel("Intensidad (0-255)", fontsize=12)
    ax[0].set_ylabel("Píxeles", fontsize=12)
    plt.tight_layout()
    plt.savefig(DIR_RES / "fig_hist_tratamiento.png", dpi=170)
    plt.close()

    # Figura: alternativas, solo para justificar la decisión
    fig, ax = plt.subplots(1, 4, figsize=(12, 2.9))
    for a, nombre in zip(ax, list(candidatas)[1:]):
        im = candidatas[nombre]
        a.imshow(cv2.cvtColor(im, cv2.COLOR_BGR2RGB)[y0 - 100 : y1, x0 - 150 : x1 + 150])
        a.set_title(nombre, fontsize=14)
        a.axis("off")
    plt.tight_layout()
    plt.savefig(DIR_RES / "alternativas.png", dpi=170)
    plt.close()


if __name__ == "__main__":
    main()
