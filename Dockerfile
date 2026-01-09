FROM python:3.9-slim

WORKDIR /app

# Install system dependencies (for building Python packages)
RUN apt-get update && apt-get install -y \
    build-essential \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download NLTK data (if needed by your NLP extraction)
RUN python -m nltk.downloader punkt stopwords

# Copy the rest of the application
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Command to run the dashboard
CMD ["streamlit", "run", "src/dashboard/app.py", "--server.address=0.0.0.0"]
