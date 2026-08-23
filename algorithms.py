from collections import deque
import heapq


def build_path(previous, start, target):
    """
    Reconstruye el camino desde el destino hasta el origen.
    """
    if target not in previous:
        return []

    path = []
    current = target

    while current is not None:
        path.append(current)
        current = previous[current]

    path.reverse()

    if path[0] != start:
        return []

    return path


def bfs(graph, start, target):
    """
    Breadth-First Search.

    Encuentra el camino con menor cantidad
    de conexiones.
    """
    
    queue = deque([start])
    visited = {start}
    previous = {
        start: None
    }
    visit_order = []

    while queue:
        current = queue.popleft()
        visit_order.append(current)

        if current == target:
            break

        for neighbor in graph.get_neighbors(current):
            station = neighbor["station"]

            if station not in visited:
                visited.add(station)
                previous[station] = current
                queue.append(station)

    path = build_path(
        previous,
        start,
        target
    )
    return path, visit_order


def dijkstra(graph, start, target):
    """
    Algoritmo de Dijkstra.

    Encuentra el camino cuyo costo total
    sea mínimo.

    En nuestro caso el costo representa
    tiempo en minutos.
    """

    distances = {
        station: float("inf")
        for station in graph.get_stations()
    }
    previous = {
        station: None
        for station in graph.get_stations()
    }
    distances[start] = 0
    priority_queue = [
        (0, start)
    ]
    visit_order = []

    while priority_queue:
        current_distance, current = heapq.heappop(
            priority_queue
        )

        if current_distance > distances[current]:
            continue

        if current in visit_order:
            continue

        visit_order.append(current)

        if current == target:
            break

        for neighbor in graph.get_neighbors(current):
            station = neighbor["station"]
            time = neighbor["time"]
            new_distance = current_distance + time

            if new_distance < distances[station]:
                distances[station] = new_distance
                previous[station] = current
                heapq.heappush(
                    priority_queue,
                    (new_distance, station)
                )

    path = build_path(
        previous,
        start,
        target
    )

    return path, distances[target], visit_order