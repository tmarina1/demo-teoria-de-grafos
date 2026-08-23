import json
import os
from graph import Graph
from algorithms import bfs, dijkstra
from visualization_html import generate_html_report

def load_graph(filename):
    """
    Lee un archivo JSON y construye el grafo.
    """

    graph = Graph()

    with open(
        filename,
        "r",
        encoding="utf-8"
    ) as file:

        data = json.load(file)

    for station in data["stations"]:
        graph.add_station(
            station["id"],
            station["name"]
        )

    for connection in data["connections"]:
        graph.add_connection(
            connection["from"],
            connection["to"],
            connection["time"]
        )

    return graph

def show_stations(graph):
    print("\nEstaciones disponibles:")
    for name in graph.get_stations().values():
        print(
            f"  {name}"
        )

def print_path(graph, path):
    if not path:
        print(
            "No existe una ruta entre "
            "las estaciones seleccionadas."
        )
        return

    names = [
        graph.get_station_name(
            station
        )
        for station in path
    ]

    print(" → ".join(names))

def select_graph():
    print("\n==============================")
    print("       METRO ROUTE FINDER")
    print("==============================")

    print("\nSeleccione el escenario:")
    print("1. Red simple")
    print("2. Red compleja")

    while True:

        option = input(
            "\nOpción: "
        ).strip()

        if option == "1":
            return (
                load_graph(
                    "data/metro_simple.json"
                ),
                "simple"
            )

        if option == "2":
            return (
                load_graph(
                    "data/metro_complex.json"
                ),
                "complex"
            )
        print( "Opción inválida.")


def select_station(
    graph,
    message
):

    while True:
        station = input(message).strip().upper()
        if station in graph.get_stations():
            return station
        print("La estación no existe.")

def select_algorithm():
    print("\n==============================")
    print("       SELECCIONE ALGORITMO")
    print("==============================")

    print("1. BFS")
    print("2. Dijkstra")

    while True:
        option = input("\nOpción: ").strip()
        if option == "1":
            return "BFS"

        if option == "2":
            return "Dijkstra"

        print("Opción inválida.")

def main():
    os.makedirs(
        "output",
        exist_ok=True
    )

    graph, scenario = select_graph()
    scenario_output = os.path.join(
        "output",
        scenario
    )

    os.makedirs(
        scenario_output,
        exist_ok=True
    )

    show_stations(
        graph
    )

    start = select_station(graph,"\nEstación de origen: ")
    target = select_station(graph,"Estación de destino: ")
    algorithm = select_algorithm()

    print("\n==============================")
    print(f"      EJECUTANDO {algorithm}")
    print("==============================")

    if algorithm == "BFS":
        path, visit_order = bfs(
            graph,
            start,
            target
        )
        total_time = None
    else:
        (
            path,
            total_time,
            visit_order
        ) = dijkstra(
            graph,
            start,
            target
        )

    print("\n==============================")
    print("           RESULTADO")
    print("==============================")

    print(f"\nAlgoritmo: {algorithm}")
    print(f"Origen: {graph.get_station_name(start)}")
    print(f"Destino: {graph.get_station_name(target)}")
    print("\nRuta encontrada:")

    print_path(graph, path)

    print("\nOrden de visita:")

    print_path(graph, visit_order)

    if path:
        print(f"\nNúmero de estaciones: {len(path)}")
        print(f"Número de conexiones: {len(path) - 1}")

        if total_time is not None:
            print(f"Tiempo total: {total_time} minutos")

    html_file = os.path.join(scenario_output, "resultados.html")

    generate_html_report(
        graph=graph,
        visit_order=visit_order,
        path=path,
        start=start,
        target=target,
        algorithm=algorithm,
        total_time=total_time,
        output_file=html_file
    )

    print(f"✓ Generado: {html_file}")
    print("\n==============================")
    print(f"Resultados generados correctamente en '{scenario_output}'.")

if __name__ == "__main__":
    main()