#!/usr/bin/env python3
"""Uso: python3 sol-1.py ejemplo.in ejemplo.dat"""

from pathlib import Path
import re
import subprocess
import sys

# Obtenemos la carpeta en la que se encuentra nuestro script.
carpeta = Path(__file__).resolve().parent

# Funcion para obtener la ruta de los ficheros 
def ruta(nombre):
    archivo = Path(nombre).expanduser()

    # Si el nombre no contiene una ruta, buscamos el fichero directamente en la misma carpeta que nuestro script.
    if not archivo.is_absolute() and "/" not in nombre and "\\" not in nombre:
        return carpeta / archivo

    # Si ya tenemos la ruta lo devolvemos directamente 
    return archivo

# Con esta función vamos a ejecutar GLPK con .mod y .dat
def ejecutar_mathprog(modelo_mod, datos_dat, salida_sol):
    # Juntamos en la variable el comando que ejecutariamos por terminal
    comando = [
        "glpsol",
        "-m", str(modelo_mod),
        "-d", str(datos_dat),
        "-o", str(salida_sol)
    ]

    # Creamos un bloque try-except para capturar la salida y los posibles errores
    try:
        resultado = subprocess.run(
            comando,
            capture_output=True,
            text=True
        )
    # Si GLPK no esta instalado lanzamos este mensaje
    except FileNotFoundError:
        sys.exit("Error: no se encuentra glpsol.")

    # Si algo falla en el comando devolvemos error
    if resultado.returncode != 0:
        sys.exit(resultado.stdout + resultado.stderr)

# Aseguramos que se pasan exactamente 3 argumentos
if len(sys.argv) != 3:
    sys.exit("Uso: python3 sol-1.py ejemplo.in ejemplo.dat")

# Guardamos cada argumento en una variable
entrada = ruta(sys.argv[1])
datos = ruta(sys.argv[2])
modelo = carpeta / "parte-1.mod"
solucion = Path(str(datos) + ".sol.txt")

# Leeemos el fichero .in.
filas = [
    # ELiminamos los comentarios que puedan existir
    linea.split("#")[0].split()
    for linea in entrada.read_text(encoding="utf-8-sig").splitlines()
]
# ELiminamos posbiles filas vacias 
filas = [fila for fila in filas if fila]

# Verificamos que el archivo .in este bien construido acorde al enunciado 
if len(filas) != 2 or len(filas[0]) != 1:
    sys.exit("La entrada debe contener: lado l; prioridades.")

# Guardamos el valor de l en una variable
l = int(filas[0][0])
prioridades = list(map(int, filas[1]))
n = l * l

if l < 1 or len(prioridades) != n or any(p < 1 for p in prioridades):
    sys.exit("El lado y las prioridades deben ser positivos y debe haber l^2 prioridades.")


# Generamos el fichero .dat.
datos.parent.mkdir(parents=True, exist_ok=True)

with datos.open("w", encoding="utf-8") as f:
    f.write(f"data;\nparam l := {l};\nparam n := {n};\n")
    f.write("param p :=\n")

    for k, prioridad in enumerate(prioridades, 1):
        f.write(f"{k} {prioridad}\n")

    f.write(";\nend;\n")


# Resolvemos usando GLPK de la funcion 
ejecutar_mathprog(modelo, datos, solucion)


# Leemos el resultado para luego enseñarlo por pantalla 
texto = solucion.read_text(encoding="utf-8")

# Si la solución no es óptima enseñamos por pantalla lo siguiente
if not re.search(r"Status:\s+INTEGER OPTIMAL", texto):
    sys.exit("GLPK no ha encontrado una solucion optima entera.")

# De la variable de texto, que tiene la solucion, sacamos: variables, restricciones y el valor de la función objetivo 
variables = int(re.search(r"Columns:\s+(\d+)", texto).group(1))
# Aqui tenemos que restar 1 pq GLPK cuenta la función objetivo como una fila más y no es una restriccion
restricciones = int(re.search(r"Rows:\s+(\d+)", texto).group(1)) - 1
objetivo = float(
    re.search(r"Objective:\s+\S+\s+=\s+([^\s]+)", texto).group(1)
)

# Resultado.
print(variables, restricciones, format(objetivo, ".3f"))
