# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.11 as base

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Set Timezne
ENV TZ="America/Chicago"

WORKDIR /src

# Install pip requirements
RUN python -m pip install --upgrade pip
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser app
USER appuser

FROM base as prod

CMD ["python", "app/prepaid-monitor.py"]
