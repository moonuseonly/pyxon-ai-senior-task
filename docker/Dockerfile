# Slim Python base — no need for the full image, this project has no
# compiled/system dependencies beyond what pip installs.
FROM python:3.11-slim

WORKDIR /app

# Copy requirements first so Docker can cache this layer — it only
# re-installs dependencies when requirements.txt actually changes,
# not on every code edit.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the rest of the source.
COPY . .

# API keys are NOT baked into the image (see .dockerignore) — they're
# passed at runtime via --env-file, same principle as the rest of the
# project: no secrets in source control or in the image layers.
ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]
