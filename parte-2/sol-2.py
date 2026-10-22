
#!/usr/bin/env python3
"""Uso: python3 sol-2.py ejemplo.in ejemplo.dat"""

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

# Con esta funcion vamos a ejecutar GLPK con .mod y .dat
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
    sys.exit("Uso: python3 sol-2.py ejemplo.in ejemplo.dat")

# Guardamos cada argumento en una variable
entrada = ruta(sys.argv[1])
datos = ruta(sys.argv[2])
modelo = carpeta / "parte-2.mod"
solucion = Path(str(datos) + ".sol.txt")

# Leemos el fichero .in.
filas = [
    # Eliminamos los comentarios que puedan existir
    linea.split("#")[0].split()
    for linea in entrada.read_text(encoding="utf-8-sig").splitlines()
]
# Eliminamos posibles filas vacias
filas = [fila for fila in filas if fila]

# Verificamos que el archivo .in este bien construido acorde al enunciado
if len(filas) != 4 or len(filas[0]) != 2:
    sys.exit("La entrada debe contener: l h; prioridades; pesos; capacidades.")

# Guardamos los valores de l, h, prioridades, pesos y capacidades
l, h = map(int, filas[0])
prioridades = list(map(int, filas[1]))
pesos = list(map(float, filas[2]))
capacidades = list(map(float, filas[3]))
n = h * l * l

# Comprobamos que las dimensiones sean positivas y que haya
# exactamente n prioridades, pesos y capacidades
if l < 1 or h < 1 or len(prioridades) != n or len(pesos) != n or len(capacidades) != n:
    sys.exit("Las dimensiones deben ser positivas y debe haber n = h*l*l cajas con sus datos.")


# Generamos el fichero .dat.
datos.parent.mkdir(parents=True, exist_ok=True)

with datos.open("w", encoding="utf-8") as f:
    f.write(f"data;\nparam l := {l};\nparam h := {h};\nparam n := {n};\n")

    # Escribimos las prioridades, pesos y capacidades de cada caja
    for nombre, valores in [("p", prioridades), ("peso", pesos), ("capacidad", capacidades)]:
        f.write(f"param {nombre} :=\n")

        for k, valor in enumerate(valores, 1):
            f.write(f"{k} {valor}\n")

        f.write(";\n")

    f.write("end;\n")


# Resolvemos usando GLPK de la funcion
ejecutar_mathprog(modelo, datos, solucion)


# Leemos el resultado para luego enseñarlo por pantalla
texto = solucion.read_text(encoding="utf-8")

# Si la solucion no es optima enseñamos por pantalla lo siguiente
if not re.search(r"Status:\s+INTEGER OPTIMAL", texto):
    sys.exit("GLPK no ha encontrado una solucion optima entera.")

# De la variable de texto, que tiene la solucion, sacamos: variables, restricciones y el valor de la funcion objetivo
variables = int(re.search(r"Columns:\s+(\d+)", texto).group(1))
# Aqui tenemos que restar 1 pq GLPK cuenta la funcion objetivo como una fila mas y no es una restriccion
restricciones = int(re.search(r"Rows:\s+(\d+)", texto).group(1)) - 1
objetivo = float(
    re.search(r"Objective:\s+\S+\s+=\s+([^\s]+)", texto).group(1)
)

# Resultado.
print(variables, restricciones, format(objetivo, ".3f"))
