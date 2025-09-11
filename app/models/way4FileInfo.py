class WAY4FileInfo:
    def __init__(self, creation_date, file_id, file_name, transactions, amount) -> None:
        self.creation_date = creation_date
        self.file_id = file_id
        self.file_name = file_name
        self.transactions = transactions
        self.amount = amount

    def __repr__(self):
        return f"WAY4FileInfo: {self.creation_date}, {self.file_id}, {self.file_name}, {self.transactions}, {self.amount}"


class WAY4Files:
    def __init__(self, db, query):
        self.db = db
        self.list = []
        for row in self.db.fetchRows(query):
            self.list.append(WAY4FileInfo(row[0], row[1], row[2], row[3], row[4]))

    def get(self):
        return self.list
