# Tratamiento de imagen con OpenCV: diagnóstico y corrección de subexposición

Actividad R2-A2-S8 de Percepción Computacional (Especialización en Inteligencia Artificial).

Se fotografió un mismo objeto (una figura coleccionable) bajo cinco condiciones de captura, se diagnosticó
cada imagen con métricas simples (brillo, contraste, nitidez, resolución, ruido), se eligió la imagen
problemática (`oscura.jpg`, subexpuesta) y se le aplicó una corrección gamma sobre el canal V, evaluando el
resultado antes y después.

## Estructura

```
imagenes/     las cinco fotografías originales (sin edición)
scripts/      config.py, 01_diagnostico.py, 02_formatos.py, 03_tratamiento.py
resultados/   métricas (CSV/JSON), figuras e imagen tratada
informe/      construir_informe.py y el informe en PDF
```

## Cómo reproducirlo

```bash
pip install -r requirements.txt
python scripts/01_diagnostico.py     # métricas + figuras de diagnóstico
python scripts/02_formatos.py        # comparación JPG vs PNG
python scripts/03_tratamiento.py     # tratamiento y evaluación antes/después
```

Los scripts se ejecutan desde la raíz del proyecto. Las regiones de interés (ROI) alrededor de la figura
están definidas en `scripts/config.py`.

## Resultado principal

Gamma = 0,44 sobre el canal V: el brillo medio pasó de 37,3 a 103,6, los píxeles por debajo de 50 de 82,9 %
a 5,7 % y el rango dinámico de 63 a 118 niveles, a costa de un aumento del ruido estimado de 46 %.
El detalle y la discusión están en el informe PDF.
