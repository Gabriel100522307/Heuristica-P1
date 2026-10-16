/* --- PARÁMETROS ESCALARES --- */
param l, integer, >= 1;              /* Longitud del lado del pallet */
param n, integer, >= 1, == l * l;    /* Número total de cajas (pallet lleno) */

/* --- CONJUNTOS --- */
set FILAS    := 1..l;                /* Filas del pallet (l = más cercana al acceso) */
set COLUMNAS := 1..l;                /* Columnas del pallet */
set CAJAS    := 1..n;                /* Identificadores de las cajas */

/* --- PARÁMETROS VECTORIALES --- */
param p{CAJAS}, integer, >= 1;       /* Prioridad de cada caja k (menor valor = mayor prioridad) */

/* --- VARIABLES DE DECISIÓN --- */
/* X[i,j,k] = 1 si la caja k se coloca en la fila i y columna j; 0 en caso contrario */
var X{FILAS, COLUMNAS, CAJAS}, binary;

/* --- FUNCIÓN OBJETIVO --- */
/* Minimizar el coste medio de disposición de las n cajas en el pallet */
minimize Coste_Medio:
    (1 / n) * sum{i in FILAS, j in COLUMNAS, ip in (i + 1)..l, k in CAJAS} p[k] * X[ip, j, k];

/* --- RESTRICCIONES --- */

/* Restricción 1: Cada caja k debe ocupar exactamente una posición en el pallet */
s.t. Una_Posicion_Por_Caja{k in CAJAS}:
    sum{i in FILAS, j in COLUMNAS} X[i, j, k] = 1;

/* Restricción 2: Cada posición (i,j) del pallet debe contener exactamente una caja */
s.t. Una_Caja_Por_Posicion{i in FILAS, j in COLUMNAS}:
    sum{k in CAJAS} X[i, j, k] = 1;

/* Restricción 3: En una misma columna j, las cajas más cercanas al acceso (fila i > t)
 * deben tener mayor o igual prioridad (valor numérico menor o igual) */
s.t. Orden_Prioridad{j in COLUMNAS, t in FILAS, i in FILAS: t < i}:
    sum{k in CAJAS} p[k] * X[i, j, k] <= sum{k in CAJAS} p[k] * X[t, j, k];

end;
