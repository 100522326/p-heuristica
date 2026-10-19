#!/usr/bin/env python3

import subprocess, argparse, sys, re, os


# Directorio del script: el modelo se busca aqui y los ficheros indicados
# sin ruta se buscan/crean en la carpeta ejemplos.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_FILE = os.path.join(SCRIPT_DIR, "parte-4.mod")
EXAMPLES_DIR = os.path.join(SCRIPT_DIR, "ejemplos")


def resolve_path(path: str) -> str:
    """
    Si el fichero se indica sin ninguna ruta, se asume la carpeta ejemplos.
    En otro caso, se respeta la ruta indicada.
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
    line = line.replace(',', ' ')
    tokens = []

    for token in line.split():
        if token:
            tokens.append(token)

    return tokens


def read_file(path: str) -> dict:
    """
    Lee el fichero de entrada, valida los datos y devuelve un diccionario
    con los datos del problema.
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

    line = tokenize_line(lines[0])
    if len(line) != 3:
        raise ValueError(
            "La primera linea debe contener el lado del pallet, el numero de niveles y el coste P")

    side = int(line[0])
    levels = int(line[1])
    pallet_cost = float(line[2])

    if side <= 0:
        raise ValueError("El lado del pallet debe ser mayor que 0")
    if levels <= 0:
        raise ValueError("El numero de niveles debe ser mayor que 0")
    if pallet_cost < 0:
        raise ValueError("El coste P no puede ser negativo")

    priorities = tuple(int(x) for x in tokenize_line(lines[1]))
    n = len(priorities)
    if n <= 0:
        raise ValueError("Debe existir al menos una caja")

    weights = tuple(int(x) for x in tokenize_line(lines[2]))
    if len(weights) != n:
        raise ValueError(f"La tercera linea debe contener {n} pesos")
    if any(x < 0 for x in weights):
        raise ValueError("Los pesos no pueden ser negativos")

    capacities = tuple(int(x) for x in tokenize_line(lines[3]))
    if len(capacities) != n:
        raise ValueError(f"La cuarta linea debe contener {n} capacidades")
    if any(x < 0 for x in capacities):
        raise ValueError("Las capacidades no pueden ser negativas")

    return {
        "side": side,
        "levels": levels,
        "pallet_cost": pallet_cost,
        "n": n,
        "priorities": priorities,
        "weights": weights,
        "capacities": capacities,
    }


def write_dat_file(path: str, data: dict) -> None:
    """
    Escribe el fichero .dat a partir de los datos de entrada.
    """
    with open(path, 'w', encoding='utf-8') as dat:
        dat.write("data;\n\n")
        dat.write(f"param l := {data['side']};\n")
        dat.write(f"param h := {data['levels']};\n")
        dat.write(f"param n := {data['n']};\n")
        dat.write(f"param P := {data['pallet_cost']};\n\n")

        dat.write("param p :=\n")
        for box, value in enumerate(data["priorities"], start=1):
            dat.write(f"{box} {value}\n")
        dat.write(";\n\n")

        dat.write("param w :=\n")
        for box, value in enumerate(data["weights"], start=1):
            dat.write(f"{box} {value}\n")
        dat.write(";\n\n")

        dat.write("param c :=\n")
        for box, value in enumerate(data["capacities"], start=1):
            dat.write(f"{box} {value}\n")
        dat.write(";\n\n")

        dat.write("end;\n")

def run_glpk_solver(model: str, dat: str) -> str:
    """
    Ejecuta GLPK con el modelo y los datos del problema.
    """
    command = ["glpsol", "-m", str(model), "-d", str(dat)]
    process = subprocess.run(command, capture_output=True, text=True)

    output = process.stdout + "\n" + process.stderr

    if process.returncode != 0:
        raise RuntimeError(
            f"Fallo al ejecutar GLPK {process.returncode}\n{output}"
        )

    return output


