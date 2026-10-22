param l, integer, >= 1;
param h, integer, >= 1;
param n, integer, >= 1, <= h * l * l;

set FILAS    := 1..l;
set COLUMNAS := 1..l;
set NIVELES  := 1..h;
set CAJAS    := 1..n;

param p{CAJAS}, integer, >= 1;
param peso{CAJAS}, >= 0;
param capacidad{CAJAS}, >= 0;

/* Constantes Big-M ajustadas y optimizadas */
param Mp := (max{k in CAJAS} p[k]) + 1;
param Mc := (l - 1) * (max{k in CAJAS} p[k]);

var X{FILAS, COLUMNAS, NIVELES, CAJAS}, binary;
var C{FILAS, COLUMNAS, NIVELES} >= 0;

minimize Coste_Medio:
    (1 / n) * sum{i in FILAS, j in COLUMNAS, z in NIVELES} C[i, j, z];

s.t. Una_Posicion_Por_Caja{k in CAJAS}:
    sum{i in FILAS, j in COLUMNAS, z in NIVELES} X[i, j, z, k] = 1;

s.t. Maxima_Una_Caja_Por_Posicion{i in FILAS, j in COLUMNAS, z in NIVELES}:
    sum{k in CAJAS} X[i, j, z, k] <= 1;

s.t. Orden_Prioridad{j in COLUMNAS, z in NIVELES, t in FILAS, i in FILAS: t < i}:
    sum{k in CAJAS} p[k] * X[i, j, z, k] + Mp * (1 - sum{k in CAJAS} X[i, j, z, k])
    <=
    sum{k in CAJAS} p[k] * X[t, j, z, k] + Mp * (1 - sum{k in CAJAS} X[t, j, z, k]);

s.t. Sin_Cajas_Flotantes{i in FILAS, j in COLUMNAS, z in 1..(h-1)}:
    sum{k in CAJAS} X[i, j, z + 1, k] <= sum{k in CAJAS} X[i, j, z, k];

s.t. Definicion_Coste{i in FILAS, j in COLUMNAS, z in NIVELES}:
    C[i, j, z] >= sum{ip in (i + 1)..l, k in CAJAS} p[k] * X[ip, j, z, k] 
                  - Mc * (1 - sum{k in CAJAS} X[i, j, z, k]);

s.t. Respetar_Capacidad{i in FILAS, j in COLUMNAS, z in 1..(h-1)}:
    sum{kp in CAJAS, zp in (z + 1)..h} peso[kp] * X[i, j, zp, kp]
    <=
    sum{k in CAJAS} capacidad[k] * X[i, j, z, k];

end;