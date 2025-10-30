FROM python:3.12.11

# Set the working directory
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# Copy the rest of the application code into the container
COPY . .

# Expose the port the app runs on
EXPOSE 6000

# Run the application
CMD ["uvicorn", "embedding_service:app", "--host", "0.0.0.0", "--port", "6000"]