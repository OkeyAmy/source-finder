# Base image
FROM python:3.12-slim

# System dependencies for Playwright Chromium
RUN apt-get update && apt-get install -y \
    libgtk-3-0 \
    libdbus-glib-1-2 \
    libxt6 \
    libxaw7 \
    libnss3 \
    libnspr4 \
    libpcre3 \
    libasound2 \
    libxdamage1 \
    libgbm1 \
    libxfixes3 \
 && apt-get clean

# Set work directory
WORKDIR /app

# Copy code
COPY . .

# Install dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Install Playwright
RUN python -m playwright install chromium

# Expose the port your app runs on (e.g., for FastAPI it's usually 8000)
EXPOSE 8000

# Start the app (customize this!)
CMD ["gunicorn", "app.main:app", "--bind", "0.0.0.0:8000"]
