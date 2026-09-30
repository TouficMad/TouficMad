# ---- build stage: install dependencies into a virtualenv ----
FROM python:3.12-slim AS build
WORKDIR /app
RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- runtime stage: small image, non-root user ----
FROM python:3.12-slim
ARG APP_VERSION=dev
ENV PATH="/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    APP_VERSION=${APP_VERSION}
RUN useradd --create-home --uid 10001 appuser
WORKDIR /app
COPY --from=build /venv /venv
COPY app.py .
USER appuser
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')"
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "4", "app:app"]
