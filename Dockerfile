# Use lightweight Python
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir fastapi uvicorn pydantic openenv-core openai

# Expose port
EXPOSE 7860

# Run app
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]