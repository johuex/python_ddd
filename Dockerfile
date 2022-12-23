FROM python:3.11-slim

COPY requirements.txt  /tmp/
RUN pip install -r /tmp/requirements.txt
RUN rm /tmp/requirements.txt

CMD uvicorn "src.allocation.entrypoints.main:fastapi_app" --host 0.0.0.0 --port 8000
