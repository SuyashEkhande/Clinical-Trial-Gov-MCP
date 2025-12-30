FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY server.py .
COPY config.py .
COPY core/ ./core/
COPY tools/ ./tools/
COPY utils/ ./utils/

# Expose port
EXPOSE 8000

# Run the server
CMD ["python", "server.py"]
