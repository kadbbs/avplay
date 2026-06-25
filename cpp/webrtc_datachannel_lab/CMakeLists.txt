cmake_minimum_required(VERSION 3.20)

project(streamforge_webrtc_datachannel_lab CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

include(FetchContent)

set(RTC_BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
set(RTC_BUILD_TESTS OFF CACHE BOOL "" FORCE)
set(RTC_ENABLE_WEBSOCKET OFF CACHE BOOL "" FORCE)

FetchContent_Declare(
    libdatachannel
    GIT_REPOSITORY https://github.com/paullouisageneau/libdatachannel.git
    GIT_TAG v0.24.0
)

FetchContent_MakeAvailable(libdatachannel)

add_executable(webrtc_manual_peer
    src/manual_peer.cpp
)

target_link_libraries(webrtc_manual_peer
    PRIVATE
        LibDataChannel::LibDataChannel
        nlohmann_json::nlohmann_json
)

if (CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    target_compile_options(webrtc_manual_peer PRIVATE -Wall -Wextra)
endif()
