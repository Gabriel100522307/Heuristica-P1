#!/usr/bin/env python3
"""Uso: python3 sol-2.py ejemplo.in ejemplo.dat

Requiere glpsol en el PATH y parte-2.mod junto a este script.
"""

from pathlib import Path
import re
import subprocess
import sys

carpeta = Path(__file__).resolve().parent


def ruta(nombre):
    # Los nombres sin directorio se buscan junto al script.
    archivo = Path(nombre).expanduser()
    if not archivo.is_absolute() and "/" not in nombre:
        return carpeta / archivo
    return archivo


if len(sys.argv) != 3:
    sys.exit("Uso: python3 sol-2.py ejemplo.in ejemplo.dat")

entrada = ruta(sys.argv[1])
datos = ruta(sys.argv[2])
modelo = carpeta / "parte-2.mod"
solucion = Path(str(datos) + ".sol.txt")

if not modelo.is_file():
    sys.exit("Coloca parte-2.mod en la misma carpeta que sol-2.py.")
for archivo in (datos, solucion):
    if archivo.resolve() in {entrada.resolve(), modelo.resolve(), Path(__file__).resolve()}:
        sys.exit("La salida no puede sobrescribir la entrada ni el codigo.")

# 1. Leer las cuatro filas del .in.
try:
    filas = [linea.split("#")[0].split()
             for linea in entrada.read_text(encoding="utf-8-sig").splitlines()]
    filas = [fila for fila in filas if fila]
    if len(filas) != 4 or len(filas[0]) != 2:
        sys.exit("La entrada debe contener: l h; prioridades; pesos; capacidades.")
    l, h = map(int, filas[0])
    prioridades = list(map(int, filas[1]))
    pesos = list(map(float, filas[2]))
    capacidades = list(map(float, filas[3]))
except (OSError, ValueError) as error:
    sys.exit(f"No se puede leer la entrada: {error}")

n = len(prioridades)
if l < 1 or h < 1 or n != h * l * l:
    sys.exit("En la parte 2, l y h deben ser positivos y debe haber n = h*l*l cajas.")
if len(pesos) != n or len(capacidades) != n:
    sys.exit("Debe haber una prioridad, un peso y una capacidad por caja.")

# 2. Crear el .dat que entiende parte-2.mod.
datos.parent.mkdir(parents=True, exist_ok=True)
with datos.open("w", encoding="utf-8") as f:
    f.write(f"data;\nparam l := {l};\nparam h := {h};\nparam n := {n};\n")
    for nombre, valores in [("p", prioridades), ("peso", pesos), ("capacidad", capacidades)]:
        f.write(f"param {nombre} :=\n")
        for k, valor in enumerate(valores, 1):
            f.write(f"{k} {valor}\n")
        f.write(";\n")
    f.write("end;\n")

# 3. Resolver el modelo mediante glpsol.
try:
    resultado = subprocess.run(
        ["glpsol", "-m", str(modelo), "-d", str(datos), "-o", str(solucion)],
        capture_output=True, text=True,
    )
except FileNotFoundError:
    sys.exit("No se encuentra glpsol. Instala GLPK y comprueba que funciona en la terminal.")
if resultado.returncode != 0:
    sys.exit(resultado.stdout + resultado.stderr)

# 4. Comprobar la optimalidad y mostrar: variables restricciones coste.
texto = solucion.read_text(encoding="utf-8")
estado = re.search(r"Status:\s+([^\n]+)", texto).group(1).strip()
if estado != "INTEGER OPTIMAL":
    sys.exit(f"No se ha obtenido un optimo entero. Estado: {estado}. Revisa {solucion}")

variables = int(re.search(r"Columns:\s+(\d+)", texto).group(1))
# GLPK cuenta el objetivo como una fila adicional; no es una restriccion.
restricciones = int(re.search(r"Rows:\s+(\d+)", texto).group(1)) - 1
coste = re.search(r"Objective:\s+\S+\s*=\s*(\S+)", texto).group(1)
print(variables, restricciones, coste)