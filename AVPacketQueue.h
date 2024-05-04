//
// Created by bbs on 24-5-4.
//

#ifndef PLAYER_AVPACKETQUEUE_H
#define PLAYER_AVPACKETQUEUE_H
#include "queue.h"
extern "C"{
#include <libavformat/avformat.h>
#include <libavcodec/avcodec.h>
#include <libavutil/avutil.h>
#include <libavutil/mem.h>
#include <libavutil/rational.h>
#include <libavutil/timestamp.h>
#include <libavutil/mathematics.h>
};

class AVPacketQueue{

public:

    AVPacketQueue();
    ~AVPacketQueue();



    void Abort();
    int Push(AVPacket * val);
    int Size();
    int release();

    AVPacket *Pop(const int timeout);

private:
    queue<AVPacket *> queue_;

};


#endif //PLAYER_AVPACKETQUEUE_H
