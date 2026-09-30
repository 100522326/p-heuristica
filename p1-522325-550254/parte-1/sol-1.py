import sys
import subprocess

def main():
    #Comprobar los argumentos
    if len(sys.argv) != 2:
        print("Uso: python sol-1.py <fichero_entrada.in>")
        sys.exit(1)

    fichero_entrada = sys.argv[1]

    #Lee el fichero de entrada
    with open(fichero_entrada, "r") as f:
        datos = f.read().split()

    l = int(datos[0])
    prioridades = [int(x) for x in datos[1:]]

    n = l * l

    if len(prioridades) != n:
        print("Error: el número de prioridades no coincide con l^2.")
        sys.exit(1)

    #Crear el fichero .dat
    fichero_dat = "parte1.dat"

    with open(fichero_dat, "w") as f:
        f.write("data;\n\n")
        f.write(f"param l := {l};\n\n")
        f.write(f"param p := \n")
        for k, prioridad in enumerate(prioridades, start=1):
            f.write(f"{k} {prioridad}\n")
        f.write(";\n\n")
        f.write("end;\n")


    #Ejecutar GLPK
    resultado = subprocess.run(["glpsol","-m", "parte1.mod", "-d", fichero_dat], capture_output=True, text=True)

    if resultado.returncode != 0:
        print("Error al ejecutar GLPK:")
        print(resultado.stdout)
        print(resultado.stderr)
        sys.exit(1)

    salida_glpk = resultado.stdout

    #Comprobar que se ha encontrado una solución óptima
    if "INTEGER OPTIMAL SOLUTION FOUND" not in salida_glpk.upper():
        print("Error: GLPK no ha encontrado una solución óptima.")
        sys.exit(1)

    # Obtener el valor de la función objetivo
    objetivo = None
    for linea in salida_glpk.splitlines():
        if "mip =" in linea and "not found yet" not in linea:
            partes = linea.split()
            objetivo = float(partes[4])
            break

    if objetivo is None:
        print("Error: no se ha encontrado el valor de la función objetivo.")
        sys.exit(1)

    #Calcular el número de variables
    numero_variables = n * l * l

    #Calcular el número de restricciones
    numero_prioridad = 0

    for k in range(n):
        for q in range(n):
            if prioridades[k] < prioridades[q]:
                numero_prioridad += 1

    numero_restricciones = (n + l * l + numero_prioridad)

    print(numero_variables, numero_restricciones, objetivo)

if __name__ == "__main__":
    main()