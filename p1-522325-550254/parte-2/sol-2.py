#!/usr/bin/env python3

import subprocess, argparse, sys, re, os


# Directorio del script: el modelo se busca aqui y los ficheros indicados
# sin ruta se buscan/crean en la carpeta ejemplos.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_FILE = os.path.join(SCRIPT_DIR, "parte-2.mod")
EXAMPLES_DIR = os.path.join(SCRIPT_DIR, "ejemplos")


def resolve_path(path: str) -> str:
    """
    Si el fichero se indica sin ninguna ruta, se asume la carpeta ejemplos
    del script. En otro caso, se respeta la ruta (absoluta o relativa).

    Args:
        path (str): fichero indicado como argumento

    Returns:
        str: path al fichero
    """
    if os.path.dirname(path) == "":
        os.makedirs(EXAMPLES_DIR, exist_ok=True)
        return os.path.join(EXAMPLES_DIR, path)
    return path


def tokenize_line(line: str) -> list[str]:
    """
    Dada una linea del fichero de entrada, devuelve una lista
    con cada uno de los numeros que esta contiene `tokens`.

    Args:
        line (str): linea del fichero

    Returns:
        list[str]: tokens
    """

    line = line.strip()

    # Para tener en cuenta que los valores puedan estar separados por ','
    # o por espacios, transformamos las posibles ',' en ' '.
    line = line.replace(',', ' ')

    # Lista de salida
    tokens = []

    for token in line.split():
        if token:
            tokens.append(token)

    return tokens


