FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

EXPOSE 5000

# Start the server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]
