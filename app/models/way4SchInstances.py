class WAY4SchState:
    def __init__(self, name, started, closed, station, status, last_event) -> None:
        self.name = name
        self.started = started
        self.closed = closed
        self.station = station
        self.status = status
        self.last_event = last_event

    def __repr__(self):
        return f"Sch State: {self.name}, {self.started}, {self.closed}, {self.station}, {self.status}, {self.last_event}"


class WAY4SchInstances:
    def __init__(self, db, query):
        self.list = []
        self.db = db

        for row in self.db.fetchRows(query):
            self.list.append(
                WAY4SchState(row[0], row[1], row[2], row[3], row[4], row[5])
            )

    def get(self):
        return self.list
