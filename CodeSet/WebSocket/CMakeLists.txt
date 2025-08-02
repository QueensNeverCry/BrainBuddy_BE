cmake_minimum_required(VERSION 3.15)
project(WebSocket)

# set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)


# 이 경로를 반드시 포함
set(unofficial-uwebsockets_DIR "/Users/v/vcpkg/installed/arm64-osx/share/unofficial-uwebsockets")

find_package(unofficial-uwebsockets CONFIG REQUIRED)

add_executable(main main.cpp)

target_link_libraries(main PRIVATE unofficial::uwebsockets::uwebsockets)
