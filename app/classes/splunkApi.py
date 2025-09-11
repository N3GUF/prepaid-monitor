from abc import ABC
import json
import requests


class ISplunkApi(ABC):
    def SendToSplunk(self, event: dict, verify: bool):
        pass


class SplunkApi:
    def __init__(self, logger, url, token, index, eventCacheFile):
        self.__logger = logger
        self.__url = url
        self.__token = token
        self.__index = index
        self.__eventCacheFile = eventCacheFile

    def SendToSplunk(self, event: dict, host: str = "", verify: bool = True) -> str:
        """Send the event to the Splunk Http Event collector.

        Arguments:
            event: dictionary with event values
            host: hostname
            verify: verify https certificate

        """
        self.__message = ""

        try:
            r = requests.post(
                self.__url,
                verify=verify,
                json={
                    "event": event,
                    "index": self.__index,
                    "host": host,
                    "source": "PayCard Monitor",
                    "sourcetype": "application/json",
                },
                headers={
                    "Authorization": self.__token,
                    "content-type": "application/json",
                },
            )

        except Exception as e:
            self.__message += "Unable to connnect to splunk http event collector. \r\n"
            self.__logger.warning("Unable to connnect to splunk http event collector.")

            for arg in e.args:
                self.__logger.warning(arg)

            self.__sendToCache(event)
            return self.__message

        if r.reason == "OK":
            self.__message += "Event sent to the splunk http event collector"
            self.__logger.info(self.__message)
        else:
            self.__message += f"http post failed to splunk HEC: {r} - {r.text}" + "\r\n"
            self.__logger.warning(self.__message)
            self.__sendToCache(event)

        return self.__message

    def __sendToCache(self, event):
        if self.__eventCacheFile is None:
            return

        try:
            with open(self.__eventCacheFile, "a") as f:
                json.dump(event, f, indent=4)
                self.__message += "Event sent to the splunk event cache"
                self.__logger.warning("Event sent to the splunk event cache")

        except Exception as e:
            self.__logger.error("Unable to write to the splunk event cache.")
