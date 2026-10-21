# PARTE 2: Montaje volumétrico

# Parámetros
# l: lado del pallet; h: niveles; n: número de cajas (pallet lleno)
param l integer, > 0;
param h integer, > 0;
param n := h * l * l;

set K := 1..n;
set F := 1..l;
set C := 1..l;
set N := 1..h;

# Prioridad, peso y capacidad de carga de cada caja
param p{K} integer, > 0;
param w{K} >= 0;
param c{K} >= 0;

# Variables
# x[k,i,j,z] = 1 si la caja k se coloca en la fila i, columna j y nivel z.
var x{K,F,C,N} binary;

# Restricciones

# 1. Cada caja ocupa una única posición.
s.t. UnaPosicionPorCaja{k in K}:
    sum{i in F, j in C, z in N} x[k,i,j,z] = 1;

# 2. Cada posición contiene exactamente una caja.
s.t. UnaCajaPorPosicion{i in F, j in C, z in N}:
    sum{k in K} x[k,i,j,z] = 1;

# 3. Orden de prioridades dentro de cada nivel: si q está en la fila i del
#    nivel z, la caja k (más prioritaria) no puede estar detrás (filas < i).
s.t. OrdenPrioridades{z in N, i in F, k in K, q in K : i > 1 and p[k] < p[q]}:
    sum{j in C} x[q,i,j,z]
    + sum{i2 in F, j in C : i2 < i} x[k,i2,j,z]
    <= 1;

# 4. Capacidad de carga: el peso apilado sobre (i,j,z) no supera la
#    capacidad de la caja que ocupa esa posición.
s.t. Capacidad{i in F, j in C, z in N : z < h}:
    sum{k in K, z2 in N : z2 > z} w[k] * x[k,i,j,z2]
    <=
    sum{k in K} c[k] * x[k,i,j,z];


# Función objetivo: coste medio (el nivel no influye en el coste).
minimize CosteMedio:
    (1 / n) *
    sum{k in K, i in F, j in C, z in N}
        (i-1) * p[k] * x[k,i,j,z];

solve;

# Salida para el script: valor de la función objetivo
printf "OBJ %f\n", CosteMedio;

# Salida para el script: nivel, fila, columna, prioridad, peso y capacidad
# de la caja colocada en cada posición
printf {z in N, i in F, j in C, k in K : x[k,i,j,z] > 0.5}
    "SOL %d %d %d %d %g %g\n", z, i, j, p[k], w[k], c[k];

end;
