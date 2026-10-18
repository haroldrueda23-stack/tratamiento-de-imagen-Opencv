"""Construye el informe PDF (APA 7, Times 12 pt, interlineado doble) con los resultados reales.

Uso:  python informe/construir_informe.py
Lee: resultados/*.json y *.png. Datos de portada: informe/datos_portada.json
Salida: informe/Informe_tratamiento_de_imagen.pdf
"""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, Preformatted,
                                SimpleDocTemplate, Spacer, Table, TableStyle)

RAIZ = Path(__file__).resolve().parent.parent
RES = RAIZ / "resultados"
OUT = RAIZ / "informe" / "Informe_tratamiento_de_imagen.pdf"

FD = "/usr/share/fonts/truetype/liberation/"
pdfmetrics.registerFont(TTFont("Serif", FD + "LiberationSerif-Regular.ttf"))
pdfmetrics.registerFont(TTFont("Serif-B", FD + "LiberationSerif-Bold.ttf"))
pdfmetrics.registerFont(TTFont("Serif-I", FD + "LiberationSerif-Italic.ttf"))
pdfmetrics.registerFont(TTFont("Serif-BI", FD + "LiberationSerif-BoldItalic.ttf"))
pdfmetrics.registerFont(TTFont("Mono", FD + "LiberationMono-Regular.ttf"))
pdfmetrics.registerFontFamily("Serif", normal="Serif", bold="Serif-B", italic="Serif-I", boldItalic="Serif-BI")

# ------------------------------------------------------------------ datos
datos_portada = {
    "titulo": "Informe de resultados de tratamiento de imagen",
    "estudiante": "Harold Steven Rueda Lara",
    "programa": "Especialización en Inteligencia Artificial",
    "curso": "Percepción Computacional",
    "cadi": "[CADI]",
    "profesor": "[Nombre del profesor]",
    "fecha": "18 de octubre de 2026",
    "github": "[Enlace al repositorio de GitHub]",
}
p_datos = RAIZ / "informe" / "datos_portada.json"
if p_datos.exists():
    datos_portada.update(json.loads(p_datos.read_text(encoding="utf-8")))
else:
    p_datos.write_text(json.dumps(datos_portada, indent=2, ensure_ascii=False), encoding="utf-8")

M = json.loads((RES / "metricas.json").read_text())
T = json.loads((RES / "tratamiento.json").read_text())
F = json.loads((RES / "formatos.json").read_text())

ETQ = {"referencia": "Referencia", "oscura": "Baja iluminación", "desenfocada": "Desenfocada",
       "fondo": "Fondo complejo", "angulo": "Otra perspectiva"}
ORDEN = ["referencia", "oscura", "desenfocada", "fondo", "angulo"]
ROI = {"referencia": (660, 10, 1350, 1480), "oscura": (760, 340, 1440, 1320),
       "desenfocada": (40, 570, 600, 1430), "fondo": (700, 460, 1075, 1040),
       "angulo": (925, 410, 1490, 1440)}


def n(v, d=1):
    """Formato numérico en español: coma decimal y punto de miles."""
    s = f"{v:,.{d}f}"
    return s.replace(",", "§").replace(".", ",").replace("§", ".")


def frac_roi(k):
    x0, y0, x1, y1 = ROI[k]
    return 100 * (x1 - x0) * (y1 - y0) / (M[k]["ancho"] * M[k]["alto"])


# ------------------------------------------------------------------ estilos
BASE = dict(fontName="Serif", fontSize=12, leading=24, alignment=TA_LEFT)
cuerpo = ParagraphStyle("cuerpo", firstLineIndent=0.5 * inch, **BASE)
sinsangria = ParagraphStyle("sin", **BASE)
h1 = ParagraphStyle("h1", **{**BASE, "fontName": "Serif-B", "alignment": TA_CENTER})
h2 = ParagraphStyle("h2", **{**BASE, "fontName": "Serif-B"})
h3 = ParagraphStyle("h3", **{**BASE, "fontName": "Serif-BI"})
tit_portada = ParagraphStyle("tp", **{**BASE, "fontName": "Serif-B", "alignment": TA_CENTER})
centro = ParagraphStyle("c", **{**BASE, "alignment": TA_CENTER})
rotulo = ParagraphStyle("rot", **{**BASE, "fontName": "Serif-B", "leading": 16, "spaceBefore": 8})
rotulo_t = ParagraphStyle("rott", **{**BASE, "fontName": "Serif-I", "leading": 16, "spaceAfter": 6})
nota = ParagraphStyle("nota", **{**BASE, "fontSize": 10, "leading": 13, "spaceBefore": 4, "spaceAfter": 10})
celda = ParagraphStyle("celda", **{**BASE, "fontSize": 9.5, "leading": 11.5})
celda_c = ParagraphStyle("celdac", **{**BASE, "fontSize": 9.5, "leading": 11.5, "alignment": TA_CENTER})
celda_h = ParagraphStyle("celdah", **{**BASE, "fontSize": 9.5, "leading": 11.5, "fontName": "Serif-B", "alignment": TA_CENTER})
codigo = ParagraphStyle("cod", fontName="Mono", fontSize=8.4, leading=10.5, leftIndent=6, rightIndent=6,
                        borderColor="black", borderWidth=0.5, borderPadding=6, spaceBefore=6, spaceAfter=14)

S = []  # historia (flowables)
contador = {"tabla": 0, "figura": 0}


def P(t, estilo=cuerpo):
    S.append(Paragraph(t, estilo))


def H1(t):
    S.append(Paragraph(t, h1))


def H2(t):
    S.append(Paragraph(t, h2))


