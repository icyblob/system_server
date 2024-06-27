# system_server

A server for handling the request and respond to the nodes and have ability to saving things into database.
This server code is Flask based at the momment.

# Structure
- **app.py** : Python file for handle connection with data base and web app
- **quottery_cpp_wrapper.py**: A Python wrapper for quottery function
- **quottery_cpp** : folder contain cpp source to expose the core functions of qubic-cli's quottery related function

## quottery_cpp

This CMake project will use function implement in **submodule/qubic-cli** and create a C++ library so that Python server can load and use C/C++ function

It try to replicate what qubic-cli handle the quoterry

# Use Docker

## Run with docker
- Change your settings in `docker-compose.yml`
- Run
```commandline
docker compose up
```

## Build with docker
If you want to build a local image, use `build_docker.sh` to manually build your customized docker image.
```commandline
./build_docker.sh
```
Then update the image in section `image` in `docker-compose.yml`

# How to build on local machine

## Requirement

### C++
```
sudo apt update
sudo apt install build-essentials cmake
```

### Python

Depend on purpose, can use venv or install on local machine
```
pip install -r requirements.txt
```

## quottery_cpp
At current source

```
mkdir build
cd build
cmake .. -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=../libs/quottery_cpp
make install
```
After this a **quottery_cpp** library will be install into ../libs/quottery_cpp

# How to run

## Setting

### Config the SSL certification
Setting 2 environment point to crt and key location

```
CERT_PATH=
KEY_PATH=
```

### Set the connection to a node
In app.py modify below value pointing to the node server

```
NODE_IP =
NODE_PORT =
```

## Run

```
python3 app.py
```

### Clean up the database

You can delete the **database.db** to get a fresh version of quottery information

### Test the loading data
Open https://127.0.0.1:5000/get_active_bets

# Troubleshoot

- Enable UFW (if not already enabled)
```commandline
sudo ufw enable
sudo ufw allow 5000
```

Check UFW status
```commandline
sudo ufw status
```