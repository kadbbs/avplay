cmake_minimum_required(VERSION 3.16)

project(mediaforge C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)

find_package(PkgConfig REQUIRED)
pkg_check_modules(FFMPEG REQUIRED IMPORTED_TARGET
    libavformat
    libavcodec
    libavutil
    libswscale
    libswresample
)

add_executable(mediaforge src/main.c)
target_link_libraries(mediaforge PRIVATE PkgConfig::FFMPEG)

if (CMAKE_C_COMPILER_ID MATCHES "GNU|Clang")
    target_compile_options(mediaforge PRIVATE -Wall -Wextra -Wpedantic)
endif()