def parse_out_info(output: str) -> dict:
    """
    Lee la salida de GLPK y extrae la informacion de la solucion.
    """
    if "INTEGER OPTIMAL SOLUTION FOUND" not in output:
        raise RuntimeError("No hay solución óptima")

    # Obtener el número de filas y columnas del modelo
    m = re.search(
        r'^\s*(\d+) rows,\s*(\d+) columns',
        output,
        flags=re.M
    )

    if m is None:
        raise RuntimeError("No se pudo obtener el tamaño del modelo")

    constraints_count = int(m.group(1))
    var_count = int(m.group(2))

    # Obtener el valor de la función objetivo
    m = re.search(r'^OBJ\s+(\S+)', output, flags=re.M)

    if m is None:
        raise RuntimeError("No se pudo obtener el valor de la funcion objetivo")

    obj_value = float(m.group(1))

    # Obtener el número de pallets utilizados
    m = re.search(r'^PALLETS\s+(\d+)', output, flags=re.M)

    if m is None:
        raise RuntimeError("No se pudo obtener el numero de pallets")

    pallets_count = int(m.group(1))

    # Obtener la posición de cada caja
    pallets = {}

    for pallet, level, row, col, priority, weight, capacity in re.findall(
        r'^SOL\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\S+)\s+(\S+)',
        output,
        flags=re.M
    ):
        key = int(pallet)

        pallets.setdefault(key, {})[
            (int(level), int(row), int(col))
        ] = (int(priority), weight, capacity)

    # Obtener las posiciones vacías
    empty_positions = {}

    for pallet, level, row, col in re.findall(
        r'^EMPTY\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)',
        output,
        flags=re.M
    ):
        key = int(pallet)

        empty_positions.setdefault(key, set()).add(
            (int(level), int(row), int(col))
        )

    return {
        "obj_value": obj_value,
        "var_count": var_count,
        "constraints_count": constraints_count,
        "pallets_count": pallets_count,
        "pallets": pallets,
        "empty_positions": empty_positions,
    }

def write_sol_file(path: str, data: dict, info: dict) -> None:
    """
    Escribe el fichero de salida con una representación visual
    de cada nivel de cada pallet.
    """
    side = data["side"]
    levels = data["levels"]
    pallets = info["pallets"]
    empty_positions = info["empty_positions"]

    # Ancho de las celdas para que todo quede alineado
    width = max(11, max(len(str(p)) for p in data["priorities"]) + 8)
    separator = "         +" + ("-" * width + "+") * side

    with open(path, "w", encoding="utf-8") as sol:
        sol.write(
            f"Pallet {side}x{side} con {levels} niveles "
            f"- coste total = {info['obj_value']:.2f}\n"
        )
        sol.write("Cada caja: prioridad (peso/capacidad)\n")

        # Mostrar cada pallet utilizado
        for pallet_num in sorted(pallets):
            sol.write(f"\nPALLET {pallet_num}\n")

            for level in range(1, levels + 1):
                sol.write(f"\nNivel {level}\n")
                sol.write("              ACCESO\n")
                sol.write("                v\n")
                sol.write(separator + "\n")

                # Mostrar las filas desde la parte trasera hasta el acceso
                for row in range(side, 0, -1):
                    cells = []

                    for col in range(1, side + 1):
                        key = (level, row, col)

                        if key in pallets[pallet_num]:
                            priority, weight, capacity = pallets[pallet_num][key]
                            value = f"{priority} ({weight}/{capacity})"
                        else:
                            value = ""

                        cells.append(value.center(width))

                    sol.write(
                        f"Fila {row:>3} |"
                        + "|".join(cells)
                        + "|\n"
                    )
                    sol.write(separator + "\n")

                # Etiquetas de las columnas
                labels = "".join(
                    f"Col {col}".center(width + 1)
                    for col in range(1, side + 1)
                )
                sol.write("          " + labels + "\n")

        sol.write(f"\nCoste total = {info['obj_value']:.2f}\n")
        sol.write(f"Numero de pallets = {info['pallets_count']}\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("in_file", type=str, help="fichero de entrada (.in)")
    parser.add_argument("dat_file", type=str, help="fichero de datos (.dat)")
    args = parser.parse_args()

    infile = resolve_path(args.in_file)
    datfile = resolve_path(args.dat_file)
    solfile = os.path.splitext(datfile)[0] + ".sol"

    try:
        data = read_file(infile)
    except Exception as e:
        print(f"Error al leer el fichero de entrada: {e}", file=sys.stderr)
        sys.exit(-1)

    try:
        write_dat_file(datfile, data)
    except Exception as e:
        print(f"Error al escribir el fichero .dat: {e}", file=sys.stderr)
        sys.exit(-1)

    try:
        output = run_glpk_solver(MODEL_FILE, datfile)
        info = parse_out_info(output)
    except Exception as e:
        print(f"Error al ejecutar GLPK: {e}", file=sys.stderr)
        sys.exit(-1)

    try:
        write_sol_file(solfile, data, info)
    except Exception as e:
        print(f"Error al escribir el fichero de salida: {e}", file=sys.stderr)
        sys.exit(-1)

    print(f"Variables: {info['var_count']} | Restricciones: {info['constraints_count']} | "
          f"Pallets: {info['pallets_count']} | Coste total: {info['obj_value']:.2f}")


if __name__ == "__main__":
    main()
