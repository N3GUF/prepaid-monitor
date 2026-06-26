import logging
import os
import time

import datalayer
import lib
import monitors
import schedule
import yaml

"""                              Prepaid Monitor

    This will moniter various Prepaid Processes, Failed files, and delayed files. 
"""


def init(name: str):
    configPath = os.environ.get("CONF_HOME")
    logPath = os.environ.get("LOG_HOME")
    oraDbDsn = os.environ.get("ORA_DB_DSN")
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
        settingsJson = os.path.join(configPath, f"{name}Settings.yml")
    else:
        raise Exception("Config path not set.")

    settings = loadSettings(logger, settingsJson)

    setLoggingLevel(logger, settings.get("log_level"))

    if oraDbDsn:
        if "jdbc:" in oraDbDsn:
            oraDbDsn = oraDbDsn[19:]
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
        settingsJson:  SettingsFile pathname
    """
    global settings
    logger.debug(f"Loading settings from {settingsJson}.")

    try:
        with open(settingsJson) as json_file:
            settings = yaml.safe_load(json_file)

    except Exception as error:
        raise Exception(f"Unable to load settings from {settingsJson}.") from error

    setLoggingLevel(logger, settings.get("log_level"))
    return settings


def setLoggingLevel(logger, logLevel) -> None:
    """Create application Log"""
    if logLevel is None:
        return
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
        yaml.dump(settings, json_file)


def load_schedule(alerts, tasks):
    logger.info("Loading monitoring schedule:")
    interval = ":{:02d}"
    schedule.clear()

    for i in range(0, 60):
        schedule.every().hour.at(interval.format(i)).do(
            loadSettings, logger, settingsJson
        )

    for alert in alerts:
        enabled = alerts.get(alert).get("enabled")
        intvl = alerts.get(alert).get("interval_minutes")
        funct = tasks.get(alert)

        if enabled:
            logger.info(f"{alert} will run every {intvl} minutes")
            for i in range(0, 60, intvl):
                schedule.every().hour.at(interval.format(i)).do(funct)


def settings_updated(settings, notifications, ecbm, sm, pm):
    logger.info("settings updated...")
    ecbm.update_settings(settings)
    notifications.update_settings(settings)
    pm.update_settings(settings)
    sm.update_settings(settings)


if __name__ == "__main__":
    scriptName = os.path.splitext(os.path.basename(__file__))[0]
    logger, settings, settingsJson, dbDsn, dbUser, dbPassword = init(scriptName)

    try:
        emailer = lib.Emailer(logger)
        splunkApi = lib.SplunkApi(
            logger,
            settings["splunk_url"],
            settings["splunk_token"],
            settings["splunk_index"],
            settings.get("splunk_cache"),
        )

        db = datalayer.way4Db(logger, dsn=dbDsn, user=dbUser, password=dbPassword)
        # db = datalayer.way4Db(logger, dsn=dbDsn, user=dbUser, password=dbPassword)
        notifications = lib.NotificationManager(logger, settings, db, emailer)
        ecbm = monitors.EcbConversionMonitor(
            logger, settings, db, emailer, splunkApi, notifications
        )
        sm = monitors.SchedulerMonitor(
            logger, settings, db, emailer, splunkApi, notifications
        )
        pm = monitors.ProcessMonitor(logger, settings, emailer, splunkApi)

    except Exception:
        logger.exception("Fatal error during startup — cannot continue.")
        raise

    """ Start the WAY4 process monitors.
    """
    logger.info("Starting Daily Monitors")
    loadSettings(logger, settingsJson)

    tasks = {}
    tasks["checkExpectedProcesses"] = pm.checkExpectedProcesses
    tasks["checkSchedulerInstances"] = sm.checkSchedulerInstances
    tasks["checkForWAY4SchedulerInvaildJobs"] = sm.checkForWAY4SchedulerInvaildJobs
    tasks["checkSchedulerForDelays"] = sm.checkSchedulerForDelays
    tasks["checkForDelayedEcbFiles"] = ecbm.checkForDelayedEcbFiles

    current_settings = settings
    current_alerts = None

    while True:
        try:
            if current_settings != settings:
                current_settings = settings
                settings_updated(current_settings, notifications, ecbm, sm, pm)

            if current_alerts != settings.get("alerts").get("configured_alerts"):
                logger.info("Loading new schedule...")
                current_alerts = settings.get("alerts").get("configured_alerts")
                load_schedule(current_alerts, tasks)

            schedule.run_pending()

        except Exception:
            logger.exception(
                "Unhandled exception in monitor loop — monitoring will continue."
            )

        time.sleep(1)
