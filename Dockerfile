FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .

# Install only runtime dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user for security
RUN useradd -m -r runner
USER runner

# Set up working directory for code execution
WORKDIR /app/run

# Command will be provided when running the container
CMD ["python", "code.py"] 