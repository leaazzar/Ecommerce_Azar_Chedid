# Use a lightweight Python image
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose the port Flask will run on
EXPOSE 5001

# Set environment variables for database credentials
ENV DB_USER=admin
ENV DB_PASSWORD=admin123
ENV DB_HOST=postgres-db
ENV DB_NAME=ecommerce

# Command to run the application
CMD ["python", "app.py"]
