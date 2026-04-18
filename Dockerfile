# Use an official Python image as the base
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install pip and uv (a Python packaging tool by Astral)
RUN pip install --upgrade pip \
    && pip install uv

# Copy project files into the container
COPY pyproject.toml uv.lock ./
COPY src ./src

# Install dependencies using uv
RUN uv sync

# Expose the application port
EXPOSE 8000

# Set the command to run the application
CMD ["uv", "run", "src/app.py"]
