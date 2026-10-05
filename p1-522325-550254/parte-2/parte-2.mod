# PARTE 2: Montaje volumétrico
#
# Pallet cuadrado de lado l con h niveles y n = h * l^2 cajas (se llena
# entero). En cada nivel, la fila 1 es el fondo y la fila l la más cercana
# al punto de acceso. El nivel 1 es el inferior y el nivel h el superior.

# Parámetros
param l integer, > 0;               # lado del pallet
param h integer, > 0;               # número de niveles
param n := h * l * l;               # número de cajas

set K := 1..n;                      # cajas
set F := 1..l;                      # filas (1 = fondo, l = junto al acceso)
set C := 1..l;                      # columnas
set N := 1..h;                      # niveles (1 = inferior, h = superior)

param p{K} integer, > 0;            # prioridad de cada caja (1 = la máxima)
param peso{K} >= 0;                 # peso de cada caja (g)
param capacidad{K} >= 0;            # peso máximo que soporta encima (g)

# Variables
# x[k,i,j,z] = 1 si la caja k se coloca en la fila i, columna j y nivel z;
# 0 en otro caso
var x{K,F,C,N} binary;

# Restricciones
# Cada caja ocupa exactamente una posición
s.t. UnaPosicionPorCaja{k in K}:
    sum{i in F, j in C, z in N} x[k,i,j,z] = 1;

# Cada posición contiene exactamente una caja (el pallet se llena entero)
s.t. UnaCajaPorPosicion{i in F, j in C, z in N}:
    sum{k in K} x[k,i,j,z] = 1;

# Prioridad únicamente dentro del mismo nivel: si la caja q (menos
# prioritaria que k) está en la fila i del nivel z, entonces k no puede estar
# en ninguna fila por detrás de i (filas < i) de ese mismo nivel. Si k y q
# están en niveles distintos, la restricción no les afecta.
# Para i = 1 no hay filas por detrás, así que se omite.
s.t. OrdenPrioridades{z in N, i in F, k in K, q in K : i > 1 and p[k] < p[q]}:
    sum{j in C} x[q,i,j,z]
    + sum{i2 in F, j in C : i2 < i} x[k,i2,j,z]
    <= 1;

# El peso de las cajas que hay encima de cada posición (misma fila y
# columna, niveles superiores) no puede superar la capacidad de la caja
# colocada en ella. Como cada posición tiene exactamente una caja, el lado
# derecho es justo la capacidad de esa caja. En el nivel superior no hay nada
# encima, así que se omite.
s.t. Capacidad{i in F, j in C, z in N : z < h}:
    sum{k in K, z2 in N : z2 > z} peso[k] * x[k,i,j,z2]
    <=
    sum{k in K} capacidad[k] * x[k,i,j,z];


# Función objetivo
# Mismo coste que en la parte 1, aplicado a cada nivel por separado: una
# caja en la fila i contribuye con su prioridad al coste de las (i-1) cajas
# que tiene detrás en su columna y nivel. El nivel no altera el coste.
# Se divide entre n para obtener el coste medio.
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
    "SOL %d %d %d %d %g %g\n", z, i, j, p[k], peso[k], capacidad[k];

end;
