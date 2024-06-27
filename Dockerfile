ARG base_image="ubuntu:22.04"
ARG image_type="release"
ARG package_location=""

# Set environment variables to avoid user prompts during installation
ARG DEBIAN_FRONTEND=noninteractive

#********************Setup an runtime environment for running.
# If this scale up, we will switch to dual images
FROM ${base_image} as build_image_runtime
ARG DEBIAN_FRONTEND
ARG package_location

# Install runtime environment
RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    apt-get clean

#********************Setup an develop environment for building.
# If this scale up, we will switch to dual images
FROM ${base_image} as build_image_develop
ARG DEBIAN_FRONTEND
ARG package_location

# Install cmake, git and dev environments
RUN apt-get update && \
    apt-get install -y cmake build-essential && \
    apt-get clean

#********************Package
FROM ${base_image} as build_image_release
ARG DEBIAN_FRONTEND
ARG APP_DEPENDENCIES
ARG package_location

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create and set the working directory
WORKDIR /app

# Copy the requirements.txt file
COPY ${package_location}/ /app/

# Install the required Python packages
RUN pip3 install --no-cache-dir -r requirements.txt

# Expose the port that the Flask app runs on
EXPOSE 5000

# Place holder to trigger above build
FROM build_image_${image_type}
ARG DEBIAN_FRONTEND
ARG APP_DEPENDENCIES
ARG CMD_BUILD
ARG package_location
