class WAY4AchFile:
    def __init__(
        self,
        file_type,
        status,
        file_name,
        file_rec_date,
        total_debit_amt,
        total_credit_amt,
    ) -> None:
        self.file_type = file_type
        self.status = status
        self.file_name = file_name
        self.file_rec_date = file_rec_date
        self.total_debit_amt = total_debit_amt
        self.total_credit_amt = total_credit_amt

    def __repr__(self):
        return f"WAY4AchFile {self.file_type}, {self.status}, {self.file_name}, {self.file_rec_date}, {self.total_debit_amt}, {self.total_credit_amt}"


class WAY4AchFiles:
    def __init__(self, db, query):
        self.db = db
        self.list = []
        for row in self.db.fetchRows(query):
            self.list.append(
                WAY4AchFile(row[0], row[1], row[2], row[3], row[4], row[5])
            )

    def get(self):
        return self.list
