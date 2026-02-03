FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

# Expose port
EXPOSE 8080

# Set environment variables
ENV PORT=8080
ENV BACKEND_URL=""

# Run Streamlit
CMD streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true



