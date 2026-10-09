# PARTE 3: Optimización de pallets incompletos

# Parámetros
param l integer, > 0;
param h integer, > 0;
param n integer, > 0, <= h * l * l;

set K := 1..n;
set F := 1..l;
set C := 1..l;
set N := 1..h;

param p{K} integer, > 0;
param w{K} >= 0;
param c{K} >= 0;



# Variables

var x{K,F,C,N} binary;

# y[i,j,z] = 1 si la posición (i,j,z) está vacía.
var y{F,C,N} binary;

# Restricciones

s.t. UnaPosicionPorCaja{k in K}:
    sum{i in F, j in C, z in N} x[k,i,j,z] = 1;

s.t. UnaCajaOVacia{i in F, j in C, z in N}:
    sum{k in K} x[k,i,j,z] + y[i,j,z] = 1;

s.t. OrdenPrioridades{z in N, i in F, k in K, q in K : i > 1 and p[k] < p[q]}:
    sum{j in C} x[q,i,j,z]
    + sum{i2 in F, j in C : i2 < i} x[k,i2,j,z]
    <= 1;

s.t. OrdenVacios{z in N, i in F, j in C, k in K : i > 1}:
    y[i,j,z]
    + sum{i2 in F, j2 in C : i2 < i} x[k,i2,j2,z]
    <= 1;

s.t. Capacidad{i in F, j in C, z in N : z < h}:
    sum{k in K, z2 in N : z2 > z} w[k] * x[k,i,j,z2]
    <=
    sum{k in K} c[k] * x[k,i,j,z];


#Función objetivo

minimize CosteMedio:
    (1 / n) *
    sum{k in K, i in F, j in C, z in N}
        (i - 1) * p[k] * x[k,i,j,z];

solve;


# Salida para el script
printf "OBJ %f\n", CosteMedio;


# Nivel, fila, columna, prioridad, peso y capacidad
# de cada caja colocada.

printf {z in N, i in F, j in C, k in K : x[k,i,j,z] > 0.5}
    "SOL %d %d %d %d %g %g\n", z, i, j, p[k], w[k], c[k];

# Posiciones vacías.

printf {z in N, i in F, j in C : y[i,j,z] > 0.5}
    "EMPTY %d %d %d\n", z, i, j;

end;