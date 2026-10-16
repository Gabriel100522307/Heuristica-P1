#!/usr/bin/env python3
"""Genera .dat, resuelve parte-3.mod con GLPK y exporta JSON y HTML."""

from __future__ import annotations

import html
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


def guardar_html(datos: dict, solucion: dict, path: Path) -> None:
    esc = html.escape
    celdas = {(a["i"], a["j"], a["z"]): a["k"] for a in solucion["colocaciones"]}
    costes = {(a["i"], a["j"], a["z"]): a["coste"] for a in solucion["costes_posicion"]}
    niveles_html = []
    for z in range(1, datos["h"] + 1):
        celdas_html = []
        for i in range(datos["l"], 0, -1):
            for j in range(1, datos["l"] + 1):
                clave = (i, j, z)
                k = celdas.get(clave)
                posicion = f"Fila {i} · Columna {j}"
                if k is None:
                    interior = f"<small>{posicion}</small><span>Vacío</span>"
                    clase = "celda vacia"
                else:
                    interior = (
                        f"<small>{posicion}</small><strong>Caja {k}</strong>"
                        f"<span>Prioridad {datos['p'][k - 1]}</span>"
                        f"<span>Peso {numero(datos['peso'][k - 1])} g</span>"
                        f"<span>Capacidad {numero(datos['capacidad'][k - 1])} g</span>"
                        f"<b>Coste {numero(costes.get(clave, 0))}</b>"
                    )
                    clase = "celda"
                celdas_html.append(f'<div class="{clase}">{interior}</div>')
        niveles_html.append(
            f'<article class="nivel"><h3>Nivel {z}'
            + (' · base' if z == 1 else '')
            + f'</h3><div class="acceso">Acceso · fila {datos["l"]}</div>'
            + f'<div class="rejilla" style="--lado:{datos["l"]}">'
            + "".join(celdas_html)
            + "</div></article>"
        )

    documento = f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Parte 3 · Pallets incompletos</title><style>
*{{box-sizing:border-box}}body{{margin:0;background:#f4f7fb;color:#172337;font:16px system-ui,sans-serif}}
main{{max-width:1400px;margin:auto;padding:32px}}h1{{margin:8px 0 12px;font-size:30px}}h3{{margin:0 0 10px;font-size:18px}}
.marca{{text-transform:uppercase;letter-spacing:2px;color:#276b63;font-size:12px;font-weight:700}}
.resumen{{display:flex;flex-wrap:wrap;gap:12px;margin:20px 0}}.dato{{padding:14px 20px;background:#fff;border:1px solid #dbe3ed;border-radius:12px}}
.dato strong{{display:block;font-size:24px}}.dato span{{font-size:13px;color:#526174}}
section{{background:#fff;border:1px solid #dbe3ed;border-radius:16px;padding:22px;margin:20px 0}}
.niveles{{display:flex;flex-wrap:wrap;gap:24px}}.nivel{{max-width:100%;overflow:auto}}.acceso{{padding:8px;background:#e1f3f0;color:#1b655a;text-align:center;font-size:13px;border-radius:7px 7px 0 0;font-weight:600}}
.rejilla{{display:grid;grid-template-columns:repeat(var(--lado),minmax(120px,1fr));gap:8px;padding-top:8px}}
.celda{{padding:12px;min-height:140px;border:1px solid #89c8bd;border-radius:8px;background:#f0faf7;display:flex;flex-direction:column;gap:4px;font-size:12px}}
.celda strong{{font-size:17px}}.celda b{{margin-top:4px;color:#175b51}}.vacia{{background:#f7f8fa;border:1px dashed #c5cfdc;color:#7b8798}}
.vacia>span{{margin:auto;text-align:center}}small{{font-size:12px;color:#5f6f84}}
footer{{margin-top:20px;font-size:12px;color:#64748b}}
</style></head><body><main><div class="marca">Heurística y optimización · Parte 3</div>
<h1>Optimización de pallets incompletos (l = {datos['l']}, h = {datos['h']}, n = {datos['n']})</h1>
<div class="resumen">
  <div class="dato"><strong>{numero(solucion['objetivo'])}</strong><span>Coste medio (Z)</span></div>
  <div class="dato"><strong>{datos['n']}</strong><span>Cajas dispuestas</span></div>
  <div class="dato"><strong>{solucion['tiempo_s']} s</strong><span>Tiempo GLPK</span></div>
</div>
<section><h2>Distribución por niveles</h2><div class="niveles">{''.join(niveles_html)}</div></section>
<footer>Óptimo certificado por {esc(solucion['solver'])}. {solucion['variables']} variables y {solucion['restricciones']} restricciones.</footer>
</main></body></html>"""
    path.write_text(documento, encoding="utf-8")


def ruta_argumento(texto: str) -> Path:
    path = Path(texto).expanduser()
    if path.is_absolute():
        return path
    if "/" not in texto and "\\" not in texto:
        return Path(__file__).resolve().parent / path
    return Path.cwd() / path


def ejecutar(entrada: Path, salida_dat: Path, limite_segundos: float | None = 15.0) -> dict:
    modelo = Path(__file__).resolve().with_name("parte-3.mod")
    salida_html = salida_dat.with_suffix(".html")
    salida_json = salida_dat.with_suffix(".solucion.json")
    protegidos = {entrada.resolve(), modelo.resolve(), Path(__file__).resolve()}
    if any(p.resolve() in protegidos for p in (salida_dat, salida_html, salida_json)):
        raise ErrorModelo("La ruta de salida pisaria un fichero de entrada o de codigo.")
    datos = leer_entrada(entrada)
    escribir_dat(datos, salida_dat)
    solucion = resolver(modelo, salida_dat, limite_segundos)
    solucion["datos"] = datos
    salida_json.write_text(json.dumps(solucion, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    guardar_html(datos, solucion, salida_html)
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
