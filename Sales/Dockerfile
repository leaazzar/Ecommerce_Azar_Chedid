# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app


# Install the dependencies directly
RUN pip install --no-cache-dir Flask Flask_SQLAlchemy requests

# Copy the application code into the container
COPY . /app

# Expose the port the app runs on
EXPOSE 5003

# Set environment variables, if necessary
ENV FLASK_APP=app.py

# Define the command to run your application
CMD ["flask", "run", "--host=0.0.0.0", "--port=5003"]
