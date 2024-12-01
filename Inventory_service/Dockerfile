# Use a lightweight Python base image
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire inventory service code into the container
COPY . .

# Expose the port Flask will run on
EXPOSE 5002

# Set environment variables for database credentials
ENV DB_USER=admin
ENV DB_PASSWORD=admin123
ENV DB_HOST=postgres-db
ENV DB_NAME=ecommerce

# Command to run the Flask application
CMD ["python", "app.py"]
