cmake_minimum_required(VERSION 3.16)

project(ffmpeg_five_lab C)

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

add_executable(ff5lab src/main.c)
target_link_libraries(ff5lab PRIVATE PkgConfig::FFMPEG)

if (CMAKE_C_COMPILER_ID MATCHES "GNU|Clang")
    target_compile_options(ff5lab PRIVATE -Wall -Wextra -Wpedantic)
endif()
