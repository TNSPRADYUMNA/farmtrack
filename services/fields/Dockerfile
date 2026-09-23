FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd --uid 10001 --create-home appuser
COPY common ./common
COPY services/__init__.py ./services/__init__.py
COPY services/fields ./services/fields
USER 10001
EXPOSE 8000
CMD ["uvicorn", "services.fields.app:app", "--host", "0.0.0.0", "--port", "8000"]
