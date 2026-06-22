FROM apache/airflow:2.10.4-python3.11

USER root
RUN mkdir -p /opt/etl-venv && chown -R airflow:root /opt/etl-venv

USER airflow
COPY docker/airflow-requirements.txt /requirements.txt
RUN python -m venv /opt/etl-venv \
    && /opt/etl-venv/bin/pip install --upgrade pip \
    && /opt/etl-venv/bin/pip install --no-cache-dir -r /requirements.txt

ENV ETL_PYTHON=/opt/etl-venv/bin/python
