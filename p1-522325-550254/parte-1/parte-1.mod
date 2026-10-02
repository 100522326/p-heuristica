# PARTE 1: Minimización del coste medio

# Parámetros
param l integer, > 0;
param n := l * l;

set K := 1..n;
set F := 1..l;
set C := 1..l;

param p{K} integer, > 0;


#Variables
var x{K,F,C} binary;

#Restricciones
s.t. UnaPosicionPorCaja{k in K}:
    sum{i in F, j in C} x[k,i,j] = 1;

s.t. UnaCajaPorPosicion{i in F, j in C}:
    sum{k in K} x[k,i,j] = 1;

s.t. OrdenPrioridades{k in K, q in K : p[k] < p[q]}:
    sum{i in F, j in C} i * x[k,i,j]
    >=
    sum{i in F, j in C} i * x[q,i,j];


# Función objetivo
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
