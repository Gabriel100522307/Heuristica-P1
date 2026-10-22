# Parte 3: montaje volumetrico de un pallet posiblemente incompleto.
# X[i,j,z,k]: caja k en fila i, columna j y nivel z.
# Las filas mayores estan mas cerca del acceso; el suelo es z = 1.

param l, integer, >= 1;
param h, integer, >= 1;
param n, integer, >= 1, <= h*l*l;

set FILAS := 1..l;
set COLUMNAS := 1..l;
set NIVELES := 1..h;
set CAJAS := 1..n;

param p{CAJAS}, integer, >= 1;
param peso{CAJAS}, >= 0;
param capacidad{CAJAS}, >= 0;
param p_max := max{k in CAJAS} p[k];
param M_p := p_max + 1;
# El coste suma prioridades reales, sin incluir la prioridad de los huecos.
param M_c := (l - 1) * p_max;

var X{FILAS, COLUMNAS, NIVELES, CAJAS}, binary;
var C{FILAS, COLUMNAS, NIVELES}, >= 0;

# Coste medio: suma de costes de las posiciones ocupadas, dividida entre n.
minimize CosteMedio:
    (1 / n) * sum{i in FILAS, j in COLUMNAS, z in NIVELES}
        C[i,j,z];

# 1. Cada caja ocupa exactamente una posicion.
s.t. CajaUnaVez{k in CAJAS}:
    sum{i in FILAS, j in COLUMNAS, z in NIVELES} X[i,j,z,k] = 1;

# 2. Como maximo una caja por posicion.
s.t. PosicionMaxUnaCaja{i in FILAS, j in COLUMNAS, z in NIVELES}:
    sum{k in CAJAS} X[i,j,z,k] <= 1;

# 3. i > r: la fila i esta delante y debe tener prioridad numerica menor.
# Ocupada: prioridad de su caja. Vacia: M_p, mayor que todas las reales.
s.t. OrdenPrioridades{j in COLUMNAS, z in NIVELES,
                      r in FILAS, i in FILAS: r < i}:
    sum{k in CAJAS} p[k] * X[i,j,z,k]
      + M_p * (1 - sum{k in CAJAS} X[i,j,z,k])
    <=
    sum{k in CAJAS} p[k] * X[r,j,z,k]
      + M_p * (1 - sum{k in CAJAS} X[r,j,z,k]);

# 4. No hay cajas flotantes, incluso si su peso es cero.
s.t. Apoyo{i in FILAS, j in COLUMNAS, z in NIVELES: z < h}:
    sum{k in CAJAS} X[i,j,z+1,k]
    <= sum{k in CAJAS} X[i,j,z,k];

# 5. C >= 0 se declara en la variable. Al minimizar, esta cota basta:
# ocupada -> C = suma de prioridades delante; vacia -> C = 0.
s.t. CostePosicion{i in FILAS, j in COLUMNAS, z in NIVELES}:
    C[i,j,z]
    >= sum{ip in FILAS, k in CAJAS: ip > i} p[k] * X[ip,j,z,k]
       - M_c * (1 - sum{k in CAJAS} X[i,j,z,k]);

# 6. Se cuenta todo el peso situado encima, no solo el nivel siguiente.
s.t. CapacidadCarga{i in FILAS, j in COLUMNAS, z in NIVELES: z < h}:
    sum{zp in NIVELES, k in CAJAS: zp > z} peso[k] * X[i,j,zp,k]
    <= sum{k in CAJAS} capacidad[k] * X[i,j,z,k];

solve;
end;