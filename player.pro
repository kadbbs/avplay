TEMPLATE = app
CONFIG += console c++11
CONFIG -= app_bundle
CONFIG -= qt
CONFIG +=debug

SOURCES += main.cpp \
    log.cpp \
    DemuxThread.cpp \
    AVPacketQueue.cpp \
    AVFrameQueue.cpp \
    decodecthread.cpp \


unix{

INCLUDEPATH+=\
        /usr/local/include/SDL2 \
        /usr/local/include
LIBS +=\
        /usr/local/lib/libavcodec.so \
        /usr/local/lib/libavdevice.so \
        /usr/local/lib/libavfilter.so \
        /usr/local/lib/libavformat.so \
        /usr/local/lib/libavutil.so \
        /usr/local/lib/libpostproc.so \
        /usr/local/lib/libswresample.so \
        /usr/local/lib/libswscale.so \
#        /usr/lib/x86_64-linux-gnu/libx264.so \
        /usr/local/lib/libSDL2.so \
        -lpthread

}


win32 {
INCLUDEPATH += $$PWD/ffmpeg-4.2.1-win32-dev/include \
            $$PWD/SDL2-2.0.10/include
LIBS += $$PWD/ffmpeg-4.2.1-win32-dev/lib/avformat.lib   \
        $$PWD/ffmpeg-4.2.1-win32-dev/lib/avcodec.lib    \
        $$PWD/ffmpeg-4.2.1-win32-dev/lib/avdevice.lib   \
        $$PWD/ffmpeg-4.2.1-win32-dev/lib/avfilter.lib   \
        $$PWD/ffmpeg-4.2.1-win32-dev/lib/avutil.lib     \
        $$PWD/ffmpeg-4.2.1-win32-dev/lib/postproc.lib   \
        $$PWD/ffmpeg-4.2.1-win32-dev/lib/swresample.lib \
        $$PWD/ffmpeg-4.2.1-win32-dev/lib/swscale.lib
LIBS += $$PWD/SDL2-2.0.10/lib/x86/SDL2.lib
}

HEADERS += \
    log.h \
    queue.h \
    Thread.h\
    log.h \
    DemuxThread.h \
    AVPacketQueue.h \
    AVFrameQueue.h \
    decodecthread.h s

DISTFILES += \
    time.mp4

