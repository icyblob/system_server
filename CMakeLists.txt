cmake_minimum_required(VERSION 3.10)
project(quottery_cpp_server)

# Set the C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED True)

# Add executable
add_executable(quottery_server main.cpp)

# Include directories
target_include_directories(quottery_server PRIVATE ${CMAKE_SOURCE_DIR} ${CMAKE_SOURCE_DIR}/include)

# Find and link libraries
find_package(Threads REQUIRED)
target_link_libraries(quottery_server PRIVATE Threads::Threads)