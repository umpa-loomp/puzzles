FROM python:3.9-slim-bullseye

# Create non-root user
RUN groupadd -g 1000 puzzleapp && \
    useradd -u 1000 -g puzzleapp puzzleapp

WORKDIR /app

# Copy and install requirements first (for better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create directories and set permissions
RUN mkdir -p /app/data /app/logs /app/exports && \
    chown -R puzzleapp:puzzleapp /app && \
    chmod -R 755 /app

# Copy application files with correct ownership
COPY --chown=puzzleapp:puzzleapp backend/src/ /app/
COPY --chown=puzzleapp:puzzleapp backend/data/ /app/data/
COPY --chown=puzzleapp:puzzleapp frontend/ /app/static/

USER puzzleapp
EXPOSE 5000

CMD ["python", "main.py"]