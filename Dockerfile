FROM python:3.11-slim

# Create user with UID 1000 (required by HuggingFace Spaces)
RUN useradd -m -u 1000 user

WORKDIR /app

# Install dependencies
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all source files with correct ownership
COPY --chown=user . /app

# Switch to non-root user
USER user

# HuggingFace Spaces expects port 7860
EXPOSE 7860

# Run the FastAPI server
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]
