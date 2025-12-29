# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

FROM python:3.13-alpine3.20
CMD ["uvicorn", "src.main:app", "--reload", "--port", "80", "--host", "0.0.0.0"]
EXPOSE 80

ARG DOCKER_USER
ARG DOCKER_UID
ARG DOCKER_GID

RUN apk add --no-cache gcc python3-dev musl-dev linux-headers postgresql-dev

WORKDIR /app

RUN addgroup -g ${DOCKER_GID} ${DOCKER_USER} || true && \
    adduser -D -u ${DOCKER_UID} ${DOCKER_USER} || true && \
    addgroup ${DOCKER_USER} ${DOCKER_USER} || true

COPY *.txt .

RUN pip install -r requirements.txt

USER $DOCKER_UID
