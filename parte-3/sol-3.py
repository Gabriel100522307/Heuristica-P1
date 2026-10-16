#!/usr/bin/env python3
"""Genera .dat, resuelve parte-3.mod con GLPK y exporta JSON.

Uso: python3 sol-3.py fichero-entrada fichero-salida.dat
Dependencia: swiglpk (interfaz de Python para la biblioteca GLPK).
"""

from __future__ import annotations

import json
import math
from pathlib import Path
import re
import sys
import time


class ErrorModelo(Exception):
    """Error de entrada, de generacion o de resolucion."""


def leer_entrada(path: Path) -> dict:
    lineas = []
    for linea in path.read_text(encoding="utf-8-sig").splitlines():
        contenido = linea.split("#", 1)[0].strip()
        if contenido:
            lineas.append(contenido.split())
    if len(lineas) != 4 or len(lineas[0]) != 2:
        raise ErrorModelo("El .in debe tener cuatro filas: l h; prioridades; pesos; capacidades.")

    def entero(texto: str, nombre: str) -> int:
        try:
            valor = int(texto)
        except ValueError as exc:
            raise ErrorModelo(f"{nombre} debe ser un entero positivo.") from exc
        if valor < 1:
            raise ErrorModelo(f"{nombre} debe ser un entero positivo.")
        return valor

    def real(texto: str, nombre: str) -> float:
        try:
            valor = float(texto)
        except ValueError as exc:
            raise ErrorModelo(f"{nombre} debe ser un numero no negativo.") from exc
        if not math.isfinite(valor) or valor < 0:
            raise ErrorModelo(f"{nombre} debe ser finito y no negativo.")
        return valor

    l = entero(lineas[0][0], "l")
    h = entero(lineas[0][1], "h")
    p = [entero(v, "La prioridad") for v in lineas[1]]
    peso = [real(v, "El peso") for v in lineas[2]]
    capacidad = [real(v, "La capacidad") for v in lineas[3]]
    n = len(p)
    if n > h * l * l:
        raise ErrorModelo(f"El numero de cajas n={n} supera la capacidad maxima del pallet h*l^2={h*l*l}.")
    if len(peso) != n or len(capacidad) != n:
        raise ErrorModelo("Debe haber exactamente una prioridad, un peso y una capacidad por cada caja.")
    return {"l": l, "h": h, "n": n, "p": p, "peso": peso, "capacidad": capacidad}


def numero(valor: float) -> str:
    return format(valor, ".15g")


def escribir_dat(datos: dict, path: Path) -> None:
    lineas = ["data;"]
    for nombre in ("l", "h", "n"):
        lineas.append(f"param {nombre} := {datos[nombre]};")
    for nombre in ("p", "peso", "capacidad"):
        lineas.append(f"param {nombre} :=")
        lineas.extend(f"  {k} {numero(v)}" for k, v in enumerate(datos[nombre], 1))
        lineas.append(";")
    lineas.extend(["end;", ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lineas), encoding="utf-8")


def resolver(modelo: Path, dat: Path, limite_segundos: float | None = 15.0) -> dict:
    try:
        import swiglpk as glp
    except ImportError as exc:
        raise ErrorModelo("Falta swiglpk. Instalalo con: python3 -m pip install swiglpk") from exc

    t0 = time.perf_counter()
    anterior = glp.glp_term_out(glp.GLP_OFF)
    traductor = glp.glp_mpl_alloc_wksp()
    problema = glp.glp_create_prob()
    try:
        if glp.glp_mpl_read_model(traductor, str(modelo), 1) != 0:
            raise ErrorModelo("GLPK no ha podido leer el modelo .mod.")
        if glp.glp_mpl_read_data(traductor, str(dat)) != 0:
            raise ErrorModelo("GLPK no ha podido leer el fichero .dat.")
        if glp.glp_mpl_generate(traductor, None) != 0:
            raise ErrorModelo("GLPK no ha podido generar el modelo con estos datos.")
        glp.glp_mpl_build_prob(traductor, problema)

        opciones = glp.glp_iocp()
        glp.glp_init_iocp(opciones)
        opciones.presolve = glp.GLP_ON
        opciones.msg_lev = glp.GLP_MSG_OFF
        opciones.mip_gap = 0.0
        if limite_segundos is not None:
            opciones.tm_lim = max(1, round(limite_segundos * 1000))
        codigo = glp.glp_intopt(problema, opciones)
        estado = glp.glp_mip_status(problema)
        if codigo != 0 or (estado != glp.GLP_OPT and estado != glp.GLP_FEAS):
            raise ErrorModelo(
                f"GLPK no ha certificado una solucion optima (codigo={codigo}, estado={estado})."
            )

        colocaciones = []
        costes = []
        for col in range(1, glp.glp_get_num_cols(problema) + 1):
            nombre = glp.glp_get_col_name(problema, col)
            valor = glp.glp_mip_col_val(problema, col)
            indices = [int(v) for v in re.findall(r"\d+", nombre)]
            if nombre.startswith("X[") and valor > 0.5:
                i, j, z, k = indices
                colocaciones.append({"i": i, "j": j, "z": z, "k": k})
            elif nombre.startswith("C["):
                i, j, z = indices
                costes.append({"i": i, "j": j, "z": z, "coste": valor})

        restricciones = sum(
            glp.glp_get_row_type(problema, fila) != glp.GLP_FR
            for fila in range(1, glp.glp_get_num_rows(problema) + 1)
        )
        resultado = {
            "estado": "OPTIMO" if estado == glp.GLP_OPT else "FACTIBLE",
            "solver": f"GLPK {glp.glp_version()}",
            "variables": glp.glp_get_num_cols(problema),
            "restricciones": restricciones,
            "objetivo": glp.glp_mip_obj_val(problema),
            "tiempo_s": round(time.perf_counter() - t0, 6),
            "colocaciones": sorted(colocaciones, key=lambda a: a["k"]),
            "costes_posicion": costes,
        }
        if glp.glp_mpl_postsolve(traductor, problema, glp.GLP_MIP) != 0:
            raise ErrorModelo("Fallo en el postprocesado de MathProg.")
        return resultado
    finally:
        glp.glp_delete_prob(problema)
        glp.glp_mpl_free_wksp(traductor)
        glp.glp_term_out(anterior)


def ruta_argumento(texto: str) -> Path:
    path = Path(texto).expanduser()
    if path.is_absolute():
        return path
    if "/" not in texto and "\\" not in texto:
        return Path(__file__).resolve().parent / path
    return Path.cwd() / path


def ejecutar(entrada: Path, salida_dat: Path, limite_segundos: float | None = 15.0) -> dict:
    modelo = Path(__file__).resolve().with_name("parte-3.mod")
    salida_json = salida_dat.with_suffix(".solucion.json")
    protegidos = {entrada.resolve(), modelo.resolve(), Path(__file__).resolve()}
    if any(p.resolve() in protegidos for p in (salida_dat, salida_json)):
        raise ErrorModelo("La ruta de salida pisaria un fichero de entrada o de codigo.")
    datos = leer_entrada(entrada)
    escribir_dat(datos, salida_dat)
    solucion = resolver(modelo, salida_dat, limite_segundos)
    solucion["datos"] = datos
    salida_json.write_text(json.dumps(solucion, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return solucion


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Uso: python3 sol-3.py fichero-entrada fichero-salida.dat", file=sys.stderr)
        return 2
    try:
        resultado = ejecutar(ruta_argumento(argv[0]), ruta_argumento(argv[1]))
    except (ErrorModelo, OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(f'{resultado["variables"]} {resultado["restricciones"]} {numero(resultado["objetivo"])}')
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