def SEC(t):
    S.append(Paragraph(t, h1))


def SUB(t):
    S.append(Paragraph(t, h2))


def H3(t):
    S.append(Paragraph(t, h3))


def tabla_apa(titulo, filas, anchos, pie=None, alin_izq=(0,)):
    contador["tabla"] += 1
    k = contador["tabla"]
    datos = []
    for i, fila in enumerate(filas):
        datos.append([Paragraph(str(c), celda_h if i == 0 else (celda if j in alin_izq else celda_c))
                      for j, c in enumerate(fila)])
    t = Table(datos, colWidths=[a * inch for a in anchos], repeatRows=1)
    t.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), 1, "black"), ("LINEBELOW", (0, 0), (-1, 0), 0.75, "black"),
        ("LINEBELOW", (0, -1), (-1, -1), 1, "black"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    bloque = [Paragraph(f"Tabla {k}", rotulo), Paragraph(titulo, rotulo_t), t]
    if pie:
        bloque.append(Paragraph(pie, nota))
    else:
        bloque.append(Spacer(1, 14))
    S.append(KeepTogether(bloque))
    return k


def figura(titulo, archivo, ancho_in, pie=None):
    contador["figura"] += 1
    k = contador["figura"]
    from PIL import Image as PI
    w, h = PI.open(archivo).size
    img = Image(str(archivo), width=ancho_in * inch, height=ancho_in * inch * h / w)
    bloque = [Paragraph(f"Figura {k}", rotulo), Paragraph(titulo, rotulo_t), img]
    bloque.append(Paragraph(pie, nota) if pie else Spacer(1, 14))
    S.append(KeepTogether(bloque))
    return k


def codigo_bloque(txt):
    S.append(Preformatted(txt.strip("\n"), codigo))


# ------------------------------------------------------------------ figura del diseño
def diagrama_flujo(ruta):
    fig, ax = plt.subplots(figsize=(9, 3.9))
    ax.set_xlim(0, 9)
    ax.set_ylim(0, 3.9)
    ax.axis("off")
    plt.rcParams["font.family"] = ["Liberation Serif", "serif"]
    cajas = {
        1: (0.15, 2.1, "1. Captura\ncinco fotos del mismo objeto\n(condiciones distintas)"),
        2: (3.15, 2.1, "2. Diagnóstico\nbrillo, contraste, nitidez,\nresolución, histograma"),
        3: (6.15, 2.1, "3. Problema\nsubexposición\n(oscura.jpg)"),
        4: (6.15, 0.2, "4. Decisión técnica\ngamma sobre el canal V\n(sin alterar el tono)"),
        5: (3.15, 0.2, "5. Tratamiento\n03_tratamiento.py"),
        6: (0.15, 0.2, "6. Evaluación\nmétricas antes/después\n+ evidencia visual"),
    }
    for k, (x, y, t) in cajas.items():
        ax.add_patch(FancyBboxPatch((x, y), 2.7, 1.2, boxstyle="round,pad=0.03", fc="white", ec="black", lw=1.2))
        ax.text(x + 1.35, y + 0.6, t, ha="center", va="center", fontsize=13)
    fl = dict(arrowstyle="-|>", lw=1.3, color="black")
    ax.annotate("", xy=(3.12, 2.7), xytext=(2.88, 2.7), arrowprops=fl)
    ax.annotate("", xy=(6.12, 2.7), xytext=(5.88, 2.7), arrowprops=fl)
    ax.annotate("", xy=(7.5, 1.43), xytext=(7.5, 2.07), arrowprops=fl)
    ax.annotate("", xy=(5.88, 0.8), xytext=(6.12, 0.8), arrowprops=fl)
    ax.annotate("", xy=(2.88, 0.8), xytext=(3.12, 0.8), arrowprops=fl)
    plt.tight_layout()
    plt.savefig(ruta, dpi=170)
    plt.close()


diagrama_flujo(RES / "fig_diseno.png")

# ------------------------------------------------------------------ valores clave
ref, osc, des, fon, ang = (M[k] for k in ORDEN)
tm = T["metricas"]
k_orig = "Original"
k_gam = [k for k in tm if k.startswith("Gamma")][0]
k_lin, k_eq, k_cl = "Lineal (a=2, b=40)", "Ecualización (V)", "CLAHE (L)"
a, d = tm[k_orig], tm[k_gam]

# ================================================================== PORTADA
S.append(Spacer(1, 1.6 * inch))
S.append(Paragraph(datos_portada["titulo"], tit_portada))
S.append(Spacer(1, 0.4 * inch))
for linea in [datos_portada["estudiante"], datos_portada["programa"],
              f"{datos_portada['curso']} (Semana 8, actividad R2-A2-S8)",
              f"CADI: {datos_portada['cadi']}", f"Profesor: {datos_portada['profesor']}",
              datos_portada["fecha"]]:
    S.append(Paragraph(linea, centro))
S.append(PageBreak())

# ================================================================== 2. DESCRIPCIÓN DEL PROBLEMA
H1("Informe de resultados de tratamiento de imagen")
SEC("Descripción del problema")
P("Una organización hipotética recopila fotografías para construir un sistema que reconozca objetos. "
  "Antes de entrenar un modelo es necesario saber si las imágenes capturadas son adecuadas o si presentan "
  "problemas que puedan afectar el análisis. Este informe responde a esa pregunta con un conjunto pequeño de "
  "imágenes propias: se diagnostican con OpenCV, se selecciona la que presenta un problema evidente y se "
  "aplica un tratamiento justificado cuyo efecto se verifica con métricas y con evidencia visual.")
SUB("Objeto y condiciones de captura")
P("El objeto seleccionado es una figura coleccionable pequeña (un personaje de anime con traje azul y blanco) "
  "montada sobre una base circular roja translúcida. Es adecuado para el ejercicio porque combina zonas muy "
  "oscuras (cabello), muy claras (guantes y botas), colores saturados (base roja, detalles amarillos) y "
  "superficies con brillo especular. Se capturaron cinco fotografías propias, sin edición previa. Los archivos "
  "entregados no conservan metadatos EXIF, de modo que el dispositivo exacto no puede documentarse a partir "
  "de ellos; las condiciones se describen a partir de lo observado en cada imagen (Tabla 1).")
contador_fig = 0
tabla_apa("Registro de captura de las cinco imágenes", [
    ["Archivo", "Condición", "Observación de la toma"],
    ["referencia.jpg", "Referencia", "Buena iluminación, figura enfocada y centrada, fondo limpio (pared texturizada y mesa de madera)."],
    ["oscura.jpg", "Baja iluminación", "Misma escena con poca luz. La figura aparece más lejos y más pequeña en el encuadre que en la referencia."],
    ["desenfocada.jpg", "Desenfoque o movimiento", "Figura y mesa con pérdida visible de nitidez. Cámara más baja y cerca de la mesa, figura a la izquierda y base de un monitor a la derecha."],
    ["fondo.jpg", "Fondo complejo", "Figura nítida rodeada de una báscula, un peluche, una tela estampada y un cojín de pelo; cámara baja y figura en diagonal."],
    ["angulo.jpg", "Otra perspectiva", "Vista lateral (perfil) y desde más arriba, con buena luz, buen enfoque y fondo limpio."],
], [1.2, 1.3, 4.0], alin_izq=(0, 1, 2))
P("Importa señalar desde ahora una limitación del conjunto: aunque cada fotografía debía cambiar una sola "
  "condición, en la práctica cambiaron también la distancia o el encuadre (la figura ocupa entre el "
  f"{n(frac_roi('fondo'), 0)} % y el {n(frac_roi('referencia'), 0)} % del cuadro según la imagen) y la resolución de la "
  f"fotografía desenfocada, que es mayor ({des['ancho']} × {des['alto']} px frente a {ref['ancho']} × {ref['alto']} px). "
  "Estas diferencias se tienen en cuenta al interpretar las métricas.", cuerpo)

# ================================================================== 3. DIAGNÓSTICO
SEC("Diagnóstico")
figura("Conjunto de imágenes capturadas", RES / "fig_conjunto.png", 6.3,
       "Nota. Las cinco fotografías sin edición, tal como se cargaron en OpenCV.")
SUB("Métricas utilizadas")
P("Todas las imágenes se leyeron con <font name='Mono'>cv2.imread</font> (orden de canales BGR, 3 canales, 8 bits por canal) "
  "y se convirtieron a escala de grises. Se calcularon las cuatro métricas de la guía y otras tres que se "
  "justifican a continuación:")
codigo_bloque("""
gris      = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
brillo    = gris.mean()                          # luminosidad media (0-255)
contraste = gris.std()                           # dispersión de intensidades
nitidez   = cv2.Laplacian(gris, cv2.CV_64F).var()   # respuesta de bordes
""")
P("El <i>brillo</i> (media de gris) indica la exposición global. El <i>contraste</i> (desviación estándar) "
  "aproxima la separación entre zonas claras y oscuras. La <i>nitidez</i> (varianza del Laplaciano) crece cuando "
  "hay bordes bien definidos. Como la nitidez depende de la escala de la imagen, también se calculó sobre las "
  f"imágenes reescaladas a un mismo ancho ({ref['ancho']} px). Las métricas añadidas son: el <i>rango dinámico</i> "
  "(percentil 99 menos percentil 1), útil para saber cuánta escala tonal se usa realmente; el porcentaje de píxeles "
  "oscuros (intensidad menor que 50), que cuantifica la subexposición; y una estimación del <i>ruido</i> "
  "(método de Immerkaer), pertinente porque aclarar una imagen oscura tiende a amplificarlo. Además se midió la "
  "nitidez dentro de una <i>región de interés</i> (ROI) rectangular alrededor de la figura, por una razón que "
  "se aclara en el análisis: la medida global puede estar dominada por el fondo.")
codigo_bloque("""
g_norm = cv2.resize(gris, (2016, round(alto * 2016 / ancho)), interpolation=cv2.INTER_AREA)
x0, y0, x1, y1 = ROI[nombre]                  # caja alrededor de la figura (escalada)
nitidez_roi = cv2.Laplacian(g_norm[y0:y1, x0:x1], cv2.CV_64F).var()
""")

adec = {"referencia": "Sí", "oscura": "No", "desenfocada": "No", "fondo": "Parcial", "angulo": "Sí*"}
prob = {"referencia": "Ninguno relevante",
        "oscura": "Subexposición: brillo y contraste muy bajos",
        "desenfocada": "Pérdida de nitidez en la figura",
        "fondo": "Fondo que compite con el objeto; figura pequeña y en sombra",
        "angulo": "Solo cambio de punto de vista"}
filas = [["Imagen", "Brillo", "Contraste", "Nitidez", "Resolución (px)", "Problema", "¿Adecuada?"]]
for k in ORDEN:
    m = M[k]
    filas.append([ETQ[k], n(m["brillo"]), n(m["contraste"]), n(m["nitidez_global"]),
                  f"{m['ancho']} × {m['alto']}<br/>({n(m['megapixeles'], 2)} MP)", prob[k], adec[k]])
tabla_apa("Comparación de las cinco imágenes con las métricas de la guía", filas,
          [1.15, 0.6, 0.75, 0.7, 1.0, 1.7, 0.7], alin_izq=(0, 5),
          pie="Nota. Brillo y contraste en escala 0-255; nitidez = varianza del Laplaciano sobre la imagen completa. "
              "*Adecuada como vista lateral; ver la interpretación de los datos.")
tabla_apa("Métricas ampliadas del diagnóstico", [
    ["Imagen", "Nitidez global (reescalada)", "Nitidez en ROI", "Brillo en ROI", "Rango dinámico", "Píxeles &lt; 50 (%)", "Ruido (σ)", "Figura en el cuadro (%)"]
] + [[ETQ[k], n(M[k]["nitidez_global_norm"]), n(M[k]["nitidez_roi"]), n(M[k]["brillo_roi"]),
      n(M[k]["rango_dinamico"], 0), n(M[k]["pct_pixeles_oscuros"]), n(M[k]["ruido"], 2), n(frac_roi(k))] for k in ORDEN],
    [1.15, 0.85, 0.7, 0.7, 0.75, 0.75, 0.6, 0.8],
    pie="Nota. ROI = rectángulo alrededor de la figura y su base. El rango dinámico es la diferencia entre los percentiles 99 y 1 "
        "de la escala de grises. La estimación de ruido se inflará en imágenes con mucha textura (pared, pelo).")

SUB("Interpretación de los datos básicos")
P(f"Cuatro imágenes tienen {ref['ancho']} × {ref['alto']} píxeles ({n(ref['megapixeles'], 2)} MP, proporción 4:3) y la desenfocada "
  f"{des['ancho']} × {des['alto']} ({n(des['megapixeles'], 2)} MP), con la misma proporción. Que la resolución no sea idéntica es un "
  "dato relevante para un conjunto de entrenamiento: obligaría a un redimensionamiento uniforme antes de alimentar un modelo. Todas "
  "tienen 3 canales, es decir, conservan color.")
P(f"La imagen oscura es la más afectada en las tres métricas: su brillo es {n(osc['brillo'])} frente a {n(ref['brillo'])} de la referencia "
  f"({n(100*(1-osc['brillo']/ref['brillo']), 0)} % menos), su contraste cae a {n(osc['contraste'])} y su nitidez a {n(osc['nitidez_global'])}. El histograma "
  f"(Figura 2) lo confirma: casi todos los píxeles quedan agrupados cerca de cero ({n(osc['pct_pixeles_oscuros'])} % por debajo de 50) y el rango "
  f"dinámico es de solo {n(osc['rango_dinamico'], 0)} niveles frente a {n(ref['rango_dinamico'], 0)} en la referencia. Sin embargo, el percentil 1 está en {n(osc['p1'], 0)} y el 99 en {n(osc['p99'], 0)}: "
  "la información está comprimida en un rango estrecho, pero no recortada en cero, lo que indica que es recuperable.")
P(f"En la desenfocada, la nitidez global ({n(des['nitidez_global'])}) es prácticamente igual a la de la referencia ({n(ref['nitidez_global'])}), "
  f"pese a que la figura está claramente borrosa. Al medir solo en la ROI la nitidez baja a {n(des['nitidez_roi'])} frente a {n(ref['nitidez_roi'])} "
  f"({n(100*(1-des['nitidez_roi']/ref['nitidez_roi']), 0)} % menos), lo que sí refleja el problema (Figura 3). El fondo (pared texturizada y monitor), que está "
  "enfocado, domina la medida global.")
P(f"En el fondo complejo ocurre lo contrario: la figura está nítida, pero la ROI registra una nitidez muy alta ({n(fon['nitidez_roi'])}) porque el cojín de pelo y "
  f"la tela estampada aportan muchos bordes. La métrica no mide si el objeto está enfocado, sino cuánto contenido de alta frecuencia hay. Además la figura "
  f"ocupa solo el {n(frac_roi('fondo'))} % del cuadro y su brillo en la ROI ({n(fon['brillo_roi'])}) es mucho menor que el global ({n(fon['brillo'])}), "
  "porque el cuadro incluye zonas muy iluminadas (pared y ventana al fondo) mientras la figura queda bajo la báscula, en sombra. Por eso se la califica como adecuada solo en forma parcial.")
P(f"La imagen de otra perspectiva tiene la nitidez global más alta ({n(ang['nitidez_global'])}, unas tres veces la de la referencia) sin estar «mejor enfocada» "
  "que ella: la pared texturizada ocupa gran parte del cuadro y su relieve genera muchos bordes. Es una imagen sin defectos de captura, "
  "pero muestra la figura de perfil, un punto de vista distinto que un modelo debería ver durante el entrenamiento y no como defecto.")

figura("Histogramas de escala de grises de las cinco imágenes", RES / "fig_histogramas.png", 6.3,
       "Nota. La línea punteada marca la media de cada imagen.")
figura("Nitidez de la figura: referencia frente a desenfocada", RES / "fig_nitidez_roi.png", 5.0,
       "Nota. Arriba, recorte de la figura; abajo, valor absoluto del Laplaciano (ampliado cuatro veces para visualizarlo). "
       "Los bordes aparecen como líneas claras en la referencia y casi desaparecen en la desenfocada.")

SUB("Formato y tamaño de archivo")
P(f"Se tomó la imagen de referencia y se guardó en JPG (calidad 90) y en PNG con <font name='Mono'>cv2.imwrite</font>. Ambas conservan la misma resolución "
  f"({F['resolucion'][0]} × {F['resolucion'][1]} px).")
codigo_bloque("""
cv2.imwrite('comparacion.jpg', imagen, [cv2.IMWRITE_JPEG_QUALITY, 90])
cv2.imwrite('comparacion.png', imagen)
""")
tabla_apa("Comparación de formatos para la imagen de referencia", [
    ["Formato", "Resolución", "Tamaño de archivo", "Observación"],
    ["JPG (calidad 90)", f"{F['resolucion'][0]} × {F['resolucion'][1]}", f"{n(F['jpg_q90_kb'])} KB",
     f"Compresión con pérdida; PSNR de {n(F['psnr_jpg_db'], 1)} dB respecto a los píxeles de partida, sin diferencias perceptibles."],
    ["PNG", f"{F['resolucion'][0]} × {F['resolucion'][1]}", f"{n(F['png_kb'])} KB",
     f"Compresión sin pérdida; diferencia máxima de píxel igual a {F['dif_max_png']}. Pesa {n(F['razon_png_jpg'], 1)} veces más que el JPG."],
], [1.3, 1.1, 1.2, 2.9], alin_izq=(0, 3),
    pie=f"Nota. El archivo original de la cámara pesaba {n(F['original_kb'])} KB.")
P("Dos archivos con la misma resolución pueden ocupar espacios muy diferentes porque la resolución solo dice cuántos píxeles hay, no cuántos bytes cuesta describirlos. "
  "JPG descarta información que el ojo percibe poco (submuestrea el color, cuantiza los coeficientes de una transformada de coseno por bloques) y por eso logra archivos "
  "pequeños; PNG guarda cada píxel exactamente, aplicando una compresión que no pierde nada, y en una fotografía con ruido y texturas el resultado es mucho mayor. "
  "Una precisión: guardar en PNG una foto que ya venía en JPG no recupera lo que la compresión original eliminó; solo evita pérdidas adicionales. "
  "Para un conjunto de entrenamiento, JPG a calidad alta suele bastar; PNG conviene cuando se encadenan varias ediciones o se trabajan máscaras.")

# ================================================================== 4. TRATAMIENTO
SEC("Tratamiento")
SUB("Diseño de la solución")
P("La solución sigue la lógica pedida por la actividad: partir de un problema identificado, tomar una decisión técnica y evaluar el resultado (Figura 4). "
  "El diagnóstico no se limita a mirar las imágenes; cada problema posible se asocia con una métrica que lo delata y con la intervención que corresponde (Tabla 5). "
  "La regla de decisión es que el tratamiento debe elegirse por el problema y no por el filtro disponible, y que algunos problemas no tienen tratamiento "
  "razonable y exigen volver a capturar.")
figura("Diseño de la solución", RES / "fig_diseno.png", 6.2)
tabla_apa("Reglas de decisión: del problema al tratamiento", [
    ["Problema", "Métrica que lo delata", "Tratamiento candidato", "¿Corregible por procesamiento?"],
    ["Subexposición", "Brillo y contraste bajos; muchos píxeles oscuros", "Gamma, ajuste lineal, ecualización", "Sí, si no hay recorte en cero"],
    ["Desenfoque fuerte", "Nitidez baja en la ROI", "Realce de bordes (limitado)", "No de forma fiable; conviene recapturar"],
    ["Fondo complejo", "Muchos bordes alrededor del objeto", "Recorte, segmentación", "Parcialmente; exige más que un filtro"],
    ["Otra perspectiva", "Ninguna (no es defecto)", "Ninguno", "No aplica; es variabilidad útil"],
    ["Resolución distinta", "Dimensiones diferentes", "Redimensionamiento", "Sí"],
], [1.2, 1.9, 1.7, 1.7], alin_izq=(0, 1, 2, 3))
SUB("Problema seleccionado y justificación")
P(f"Se eligió la imagen <i>oscura.jpg</i> porque es la que presenta el problema más evidente y mejor medido. La frase de trabajo que guía el tratamiento es: "
  f"<i>«La imagen presenta subexposición (brillo medio de {n(a['brillo'])} sobre 255, contraste de {n(a['contraste'])} y {n(a['pct_oscuros'])} % de los píxeles por debajo de 50). "
  "Aplicaré una corrección gamma sobre el canal de valor (V) del espacio HSV porque espero mejorar el brillo y el rango dinámico sin alterar el color ni saturar las zonas claras»</i>.")
P("Se descartó tratar la imagen desenfocada porque, con las herramientas básicas de la actividad, el desenfoque no se corrige de manera fiable: un realce de bordes "
  "solo amplificaría ruido sin recuperar detalle que la cámara no registró. La subexposición, en cambio, comprime la información en un rango estrecho "
  "pero no la elimina, de modo que una transformación de intensidades puede redistribuirla.")
P("¿Por qué gamma y no otra transformación? La función gamma es no lineal: con un exponente menor que 1 eleva mucho más las sombras que las luces, que es lo que necesita una imagen "
  f"cuyo percentil 99 está en {n(osc['p99'], 0)}. Se aplica solo al canal V para conservar el tono y la saturación. El exponente no se fijó a ojo: se calcula para que la media "
  "pase a un valor objetivo moderado (110), por debajo del brillo de la referencia, para no aclarar más de lo necesario y limitar la amplificación del ruido.")
codigo_bloque("""
def gamma_para_objetivo(bgr, objetivo):
    media = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY).mean()
    return np.log(objetivo / 255.0) / np.log(media / 255.0)   # (media/255)^gamma = objetivo/255

def gamma_v(bgr, gamma):
    lut = np.array([255 * (i / 255.0) ** gamma for i in range(256)]).clip(0, 255).astype(np.uint8)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    hsv[:, :, 2] = cv2.LUT(hsv[:, :, 2], lut)                 # solo el canal V
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

gamma    = gamma_para_objetivo(original, 110)    # = {g}
tratada  = gamma_v(original, gamma)
""".replace("{g}", n(T["gamma"], 3)))
P("Solo para contrastar la decisión se probaron tres alternativas habituales sobre la misma imagen: el ajuste lineal del ejemplo de la guía (<font name='Mono'>alpha</font> = 2, "
  "<font name='Mono'>beta</font> = 40), la ecualización global del histograma y CLAHE. Los resultados (Tabla 6, Figura 5) sustentan la elección.")
filas = [["Método", "Brillo", "Contraste", "Nitidez", "Ruido (σ)", "Píxeles &lt; 50 (%)"]]
for nombre in [k_orig, k_gam, k_lin, k_eq, k_cl]:
    m = tm[nombre]
    filas.append([nombre.replace(" (elegida)", " (elegida)"), n(m["brillo"]), n(m["contraste"]), n(m["nitidez"]), n(m["ruido"], 2), n(m["pct_oscuros"])])
tabla_apa("Comparación de alternativas para corregir la subexposición", filas, [2.0, 0.8, 0.9, 0.9, 0.9, 1.1],
          pie="Nota. Métricas sobre la imagen completa. Nitidez = varianza del Laplaciano.")
figura("Resultado visual de los cuatro métodos", RES / "alternativas.png", 6.4,
       "Nota. Recorte alrededor de la figura. De izquierda a derecha: gamma, lineal, ecualización y CLAHE.")
P(f"La ecualización lleva el brillo a {n(tm[k_eq]['brillo'])} y el contraste a {n(tm[k_eq]['contraste'])}, pero multiplica el ruido por {n(tm[k_eq]['ruido']/a['ruido'], 1)} y aplasta el cabello en negro; "
  f"es un resultado vistoso pero poco fiel. CLAHE no aclara lo suficiente (brillo de {n(tm[k_cl]['brillo'])}) y deja {n(tm[k_cl]['pct_oscuros'])} % de píxeles oscuros. El ajuste lineal y la gamma "
  f"logran brillos parecidos; la gamma amplifica algo menos el ruido ({n(tm[k_gam]['ruido'], 2)} frente a {n(tm[k_lin]['ruido'], 2)}) y se comporta de forma más suave en las sombras. "
  "La diferencia entre ambas es moderada, y se reconoce como tal: la elección de gamma se apoya en esa ventaja pequeña y en que su criterio (llevar la media a un objetivo) es explícito.")
SUB("Descripción de los scripts")
P("El código está organizado en cuatro archivos dentro de la carpeta <font name='Mono'>scripts</font> del repositorio. Todos se ejecutan desde la raíz del proyecto y escriben sus salidas en <font name='Mono'>resultados</font>.")
P("<font name='Mono'>config.py</font> concentra los parámetros compartidos: las rutas, el orden de las cinco condiciones, las etiquetas, el ancho común para reescalar (2016 px) y las ROI de cada imagen. "
  "Las ROI se definieron una sola vez, a mano, observando cada fotografía, y se verificaron superponiéndolas sobre las imágenes.")
P("<font name='Mono'>01_diagnostico.py</font> carga las cinco imágenes y, para cada una, calcula resolución, megapíxeles, tamaño de archivo, brillo, contraste, nitidez global (con y sin reescalar), "
  "nitidez y brillo en la ROI, percentiles 1 y 99, porcentaje de píxeles oscuros y ruido. Guarda la tabla en <font name='Mono'>metricas.csv</font> y <font name='Mono'>metricas.json</font> y genera las Figuras 1 a 3. "
  "Las funciones principales son <font name='Mono'>nitidez</font> (varianza del Laplaciano), <font name='Mono'>ruido_immerkaer</font> (convolución con un núcleo de segundas diferencias) y "
  "<font name='Mono'>a_ancho_comun</font> (reescala con <font name='Mono'>INTER_AREA</font>).")
P("<font name='Mono'>02_formatos.py</font> guarda la referencia como JPG (calidad 90) y PNG, compara tamaños y verifica que el PNG es idéntico píxel a píxel y que el JPG tiene un PSNR alto, lo que alimenta la Tabla 4.")
P("<font name='Mono'>03_tratamiento.py</font> implementa el tratamiento: calcula la gamma objetivo, aplica <font name='Mono'>gamma_v</font> a <i>oscura.jpg</i>, guarda <font name='Mono'>oscura_tratada.png</font>, "
  "repite las métricas sobre el resultado y sobre las tres alternativas (<font name='Mono'>lineal</font>, <font name='Mono'>ecualizar_v</font>, <font name='Mono'>clahe_l</font>) y genera las figuras de antes y después. "
  "Todo el repositorio puede reproducirse con <font name='Mono'>opencv-python</font>, <font name='Mono'>numpy</font> y <font name='Mono'>matplotlib</font>.")

# ================================================================== 5. RESULTADOS
SEC("Resultados")
P(f"La imagen tratada se obtuvo con un exponente gamma de {n(T['gamma'], 2)} (Figura 6). El cambio es visible en la imagen completa y en el detalle de la figura: aparecen el relieve del cabello, "
  "los pliegues del traje y la textura de la pared, que en la original eran casi indistinguibles. Para confirmar que la mejora es real y no solo aparente, se repitieron las métricas (Tabla 7).")
figura("Imagen oscura antes y después de la corrección gamma", RES / "fig_antes_despues.png", 5.6,
       f"Nota. Arriba, imagen completa; abajo, detalle de la figura. Gamma = {n(T['gamma'], 2)} aplicada al canal V.")
filas = [["Métrica", "Antes", "Después", "Interpretación"],
         ["Brillo", n(a["brillo"]), n(d["brillo"]), f"Multiplicado por {n(d['brillo']/a['brillo'], 1)}; todavía por debajo de la referencia ({n(ref['brillo'])})."],
         ["Contraste", n(a["contraste"]), n(d["contraste"]), f"Casi se duplica; sigue lejos de la referencia ({n(ref['contraste'])})."],
         ["Nitidez", n(a["nitidez"]), n(d["nitidez"]), "Sube, pero sobre todo por el mayor contraste; no hay enfoque nuevo."],
         ["Resolución", f"{a['ancho']} × {a['alto']}", f"{d['ancho']} × {d['alto']}", "Sin cambios (no se redimensionó)."],
         ["Rango dinámico", n(a["rango_dinamico"], 0), n(d["rango_dinamico"], 0), "La escala tonal usada casi se duplica."],
         ["Píxeles &lt; 50 (%)", n(a["pct_oscuros"]), n(d["pct_oscuros"]), "Desaparece casi toda la zona subexpuesta."],
         ["Ruido (σ)", n(a["ruido"], 2), n(d["ruido"], 2), f"Aumenta {n(100*(d['ruido']/a['ruido']-1), 0)} %: costo del aclarado."],
         ["Nitidez en ROI", n(a["nitidez_roi"]), n(d["nitidez_roi"]), "Los detalles de la figura se vuelven medibles."]]
tabla_apa("Evaluación antes y después del tratamiento", filas, [1.3, 0.9, 0.9, 3.4], alin_izq=(0, 3),
          pie="Nota. Brillo y contraste en escala 0-255; ruido estimado con el método de Immerkaer.")
figura("Histogramas antes y después del tratamiento, y referencia", RES / "fig_hist_tratamiento.png", 6.4,
       "Nota. La línea punteada es la media. El histograma tratado se desplaza y se abre; el de la referencia ocupa un rango mucho mayor.")
P(f"Los datos muestran que el tratamiento mejoró el problema que se decidió tratar. El brillo pasó de {n(a['brillo'])} a {n(d['brillo'])}, el porcentaje de píxeles oscuros bajó de {n(a['pct_oscuros'])} % a {n(d['pct_oscuros'])} %, "
  f"y el rango dinámico subió de {n(a['rango_dinamico'], 0)} a {n(d['rango_dinamico'], 0)} niveles. El histograma (Figura 7) pasó de estar pegado a cero a ocupar la zona media de la escala.")
P(f"Hay que leer el resultado con cautela. La imagen tratada no alcanza a la referencia (brillo de {n(d['brillo'])} frente a {n(ref['brillo'])}; contraste de {n(d['contraste'])} frente a {n(ref['contraste'])}). "
  f"El ruido estimado aumentó {n(100*(d['ruido']/a['ruido']-1), 0)} %, aunque el contraste creció {n(100*(d['contraste']/a['contraste']-1), 0)} %, de modo que la señal útil creció más que el ruido. "
  "Y el aumento de la nitidez (de "
  f"{n(a['nitidez'])} a {n(d['nitidez'])}) no significa que la imagen esté mejor enfocada: la varianza del Laplaciano depende del contraste, y la gamma lo aumentó. "
  "Ninguna transformación de intensidades crea detalle nuevo; solo hace visible el que existía.")

# ================================================================== 6. ANÁLISIS
SEC("Análisis")
H3("1. ¿Qué características de una imagen pueden afectar un sistema de percepción computacional?")
P(f"Las que se midieron aquí y otras relacionadas: la iluminación (brillo, contraste, rango dinámico), el enfoque, el ruido, la resolución y su coherencia dentro del conjunto, el tamaño del objeto en el encuadre "
  f"(entre {n(frac_roi('fondo'))} % y {n(frac_roi('referencia'))} % del cuadro en estas fotos), la complejidad del fondo, el punto de vista y el formato de compresión. "
  "Un modelo que aprende de imágenes con luz o fondo muy distintos puede asociar el objeto con esas condiciones en lugar de con su forma.")
H3("2. ¿Una imagen de mayor resolución necesariamente es mejor para un modelo?")
P(f"No. La imagen desenfocada tiene más píxeles ({n(des['megapixeles'], 2)} MP frente a {n(ref['megapixeles'], 2)} MP) y, aun así, la nitidez de la figura es "
  f"{n(100*(1-des['nitidez_roi']/ref['nitidez_roi']), 0)} % menor. Más píxeles dan más muestras, no necesariamente más información. Además, la mayoría de los modelos recibe una entrada de tamaño fijo, por lo que se redimensiona de todos modos, y una resolución mayor aumenta el costo de memoria y cómputo. "
  "Cuenta más que el objeto esté bien enfocado, bien iluminado y con suficientes píxeles propios.")
H3("3. ¿Qué efecto tuvo la iluminación sobre los datos obtenidos?")
P(f"Fue el efecto más grande del conjunto. Con poca luz el brillo cayó de {n(ref['brillo'])} a {n(osc['brillo'])} ({n(100*(1-osc['brillo']/ref['brillo']), 0)} % menos), el contraste de {n(ref['contraste'])} a {n(osc['contraste'])} y el rango dinámico de {n(ref['rango_dinamico'], 0)} a {n(osc['rango_dinamico'], 0)}. "
  f"La nitidez medida también cayó ({n(ref['nitidez_global'])} a {n(osc['nitidez_global'])}), aunque la figura conserva su enfoque a simple vista: la métrica baja porque hay menos diferencias de intensidad en los bordes. "
  "La iluminación afecta, entonces, no solo cómo se ve la imagen sino los números que se usan para juzgar su calidad.")
H3("4. ¿Qué ocurrió con la imagen desenfocada y cómo se reflejó en la medida de nitidez?")
P(f"La figura perdió definición, pero la nitidez global casi no cambió ({n(des['nitidez_global'])} frente a {n(ref['nitidez_global'])}), porque la pared texturizada, el monitor y parte de la mesa estaban enfocados y dominan el cálculo. "
  f"Al medir solo en la ROI la diferencia aparece: {n(des['nitidez_roi'])} frente a {n(ref['nitidez_roi'])}. Conclusión práctica: la nitidez debe medirse donde está el objeto de interés. "
  "Esta comparación es aproximada, porque la ROI incluye algo de fondo y la figura ocupa menos píxeles que en la referencia; la evidencia visual de la Figura 3 respalda el resultado numérico.")
H3("5. ¿Todos los problemas encontrados pueden corregirse mediante procesamiento?")
P("No. La subexposición se pudo corregir porque la información seguía en la imagen, solo comprimida en un rango bajo. El desenfoque marcado no se corrige de manera fiable con operaciones básicas: no se puede recuperar detalle que nunca se registró. "
  "El fondo complejo exigiría segmentar el objeto o recapturar. La perspectiva no es un defecto y tampoco se «corrige». Incluso en el caso tratado quedó un residuo: "
  f"el ruido aumentó y la imagen sigue por debajo de la referencia. Cuando es posible, volver a capturar es mejor que reparar.")
H3("6. ¿Por qué es importante analizar una imagen antes de utilizarla como entrada de un modelo?")
P("Porque un modelo aprende lo que recibe. Imágenes oscuras, borrosas o con fondos que dominan la escena pueden degradar el entrenamiento o introducir sesgos que luego parecen errores del modelo. "
  "El análisis previo permite decidir con datos qué imágenes se conservan, cuáles se corrigen, cuáles se recapturan y cuáles se descartan, y deja registro de por qué. Como mostró el caso de la nitidez, "
  "también evita confiar en una métrica que no mide lo que se creía.")
H3("7. ¿El tratamiento aplicado mejoró realmente la imagen para el propósito planteado?")
P(f"Sí para el problema tratado, y parcialmente respecto a la calidad de una buena toma. Mejoró el brillo (×{n(d['brillo']/a['brillo'], 1)}), el contraste (×{n(d['contraste']/a['contraste'], 1)}) y la proporción de píxeles útiles "
  f"(los píxeles oscuros bajaron de {n(a['pct_oscuros'])} % a {n(d['pct_oscuros'])} %), y los detalles de la figura quedaron visibles. No iguala a la referencia y añadió algo de ruido. "
  "Para un sistema de percepción, la imagen tratada es mucho más utilizable que la original, pero no sustituye a una captura bien iluminada.")

# ================================================================== 7. CONCLUSIONES
SEC("Conclusiones y recomendaciones")
P("El diagnóstico mostró que una imagen puede verse aceptable y tener métricas engañosas (otra perspectiva, con la mayor nitidez del conjunto), o verse mal y pasar inadvertida en una métrica global "
  "(desenfocada). Las métricas son útiles solo si se interpretan junto con la imagen y se calculan donde importa. La corrección gamma sobre el canal V resolvió la subexposición de forma "
  "controlada y medible, y la comparación con otras alternativas mostró que la ecualización ofrece un resultado vistoso pero poco fiel.")
P("Las limitaciones del trabajo son: una sola foto por condición, el cambio simultáneo de más de una variable en algunas tomas (distancia, encuadre, resolución), ROI definidas a mano, métricas simples "
  "(la varianza del Laplaciano mezcla enfoque con contraste y textura) y la ausencia de metadatos EXIF para documentar el dispositivo. Como mejoras futuras se recomienda: usar trípode y marcar la posición del objeto "
  "para que cambie una sola variable por toma; fijar la resolución y la exposición manual; segmentar el objeto para medir sobre él con precisión; incorporar otras medidas de enfoque; "
  "tomar varias fotos por condición para estimar la variabilidad; y evaluar el efecto del tratamiento con una tarea real (por ejemplo, un clasificador).")

# ================================================================== 8. GITHUB
SEC("GitHub / Colab")
P(f"Código, imágenes originales y resultados: {datos_portada['github']}")
P("Estructura del repositorio: <font name='Mono'>imagenes/</font> (las cinco fotografías originales), <font name='Mono'>scripts/</font> (<font name='Mono'>config.py</font>, <font name='Mono'>01_diagnostico.py</font>, "
  "<font name='Mono'>02_formatos.py</font>, <font name='Mono'>03_tratamiento.py</font>), <font name='Mono'>resultados/</font> (tablas, figuras e imagen tratada) e <font name='Mono'>informe/</font> (este documento).")


# ------------------------------------------------------------------ construcción
def numero_pagina(canvas, doc):
    canvas.saveState()
    canvas.setFont("Serif", 12)
    if doc.page > 0:
        canvas.drawRightString(letter[0] - inch, letter[1] - 0.6 * inch, str(doc.page))
    canvas.restoreState()


doc = SimpleDocTemplate(str(OUT), pagesize=letter, leftMargin=inch, rightMargin=inch, topMargin=inch, bottomMargin=inch,
                        title=datos_portada["titulo"], author=datos_portada["estudiante"])
doc.build(S, onFirstPage=numero_pagina, onLaterPages=numero_pagina)
print("PDF:", OUT)
