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

# Prioridad máxima, para la constante M_i = (l - i) * pmax del coste.
param pmax := max{k in K} p[k];

# Variables
# x[k,i,j,z,a] = 1 si la caja k ocupa la posición (i,j,z) del pallet a.
var x{K,F,C,N,A} binary;

# y[i,j,z,a] = 1 si la posición (i,j,z) del pallet a está vacía.
var y{F,C,N,A} binary;

# u[i,j,z,a] = coste de la posición (i,j,z) del pallet a (como en la Parte 3).
var u{i in F, j in C, z in N, a in A : i < l} >= 0;

# v[a] = 1 si se utiliza el pallet a. Como mucho hacen falta n pallets.
var v{A} binary;

# Restricciones

# 1. Cada caja ocupa una única posición en uno de los pallets.
s.t. UnaPosicionPorCaja{k in K}:
    sum{i in F, j in C, z in N, a in A} x[k,i,j,z,a] = 1;

# 2. Cada posición de un pallet usado está ocupada por una caja o vacía.
# En un pallet no usado, todas las variables de posición valen 0.
s.t. UnaCajaOVacia{i in F, j in C, z in N, a in A}:
    sum{k in K} x[k,i,j,z,a] + y[i,j,z,a] = v[a];

# 3. Cada pallet usado debe contener al menos una caja.
s.t. PalletUsado{a in A}:
    v[a] <= sum{k in K, i in F, j in C, z in N} x[k,i,j,z,a];

# 4. Orden de prioridades dentro de cada nivel y pallet.
s.t. OrdenPrioridades{a in A, z in N, i in F, k in K, q in K :
                      i > 1 and p[k] < p[q]}:
    sum{j in C} x[q,i,j,z,a]
    + sum{i2 in F, j in C : i2 < i} x[k,i2,j,z,a] <= 1;

# 5. Las posiciones vacías tienen la prioridad mínima.
s.t. OrdenVacios{a in A, z in N, i in F, j in C, k in K : i > 1}:
    y[i,j,z,a]
    + sum{i2 in F, j2 in C : i2 < i} x[k,i2,j2,z,a] <= 1;

# 6. Capacidad de carga en cada pallet.
s.t. Capacidad{i in F, j in C, z in N, a in A : z < h}:
    sum{k in K, z2 in N : z2 > z} w[k] * x[k,i,j,z2,a]
    <= sum{k in K} c[k] * x[k,i,j,z,a];

# 7. No hay cajas sobre posiciones vacías.
s.t. NoSobreVacio{i in F, j in C, z in N, a in A : z < h}:
    y[i,j,z,a] <= y[i,j,z+1,a];

# 8. Coste de cada posición (restricción condicional, sólo para i < l):
#    si y = 1 (vacía)  => u = 0
#    si y = 0 (ocupada) => u = suma de las prioridades de delante

# 8a. Coste mínimo si la posición está ocupada.
s.t. CostePosicion{i in F, j in C, z in N, a in A : i < l}:
    u[i,j,z,a] >=
    sum{k in K, i2 in F : i2 > i} p[k] * x[k,i2,j,z,a]
    - (l - i) * pmax * y[i,j,z,a];

# 8b. Coste máximo si la posición está ocupada.
s.t. CosteOcupada{i in F, j in C, z in N, a in A : i < l}:
    u[i,j,z,a] <=
    sum{k in K, i2 in F : i2 > i} p[k] * x[k,i2,j,z,a]
    + (l - i) * pmax * y[i,j,z,a];

# 8c. Coste nulo si la posición está vacía.
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

# Pallet, nivel, fila, columna, prioridad, peso y capacidad.
printf {a in A, z in N, i in F, j in C, k in K :
        x[k,i,j,z,a] > 0.5}
    "SOL %d %d %d %d %d %g %g\n", a, z, i, j, p[k], w[k], c[k];

# Posiciones vacías de los pallets usados.
printf {a in A, z in N, i in F, j in C : y[i,j,z,a] > 0.5}
    "EMPTY %d %d %d %d\n", a, z, i, j;

end;
