
FROM python:3.9-slim

WORKDIR /app

# Copy Requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Source Code
COPY . .

# Set Environment Variables (These will be overridden by docker run -e)
ENV GEMINI_API_KEY=""
ENV AWS_ACCESS_KEY_ID=""
ENV AWS_SECRET_ACCESS_KEY=""
ENV DRIFTGUARD_PAT=""

# Expose Port
EXPOSE 8000

# Run Application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
