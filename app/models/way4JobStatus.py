import calendar
import datetime


class WAY4JobState:
    def __init__(
        self,
        name,
        batch_role,
        started,
        closed,
        status,
        call_status,
        ext_next_start,
        instance,
        station,
    ) -> None:
        self.name = name
        self.batch_role = batch_role
        self.started = started
        self.closed = closed
        self.status = status
        self.call_status = call_status
        self.ext_next_start = ext_next_start
        self.instance = instance
        self.station = station

    def __repr__(self):
        return (
            f"Job State: {self.name}, {self.batch_role}, {self.started}, {self.closed}, {self.status}, "
            f"{self.call_status}, {self.ext_next_start}, {self.instance}, {self.station}"
        )


class WAY4JobStatuses:
    def __init__(self, db, query):
        self.db = db
        self.list = []

        for row in self.db.fetchRows(query):
            self.list.append(
                WAY4JobState(
                    row[0],
                    row[1],
                    row[2],
                    row[3],
                    row[4],
                    row[5],
                    row[6],
                    row[7],
                    row[8],
                )
            )

    def get(self):
        return self.list

    def getExpectedDates(self, jobname, duration):
        for job in self.list:
            if job.name == jobname:
                if job.ext_next_start is not None:
                    return job.ext_next_start, self.getExpectedEndTime(job, duration)

    def getExpectedEndTime(self, job, duration) -> datetime.datetime:
        hhmm = duration.split(":")
        expectedEnd = job.ext_next_start + datetime.timedelta(
            hours=int(hhmm[0]), minutes=int(hhmm[1])
        )
        today = datetime.datetime.today()
        day = today.day
        first_weekday, num_days_in_month = calendar.monthrange(today.year, today.month)

        if day == num_days_in_month:  # Allow extra time for Monthend End of Day
            if job.name == "End of Day":
                expectedEnd += datetime.timedelta(minutes=150)

        return expectedEnd
