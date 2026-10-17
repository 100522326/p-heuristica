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

# Prioridad máxima (valor numérico más alto). Se usa para la constante
# M_i = (l - i) * pmax de la restricción condicional del coste (7), ya que
# GLPK no permite usar infinito.
param pmax := max{k in K} p[k];



# Variables

var x{K,F,C,N} binary;

# y[i,j,z] = 1 si la posición (i,j,z) está vacía.
var y{F,C,N} binary;

# u[i,j,z] = coste de la posición (i,j,z): suma de las prioridades de las
# cajas de su misma columna y nivel que tiene delante (filas i+1..l).
# La fila l no tiene nada delante, así que no se define.
var u{i in F, j in C, z in N : i < l} >= 0;

# Restricciones

# 1. Cada caja ocupa una única posición.
s.t. UnaPosicionPorCaja{k in K}:
    sum{i in F, j in C, z in N} x[k,i,j,z] = 1;

# 2. Cada posición está ocupada por una caja o está vacía.
s.t. UnaCajaOVacia{i in F, j in C, z in N}:
    sum{k in K} x[k,i,j,z] + y[i,j,z] = 1;

# 3. Orden de las prioridades dentro de cada nivel.
s.t. OrdenPrioridades{z in N, i in F, k in K, q in K : i > 1 and p[k] < p[q]}:
    sum{j in C} x[q,i,j,z]
    + sum{i2 in F, j in C : i2 < i} x[k,i2,j,z]
    <= 1;

# 4. Las posiciones vacías tienen la prioridad mínima.
s.t. OrdenVacios{z in N, i in F, j in C, k in K : i > 1}:
    y[i,j,z]
    + sum{i2 in F, j2 in C : i2 < i} x[k,i2,j2,z]
    <= 1;

# 5. Capacidad de carga.
s.t. Capacidad{i in F, j in C, z in N : z < h}:
    sum{k in K, z2 in N : z2 > z} w[k] * x[k,i,j,z2]
    <=
    sum{k in K} c[k] * x[k,i,j,z];

# 6. No hay cajas sobre posiciones vacías.
s.t. NoSobreVacio{i in F, j in C, z in N : z < h}:
    y[i,j,z] <= y[i,j,z+1];

# 7. Coste de cada posición (restricción condicional):
#    si y = 1 (vacía)  => u = 0
#    si y = 0 (ocupada) => u = suma de las prioridades de delante

# 7a. Coste mínimo si la posición está ocupada.
s.t. CostePosicion{i in F, j in C, z in N : i < l}:
    u[i,j,z]
    >=
    sum{k in K, i2 in F : i2 > i} p[k] * x[k,i2,j,z]
    - (l - i) * pmax * y[i,j,z];

# 7b. Coste máximo si la posición está ocupada.
s.t. CosteOcupada{i in F, j in C, z in N : i < l}:
    u[i,j,z]
    <=
    sum{k in K, i2 in F : i2 > i} p[k] * x[k,i2,j,z]
    + (l - i) * pmax * y[i,j,z];

# 7c. Coste nulo si la posición está vacía.
s.t. CosteVacia{i in F, j in C, z in N : i < l}:
    u[i,j,z] <= (l - i) * pmax * (1 - y[i,j,z]);


# Función objetivo: coste medio, sumando el coste de cada posición.

minimize CosteMedio:
    (1 / n) *
    sum{i in F, j in C, z in N : i < l} u[i,j,z];

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