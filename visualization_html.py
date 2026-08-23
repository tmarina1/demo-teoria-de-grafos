import os
from html import escape

import networkx as nx


SIMPLE_POSITIONS = {
    "FLORESTA": (0, 2),
    "ESTADIO": (2, 3),
    "CENTRO": (2, 1),
    "PARQUE BERRIO": (4, 2),
    "SAN ANTONIO": (6, 2),
}


def create_networkx_graph(graph):
    nx_graph = nx.Graph()

    for station_id, name in graph.get_stations().items():
        nx_graph.add_node(station_id, name=name)

    for source, neighbors in graph.connections.items():
        for neighbor in neighbors:
            destination = neighbor["station"]
            if nx_graph.has_edge(source, destination):
                continue
            nx_graph.add_edge(
                source,
                destination,
                weight=neighbor["time"]
            )

    return nx_graph


def get_positions(graph):
    nx_graph = create_networkx_graph(graph)
    station_ids = list(graph.get_stations().keys())

    if len(station_ids) <= 5:
        positions = {
            station: SIMPLE_POSITIONS[station]
            for station in station_ids
            if station in SIMPLE_POSITIONS
        }
        missing = [station for station in station_ids if station not in positions]
        if missing:
            extra = nx.spring_layout(nx_graph.subgraph(missing), seed=42, scale=2)
            positions.update({
                station: (extra[station][0] + 6, extra[station][1] + 2)
                for station in missing
            })
        return positions

    components = sorted(nx.connected_components(nx_graph), key=len, reverse=True)
    layout_graph = nx_graph.subgraph(components[0]).copy()
    positions = nx.spring_layout(
        layout_graph,
        seed=42,
        k=5.5,
        iterations=500,
        scale=5
    )

    x_values = [point[0] for point in positions.values()]
    y_values = [point[1] for point in positions.values()]
    min_x, max_x = min(x_values), max(x_values)
    min_y, max_y = min(y_values), max(y_values)
    width = max(max_x - min_x, 1)
    height = max(max_y - min_y, 1)

    normalized = {
        station: (
            ((point[0] - min_x) / width) * 42,
            ((point[1] - min_y) / height) * 24
        )
        for station, point in positions.items()
    }

    isolated = [station for component in components[1:] for station in component]
    for index, station in enumerate(isolated):
        normalized[station] = (
            21 + (index % 4) * 5,
            27 + (index // 4) * 4
        )

    return normalized


def _svg_graph(graph, position, visit_order=None, path=None, start=None, target=None):
    visit_order = visit_order or []
    path = path or []
    padding = 90
    scale = 28
    max_x = max(point[0] for point in position.values())
    max_y = max(point[1] for point in position.values())
    width = max(900, int(max_x * scale + padding * 2))
    height = max(520, int(max_y * scale + padding * 2))

    def point(station):
        x, y = position[station]
        return padding + x * scale, height - padding - y * scale

    nx_graph = create_networkx_graph(graph)
    route_edges = set(zip(path[:-1], path[1:]))
    route_edges.update((destination, source) for source, destination in tuple(route_edges))
    lines = []

    for source, destination in nx_graph.edges():
        source_x, source_y = point(source)
        destination_x, destination_y = point(destination)
        route_class = "route" if (source, destination) in route_edges else ""
        lines.append(
            f'<line class="edge {route_class}" x1="{source_x:.1f}" '
            f'y1="{source_y:.1f}" x2="{destination_x:.1f}" '
            f'y2="{destination_y:.1f}" />'
        )
        label_x = (source_x + destination_x) / 2
        label_y = (source_y + destination_y) / 2 - 8
        lines.append(
            f'<text class="edge-label" x="{label_x:.1f}" y="{label_y:.1f}">'
            f'{nx_graph[source][destination]["weight"]} min</text>'
        )

    nodes = []
    for station, name in graph.get_stations().items():
        x, y = point(station)
        if station == start:
            node_class = "start"
        elif station == target:
            node_class = "target"
        elif station in path:
            node_class = "route-node"
        elif station in visit_order:
            node_class = "visited"
        else:
            node_class = "normal"
        nodes.append(
            f'<g class="node {node_class}"><circle cx="{x:.1f}" cy="{y:.1f}" r="18" />'
            f'<text x="{x:.1f}" y="{y - 28:.1f}">{escape(str(name))}</text></g>'
        )

    return (
        f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="Grafo de la red de metro">'
        f'<g class="zoom-layer">{"".join(lines)}{"".join(nodes)}</g></svg>'
    )


def generate_html_report(graph, visit_order, path, start, target, algorithm, total_time, output_file):
    position = get_positions(graph)
    if algorithm == "BFS":
        algorithm_title = "BFS: búsqueda por niveles"
        algorithm_description = (
            "BFS visita primero las estaciones más cercanas al origen y busca la ruta "
            "con menos conexiones, sin utilizar los tiempos."
        )
        criterion = "Prioridad: menor número de conexiones"
    else:
        algorithm_title = "Dijkstra: búsqueda por menor costo"
        algorithm_description = (
            "Dijkstra visita primero la estación cuya distancia acumulada es menor y "
            "busca la ruta con menor tiempo total."
        )
        criterion = "Prioridad: menor tiempo acumulado"

    total_time_text = f"{total_time} min" if total_time is not None else "No aplica para BFS"
    panels = [
        (
            "initial",
            "Grafo inicial",
            "Estado de la red antes de ejecutar el algoritmo",
            _svg_graph(graph, position, start=start, target=target)
        ),
        ("visited", "Grafo recorrido", f"Estaciones inspeccionadas por {algorithm}", _svg_graph(graph, position, visit_order=visit_order, start=start, target=target)),
        ("route", "Ruta final", f"Camino encontrado entre {start} y {target}", _svg_graph(graph, position, path=path, start=start, target=target)),
    ]
    tabs = []
    content = []
    for index, (panel_id, title, subtitle, svg) in enumerate(panels):
        active = " active" if index == 0 else ""
        tabs.append(f'<button class="tab{active}" data-panel="{panel_id}">{title}</button>')
        content.append(f'<section id="{panel_id}" class="panel{active}"><p>{escape(subtitle)}</p><div class="canvas">{svg}</div></section>')

    html = f'''<!doctype html>
        <html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Resultados de la red de metro</title>
        <style>
        :root {{ color-scheme: light; font-family: Georgia, serif; color: #17202a; background: #f5f1ea; }}
        * {{ box-sizing: border-box; }} body {{ margin: 0; padding: 32px; }} main {{ max-width: 1500px; margin: auto; }}
        h1 {{ margin: 0; font-size: clamp(2rem, 4vw, 3.8rem); letter-spacing: -.03em; }}
        .intro, .panel p {{ color: #65727e; font: .95rem system-ui, sans-serif; }} .intro {{ margin: 8px 0 26px; }}
        .explanation {{ display: grid; grid-template-columns: minmax(280px, 1.1fr) 1.6fr auto; gap: 24px; align-items: center; margin-bottom: 26px; padding: 24px; background: #173f5f; color: #f7f3ed; }}
        .explanation-heading h2 {{ margin: 5px 0 8px; font-size: 1.8rem; }} .explanation-heading p {{ margin: 0; color: #dbe6eb; line-height: 1.55; font: .95rem system-ui, sans-serif; }}
        .eyebrow {{ color: #f4b942; text-transform: uppercase; letter-spacing: .12em; font: 700 .72rem system-ui, sans-serif; }}
        .steps {{ display: grid; gap: 12px; font: .92rem system-ui, sans-serif; }} .step {{ display: flex; gap: 12px; align-items: center; }}
        .step strong {{ display: grid; place-items: center; flex: 0 0 28px; height: 28px; border: 1px solid #f4b942; color: #f4b942; border-radius: 50%; }} .step b {{ color: white; }}
        .criterion {{ border-left: 2px solid #f4b942; padding-left: 16px; color: #f4b942; font: 700 .84rem system-ui, sans-serif; max-width: 190px; }}
        .results {{ display: grid; grid-template-columns: repeat(7, minmax(110px, 1fr)); gap: 1px; margin-bottom: 26px; background: #c9c0b6; border: 1px solid #c9c0b6; }}
        .result {{ display: grid; gap: 7px; align-content: center; min-height: 82px; padding: 14px; background: #fffdf9; }} .result span {{ color: #65727e; font: .72rem system-ui, sans-serif; }} .result strong {{ color: #173f5f; font: 700 1.1rem system-ui, sans-serif; }} .result small {{ color: #8a969e; font: .68rem system-ui, sans-serif; }}
        .tabs {{ display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 12px; }} .tab {{ border: 1px solid #c9c0b6; background: #fffaf2; color: #34414c; padding: 11px 17px; cursor: pointer; font-weight: 700; }} .tab.active {{ background: #173f5f; color: white; border-color: #173f5f; }}
        .panel {{ display: none; }} .panel.active {{ display: block; }} .panel p {{ margin: 0 0 10px; }} .canvas {{ background: #fffdf9; border: 1px solid #d8d0c7; min-height: 540px; overflow: hidden; cursor: grab; }} .canvas:active {{ cursor: grabbing; }} svg {{ display: block; width: 100%; height: min(72vh, 760px); }}
        .edge {{ stroke: #b9c3ca; stroke-width: 4; }} .edge.route {{ stroke: #e05a47; stroke-width: 7; }} .edge-label {{ fill: #263746; font: 500 15px system-ui, sans-serif; text-anchor: middle; paint-order: stroke; stroke: #fffdf9; stroke-width: 6px; stroke-linejoin: round; }}
        .node circle {{ stroke-width: 3; fill: #fffdf9; stroke: #83919b; }} .node text {{ fill: #17202a; font: 700 16px system-ui, sans-serif; text-anchor: middle; }} .node.visited circle {{ fill: #b9d8e8; stroke: #247ba0; }} .node.route-node circle {{ fill: #ffd6a5; stroke: #e05a47; }} .node.start circle {{ fill: #73c6b6; stroke: #197278; }} .node.target circle {{ fill: #f28f8f; stroke: #a33f3f; }}
        .hint {{ margin-top: 12px; color: #65727e; font: .82rem system-ui, sans-serif; }}
        @media (max-width: 1100px) {{ .results {{ grid-template-columns: repeat(4, 1fr); }} }} @media (max-width: 900px) {{ .explanation {{ grid-template-columns: 1fr; gap: 18px; }} .criterion {{ max-width: none; }} .results {{ grid-template-columns: repeat(2, 1fr); }} }}
        </style></head><body><main><h1>Teoría de grafos aplicada en una red de metro</h1>
        <div class="intro">{escape(algorithm)} · {escape(str(start))} → {escape(str(target))}</div>
        <section class="explanation"><div class="explanation-heading"><span class="eyebrow">Cómo se comporta la red</span><h2>{escape(algorithm_title)}</h2><p>{escape(algorithm_description)}</p></div>
        <div class="steps"><div class="step"><strong>1</strong><span><b>Inicio</b> · Se parte de {escape(str(start))}.</span></div><div class="step"><strong>2</strong><span><b>Exploración</b> · El azul muestra estaciones inspeccionadas.</span></div><div class="step"><strong>3</strong><span><b>Resultado</b> · El naranja muestra la ruta elegida.</span></div></div><div class="criterion">{escape(criterion)}</div></section>
        <section class="results"><div class="result"><span>Algoritmo</span><strong>{escape(algorithm)}</strong></div><div class="result"><span>Origen</span><strong>{escape(str(start))}</strong></div><div class="result"><span>Destino</span><strong>{escape(str(target))}</strong></div><div class="result"><span>Estaciones incluidas</span><strong>{len(path)}</strong><small>Paradas de la ruta</small></div><div class="result"><span>Tramos recorridos</span><strong>{max(0, len(path) - 1)}</strong><small>Conexiones entre paradas</small></div><div class="result"><span>Estaciones visitadas</span><strong>{len(visit_order)}</strong></div><div class="result"><span>Tiempo total</span><strong>{escape(total_time_text)}</strong></div></section>
        <nav class="tabs">{"".join(tabs)}</nav>{"".join(content)}<div class="hint">Use la rueda del mouse para ampliar y arrastre el grafo para desplazarlo.</div></main>
        <script>
        document.querySelectorAll('.tab').forEach(tab => tab.addEventListener('click', () => {{ document.querySelectorAll('.tab, .panel').forEach(element => element.classList.remove('active')); tab.classList.add('active'); document.getElementById(tab.dataset.panel).classList.add('active'); }}));
        document.querySelectorAll('.canvas').forEach(canvas => {{ const svg = canvas.querySelector('svg'); const layer = svg.querySelector('.zoom-layer'); let scale = 1, offsetX = 0, offsetY = 0, dragging = false, lastX = 0, lastY = 0; const update = () => layer.setAttribute('transform', `translate(${{offsetX}} ${{offsetY}}) scale(${{scale}})`); canvas.addEventListener('wheel', event => {{ event.preventDefault(); scale = Math.max(.65, Math.min(3.5, scale * (event.deltaY < 0 ? 1.12 : .89))); update(); }}); canvas.addEventListener('mousedown', event => {{ dragging = true; lastX = event.clientX; lastY = event.clientY; }}); window.addEventListener('mouseup', () => dragging = false); canvas.addEventListener('mousemove', event => {{ if (!dragging) return; offsetX += (event.clientX - lastX) / canvas.clientWidth * 900; offsetY += (event.clientY - lastY) / canvas.clientHeight * 600; lastX = event.clientX; lastY = event.clientY; update(); }}); }});
        </script></body></html>
    '''

    directory = os.path.dirname(output_file)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as file:
        file.write(html)
