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
        return f"{self.jobname:<35}\t{self.station:<35}\t{self.status}\t{self.call_status}\t{self.expectedStart}\t{self.expectedEnd}\t{self.actualStart}\t{self.actualEnd}"

    def get(self):
        return self.list

    def CalculateExpectedEndTime(self, duration) -> datetime.datetime:
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
        if status != None:
            self.status = status

        if status != None:
            self.call_status = call_status

        if expectedStart != None:
            self.expectedStart = expectedStart

        if expectedEnd != None:
            self.expectedEnd = expectedEnd

        if actualStart != None:
            self.actualStart = actualStart

        if actualEnd != None:
            self.actualEnd = actualEnd

        if station != None:
            self.station = station


class WAY4Schedule:
    def __init__(self, jobTimes) -> None:
        self.list = []

        for job in jobTimes:
            self.list.append(WAY4Job(job))

    def getExpectedDates(self, jobname, duration):
        for job in self.list:
            if job.jobname == jobname:
                if job.expectedStart != None:
                    return job, self.getExpectedEndTime(job, duration)
