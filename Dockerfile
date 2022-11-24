FROM python:3.11-slim

WORKDIR /code
COPY src/allocation/entrypoints api
COPY src/allocation/helpers helpers
COPY src/allocation/models models
COPY src/allocation/service_layer services
COPY ./requirements.txt .

RUN pip install -r requirements.txt
CMD uvicorn "api.main:fastapi_app" --host 0.0.0.0 --port 8000
