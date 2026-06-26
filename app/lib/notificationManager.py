import datetime
from abc import ABC, abstractmethod

import datalayer
import models


class INotificationManager(ABC):
    """Provide Email Notifications"""

    @abstractmethod
    def sendNotification(
        self,
        job: models.WAY4Job,
        last_run_time: datetime.datetime,
        last_ach_import_finished: datetime.datetime,
    ):
        pass


class NotificationManager(INotificationManager):
    """Provide Email Notifications"""

    def __init__(self, logger, settings, db, emailer):
        self.__logger = logger
        self.__settings = settings
        self.__db = db
        self.__emailer = emailer

    def sendNotification(
        self,
        job: models.WAY4Job,
        last_run_time: datetime.datetime,
        last_ach_import_finished: datetime.datetime,
    ):
        notification_settings = self.__settings.get("notifications") or {}
        settings = notification_settings.get(job.jobname)
        sponsor_banks = self.__settings.get("sponsor_banks")

        if settings is None or job.actualEnd is None:
            return

        if job.actualEnd < last_run_time:
            return

        subject = (
            f"PayCard WAY4 Job {job.jobname} has completed at {job.actualEnd:%-I:%M %p}"
        )
        message = (
            f"PayCard WAY4 job {job.jobname} started at {job.actualStart:%-I:%M %p},"
            f" and completed at {job.actualEnd:%-I:%M %p}."
        )

        if settings["report_file_totals"]:
            if "ach" in job.jobname.lower():
                files = models.WAY4AchFiles(
                    self.__db,
                    datalayer.Query.AchFileQuery(last_run=last_ach_import_finished),
                ).get()

                if not files:
                    return

                for file in files:
                    bank_name = self.__get_bank_name(file.file_name, sponsor_banks)
                    additional_message = self.__get_ach_file_details(
                        job.jobname, bank_name, file
                    )
                    if additional_message:
                        message += additional_message
            else:
                files = models.WAY4Files(
                    self.__db, datalayer.Query.FileInfoQuery(last_run=last_run_time)
                ).get()

                if not files:
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
            notification_settings.get("emailFrom"),
            settings.get("emailTo"),
            settings.get("emailCc"),
            settings.get("emailBcc"),
        )
        self.__logger.info(message)

    def update_settings(self, settings) -> None:
        self.__settings = settings

    def __get_file_details(
        self, jobname: str, bank_name: str, file: models.WAY4FileInfo
    ) -> str:
        if "directdep" in file.file_name.lower() and "direct deposit" in jobname.lower():
            return (
                f"\n\nA file was created for {bank_name} at"
                f" {file.creation_date:%-I:%M %p} with {file.transactions:,}"
                f" transactions totaling ${file.amount:,.2f}."
            )
        if "prenote" in file.file_name.lower() and "prenote" in jobname.lower():
            return (
                f"\n\nA file was created for {bank_name} at"
                f" {file.creation_date:%-I:%M %p} with {file.transactions:,}"
                f" transactions."
            )
        return ""

    def __get_ach_file_details(
        self, jobname: str, bank_name: str, file: models.WAY4AchFile
    ) -> str:
        if "ach" in file.file_name.lower() and "ach" in jobname.lower():
            return (
                f"\n\nA file was received from {bank_name} at"
                f" {file.file_rec_date:%-I:%M %p} with"
                f" {file.total_debit_amt:,.2f} in debits,"
                f" and {file.total_credit_amt:,.2f} in credits."
            )
        return ""

    def __get_bank_name(self, file_name: str, sponsor_banks: list) -> str:
        return next(
            (
                sb["name"]
                for sb in sponsor_banks
                if sb.get("file_identifier") in file_name.lower()
            ),
            "Unknown Bank",
        )
