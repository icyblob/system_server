# system_server

A server for handling the request and respond to the nodes and have ability to saving things into database

# Structure
- **app.py** : Python file for handle connection with data base and web app
- **quottery_cpp_wrapper.py**: A Python wrapper for quottery function
- **quottery_cpp** : folder contain cpp source to expose the core functions of qubic-cli's quottery related function

## quottery_cpp

This CMake project will use function implement in **submodule/qubic-cli** and create a C++ library so that Python server can load and use C/C++ function

It try to replicate what qubic-cli handle the quoterry

# How to build

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
Open http://127.0.0.1:5000/get_active_bets