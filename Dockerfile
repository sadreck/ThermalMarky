# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies for python-escpos (USB and other drivers)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libusb-1.0-0-dev \
    libjpeg-dev \
    zlib1g-dev \
    libcups2-dev \
    python3-dev \
    gcc \
    usbutils \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Create the data directory
RUN mkdir -p data

# Expose the port the app runs on
EXPOSE 8000

# Define environment variables (can be overridden at runtime)
# ENV TYPE=usb
# ENV VENDOR_ID=0x04b8
# ENV PRODUCT_ID=0x0e20

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--ssl-keyfile", "certs/key.pem", "--ssl-certfile", "certs/cert.pem"]
