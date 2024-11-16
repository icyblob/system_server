#!/bin/bash

# If this is enabled both runtime and develop image will be re-built
BUILD_ALL=1

# Build the environment Docker image
DEV_IMAGE="flask-app-dev"
RUNTIME_IMAGE="flask-app-rt"
RELEASE_IMAGE="flask-app"
DOCKER_SRC_DIR="/app_code"

if [ "$BUILD_ALL" == 1 ]; then
    # Trigger build the runtime image
    echo "Building the runtime Docker image"
    docker build -f Dockerfile --build-arg image_type=runtime -t ${RUNTIME_IMAGE} .

    # Build the dev image with tool for compilation
    echo "Building the develop Docker image"
    docker build -f Dockerfile --build-arg base_image=${RUNTIME_IMAGE} --build-arg image_type=develop -t ${DEV_IMAGE} .
fi


# Compile the code if neccessary
package_location=build_docker
build_cmd="rm -rf ${package_location} || true && \
mkdir ${package_location} && \
cd ${package_location} && \
cmake .. -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=./redist/libs/quottery_cpp && \
make install"
install_cmd="cp -r ${DOCKER_SRC_DIR}/quottery_rpc_wrapper.py ${DOCKER_SRC_DIR}/qtry_utils.py ${DOCKER_SRC_DIR}/db_updater.py ${DOCKER_SRC_DIR}/app.py ${DOCKER_SRC_DIR}/${package_location}/redist"
docker run --rm -v ./:${DOCKER_SRC_DIR} -u $(id -u) ${DEV_IMAGE} bash -c "cd /app_code && $build_cmd && $install_cmd"

# Package into a new release image base on runtime time
echo "Packaging..."
docker build --build-arg base_image=${RUNTIME_IMAGE} --build-arg image_type=release --build-arg package_location=${package_location}/redist -t ${RELEASE_IMAGE} .