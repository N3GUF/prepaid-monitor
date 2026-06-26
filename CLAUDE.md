# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

`prepaid-monitor` is a long-running Python daemon that monitors WAY4 Scheduler jobs, delayed ECB/ACH files, and expected Linux processes. On each polling interval it queries an Oracle database, checks conditions, and sends alerts via email and/or Splunk HEC.

## Common Commands

```bash
# Install dependencies
uv sync

# Run the app locally (requires env vars to be set)
python app/prepaid-monitor.py

# Lint / format (Ruff is the configured formatter)
ruff check app/
ruff format app/

# Production start/stop via shell wrapper
./prepaid-monitor.sh start
./prepaid-monitor.sh stop
./prepaid-monitor.sh restart
```

There are no automated tests in this codebase.

## Required Environment Variables

The app fails fast at startup if any of these are missing:

| Variable | Description |
|---|---|
| `CONF_HOME` | Directory containing `prepaid-monitorSettings.yml` |
| `LOG_HOME` | Directory where `prepaid-monitor.log` is written |
| `ORA_DB_DSN` | Oracle DB DSN (JDBC prefix is stripped automatically) |
| `ORA_DB_USER` | Oracle DB user |
| `ORA_PW_FILE` | Path to a file whose first line is the Oracle DB password |
| `SPLUNK_TOKEN` | Splunk HEC bearer token |
| `SPLUNK_INDEX` | Splunk index name |
| `SPLUNK_CACHE` | (optional) JSON file path for caching events that fail to send |

For local dev, populate `.env` (used by the devcontainer and `docker-compose.yml`) or `.vscode/pc-local.env` / `.vscode/mac-local.env` for VS Code launch configs.

## Architecture

### Entry Point & Scheduling (`app/prepaid-monitor.py`)

`init()` loads all env vars and the YAML settings file, then the `__main__` block wires up all services and enters a `while True` loop driven by the `schedule` library. Every minute it reloads `settings.yml` and rebuilds the task schedule from `settings["alerts"]["configured_alerts"]`. Each configured alert maps to a method on a monitor class and runs at its configured `interval_minutes`.

### Layer Overview

```
app/
├── prepaid-monitor.py    # Entry point; wires services, owns the run loop
├── lib/                  # Services (injected into monitors)
│   ├── emailer.py        # SMTP email sender (IEmailer protocol)
│   ├── splunkApi.py      # Splunk HEC sender + local JSON event cache
│   └── notificationManager.py  # Job-completion email notifications
├── monitors/             # Monitor logic
│   ├── monitor.py        # Base class: createIncident(), createAlert()
│   ├── schedulerMonitor.py   # WAY4 scheduler health + job delay detection
│   ├── EcbConversionMonitor.py  # Delayed ECB file detection
│   └── processMonitor.py    # Linux process presence check (via SSH ps)
├── datalayer/            # Database access
│   ├── way4Db.py         # Oracle connection wrapper (oracledb); fetchRows()
│   └── way4Query.py      # All SQL queries as static methods on Query class
└── models/               # Domain models (hydrate from DB rows)
    ├── way4Schedule.py   # WAY4Schedule (list of WAY4Job); CalculateExpectedEndTime
    ├── way4JobStatus.py  # WAY4JobStatuses — current scheduler job states
    ├── way4SchInstances.py  # WAY4SchInstances — scheduler instance states
    ├── way4ProcessLog.py # WAY4ProcessLog — job run history from OWS.process_log
    ├── WAY4AchFile.py    # WAY4AchFiles — ACH/ECB file records
    ├── way4FileInfo.py   # WAY4Files/WAY4FileInfo — OWS file_info records
    └── linuxProcesses.py # LinuxProcesses — SSH to servers, runs `ps -fu <user>`
```

### Key Design Patterns

**Dependency injection via constructor**: Every monitor and service receives `logger`, `settings`, `emailer`, and `splunkApi` at construction. Settings is a mutable dict — the run loop updates each monitor's `__settings` reference when the YAML reloads.

**Private attributes via name mangling**: All instance state uses `self.__attr` (double underscore). Access from the base `Monitor` class requires that subclasses pass their private references through `Monitor.__init__`.

**Settings-driven per-alert config**: Each monitor method reads its own configuration from `settings["alerts"]["configured_alerts"][method_name]`. This means the method name in Python must match the key name in the YAML config.

**Query class**: `datalayer/way4Query.py` defines `Query` (which also inherits from `Monitor`, likely unintentionally) with all SQL as `@staticmethod` methods. Queries use Python string `.format()` — no parameterized queries.

**Alert flow**: Monitor methods → `createIncident()` (builds dict) → `createAlert()` (logs, emails, sends to Splunk HEC). Failed Splunk sends are written to the local `SPLUNK_CACHE` JSON file.

**`SchedulerMonitor.UpdateSchedule`**: This function is currently defined at module scope (outside the class) rather than as a method — it takes `self` as a parameter. This is a known structural issue.

### Settings YAML Structure

Key sections in `prepaid-monitorSettings.yml`:
- `alerts.configured_alerts.<method_name>` — per-alert settings (`enabled`, `interval_minutes`, `impact`, `urgency`, `assignment_group`, plus alert-specific keys like `scheduler_instances`, `jobs_to_watch`)
- `alerts.emailFrom/emailTo/emailCc/emailBcc` — alert email recipients
- `notifications.<job_name>` — job-completion notification config (`report_file_totals`, `emailTo`, etc.)
- `sponsor_banks` — list of `{name, file_identifier}` used to match bank names from file names
- `report_to_email` / `report_to_splunk` — master toggles for alert output channels

## Dev Container

The `.devcontainer/devcontainer.json` builds from `Dockerfile` and mounts:
- `~/logs` → `/usr/prod/ppol/logs`
- `~/sys-utils/conf` → `/usr/prod/ppol/sys-utils/conf`
- `~/plsd-admin` → `/usr/prod/ppol/plsd-admin`

After container creation, `uv sync` runs automatically. The configured formatter is Ruff with format-on-save enabled.
