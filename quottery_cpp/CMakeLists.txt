project(quottery_cpp)

set(QUBIC_CLI_SRC_DIR ${CMAKE_SOURCE_DIR}/submodules/qubic-cli)
set(QUBIC_CLI_SRC
    ${QUBIC_CLI_SRC_DIR}/quottery.cpp
    ${QUBIC_CLI_SRC_DIR}/keyUtils.cpp
    ${QUBIC_CLI_SRC_DIR}/connection.cpp
    ${QUBIC_CLI_SRC_DIR}/nodeUtils.cpp
    ${QUBIC_CLI_SRC_DIR}/qubicLogParser.cpp
    ${QUBIC_CLI_SRC_DIR}/walletUtils.cpp)

add_library(${PROJECT_NAME} SHARED
            src/quottery_wrapper.cpp
            src/key_utils_wrapper.cpp
            src/node_utils_wrapper.cpp
            ${QUBIC_CLI_SRC})
target_include_directories(${PROJECT_NAME}
    PRIVATE
    include
    ${QUBIC_CLI_SRC_DIR})

# Install library to a specific location
# Below variables are set so that the export target can be relativu
set(INCLUDE_INSTALL_DIR include/${PROJECT_NAME})
set(LIBRARY_INSTALL_DIR lib)
set(BINARY_INSTALL_DIR bin)
set(CONFIG_INSTALL_DIR ${LIBRARY_INSTALL_DIR}/cmake/${PROJECT_NAME})

include(CMakePackageConfigHelpers)

install(TARGETS ${PROJECT_NAME}
    EXPORT ${PROJECT_NAME}Targets
    LIBRARY DESTINATION ${LIBRARY_INSTALL_DIR}
    RUNTIME DESTINATION ${BINARY_INSTALL_DIR}
    INCLUDES DESTINATION ${INCLUDE_INSTALL_DIR})

configure_package_config_file(
    ${PROJECT_NAME}Config.cmake.in
    "${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}Config.cmake"
    INSTALL_DESTINATION "${CONFIG_INSTALL_DIR}")

install(EXPORT quottery_cppTargets
    FILE ${PROJECT_NAME}Targets.cmake
    DESTINATION ${CONFIG_INSTALL_DIR})

install(FILES
    "${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}Config.cmake"
    DESTINATION "${CONFIG_INSTALL_DIR}")
install(DIRECTORY
    include/
    DESTINATION "${INCLUDE_INSTALL_DIR}")