ARG SDK_ORIGIN=no_sdk

FROM python:3.12-alpine AS python_base
RUN apk add --no-cache tk curl

RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

FROM python_base AS python_test_base
RUN mkdir -p /package
COPY pyproject.toml poetry.lock /package/
WORKDIR /package

RUN poetry config virtualenvs.create false && \
    poetry install --only main --no-root --no-interaction --no-ansi

COPY / /package
ENV PYTHONPATH=/package/src:/package/tests

RUN poetry install --no-interaction --no-ansi

FROM python_test_base AS unit_test
ARG CONDUCTOR_AUTH_KEY
ARG CONDUCTOR_AUTH_SECRET
ARG CONDUCTOR_SERVER_URL
ENV CONDUCTOR_AUTH_KEY ${CONDUCTOR_AUTH_KEY}
ENV CONDUCTOR_AUTH_SECRET ${CONDUCTOR_AUTH_SECRET}
ENV CONDUCTOR_SERVER_URL ${CONDUCTOR_SERVER_URL}
RUN pytest tests/unit -v
RUN pytest tests/backwardcompatibility -v
RUN pytest tests/serdesertest -v
RUN coverage run --source=./src/conductor/client/orkes -m pytest tests/integration -v
RUN coverage report -m

FROM python_test_base AS test
ARG CONDUCTOR_AUTH_KEY
ARG CONDUCTOR_AUTH_SECRET
ARG CONDUCTOR_SERVER_URL
ENV CONDUCTOR_AUTH_KEY ${CONDUCTOR_AUTH_KEY}
ENV CONDUCTOR_AUTH_SECRET ${CONDUCTOR_AUTH_SECRET}
ENV CONDUCTOR_SERVER_URL ${CONDUCTOR_SERVER_URL}
RUN python3 ./tests/integration/main.py

FROM python:3.12-alpine AS publish
RUN apk add --no-cache tk curl
WORKDIR /package

RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH "/root/.local/bin:$PATH"

COPY pyproject.toml poetry.lock /package/
COPY --from=python_test_base /package/src /package/src

RUN poetry config virtualenvs.create false && \
    poetry install --only main --no-root --no-interaction --no-ansi && \
    poetry install --no-root --no-interaction --no-ansi

ENV PYTHONPATH /package/src

ARG CONDUCTOR_PYTHON_VERSION
ENV CONDUCTOR_PYTHON_VERSION ${CONDUCTOR_PYTHON_VERSION}
RUN poetry build
ARG PYPI_USER
ARG PYPI_PASS
RUN poetry config pypi-token.pypi ${PYPI_PASS} && \
    poetry publish --username ${PYPI_USER} --password ${PYPI_PASS}
