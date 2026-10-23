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

def guardar_solucion_grafica(salida, texto, parte, l, h, prioridades,
                            pesos, capacidades, objetivo):
    """Guarda la colocacion de las cajas en una cuadricula de texto."""
    posiciones = {}
    cajas_encontradas = set()

    # Leemos las variables X cuyo valor es 1. El patron tambien funciona
    # cuando GLPK escribe el nombre y el valor en dos lineas distintas.
    patron = r"^\s*\d+\s+X\[([\d,]+)\]\s+\*\s+(\S+)"
    for indices, valor in re.findall(patron, texto, re.MULTILINE):
        if float(valor) < 0.5:
            continue
        indices = list(map(int, indices.split(",")))

        if parte == 1:
            i, j, k = indices
            z, t = 1, 1
        elif parte in (2, 3):
            i, j, z, k = indices
            t = 1
        else:
            i, j, z, t, k = indices

        posiciones[t, z, i, j] = k - 1
        cajas_encontradas.add(k)

    # No guardamos una cuadricula incompleta si no se ha leido bien el informe.
    n = len(prioridades)
    if len(posiciones) != n or cajas_encontradas != set(range(1, n + 1)):
        sys.exit("Error: no se ha podido leer la colocacion de todas las cajas.")

    # Quitamos el .0 de los numeros enteros y conservamos los decimales.
    def numero(valor):
        return str(int(valor)) if valor == int(valor) else str(valor)

    if parte == 1:
        etiquetas = [str(p) for p in prioridades]
    else:
        etiquetas = [
            f"{p}/{numero(peso)}/{numero(capacidad)}"
            for p, peso, capacidad in zip(prioridades, pesos, capacidades)
        ]

    # Ajustamos el ancho para que las columnas queden alineadas.
    ancho = max(8, len(f"Col {l}") + 2, max(map(len, etiquetas)) + 2)
    margen = len(f"Fila {l}") + 2
    pallets = sorted({posicion[0] for posicion in posiciones})

    with salida.open("w", encoding="utf-8") as f:
        f.write("SOLUCION OPTIMA\n")
        if parte != 1:
            f.write("Cada caja se muestra como prioridad/peso/capacidad; -- indica un hueco\n")
        f.write(f"El acceso esta junto a la fila {l}.\n\n")

        for t in pallets:
            if parte == 4:
                f.write(f"PALLET {t}\n\n")

            # Mostramos primero el nivel superior y la fila mas cercana al acceso.
            for z in range(h, 0, -1):
                if parte != 1:
                    f.write(f"Nivel {z}\n")
                f.write(" " * margen)
                f.write("".join(f"Col {j}".rjust(ancho) for j in range(1, l + 1)))
                f.write("\n")

                for i in range(l, 0, -1):
                    f.write(f"Fila {i}".ljust(margen))
                    for j in range(1, l + 1):
                        k = posiciones.get((t, z, i, j))
                        celda = "--" if k is None else etiquetas[k]
                        f.write(celda.rjust(ancho))
                    f.write("\n")
                f.write("\n")

        if parte == 4:
            f.write(f"Pallets utilizados: {len(pallets)}\n")
            f.write(f"Coste total: {objetivo:.2f}\n")
        else:
            f.write(f"Coste medio: {objetivo:.2f}\n")


# Aseguramos que se pasan exactamente 3 argumentos
if len(sys.argv) != 3:
    sys.exit("Uso: python3 sol-2.py ejemplo.in ejemplo.dat")

# Guardamos cada argumento en una variable
entrada = ruta(sys.argv[1])
datos = ruta(sys.argv[2])
modelo = carpeta / "parte-2.mod"
solucion = Path(str(datos) + ".sol.txt")
# Cuadricula que se guarda junto al archivo .dat.
salida_grafica = datos.with_name(datos.stem + "-solucion.txt")

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
# Si repetimos un caso y falla, no dejamos la cuadricula de una ejecucion anterior.
salida_grafica.unlink(missing_ok=True)
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

# Guardamos la distribucion en el fichero de salida.
guardar_solucion_grafica(
    salida_grafica, texto, 2, l, h, prioridades, pesos, capacidades, objetivo
)

# Resultado.
print(variables, restricciones, format(objetivo, ".3f"))