def read_file(path: str) -> dict:
    """
    Lee el fichero de entrada, valida los datos y devuelve un diccionario
    con dichos datos ordenados.

    Args:
        path (str): path al fichero de entrada

    Returns:
        dict: diccionario con el lado del pallet, el numero de niveles,
              las prioridades, los pesos y las capacidades
    """
    # Lineas del fichero (para hacer comprobaciones)
    lines = []
    with open(path, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            if not line:
                # Si la linea esta vacia la saltamos.
                continue
            lines.append(line)

    if len(lines) != 4:
        raise ValueError("El fichero de entrada debe tener 4 lineas")

    line = tokenize_line(lines[0])
    if len(line) != 2:
        raise ValueError("La primera linea debe contener el lado del pallet y el numero de niveles")

    side = int(line[0])
    if side <= 0:
        raise ValueError("El lado del pallet debe ser mayor que 0")

    levels = int(line[1])
    if levels <= 0:
        raise ValueError("El numero de niveles debe ser mayor que 0")

    # Numero total de cajas: el pallet se rellena completamente.
    n = levels * side * side

    priorities = tuple(int(x) for x in tokenize_line(lines[1]))
    if len(priorities) != n:
        raise ValueError(f"La segunda linea debe contener {n} prioridades")

    weights = tuple(int(x) for x in tokenize_line(lines[2]))
    if len(weights) != n:
        raise ValueError(f"La tercera linea debe contener {n} pesos")

    capacities = tuple(int(x) for x in tokenize_line(lines[3]))
    if len(capacities) != n:
        raise ValueError(f"La cuarta linea debe contener {n} capacidades")

    # Devolvemos diccionario para los valores leidos.
    return {
        "side": side,
        "levels": levels,
        "priorities": priorities,
        "weights": weights,
        "capacities": capacities,
    }


def write_dat_file(path: str, data: dict) -> None:
    """
    Escribe el fichero .dat dado su path y valores.

    Args:
        path (str): destino fichero .dat
        data (dict): datos del problema leidos del fichero de entrada
    """
    side = data["side"]
    levels = data["levels"]
    priorities = data["priorities"]
    weights = data["weights"]
    capacities = data["capacities"]

    with open(path, 'w', encoding='utf-8') as dat:
        dat.write("data;\n\n")
        dat.write(f"param l := {side};\n")
        dat.write(f"param h := {levels};\n\n")

        dat.write("param p :=\n")
        for box, value in enumerate(priorities, start=1):
            dat.write(f"{box} {value}\n")
        dat.write(";\n\n")

        dat.write("param w :=\n")
        for box, value in enumerate(weights, start=1):
            dat.write(f"{box} {value}\n")
        dat.write(";\n\n")

        dat.write("param c :=\n")
        for box, value in enumerate(capacities, start=1):
            dat.write(f"{box} {value}\n")
        dat.write(";\n\n")

        dat.write("end;\n")


def run_glpk_solver(model: str, dat: str) -> str:
    """
    Ejecuta glpk con el modelo y los datos del problema.

    Args:
        model (str): path al archivo .mod
        dat (str): path al archivo .dat

    Returns:
        str: salida de glpsol por pantalla
    """

    command = ["glpsol", "-m", str(model), "-d", str(dat)]

    process = subprocess.run(command, capture_output=True, text=True)

    if process.returncode != 0:
        raise RuntimeError(f"Fallo al ejecutar GLPK {process.returncode}\n{process.stdout}")

    return process.stdout


def parse_out_info(output: str) -> dict:
    """
    Lee la salida de glpsol y extrae la informacion de la solucion.

    Args:
        output (str): salida de glpsol por pantalla

    Returns:
        dict: valor objetivo, numero de variables, numero de restricciones
              y disposicion de las cajas
    """
    if "INTEGER OPTIMAL SOLUTION FOUND" not in output:
        raise RuntimeError("No hay solución óptima")

    # Tamaño del problema generado. GLPK cuenta la funcion objetivo como
    # una fila mas, asi que se descuenta.
    m = re.search(r'(\d+) rows, (\d+) columns', output)
    constraints_count = int(m.group(1)) - 1
    var_count = int(m.group(2))

    # Valor de la funcion objetivo (linea OBJ que imprime el modelo)
    m = re.search(r'^OBJ (\S+)', output, flags=re.M)
    obj_value = float(m.group(1))

    # Disposicion de las cajas (lineas SOL que imprime el modelo):
    # nivel, fila, columna, prioridad, peso y capacidad de la caja colocada.
    # El peso y la capacidad se imprimen con %g, por lo que se leen como texto.
    pallet = {}
    for level, row, col, priority, weight, capacity in re.findall(
            r'^SOL (\d+) (\d+) (\d+) (\d+) (\S+) (\S+)', output, flags=re.M):
        pallet[int(level), int(row), int(col)] = (int(priority), weight, capacity)

    return {
        "obj_value": obj_value,
        "var_count": var_count,
        "constraints_count": constraints_count,
        "pallet": pallet,
    }


def write_sol_file(path: str, data: dict, info: dict) -> None:
    """
    Escribe el fichero de salida con la vista cenital de cada nivel del
    pallet, desde el nivel 1 (inferior) hasta el nivel h (superior).
    La fila l es la mas cercana al punto de acceso. Cada caja se muestra
    como "prioridad (peso/capacidad)".

    Args:
        path (str): destino fichero .sol
        data (dict): datos del problema leidos del fichero de entrada
        info (dict): informacion de la solucion obtenida con glpsol
    """
    side = data["side"]
    levels = data["levels"]
    pallet = info["pallet"]

    # Texto de cada celda y ancho comun para todas ellas
    cells = {pos: f"{p} ({w}/{c})" for pos, (p, w, c) in pallet.items()}
    width = max(len(text) for text in cells.values()) + 2
    separator = "         +" + ("-" * width + "+") * side

    with open(path, 'w', encoding='utf-8') as sol:
        sol.write(f"Pallet {side}x{side} con {levels} niveles - "
                  f"coste medio = {info['obj_value']:.2f}\n")
        sol.write("Cada caja: prioridad (peso/capacidad)\n")

        for level in range(1, levels + 1):
            sol.write(f"\nNivel {level}\n")
            sol.write("ACCESO".center(len(separator)) + "\n")
            sol.write("v".center(len(separator)) + "\n")
            sol.write(separator + "\n")
            for row in range(side, 0, -1):
                line = "|".join(cells[level, row, col].center(width) for col in range(1, side + 1))
                sol.write(f"Fila {row:>3} |{line}|\n")
                sol.write(separator + "\n")
            sol.write("          " + " ".join(f"Col {col}".center(width) for col in range(1, side + 1)) + "\n")


def main():
    """
    Funcion principal del programa.

    Lee los argumentos, lee el fichero de entrada, genera el .dat, ejecuta
    el solver, escribe el fichero de salida y muestra la informacion en la
    pantalla.
    """
    parser = argparse.ArgumentParser()

    # Argumentos esperados.
    parser.add_argument("in_file", type=str, help="fichero de entrada (.in)")
    parser.add_argument("dat_file", type=str, help="fichero de datos (.dat)")

    args = parser.parse_args()

    infile = resolve_path(args.in_file)
    datfile = resolve_path(args.dat_file)
    solfile = os.path.splitext(datfile)[0] + ".sol"

    try:
        x = read_file(infile)
    except Exception as e:
        print(f"Error al leer el fichero de entrada: {e}", file=sys.stderr)
        sys.exit(-1)

    try:
        write_dat_file(datfile, x)
    except Exception as e:
        print(f"Error al escribir el fichero .dat: {e}", file=sys.stderr)
        sys.exit(-1)

    try:
        output = run_glpk_solver(MODEL_FILE, datfile)
        info = parse_out_info(output)
    except Exception as e:
        print(f"Error al ejecutar glpk: {e}", file=sys.stderr)
        sys.exit(-1)

    try:
        write_sol_file(solfile, x, info)
    except Exception as e:
        print(f"Error al escribir el fichero de salida: {e}", file=sys.stderr)
        sys.exit(-1)

    # Mostrar informacion por la salida estandar (en una unica linea).
    # Formato: numero de variables, numero de restricciones y valor objetivo.
    print(f"{info['var_count']} {info['constraints_count']} {info['obj_value']:.2f}")


if __name__ == "__main__":
    main()
