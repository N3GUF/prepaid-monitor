## ------------------------------- Builder Stage ------------------------------ ## 
FROM python:3.12-bookworm AS builder

RUN apt-get update && apt-get install --no-install-recommends -y \
        build-essential && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Download the latest installer, install it and then remove it
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set up the UV environment path correctly
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /app

COPY pyproject.toml .

RUN uv sync --no-cache-dir

## ------------------------------- Production Stage ------------------------------ ##
FROM python:3.12-slim-bookworm AS production

# Update system packages to fix vulnerabilities
RUN apt-get update && apt-get upgrade -y && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

ARG USERNAME=prdadmin
# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1
# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1
# Set Timezne
ENV TZ="America/Chicago"
# The following secrets are available during build time
# RUN --mount=type=secret,id=DB_PASSWORD \
# --mount=type=secret,id=DB_USER \
# --mount=type=secret,id=DB_NAME \
# --mount=type=secret,id=DB_HOST \
# --mount=type=secret,id=ACCESS_TOKEN_SECRET_KEY \
# DB_PASSWORD=/run/secrets/DB_PASSWORD \
# DB_USER=$(cat /run/secrets/DB_USER) \
# DB_NAME=$(cat /run/secrets/DB_NAME) \
# DB_HOST=$(cat /run/secrets/DB_HOST) \
# ACCESS_TOKEN_SECRET_KEY=$(cat /run/secrets/ACCESS_TOKEN_SECRET_KEY)

# RUN --mount=type=secret,id=secret-key,target=secrets.json

RUN useradd --create-home ${USERNAME}
USER ${USERNAME}

WORKDIR /usr/prod/ppol/sys-utils/bin/prepaid-monitor

COPY . .
COPY --from=builder /app/.venv .venv

# Set up environment variables for production
ENV PATH="/usr/prod/ppol/sys-utils/bin/prepaid-monitor/.venv/bin:$PATH"

CMD ["python", "app/prepaid-monitor.py"]
