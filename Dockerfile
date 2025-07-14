# Use official lightweight Python image
FROM python:3.11-slim

# Set working directory inside container
WORKDIR /app

# Install OS dependencies if needed (uncomment if you want to install fonts, etc.)
# RUN apt-get update && apt-get install -y fonts-dejavu-core && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port for FastAPI/Uvicorn
EXPOSE 8000

# Create cache directory at runtime
RUN mkdir -p cache

# Command to run app
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]
