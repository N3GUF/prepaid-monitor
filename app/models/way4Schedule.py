import calendar
import datetime


class WAY4Job:
    def __init__(self, jobname) -> None:
        self.jobname = jobname
        self.station = None
        self.status = None
        self.call_status = None
        self.expectedStart = None
        self.expectedEnd = None
        self.actualStart = None
        self.actualEnd = None

    def __repr__(self):
        return f"{self.jobname:<35}{self.station:<25}{self.status:<15}{self.call_status:<15}{self._format(self.expectedStart):<18}{self._format(self.expectedEnd):<18}{self._format(self.actualStart):<18}{self._format(self.actualEnd):<18}"

    def _format(self, dt: datetime.datetime | None) -> str:
        if dt is None:
            return "N/A"

        return dt.strftime("%m-%d-%y %H:%M")

    def get(self):
        return self.list

    def CalculateExpectedEndTime(self, duration) -> None:
        if self.expectedStart is None:
            self.expectedEnd = None
            return

        hhmm = duration.split(":")
        self.expectedEnd = self.expectedStart + datetime.timedelta(
            hours=int(hhmm[0]), minutes=int(hhmm[1])
        )
        today = datetime.datetime.today()
        day = today.day
        first_weekday, num_days_in_month = calendar.monthrange(today.year, today.month)

        if day == num_days_in_month:  # Allow extra time for Monthend End of Day
            if self.jobname == "End of Day":
                self.expectedEnd += datetime.timedelta(minutes=150)

    def update(
        self,
        status,
        call_status,
        expectedStart,
        expectedEnd,
        actualStart,
        actualEnd,
        station,
    ):
        if status is not None:
            self.status = status

        if call_status is not None:
            self.call_status = call_status

        if expectedStart is not None:
            self.expectedStart = expectedStart

        if expectedEnd is not None:
            self.expectedEnd = expectedEnd

        if actualStart is not None:
            self.actualStart = actualStart

        if actualEnd is not None:
            self.actualEnd = actualEnd

        if station is not None:
            self.station = station


class WAY4Schedule:
    def __init__(self, jobTimes) -> None:
        self.list = []

        for job in jobTimes:
            self.list.append(WAY4Job(job))

    def getExpectedDates(self, jobname, duration):
        for job in self.list:
            if job.jobname == jobname:
                if job.expectedStart is not None:
                    return job, self.getExpectedEndTime(job, duration)
