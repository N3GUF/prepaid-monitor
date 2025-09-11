import datetime
from abc import ABC

import datalayer
import models


class INoticationManager(ABC):
    """Provide Email Notifications"""

    def sendNotication(
        self,
        job: models.WAY4Job,
        last_run_time: datetime.datetime,
        last_ach_import_finished: datetime.datetime,
    ):
        pass


class NoticationManager:
    """Provide Email Notifications"""

    def sendNotification(
        self,
        job: models.WAY4Job,
        last_run_time: datetime.datetime,
        last_ach_import_finished: datetime.datetime,
    ):
        """Send email Noification.

        Arguments:
            job:            job Info
            prevMinutes:    notification settings
        """
        message = ""
        settings = self.__settings.get("notifications").get(job.jobname)
        sponsor_banks = self.__settings.get("sponsor_banks")

        if settings is None or job.actualEnd is None:
            return

        if job.actualEnd < last_run_time:
            return

        subject = (
            f"PayCard WAY4 Job {job.jobname} has completed at {job.actualEnd:%-I:%M %p}"
        )
        message = f"PayCard WAY4 job {job.jobname} started at {job.actualStart:%-I:%M %p}, and completed at {job.actualEnd:%-I:%M %p}."

        if settings["report_file_totals"]:
            if "ach" in job.jobname.lower():
                files = models.WAY4AchFiles(
                    self.__db,
                    datalayer.Query.AchFileQuery(last_run=last_ach_import_finished),
                ).get()
            else:
                files = models.WAY4Files(
                    self.__db, datalayer.Query.FileInfoQuery(last_run=last_run_time)
                ).get()

            if len(files) == 0:
                return

            for file in files:
                bank_name = self.__get_bank_name(file.file_name, sponsor_banks)
                additional_message = self.__get_file_details(
                    job.jobname, bank_name, file
                )

                if additional_message:
                    message += additional_message

        self.__emailer.SendEmail(
            subject,
            message,
            None,
            self.__settings.get("notifications").get("emailFrom"),
            settings.get("emailTo"),
            settings.get("emailCc"),
            settings.get("emailBcc"),
        )
        self.__logger.info(message)

    def __get_file_details(
        self, jobname: str, bank_name: str, file: models.WAY4FileInfo
    ) -> str:
        message = ""

        if "directdep" in file.file_name.lower():
            if "direct deposit" in jobname.lower():
                message += f"\n\nA file was created for {bank_name} at {file.creation_date:%-I:%M %p} with {file.transactions:,} transactions totaling ${file.amount:,.2f}."
        elif "prenote" in file.file_name.lower():
            if "prenote" in jobname.lower():
                message += f"\n\nA file was created for {bank_name} at {file.creation_date:%-I:%M %p} with {file.transactions:,} transactions."
        elif "ach" in file.file_name.lower():
            if "ach" in jobname.lower():
                message += f"\n\nA file was received from {bank_name} at {file.file_rec_date:%-I:%M %p} with {file.total_debit_amt:,.2f} in debits, and {file.total_credit_amt:,.2f} in credits."

        return message

    def __get_bank_name(self, file_name: str, sponsor_banks: list) -> str:
        bank_name = [
            sb["name"]
            for sb in sponsor_banks
            if sb.get("file_identifier") in file_name.lower()
        ]

        if bank_name:
            return bank_name[0]
        else:
            return "Unknown Bank"

    def __init__(self, logger, settings, db, emailer):
        self.__logger = logger
        self.__settings = settings
        self.__db = db
        self.__emailer = emailer
