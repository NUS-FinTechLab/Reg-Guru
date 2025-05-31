FROM python:3.9.22

# Set the working directory
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose the port the app runs on
EXPOSE 5000

# Set the environment variable for Flask
ENV OPENAI_API_KEY=api-key
ENV FLASK_ENV=development

# Run the application
CMD ["python3", "app.py"]
