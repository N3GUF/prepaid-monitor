class Monitor:
    """Monitor Base Class

    This class contains various utility methods.
    """

    def createIncident(self, methodName: str, alert: str, alerts: list) -> dict:
        """create an incident dictionary.

        Arguments:
            methodName: calling method
            host:       host where incident occurred
            alert:      alert
            alerts:     list of all alerts

        Returns:
            dictionary of incident data
        """
        incident = {
            "type": "Incident",
            "company": "Comdata Corporate Payments",
            "business_service": "Corporate Payments - Prepaid",
            "location": "Brentwood",
            "category": "Monitoring Event",
            "subcategory": "Application",
            "Configuration item": "Prepaid Open Loop Batch",
            "short_description": alert,
            "description": "",
            "impact": 0,
            "urgency": 0,
            "assignment_group": "",
            "correlation_id": "",
        }

        for alert in alerts:
            incident["description"] += f"{alert}\r\n"

        incident["impact"] = (
            self.__settings.get("alerts")
            .get("configured_alerts")
            .get(methodName)
            .get("impact")
        )
        incident["urgency"] = (
            self.__settings.get("alerts")
            .get("configured_alerts")
            .get(methodName)
            .get("urgency")
        )
        incident["assignment_group"] = (
            self.__settings.get("alerts")
            .get("configured_alerts")
            .get(methodName)
            .get("assignment_group")
        )
        incident["correlation_id"] = methodName[0:50]
        return incident

    def createAlert(
        self, methodName: str, alert: str, alertList: list, incident: dict, host: str
    ) -> None:
        """Create an alert from the given data.

        Arguments:
            alertType:  Alert Type
            alert:      Alert message
            list:       List of items causing alert
        """
        self.__logger.warning(alert)

        if self.__settings.get("report_to_email"):
            content = ""

            for job in alertList:
                self.__logger.warning(f"\t{job}")
                content += f"\t{job}\n"

            self.__emailer.SendEmail(
                alert,
                content,
                None,
                self.__settings.get("alerts").get("emailFrom"),
                self.__settings.get("alerts").get("emailTo"),
                self.__settings.get("alerts").get("emailCc"),
                self.__settings.get("alerts").get("emailBcc"),
            )

        if self.__settings.get("report_to_splunk"):
            self.__splunkApi.SendToSplunk(incident, host)

    def __init__(self, logger, settings, emailer, splunkApi):
        self.__logger = logger
        self.__settings = settings
        self.__emailer = emailer
        self.__splunkApi = splunkApi
