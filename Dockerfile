FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir python-telegram-bot google-genai httpx certifi
CMD ["python", "app.py"]