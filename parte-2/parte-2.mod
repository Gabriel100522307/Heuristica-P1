# Parte 2: montaje volumetrico de un pallet completo.
# X[i,j,z,k]: caja k en fila i, columna j y nivel z.
# Las filas mayores estan mas cerca del acceso; el suelo es z = 1.

param l, integer, >= 1;
param h, integer, >= 1;
# Se puede indicar n en el .dat; si se omite, se calcula automaticamente.
param n, integer, >= 1, default h*l*l;

set FILAS := 1..l;
set COLUMNAS := 1..l;
set NIVELES := 1..h;
set CAJAS := 1..n;

param p{CAJAS}, integer, >= 1;
param peso{CAJAS}, >= 0;
param capacidad{CAJAS}, >= 0;

# En este apartado se ocupan todas las posiciones.
check n = h*l*l;

var X{FILAS, COLUMNAS, NIVELES, CAJAS}, binary;

# Coste medio: suma de prioridades delante de cada posicion, dividida entre n.
minimize CosteMedio:
    (1 / n) * sum{i in FILAS, j in COLUMNAS, z in NIVELES,
                  ip in FILAS, k in CAJAS: ip > i}
        p[k] * X[ip,j,z,k];

# 1. Cada caja ocupa exactamente una posicion.
s.t. CajaUnaVez{k in CAJAS}:
    sum{i in FILAS, j in COLUMNAS, z in NIVELES} X[i,j,z,k] = 1;

# 2. Cada posicion contiene exactamente una caja.
s.t. PosicionUnaCaja{i in FILAS, j in COLUMNAS, z in NIVELES}:
    sum{k in CAJAS} X[i,j,z,k] = 1;

# 3. i > r: la fila i esta delante y debe tener prioridad numerica menor o igual.
s.t. OrdenPrioridades{j in COLUMNAS, z in NIVELES,
                      r in FILAS, i in FILAS: r < i}:
    sum{k in CAJAS} p[k] * X[i,j,z,k]
    <= sum{k in CAJAS} p[k] * X[r,j,z,k];

# 4. Se cuenta todo el peso situado encima, no solo el nivel siguiente.
s.t. CapacidadCarga{i in FILAS, j in COLUMNAS, z in NIVELES: z < h}:
    sum{zp in NIVELES, k in CAJAS: zp > z} peso[k] * X[i,j,zp,k]
    <= sum{k in CAJAS} capacidad[k] * X[i,j,z,k];

solve;
end;
