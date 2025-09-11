import datetime

from abc import ABC
from models.way4FileInfo import WAY4Files
from models.WAY4AchFile import WAY4AchFiles
from datalayer.way4Query import Query
from models.way4Schedule import WAY4Job


class INoticationManager(ABC):
    """Provide Email Notifications"""

    def sendNotication(
        self,
        job: WAY4Job,
        last_run_time: datetime.datetime,
        last_ach_import_finished: datetime.datetime,
    ):
        pass


class NoticationManager:
    """Provide Email Notifications"""

    def sendNotication(
        self,
        job: WAY4Job,
        last_run_time: datetime.datetime,
        last_ach_import_finished: datetime.datetime,
    ):
        """Send email Noification.

        Arguments:
            job:            job Info
            prevMinutes:    notification settings
        """
        settings = self.__settings.get("notifications").get(job.jobname)

        if settings is None or job.actualEnd is None:
            return

        if job.actualEnd < last_run_time:
            return

        subject = (
            f"PayCard WAY4 Job {job.jobname} has completed at {job.actualEnd:%-I:%M %p}"
        )
        message = f"PayCard WAY4 job {job.jobname} started at {job.actualStart:%-I:%M %p}, and completed at {job.actualEnd:%-I:%M %p}."

        if "ACH Import" in job.jobname:
            message = self.__createAchNotication(
                job, settings, message, last_ach_import_finished  # type: ignore
            )
            if message == "":
                return
        else:
            if settings["report_file_totals"]:
                files = WAY4Files(
                    self.__db, Query.FileInfoQuery(last_run=last_run_time)
                ).get()

                for file in files:
                    if file.amount > 0:
                        message += f"\n\nA file was created at {file.creation_date:%-I:%M %p} with {file.transactions:,} transactions totaling ${file.amount:,.2f}."
                    else:
                        message += f"\n\nA file was created at {file.creation_date:%-I:%M %p} with {file.transactions:,} transactions."

        self.__emailer.SendEmail(
            subject,
            message,
            None,
            self.__settings.get("send_alerts_from").get(__class__.__name__),
            settings.get("EmailTo"),
            settings.get("EmailCc"),
            settings.get("EmailBcc"),
        )
        self.__logger.info(message)

    def __createAchNotication(
        self, job: WAY4Job, settings, message, last_run_time: datetime.datetime
    ):
        achFiles = WAY4AchFiles(
            self.__db,
            Query.AchFileQuery(last_run=last_run_time),
        ).get()

        if len(achFiles) == 0:
            return ""

        if settings["report_file_totals"]:
            # files, exception = self.__db.get_file_infos(prevMinutes=prevMinutes)

            # if exception:
            #     self.__logger.error("Unable to get file information:")

            #     for arg in exception.args:
            #         self.__logger.error(arg)
            for file in achFiles:
                message += f"\n\n{file.file_name} was received at {file.file_rec_date:%-I:%M %p} with {file.total_debit_amt:,.2f} in debits, and {file.total_credit_amt:,.2f} in credits."

            return message

    def __init__(self, logger, settings, db, emailer):
        self.__logger = logger
        self.__settings = settings
        self.__db = db
        self.__emailer = emailer
