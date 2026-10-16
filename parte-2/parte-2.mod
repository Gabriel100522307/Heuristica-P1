# Parte 2: montaje volumetrico de un pallet completo.
# X[i,j,z,k] = 1 si la caja k ocupa la posicion (i,j,z).
# Las filas con mayor i estan delante. El suelo corresponde a z = 1.
# Ejecucion: glpsol -m parte-2.mod -d datos.dat -o solucion.txt

param l, integer, >= 1;
param h, integer, >= 1;
# Se puede indicar n en el .dat; si se omite, se calcula automaticamente.
param n, integer, >= 1, default h*l*l;

param p{1..n}, integer, >= 1;
param peso{1..n}, >= 0;
param capacidad{1..n}, >= 0;

# En este apartado se ocupan todas las posiciones.
check n = h*l*l;

var X{1..l, 1..l, 1..h, 1..n}, binary;

# Coste medio: suma de prioridades delante de cada posicion, dividida entre n.
minimize CosteMedio:
    (1 / n) * sum{i in 1..l, j in 1..l, z in 1..h,
                  ip in i+1..l, k in 1..n}
        p[k] * X[ip,j,z,k];

# 1. Cada caja ocupa exactamente una posicion.
s.t. CajaUnaVez{k in 1..n}:
    sum{i in 1..l, j in 1..l, z in 1..h} X[i,j,z,k] = 1;

# 2. Cada posicion contiene exactamente una caja.
s.t. PosicionUnaCaja{i in 1..l, j in 1..l, z in 1..h}:
    sum{k in 1..n} X[i,j,z,k] = 1;

# 3. Para i > t, la prioridad numerica en i debe ser menor o igual.
s.t. OrdenPrioridades{j in 1..l, z in 1..h,
                      t in 1..l, i in 1..l: t < i}:
    sum{k in 1..n} p[k] * X[i,j,z,k]
    <= sum{k in 1..n} p[k] * X[t,j,z,k];

# 4. El peso de TODAS las cajas superiores no supera la capacidad de la caja.
# En z = h, el sumatorio de pesos superiores es vacio y vale cero.
s.t. CapacidadCarga{i in 1..l, j in 1..l, z in 1..h}:
    sum{zp in z+1..h, kp in 1..n} peso[kp] * X[i,j,zp,kp]
    <= sum{k in 1..n} capacidad[k] * X[i,j,z,k];

solve;
end;
