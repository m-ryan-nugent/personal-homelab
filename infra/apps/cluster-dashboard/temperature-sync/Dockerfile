FROM python:3.14-alpine

LABEL org.opencontainers.image.title="cluster-dashboard-temperature-sync" \
      org.opencontainers.image.description="CronJob image for syncing Raspberry Pi dashboard metrics" \
      org.opencontainers.image.source="https://github.com/m-ryan-nugent/personal-homelab"

RUN apk add --no-cache openssh-client

WORKDIR /app

COPY sync_temperatures.py /app/sync_temperatures.py

CMD ["python", "/app/sync_temperatures.py"]