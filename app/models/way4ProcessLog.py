class WAY4Process:
    def __init__(self, process_name, started, finished, status) -> None:
        self.process_name = process_name
        self.started = started
        self.finished = finished
        self.status = status

    def __repr__(self):
        return f"Process: {self.process_name}, {self.started}, {self.finished}, {self.status}"


class WAY4ProcessLog:
    def __init__(self, db, query):
        self.db = db
        self.list = []

        for row in self.db.fetchRows(query):
            self.list.append(WAY4Process(row[0], row[1], row[2], row[3]))

    def get(self):
        return self.list
