# Parte 1: montaje en un unico nivel de un pallet completo.
# X[i,j,k]: caja k en fila i y columna j.
# Las filas mayores estan mas cerca del acceso.

param l, integer, >= 1;
# Se puede indicar n en el .dat; si se omite, se calcula automaticamente.
param n, integer, >= 1, default l*l;

set FILAS := 1..l;
set COLUMNAS := 1..l;
set CAJAS := 1..n;

param p{CAJAS}, integer, >= 1;

# En este apartado se ocupan todas las posiciones.
check n = l*l;

var X{FILAS, COLUMNAS, CAJAS}, binary;

# Coste medio: suma de prioridades delante de cada posicion, dividida entre n.
minimize CosteMedio:
    (1 / n) * sum{i in FILAS, j in COLUMNAS,
                  ip in FILAS, k in CAJAS: ip > i}
        p[k] * X[ip,j,k];

# 1. Cada caja ocupa exactamente una posicion.
s.t. CajaUnaVez{k in CAJAS}:
    sum{i in FILAS, j in COLUMNAS} X[i,j,k] = 1;

# 2. Cada posicion contiene exactamente una caja.
s.t. PosicionUnaCaja{i in FILAS, j in COLUMNAS}:
    sum{k in CAJAS} X[i,j,k] = 1;

# 3. i > r: la fila i esta delante y debe tener prioridad numerica menor o igual.
s.t. OrdenPrioridades{j in COLUMNAS, r in FILAS, i in FILAS: r < i}:
    sum{k in CAJAS} p[k] * X[i,j,k]
    <= sum{k in CAJAS} p[k] * X[r,j,k];

solve;
end;
