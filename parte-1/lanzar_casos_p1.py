#!/usr/bin/env python3
"""Crea la carpeta de pruebas, genera los 8 casos .in de la Parte 1 y los ejecuta."""

from pathlib import Path
import subprocess
import sys
import time

CASOS = [
    ("c1_minimo", 1, [5]),
    ("c2_basico", 2, [10, 2, 8, 4]),
    ("c3_enunciado", 3, [4, 11, 13, 8, 5, 4, 1, 3, 9]),
    ("c4_simetrico", 3, [5] * 9),
    ("c5_inverso", 4, list(range(16, 0, -1))),
    ("c6_medio", 5, list(range(1, 26))),
    ("c7_grande", 6, list(range(1, 37))),
    ("c8_limite", 7, list(range(1, 50))),
]

def main():
    dir_actual = Path(__file__).resolve().parent
    script_sol = dir_actual / "sol-1.py"
    
    if not script_sol.exists():
        print(f"Error: No se encuentra 'sol-1.py' en {dir_actual}", file=sys.stderr)
        return

    carpeta_casos = dir_actual / "casos_prueba_p1"
    carpeta_casos.mkdir(parents=True, exist_ok=True)
    
    print(f"{'Caso de Prueba':<16} | {'l':>1} | {'n':>2} | {'Vars':>6} | {'Restr':>6} | {'Coste Medio (Z)':>15} | {'Tiempo (s)':>10}")
    print("-" * 80)
    
    for nombre, l, p in CASOS:
        f_in = carpeta_casos / f"{nombre}.in"
        f_dat = carpeta_casos / f"{nombre}.dat"
        
        # Formato Parte 1: Primera línea el lado l, segunda línea las prioridades separadas por espacios
        contenido = f"{l}\n{' '.join(map(str, p))}\n"
        f_in.write_text(contenido, encoding="utf-8")
        
        t0 = time.perf_counter()
        try:
            proceso = subprocess.run(
                [sys.executable, str(script_sol), str(f_in), str(f_dat)],
                capture_output=True,
                text=True,
                check=True
            )
            tiempo_s = time.perf_counter() - t0
            salida = proceso.stdout.strip()
            
            # sol-1.py imprime: variables restricciones objetivo
            partes = salida.split()
            if len(partes) >= 3:
                vars_n, restr_n, obj_n = partes[0], partes[1], partes[2]
            else:
                vars_n, restr_n, obj_n = "?", "?", salida
            
            print(
                f"{nombre:<16} | {l:>1} | {len(p):>2} | {vars_n:>6} | "
                f"{restr_n:>6} | {obj_n:>15} | {tiempo_s:>10.4f}"
            )
        except subprocess.CalledProcessError as exc:
            print(f"{nombre:<16} | Error al resolver: {exc.stderr.strip()}", file=sys.stderr)

if __name__ == "__main__":
    main()