import json
import os
from typing import Protocol, Tuple

import requests


class ISplunkApi(Protocol):
    def SendToSplunk(
        self, event: dict, resend: bool = False, verify: bool = False
    ) -> Tuple[bool, str]: ...


class SplunkApi:
    def __init__(self, logger, url, token, index, eventCacheFile):
        self.__logger = logger
        self.__url = url
        self.__token = token
        self.__index = index
        self.__eventCache = None
        self.__eventCacheFile = eventCacheFile

    def SendToSplunk(
        self, event: dict, host: str, resend: bool = False, verify: bool = False
    ) -> Tuple[bool, str]:
        """Send the event to the Splunk Http Event collector.

        Arguments:
            url: Splunk HEC enpoint url
            token: Splunk HEC token
            index: Splunk HEC index
            event: dictionary with event values

        """
        self.__message = ""
        self.__status = False

        payload = {
            "event": event,
            "index": self.__index,
            "host": host,
            "source": "PayCard Monitor",
            "sourcetype": "application/json",
        }
        headers = {
            "Authorization": self.__token,
            "content-type": "application/json",
        }
        try:
            response = requests.post(
                self.__url, json=payload, headers=headers, timeout=10
            )
        except requests.exceptions.Timeout:
            self.__message += "http post to splunk HEC timed out\r\n"
            self.__logger.warning(self.__message)
            if not resend:
                self.__sendToCache(event)
            return False, self.__message

        if response.ok:
            if not resend:
                self.__message += f"{event.get('priority', '')} Alarm sent to the splunk http event collector\r\n"
                self.__logger.info(self.__message)
        else:
            self.__message += (
                f"http post failed to splunk HEC: {response.status_code} - {response.reason}"
                + "\r\n"
            )
            self.__logger.warning(self.__message)

            if not resend:
                self.__sendToCache(event)

        return response.ok, self.__message

    def __sendToCache(self, event):
        if self.__eventCacheFile is None:
            return
        if os.path.exists(self.__eventCacheFile):
            try:
                with open(self.__eventCacheFile, "r") as f:
                    self.__eventCache = json.load(f)
            except json.JSONDecodeError:
                self.__logger.warning("Splunk event cache is corrupted; resetting.")
                self.__eventCache = []
        else:
            self.__eventCache = []

        self.__eventCache.append(event)

        try:
            with open(self.__eventCacheFile, "w") as f:
                json.dump(self.__eventCache, f, indent=4)
                self.__message += "Incident sent to the splunk event cache"
                self.__logger.info("Incident sent to the splunk event cache")

        except Exception as e:
            raise Exception("Unable to write to the splunk event cache.", e) from e
