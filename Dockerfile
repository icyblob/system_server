# Use the official Ubuntu 20.04 image as the base image
FROM ubuntu:22.04

# Set environment variables to avoid user prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Install Python 3, pip, cmake, and other dependencies
RUN apt-get update && \
    apt-get install -y python3 python3-pip cmake build-essential && \
    apt-get clean

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create and set the working directory
WORKDIR /app

# Copy the requirements.txt file
COPY requirements.txt /app/

# Install the required Python packages
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . /app/

# Build and install the C++ project
RUN [ -d build ] && rm -rf build || true && \
    mkdir build && \
    cd build && \
    cmake .. -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=../libs/quottery_cpp && \
    make install

# Expose the port that the Flask app runs on
EXPOSE 5000

# Command to run the Flask app
CMD ["python3", "app.py"]