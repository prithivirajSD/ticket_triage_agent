FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for Streamlit
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Streamlit app
COPY . .

# Expose internal port (Render will map automatically)
EXPOSE 8501

# Render sets $PORT automatically, so use it.
CMD streamlit run ui.py --server.port $PORT --server.address 0.0.0.0
