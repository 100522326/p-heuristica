# PARTE 1: Minimización del coste medio

# Parámetros
# l: lado del pallet; n: número de cajas (el pallet se llena: n = l^2)
param l integer, > 0;
param n := l * l;

set K := 1..n;
set F := 1..l;
set C := 1..l;

# Prioridad de cada caja (1 = máxima prioridad)
param p{K} integer, > 0;


# Variables
# x[k,i,j] = 1 si la caja k se coloca en la fila i y la columna j.
# La fila l es la más cercana al punto de acceso.
var x{K,F,C} binary;

# Restricciones

# 1. Cada caja ocupa una única posición.
s.t. UnaPosicionPorCaja{k in K}:
    sum{i in F, j in C} x[k,i,j] = 1;

# 2. Cada posición contiene exactamente una caja.
s.t. UnaCajaPorPosicion{i in F, j in C}:
    sum{k in K} x[k,i,j] = 1;

# 3. Si k tiene más prioridad que q (p[k] < p[q]), k debe estar en una fila
#    igual o más cercana al acceso que q.
s.t. OrdenPrioridades{k in K, q in K : p[k] < p[q]}:
    sum{i in F, j in C} i * x[k,i,j]
    >=
    sum{i in F, j in C} i * x[q,i,j];


# Función objetivo: coste medio. Cada caja en la fila i suma su prioridad al
# coste de las i-1 cajas que tiene detrás en su columna.
minimize CosteMedio:
    (1 / n) *
    sum{k in K, i in F, j in C}
        (i-1) * p[k] * x[k,i,j];

solve;

# Salida de la solución (archivo .sol): valor de la función objetivo
printf "OBJ %f\n", CosteMedio;

# Dibujo de la solucion: para cada posición, fila, columna y prioridad de la caja colocada
printf {i in F, j in C, k in K : x[k,i,j] > 0.5} "SOL %d %d %d\n", i, j, p[k];

end;
