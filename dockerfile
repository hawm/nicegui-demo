FROM mcr.microsoft.com/devcontainers/python:1-3.12-bullseye

WORKDIR /app

RUN pip install poetry
COPY pyproject.toml poetry.lock /app/
RUN poetry install --no-root --no-interaction
COPY main.py /app/

EXPOSE 8080
VOLUME /app/data

CMD ["poetry", "run", "python", "main.py"]


