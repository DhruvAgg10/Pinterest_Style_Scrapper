# Backend container for Hugging Face Spaces (Docker SDK).
# Runs the FastAPI + CLIP inference engine that Vercel's static frontend calls.
FROM python:3.11-slim

# HF Spaces runs containers as UID 1000. Give that user a writable home + model cache.
RUN useradd -m -u 1000 appuser
ENV HOME=/home/appuser \
    HF_HOME=/home/appuser/.cache/huggingface \
    TRANSFORMERS_CACHE=/home/appuser/.cache/huggingface \
    PORT=7860 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps kept minimal; pillow wheels are self-contained.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY server ./server

RUN chown -R appuser:appuser /app /home/appuser
USER appuser

EXPOSE 7860

# HF Spaces expects the app to listen on 0.0.0.0:7860 (app_port in README frontmatter).
CMD ["uvicorn", "server.app.main:app", "--host", "0.0.0.0", "--port", "7860"]
