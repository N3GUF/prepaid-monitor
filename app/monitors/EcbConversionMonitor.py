import datalayer
import models

import monitors


class EcbConversionMonitor(monitors.Monitor):
    def checkForDelayedEcbFiles(self) -> None:
        """Check for Delayed ECB Files."""

        delayed_ECB_Files = models.WAY4AchFiles(
            self.__db,
            datalayer.Query.DelayedEcbFileQuery(
                upper_limit_hours=self.__settings.get("alerts")
                .get("configured_alerts")
                .get(self.checkForDelayedEcbFiles.__name__)
                .get("upper_limit_hours"),
                lower_limit_hours=self.__settings.get("alerts")
                .get("configured_alerts")
                .get(self.checkForDelayedEcbFiles.__name__)
                .get("lower_limit_hours"),
            ),
        ).get()
        alert = None
        alerts = []
        host = ""

        if len(delayed_ECB_Files) > 0:
            alert = "There are PayCard delayed ECB files."
            alerts.append("The following PayCard ECB files are delayed:")
            host = "usatlppdjbatlp01/2"

            for file in delayed_ECB_Files:
                if file.imm_origin_name is None:
                    file.imm_origin_name = "Unknown"

                alerts.append(
                    "{} {} - {:<25}\t{:<45}\t{:>15}".format(
                        "{:%a at %I:%M %p}".format(file.file_rec_date),
                        file.source_corp_acnt,
                        file.imm_origin_name,
                        shorten(file.file_name),
                        "{:,.2f}".format(file.total_credit_amt),
                    )
                )

            incident = self.createIncident(
                self.checkForDelayedEcbFiles.__name__,
                alert,
                alerts,
            )

            incident["comments"] = "Please restart the PayCard ECB Daemons."
            self.createAlert(
                self.checkForDelayedEcbFiles.__name__, alert, alerts, incident, host
            )

        else:
            self.__logger.debug("No delayed ECB files.")

    def update_settings(self, settings) -> None:
        super().update_settings(settings)
        self.__settings = settings

    def __init__(self, logger, settings, db, emailer, splunkApi, notifier):
        monitors.Monitor.__init__(self, logger, settings, emailer, splunkApi)
        self.__logger = logger
        self.__settings = settings
        self.__db = db
        self.__notifier = notifier


def shorten(file_name: str) -> str:
    parts = file_name.split(".")
    if len(parts) < 4:
        return file_name
    return f"{parts[1]}.{parts[2]}.{parts[3]}"
