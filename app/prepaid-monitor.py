import json
import os
import logging
import time
import schedule
from classes.emailer import Emailer, IEmailer
from classes.notificationManager import NoticationManager, INoticationManager
from classes.splunkApi import SplunkApi

# from datalayer.PayCardDB import DB
from monitors.processMonitor import ProcessMonitor
from monitors.schedulerMonitor import SchedulerMonitor
from datalayer.way4Db import way4Db

"""                              Prepaid Monitor

    This will moniter various Prepaid Processes, Failed files, and delayed files. 
"""


def init(name: str):
    configPath = os.environ.get("CONF_HOME")
    logPath = os.environ.get("LOG_HOME")
    oraDbDsn = os.environ.get("ORA_DB_URL")
    oraDbUser = os.environ.get("ORA_DB_USER")
    oraPwFile = os.environ.get("ORA_PW_FILE")
    splunkToken = os.getenv("SPLUNK_TOKEN")
    splunkIndex = os.getenv("SPLUNK_INDEX")
    splunkCache = os.getenv("SPLUNK_CACHE")

    if logPath:
        logPathname = os.path.join(logPath, f"{name}.log")
    else:
        raise Exception("Log path not set.")

    logger = getLogger(logPathname)

    if configPath:
        settingsJson = os.path.join(configPath, f"{name}Settings.json")
    else:
        raise Exception("Config path not set.")

    settings = loadSettings(logger, settingsJson)
    setLoggingLevel(logger, settings.get("log_level"))

    if oraDbDsn:
        oraDbDsn = oraDbDsn[18:]
    else:
        raise Exception("DB DSN not set.")

    if oraDbUser:
        pass
    else:
        raise Exception("DB user not set.")

    if oraPwFile:
        pass
    else:
        raise Exception("DB password file not set.")

    if os.path.exists(oraPwFile):
        try:
            logger.debug(f"Loading DB password from {oraPwFile}.")
            with open(oraPwFile, "r") as f:
                oraDbPassword = f.readline().strip()

        except Exception as error:
            raise Exception(f"Unable to load DB password from {oraPwFile}.") from error
    else:
        raise Exception(f"DB password file: {oraPwFile} was not found.")

    if splunkIndex:
        settings["splunk_index"] = splunkIndex
    else:
        raise Exception("Splunk index not set.")

    if splunkToken:
        settings["splunk_token"] = splunkToken
    else:
        raise Exception("Splunk token not set.")

    if splunkCache:
        settings["splunk_cache"] = splunkCache

    return logger, settings, settingsJson, oraDbDsn, oraDbUser, oraDbPassword


def loadSettings(logger, settingsJson: str):
    """Load settings from a JSON file.

    Arguments:
        settingsJson:  Settings jSON pathname
    """
    logger.debug(f"Loading settings from {settingsJson}.")

    try:
        with open(settingsJson) as json_file:
            settings = json.load(json_file)

    except Exception as error:
        raise Exception(f"Unable to load settings from {settingsJson}.") from error

    setLoggingLevel(logger, settings.get("log_level"))
    return settings


def setLoggingLevel(logger, logLevel) -> None:
    """Create application Log"""
    logLevel = logLevel.lower()

    if logLevel == "debug":
        logLevel = logging.DEBUG
    elif logLevel == "warning":
        logLevel = logging.WARNING
    elif logLevel == "error":
        logLevel = logging.ERROR
    elif logLevel == "critical":
        logLevel = logging.CRITICAL
    else:
        logLevel = logging.INFO

    if logger.level != logLevel:
        logger.setLevel(logLevel)
        logger.info("Logger level has been updated.")


def getLogger(logPathname):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s: %(message)s", datefmt="%m/%d/%Y %I:%M:%S %p"
    )

    fileHandler = logging.FileHandler(logPathname)
    fileHandler.setFormatter(formatter)
    logger.addHandler(fileHandler)
    return logger


def createSettings():
    """Create a basic settings file."""

    settings = {
        "send_alerts_from": "Prepaid Process Montor@fleetcor.com",
        "send_alerts_to": "dbernhardy@comdata.com",
        "scheduler_instance": "scheduler",
        "log_pathname": ".\\dailyProcessMotitor",
    }

    with open(
        r"C:\Users\dbernhardy\source\repos\DailyProcessMonitor\settings.json", "w"
    ) as json_file:
        json.dump(settings, json_file)


if __name__ == "__main__":
    scriptName = os.path.splitext(os.path.basename(__file__))[0]
    logger, settings, settingsJson, dbDsn, dbUser, dbPassword = init(scriptName)

    try:
        emailer = Emailer(logger, settings["send_alerts_from"])
        splunkApi = SplunkApi(
            logger,
            settings["splunk_url"],
            settings["splunk_token"],
            settings["splunk_index"],
            settings["splunk_cache"],
        )

        # db = DB(dsn=dbDsn, user=dbUser, password=dbPassword)
        db = way4Db(logger, dsn=dbDsn, user=dbUser, password=dbPassword)
        notifications = NoticationManager(logger, settings, db, emailer)
        sm = SchedulerMonitor(logger, settings, db, emailer, splunkApi, notifications)
        pm = ProcessMonitor(logger, settings, emailer, splunkApi)

        """ Start the WAY4 process monitors.
        """
        logger.info("Starting Daily Monitors")
        loadSettings(logger, settingsJson)
        schedule.every(1).minutes.do(loadSettings, logger, settingsJson)
        interval = ":{:02d}"

        for i in range(0, 60, 5):
            schedule.every().hour.at(interval.format(i)).do(pm.checkExpectedProcesses)
            schedule.every().hour.at(interval.format(i)).do(sm.checkSchedulerInstances)

        for i in range(0, 60, 10):
            schedule.every().hour.at(interval.format(i)).do(
                sm.checkForWAY4SchedulerInvaildJobs
            )
            schedule.every().hour.at(interval.format(i)).do(
                sm.checkSchedulerForDelays, 10
            )

        while True:
            schedule.run_pending()
            time.sleep(1)

    except Exception as error:
        logger.exception(error)
        print(error.args)
