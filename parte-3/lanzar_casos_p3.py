#!/usr/bin/env python3
"""Crea la carpeta de pruebas, genera los 8 casos .in de la Parte 3 y los resuelve."""

from pathlib import Path
import importlib.util
import sys

def cargar_modulo_sol3(ruta_script: Path):
    spec = importlib.util.spec_from_file_location("sol3", ruta_script)
    sol3 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sol3)
    return sol3

CASOS = [
    (
        "c1_minimo", 1, 1,
        [5], [10], [50]
    ),
    (
        "c2_incompleto", 2, 2,
        [2, 5, 1, 8, 4],
        [10, 15, 20, 10, 5],
        [50, 40, 60, 30, 25]
    ),
    (
        "c3_enunciado", 2, 3,
        [1, 3, 3, 13, 9, 11, 17, 4, 3],
        [3, 11, 9, 1, 13, 4, 15, 11, 7],
        [13, 6, 2, 5, 13, 21, 14, 8, 19]
    ),
    (
        "c4_lleno", 2, 2,
        [4, 2, 7, 1, 6, 3, 8, 5],
        [10] * 8,
        [100] * 8
    ),
    (
        "c5_disperso", 2, 3,
        [2, 1, 5, 3],
        [10, 10, 10, 10],
        [100, 100, 100, 100]
    ),
    (
        "c6_pesos", 2, 3,
        [1, 2, 3, 4, 5, 6],
        [5, 5, 40, 5, 5, 40],
        [100, 100, 10, 100, 100, 10]
    ),
    (
        "c7_medio", 3, 2,
        [1, 4, 2, 5, 3, 6, 8, 7, 9, 11, 10, 12],
        [10] * 12,
        [200] * 12
    ),
    (
        "c8_estres", 3, 3,
        [1, 5, 2, 8, 3, 9, 4, 7, 6, 11, 10, 13, 12, 15, 14, 17, 16, 19, 18, 20],
        [10] * 20,
        [150] * 20
    ),
]

def main():
    dir_actual = Path(__file__).resolve().parent
    script_sol = dir_actual / "sol-3.py"
    
    if not script_sol.exists():
        print(f"Error: No se encuentra 'sol-3.py' en {dir_actual}", file=sys.stderr)
        return

    sol3 = cargar_modulo_sol3(script_sol)
    carpeta_casos = dir_actual / "casos_prueba_p3"
    carpeta_casos.mkdir(parents=True, exist_ok=True)
    
    print(f"{'Caso de Prueba':<16} | {'l':>1} | {'h':>1} | {'n':>2} | {'Vars':>6} | {'Restr':>6} | {'Coste Medio (Z)':>15} | {'Tiempo (s)':>10}")
    print("-" * 86)
    
    for nombre, l, h, p, peso, cap in CASOS:
        f_in = carpeta_casos / f"{nombre}.in"
        f_dat = carpeta_casos / f"{nombre}.dat"
        
        contenido = f"{l} {h}\n{' '.join(map(str, p))}\n{' '.join(map(str, peso))}\n{' '.join(map(str, cap))}\n"
        f_in.write_text(contenido, encoding="utf-8")
        
        try:
            res = sol3.ejecutar(f_in, f_dat)
            print(
                f"{nombre:<16} | {l:>1} | {h:>1} | {res['datos']['n']:>2} | {res['variables']:>6} | "
                f"{res['restricciones']:>6} | {res['objetivo']:>15.4f} | {res['tiempo_s']:>10.4f}"
            )
        except Exception as exc:
            print(f"{nombre:<16} | Error al resolver: {exc}", file=sys.stderr)

if __name__ == "__main__":
    main()