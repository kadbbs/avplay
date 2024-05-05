cmake_minimum_required(VERSION 3.16)
project(player)
set(CMAKE_CXX_STANDARD 11)


#file(GLOB SRC_FILES CONFIGURE_DEPENDS *.cpp *.h)
aux_source_directory(. SRC_FILES)
#aux_source_directory(mylib SRC_FILES)
set(LIB avformat avcodec avutil swresample m rt pthread z x264)

set(FFMPEG_DIR /usr/local)
include_directories(${PROJECT_SOURCE_DIR}/ ${FFMPEG_DIR}/include)

add_executable(player ${SRC_FILES} )

target_link_libraries(player PUBLIC ${LIB})

