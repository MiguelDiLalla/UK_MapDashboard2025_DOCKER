# Use official Python image
FROM python:3.10-slim

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code and data
COPY app.py ./
COPY data ./data
COPY .streamlit ./.streamlit

# Expose Streamlit port
EXPOSE 8504

HEALTHCHECK CMD curl --fail http://localhost:8504/_stcore/health

# Run Streamlit app with better logging "--server.port=8504", "--server.address=0.0.0.0",
CMD ["streamlit", "run", "app.py", "--server.port=8504", "--server.address=0.0.0.0", "--logger.level=info"]