FROM python:3.11-slim

WORKDIR /code
COPY api api
COPY helpers helpers
COPY models models
COPY services services
COPY ./requirements.txt .

RUN pip install -r requirements.txt
CMD uvicorn "api.main:fastapi_app" --host 0.0.0.0 --port 8000
