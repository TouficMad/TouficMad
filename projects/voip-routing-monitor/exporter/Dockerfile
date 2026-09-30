FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1
RUN useradd --create-home --uid 10001 monitor
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY routing_monitor/ routing_monitor/
COPY config.yaml .
USER monitor
EXPOSE 9200
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:9200/health')"
CMD ["python", "-m", "routing_monitor.app"]
