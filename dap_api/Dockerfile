FROM tiangolo/uvicorn-gunicorn:python3.9

LABEL maintainer="Amandus Butzer <amandus.butzer@heigit.de>"

# set reload for gunicorn (important to enable reload for uvicorn as well)
ENV GUNICORN_CMD_ARGS="--reload"

# get DEV argument from docker-compose file
ARG DEV

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python - && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false

# Copy using poetry.lock* in case it doesn't exist yet
COPY ./pyproject.toml ./poetry.lock* /app/

# install dev-dependencies in debug or reload environment
RUN if [ "$DEV" = "1" ] ; then poetry install --no-root --without prod ; else poetry install --no-root --only prod ; fi

# start script should be on root level
RUN cp /app/start-reload.sh /start-reload.sh
