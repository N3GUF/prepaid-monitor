import datetime

from models.way4JobStatus import WAY4JobStatuses
from models.way4ProcessLog import WAY4ProcessLog
from models.way4SchInstances import WAY4SchInstances
from datalayer.way4Query import Query

# from datalayer.PayCardDB import DB

from models.way4Schedule import WAY4Schedule
from monitors.monitor import Monitor


class SchedulerMonitor(Monitor):
    def checkSchedulerInstances(self) -> None:
        """Veriy that all WAY4 Scheduler instances are running."""
        self.__logger.debug("Checking WAY4 Scheduler Instances")
        instances = self.__settings.get("scheduler_instances")

        # with self.__db.session:
        #     instances, exception = self.__db.get_sch_instance_states(instances)

        #     if exception:
        #         self.__logger.error("Unable to get scheduler instances:")

        #         for arg in exception.args:
        #             self.__logger.error(arg)

        instances = WAY4SchInstances(
            self.__db,
            Query.SchInstanceStateQuery(self.__settings.get("scheduler_instances")),
        ).get()
        alert = None
        alerts = []
        host = ""

        for instance in instances:
            if instance.status != "R":
                alert = f"PayCard WAY4 Scheduler instance {instance.name} on {instance.station} is not running."
                alerts.append(alert)
                host = instance.station

        if alert == None:
            self.__logger.debug("All PayCard WAY4 Scheduler instance(s) are running.")
        else:
            alerts.insert(
                0, "The following PayCard WAY4 scheduler instances are stopped:"
            )
            incident = self.createIncident(
                self.checkSchedulerInstances.__name__, alert, alerts
            )
            incident["comments"] = "Please restart the stopped instances."
            self.createAlert(self.__class__.__name__, alert, alerts, incident, host)

    def checkForWAY4SchedulerInvaildJobs(self) -> None:
        """Check for WAY4 Scheduler jobs in an invalid state."""
        instances = self.__settings.get("scheduler_instances")

        # with self.__db.session:
        # invalidJobs, exception = self.__db.get_invalid_jobs(instances)

        # if exception:
        #     self.__logger.error("Unable to get scheduler invalid jobs:")

        #     for arg in exception.args:
        #         self.__logger.error(arg)

        invalidJobs = WAY4JobStatuses(
            self.__db, Query.InvalidJobsQuery(instances)
        ).get()
        alert = None
        alerts = []
        host = ""

        if len(invalidJobs) > 0:
            alert = f"There are invalid jobs in the PayCard WAY4 scheduler."
            alerts.append(
                "The following PayCard WAY4 scheduler Jobs are in an invalid state:"
            )

            for job in invalidJobs:
                alerts.append(job.name)
                host = job.station

            incident = self.createIncident(
                self.checkSchedulerForDelays.__name__,
                alert,
                alerts,
            )

            incident["comments"] = "Please investigate."
            self.createAlert(self.__class__.__name__, alert, alerts, incident, host)

        else:
            self.__logger.debug("No invalid jobs in the PayCard WAY4 scheduler.")

    def checkSchedulerForDelays(self, prevMinutes: int) -> None:
        """Check for WAY4 Scheduler jobs that have not started or ended on time."""
        self.__logger.debug("Checking status of critical path jobs")
        self.__logger.debug("Updating schedule")

        # with self.__db.session:
        # self.UpdateSchedule()

        self.UpdateSchedule(prevMinutes=prevMinutes)
        now = datetime.datetime.now()
        buffer = datetime.timedelta(minutes=10)
        alert = None
        alerts = []
        host = ""

        for job in self.sched.list:
            if job.expectedStart != None:
                if (
                    now > job.expectedStart + buffer
                    and job.call_status != "R"
                    and job.status != "S"
                ):
                    alert = f"PayCard WAY4 Scheduler job {job.jobname} has not started by {job.expectedStart}."
                    alerts.append(alert)
                    host = job.station

            if job.expectedEnd != None:
                if now > job.expectedEnd and job.call_status != "F":
                    alert = f"PayCard Scheduler job {job.jobname} has not ended by {job.expectedEnd}."
                    alerts.append(alert)
                    host = job.station

            if job.call_status == "R":
                self.__logger.debug(
                    f"PayCard WAY4 Scheduler job {job.jobname} is running."
                )

        if alert == None:
            self.__logger.debug("All PayCard WAY4 Scheduler jobs are on schedule.")
        else:
            alerts.insert(0, "The following PayCard WAY4 scheduler jobs are delayed:")
            incident = self.createIncident(
                self.checkSchedulerForDelays.__name__,
                alert,
                alerts,
            )
            incident["comments"] = "Please investigate the delay."
            self.createAlert(self.__class__.__name__, alert, alerts, incident, host)

    def UpdateSchedule(self, prevMinutes: int) -> None:
        """Update the internal representation of the WAY4 Scheduler."""
        self.__logger.debug("Loading scheduler instances.")
        instances = self.__settings.get("scheduler_instances")
        self.__logger.debug("Loading scheduler status.")
        # self.jobStatuses, exception = self.__db.get_sch_job_states(instances)

        # if exception:
        #     self.__logger.error("Unable to get scheduler job states:")

        #     for arg in exception.args:
        #         self.__logger.error(arg)

        self.jobStatuses = WAY4JobStatuses(
            self.__db,
            Query.JobStatusQuery(self.__settings.get("scheduler_instances")),
        ).get()

        for job in self.sched.list:  # Status and Update Expected Times
            for status in self.jobStatuses:
                # if job.jobname != status.Sch_Job_State.name:
                #     continue

                # job.station = status.Sch_Instance_State.station
                # job.status = status.Sch_Job_State.status
                # job.call_status = status.Sch_Job_State.call_status

                # if status.Sch_Job_State.next_start:
                #     job.expectedStart = status.Sch_Job_State.next_start

                if job.jobname != status.name:
                    continue

                job.station = status.station
                job.status = status.status
                job.call_status = status.call_status

                if status.ext_next_start:
                    job.expectedStart = status.ext_next_start
                    duration = self.__settings["jobs_to_watch"][job.jobname][
                        "daily_duration"
                    ]
                    job.CalculateExpectedEndTime(duration)

        self.__logger.debug("Loading scheduler process data.")
        # processes, exception = self.__db.get_sch_job_processes()

        # if exception:
        #     self.__logger.error("Unable to get scheduler process_log data:")

        #     for arg in exception.args:
        #         self.__logger.error(arg)
        last_run_time = self.get_last_run_time(prevMinutes)

        if self.__sched_initialized:
            processes = WAY4ProcessLog(
                self.__db, Query.ProcessLogJobQuery(last_run=last_run_time)
            ).get()
        else:
            processes = WAY4ProcessLog(
                self.__db, Query.ProcessLogJobQuery(last_run=None)
            ).get()

        for job in self.sched.list:  # Update Actual Times
            for process in processes:
                if job.jobname != process.process_name:
                    continue

                job.actualStart = process.started

                if process.status == "C":
                    job.actualEnd = process.finished

                    if (
                        "ACH Import" in job.jobname
                        and self.__last_ach_import_finished is None
                    ):
                        self.__last_ach_import_finished = process.finished

                    self.__notifier.sendNotication(
                        job=job,
                        last_run_time=last_run_time,
                        last_ach_import_finished=self.__last_ach_import_finished,
                    )

                    if "ACH Import" in job.jobname:
                        self.__last_ach_import_finished = process.finished
                else:
                    job.actualEnd = None

                break

        self.__sched_initialized = True

        for job in self.sched.list:
            self.__logger.debug(job)

    def get_last_run_time(self, prevMinutes: int) -> datetime.datetime:
        last_run = datetime.datetime.now() - datetime.timedelta(minutes=prevMinutes)
        last_run = datetime.datetime(
            year=last_run.year,
            month=last_run.month,
            day=last_run.day,
            hour=last_run.hour,
            minute=last_run.minute,
        )

        return last_run

    def __init__(self, logger, settings, db, emailer, splunkApi, notifier):
        Monitor.__init__(self, logger, settings, emailer, splunkApi)
        self.__logger = logger
        self.__settings = settings
        self.__db = db
        self.sched = WAY4Schedule(self.__settings.get("jobs_to_watch"))
        self.__sched_initialized = False
        self.__last_ach_import_finished = None
        self.__notifier = notifier
        # self._ach_files = AchFiles()

        # with self.__db.session:
        # instances, exception = self.__db.get_sch_instance_states(["scheduler"])

        # if exception:
        #     self.__logger.error("Unable to get scheduler instances:")

        #     for arg in exception.args:
        #         self.__logger.error(arg)

        instances = WAY4SchInstances(
            self.__db,
            Query.SchInstanceStateQuery(self.__settings.get("scheduler_instances")),
        ).get()
        self.stations = {}

        for instance in instances:
            self.stations[instance.name] = instance.station
