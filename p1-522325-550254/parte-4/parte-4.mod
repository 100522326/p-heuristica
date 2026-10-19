# PARTE 4: Optimización del montaje en una cantidad arbitraria de pallets incompletos

# Parámetros
param l integer, > 0;
param h integer, > 0;
param n integer, > 0;
param P >= 0;

set K := 1..n;
set F := 1..l;
set C := 1..l;
set N := 1..h;
set A := 1..n;

param p{K} integer, > 0;
param w{K} >= 0;
param c{K} >= 0;

param pmax := max{k in K} p[k];

# Variables
var x{K,F,C,N,A} binary;
var y{F,C,N,A} binary;
var u{i in F, j in C, z in N, a in A : i < l} >= 0;
var v{A} binary;

# Restricciones

# Cada caja ocupa una única posición en uno de los pallets.
s.t. UnaPosicionPorCaja{k in K}:
    sum{i in F, j in C, z in N, a in A} x[k,i,j,z,a] = 1;

# Cada posición de un pallet usado está ocupada por una caja o vacía.
# En un pallet no usado, todas las variables de posición valen 0.
s.t. UnaCajaOVacia{i in F, j in C, z in N, a in A}:
    sum{k in K} x[k,i,j,z,a] + y[i,j,z,a] = v[a];

# Cada pallet usado debe contener al menos una caja.
s.t. PalletUsado{a in A}:
    v[a] <= sum{k in K, i in F, j in C, z in N} x[k,i,j,z,a];

# Orden de prioridades dentro de cada nivel y pallet.
s.t. OrdenPrioridades{a in A, z in N, i in F, k in K, q in K :
                      i > 1 and p[k] < p[q]}:
    sum{j in C} x[q,i,j,z,a]
    + sum{i2 in F, j in C : i2 < i} x[k,i2,j,z,a] <= 1;

# Las posiciones vacías tienen la prioridad mínima.
s.t. OrdenVacios{a in A, z in N, i in F, j in C, k in K : i > 1}:
    y[i,j,z,a]
    + sum{i2 in F, j2 in C : i2 < i} x[k,i2,j2,z,a] <= 1;

# Capacidad de carga en cada pallet.
s.t. Capacidad{i in F, j in C, z in N, a in A : z < h}:
    sum{k in K, z2 in N : z2 > z} w[k] * x[k,i,j,z2,a]
    <= sum{k in K} c[k] * x[k,i,j,z,a];

# No hay cajas sobre posiciones vacías.
s.t. NoSobreVacio{i in F, j in C, z in N, a in A : z < h}:
    y[i,j,z,a] <= y[i,j,z+1,a];

# Coste de cada posición (solo se define para i < l).
s.t. CostePosicion{i in F, j in C, z in N, a in A : i < l}:
    u[i,j,z,a] >=
    sum{k in K, i2 in F : i2 > i} p[k] * x[k,i2,j,z,a]
    - (l - i) * pmax * y[i,j,z,a];

s.t. CosteOcupada{i in F, j in C, z in N, a in A : i < l}:
    u[i,j,z,a] <=
    sum{k in K, i2 in F : i2 > i} p[k] * x[k,i2,j,z,a]
    + (l - i) * pmax * y[i,j,z,a];

s.t. CosteVacia{i in F, j in C, z in N, a in A : i < l}:
    u[i,j,z,a] <= (l - i) * pmax * (1 - y[i,j,z,a]);

# Función objetivo: coste de las posiciones más el coste P de cada pallet usado.
minimize CosteTotal:
    sum{a in A} (
        sum{i in F, j in C, z in N : i < l} u[i,j,z,a]
        + P * v[a]
    );

solve;

printf "OBJ %f\n", CosteTotal;
printf "PALLETS %d\n", sum{a in A} v[a];

# Nivel, pallet, fila, columna, prioridad, peso y capacidad.
printf {a in A, z in N, i in F, j in C, k in K :
        x[k,i,j,z,a] > 0.5}
    "SOL %d %d %d %d %d %g %g\n", a, z, i, j, p[k], w[k], c[k];

# Posiciones vacías de los pallets usados.
printf {a in A, z in N, i in F, j in C : y[i,j,z,a] > 0.5}
    "EMPTY %d %d %d %d\n", a, z, i, j;

end;
