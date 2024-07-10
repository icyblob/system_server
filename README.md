[![Docker Image CI](https://github.com/icyblob/system_server/actions/workflows/docker-image.yml/badge.svg)](https://github.com/icyblob/system_server/actions/workflows/docker-image.yml)

# system_server

A server for handling database request, respond to the frontend, and save historical data from qubic nodes.

# Structure
- **app.py** : A Python file for handling requests from the frontend.
- **db_updater.py**: A Python file for syncing with the qubic node's quottery info and updating the
database accordingly.
- **quottery_cpp_wrapper.py**: A Python wrapper for quottery function.
- **quottery_cpp** : The folder contains cpp source to expose the core functions of
qubic-cli's quottery-related feature.

## quottery_cpp

This CMake project will use function implementation in **submodule/qubic-cli** and
create a C++ library so that Python server can load and use C/C++ function.

It tries to replicate what qubic-cli handle the quoterry.

# Project Setup Guide
Please refer to [this document](docs/1.Setup.md) for detailed setup guides.
