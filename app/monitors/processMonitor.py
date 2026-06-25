import models

import monitors


class ProcessMonitor(monitors.Monitor):
    def checkExpectedProcesses(self):
        """Verify that other expected processes are running."""
        self.__logger.debug("Checking for expected processes")
        user = (
            self.__settings.get("alerts")
            .get("configured_alerts")
            .get(self.checkExpectedProcesses.__name__)
            .get("prepaid_username")
        )
        servers = (
            self.__settings.get("alerts")
            .get("configured_alerts")
            .get(self.checkExpectedProcesses.__name__)
            .get("prepaid_servers")
        )
        expexctedProcesses = (
            self.__settings.get("alerts")
            .get("configured_alerts")
            .get(self.checkExpectedProcesses.__name__)
            .get("expected_processes")
        )

        if not user:
            return

        if not servers:
            return

        if not expexctedProcesses:
            return

        processes_checked = False
        alert = None
        alert_list = []
        alerts_by_server = {}
        all_processes = models.LinuxProcesses(servers, user)

        for server, processes in all_processes.get().items():
            if len(processes) == 0:
                self.__logger.warning(f"Unable to check for processes on {server}.")
                continue
            else:
                processes_checked = True

            for expectedProcess in expexctedProcesses:
                self.__logger.debug(
                    f"Checking for process {expectedProcess} on {server}."
                )
                found = False

                for process in processes:
                    if expectedProcess in process.command:
                        found = True
                        break

                if not found:
                    alert = f"{expectedProcess} is not running as {user} on {server}."
                    alert_list.append(alert)
                    alerts_by_server[server] = alert_list

        if not processes_checked:
            return

        if not alert:
            self.__logger.debug("All Expected PayCard processes are running")
            return

        for server, alerts in alerts_by_server.items():
            alerts_by_server[server].insert(
                0, f"The following PayCard processes are not running on {server}:"
            )
            incident = self.createIncident(
                self.checkExpectedProcesses.__name__,
                alerts_by_server[server][0],
                alerts_by_server[server],
            )
            incident["comments"] = "Please restart the stopped process(es)."
            self.createAlert(
                self.checkExpectedProcesses.__name__,
                alerts_by_server[server][0],
                alerts_by_server[server],
                incident,
                server,
            )

    def update_settings(self, settings) -> None:
        super().update_settings(settings)
        self.__settings = settings

    def __init__(self, logger, settings, emailer, splunkApi):
        monitors.Monitor.__init__(self, logger, settings, emailer, splunkApi)
        self.__logger = logger
        self.__settings = settings
        self.__emailer = emailer
        self.splunkApi = splunkApi
