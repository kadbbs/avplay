//
// Created by bbs on 24-4-14.
//

#ifndef PLAYER_DECODECTHREAD_H
#define PLAYER_DECODECTHREAD_H
#include "DemuxThread.h"

class decodecthread :public Thread{
public:
    decodecthread();

    ~decodecthread();
private:
    char err2str[256]={0};
    AVCodecContext *codec_ctx_=NULL;
    AVPacketQueue *packet_queue_ = NULL;
//    AVFrameQueue *frame_queue_ = NULL;

};


#endif //PLAYER_DECODECTHREAD_H
