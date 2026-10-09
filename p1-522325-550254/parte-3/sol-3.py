#!/usr/bin/env python3

import subprocess, argparse, sys, re, os


# Directorio del script: el modelo se busca aqui y los ficheros indicados
# sin ruta se buscan/crean en la carpeta ejemplos.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_FILE = os.path.join(SCRIPT_DIR, "parte-3.mod")
EXAMPLES_DIR = os.path.join(SCRIPT_DIR, "ejemplos")


def resolve_path(path: str) -> str:
    """
    Si el fichero se indica sin ninguna ruta, se asume la carpeta ejemplos
    del script. En otro caso, se respeta la ruta indicada.
    """
    if os.path.dirname(path) == "":
        os.makedirs(EXAMPLES_DIR, exist_ok=True)
        return os.path.join(EXAMPLES_DIR, path)

    return path


def tokenize_line(line: str) -> list[str]:
    """
    Dada una linea del fichero de entrada, devuelve una lista
    con cada uno de los numeros que esta contiene.
    """

    line = line.strip()

    # Permitimos que los valores esten separados por comas
    # o por espacios.
    line = line.replace(',', ' ')

    tokens = []

    for token in line.split():
        if token:
            tokens.append(token)

    return tokens


def read_file(path: str) -> dict:
    """
    Lee el fichero de entrada, valida los datos y devuelve un diccionario
    con dichos datos ordenados.
    """

    lines = []
    with open(path, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()

            if not line:
                continue
            lines.append(line)

    if len(lines) != 4:
        raise ValueError("El fichero de entrada debe tener 4 lineas")

    # Primera linea: lado y numero maximo de niveles
    line = tokenize_line(lines[0])
    if len(line) != 2:
        raise ValueError(
            "La primera linea debe contener el lado del pallet y el numero maximo de niveles")

    side = int(line[0])
    if side <= 0:
        raise ValueError("El lado del pallet debe ser mayor que 0")

    levels = int(line[1])
    if levels <= 0:
        raise ValueError("El numero de niveles debe ser mayor que 0")

    max_boxes = levels * side * side

    # Segunda linea: prioridades

    priorities = tuple(int(x) for x in tokenize_line(lines[1]))
    n = len(priorities)
    if n <= 0:
        raise ValueError("Debe existir al menos una caja")

    if n > max_boxes:
        raise ValueError(f"El numero de cajas no puede superar "f"{max_boxes}")

    # Tercera linea: pesos

    weights = tuple(int(x) for x in tokenize_line(lines[2]))
    if len(weights) != n:
        raise ValueError(f"La tercera linea debe contener {n} pesos")

    if any(x < 0 for x in weights):
        raise ValueError("Los pesos no pueden ser negativos")

    # Cuarta linea: capacidades

    capacities = tuple(int(x) for x in tokenize_line(lines[3]))

    if len(capacities) != n:
        raise ValueError(f"La cuarta linea debe contener {n} capacidades")

    if any(x < 0 for x in capacities):
        raise ValueError("Las capacidades no pueden ser negativas")

    return {
        "side": side,
        "levels": levels,
        "n": n,
        "priorities": priorities,
        "weights": weights,
        "capacities": capacities,
    }


def write_dat_file(path: str, data: dict) -> None:
    """
    Escribe el fichero .dat a partir de los datos de entrada.
    """

    side = data["side"]
    levels = data["levels"]
    n = data["n"]
    priorities = data["priorities"]
    weights = data["weights"]
    capacities = data["capacities"]

    with open(path, 'w', encoding='utf-8') as dat:
        dat.write("data;\n\n")
        dat.write(f"param l := {side};\n")
        dat.write(f"param h := {levels};\n")
        dat.write(f"param n := {n};\n\n")
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
    Ejecuta GLPK con el modelo y los datos del problema.
    """

    command = ["glpsol", "-m", str(model), "-d", str(dat)]

    process = subprocess.run(command, capture_output=True, text=True)

    if process.returncode != 0:
        raise RuntimeError(f"Fallo al ejecutar GLPK {process.returncode}\n"f"{process.stdout}\n{process.stderr}")

    return process.stdout


def parse_out_info(output: str) -> dict:
    """
    Lee la salida de GLPK y extrae la informacion de la solucion.
    """

    if "INTEGER OPTIMAL SOLUTION FOUND" not in output:
        raise RuntimeError("No hay solución óptima")

    # GLPK cuenta la funcion objetivo como una fila.
    # Por eso se resta una fila para obtener el numero de restricciones.
    m = re.search(r'(\d+) rows, (\d+) columns', output)

    if m is None:
        raise RuntimeError("No se pudo obtener el tamaño del modelo")

    constraints_count = int(m.group(1)) - 1
    var_count = int(m.group(2))

    # Valor de la funcion objetivo.
    m = re.search(r'^OBJ (\S+)', output, flags=re.M)

    if m is None:
        raise RuntimeError("No se pudo obtener el valor de la funcion objetivo")

    obj_value = float(m.group(1))

    # Posiciones ocupadas por cajas.

    pallet = {}

    for level, row, col, priority, weight, capacity in re.findall(r'^SOL (\d+) (\d+) (\d+) (\d+) (\S+) (\S+)', output, flags=re.M):
        pallet[int(level), int(row), int(col)] = (int(priority), weight, capacity)

    # Posiciones vacias.

    empty_positions = set()
    for level, row, col in re.findall(r'^EMPTY (\d+) (\d+) (\d+)', output, flags=re.M):
        empty_positions.add((int(level), int(row), int(col)))

    return {
        "obj_value": obj_value,
        "var_count": var_count,
        "constraints_count": constraints_count,
        "pallet": pallet,
        "empty_positions": empty_positions,
    }


def write_sol_file(path: str, data: dict, info: dict) -> None:
    """
    Escribe el fichero de salida con la representacion
    de todos los niveles del pallet.

    Las posiciones vacias se representan mediante '-'.
    """

    side = data["side"]
    levels = data["levels"]
    pallet = info["pallet"]
    empty_positions = info["empty_positions"]

    # Texto de cada celda.

    cells = {}
    for pos, (priority, weight, capacity) in pallet.items():
        cells[pos] = (f"{priority} ({weight}/{capacity})")

    for pos in empty_positions:
        cells[pos] = "-"

    # Puede ocurrir que alguna posicion no se haya incluido
    # explicitamente. tambien la ponemos como vacia.
    for level in range(1, levels + 1):
        for row in range(1, side + 1):
            for col in range(1, side + 1):
                if (level, row, col) not in cells:
                    cells[level, row, col] = "-"

    width = max(len(text) for text in cells.values()) + 2
    separator = ("         +"+ ("-" * width + "+") * side)
    with open(path, 'w', encoding='utf-8') as sol:

        sol.write(f"Pallet {side}x{side} con {levels} niveles "f"y {data['n']} cajas\n")
        sol.write(f"Coste medio = {info['obj_value']:.2f}\n")
        sol.write("Cada caja: prioridad (peso/capacidad)\n")
        sol.write("Las posiciones vacias se representan mediante '-'.\n")

        for level in range(1, levels + 1):
            sol.write(f"\nNivel {level}\n")
            sol.write("ACCESO".center(len(separator))+ "\n")
            sol.write("v".center(len(separator))+ "\n")
            sol.write(separator + "\n")
            for row in range(side, 0, -1):
                cells_text = "|".join(cells[level,row, col].center(width)for col in range(1, side + 1))
                sol.write(f"Fila {row:>3} |"f"{cells_text}|\n")
                sol.write(separator + "\n")
            sol.write("          " + " ".join(f"Col {col}".center(width) for col in range(1, side + 1)) + "\n")


def main():
    """
    Funcion principal.

    Lee los argumentos, lee el fichero de entrada, genera
    el .dat, ejecuta GLPK, escribe el fichero de salida
    y muestra por pantalla las estadisticas del modelo.
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("in_file", type=str, help="fichero de entrada (.in)")
    parser.add_argument("dat_file", type=str, help="fichero de datos (.dat)")

    args = parser.parse_args()

    infile = resolve_path(args.in_file)
    datfile = resolve_path(args.dat_file)
    solfile = os.path.splitext(datfile)[0] + ".sol"

    # Lectura del fichero de entrada.

    try:
        data = read_file(infile)

    except Exception as e:
        print(f"Error al leer el fichero de entrada: {e}", file=sys.stderr)
        sys.exit(-1)

    # Generacion del fichero .dat.

    try:
        write_dat_file(datfile, data)
    except Exception as e:
        print(f"Error al escribir el fichero .dat: {e}", file=sys.stderr)
        sys.exit(-1)

    # Ejecucion de GLPK.

    try:
        output = run_glpk_solver(MODEL_FILE, datfile)
        info = parse_out_info(output)

    except Exception as e:
        print(f"Error al ejecutar glpk: {e}", file=sys.stderr)
        sys.exit(-1)

    try:
        write_sol_file(solfile, data, info)

    except Exception as e:
        print(f"Error al escribir el fichero de salida: {e}", file=sys.stderr)
        sys.exit(-1)

    # Salida
    print(f"{info['var_count']} {info['constraints_count']} {info['obj_value']:.2f}")


if __name__ == "__main__":
    main()