class Graph:

    def __init__(self):
        self.stations = {}
        self.connections = {}

    def add_station(self, station_id, name):
        self.stations[station_id] = name

        if station_id not in self.connections:
            self.connections[station_id] = []

    def add_connection(self, source, destination, time):
        self.connections[source].append({
            "station": destination,
            "time": time
        })

        self.connections[destination].append({
            "station": source,
            "time": time
        })

    def get_neighbors(self, station):
        return self.connections.get(station, [])

    def get_station_name(self, station_id):
        return self.stations.get(station_id, station_id)

    def get_stations(self):
        return self.stations