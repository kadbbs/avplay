//
// Created by bbs on 24-4-14.
//

#ifndef PLAYER_DECODECTHREAD_H
#define PLAYER_DECODECTHREAD_H
#include "DemuxThread.h"
#include "AVFrameQueue.h"
#include "AVPacketQueue.h"


class decodecthread :public Thread{
public:
    decodecthread(AVPacketQueue *packetQueue,AVFrameQueue *frameQueue);
    ~decodecthread();

    int Init(AVCodecParameters *par);
    int Start();
    int Stop();
    void Run();


private:
    char err2str[256]={0};
    AVCodecContext *codec_ctx_=NULL;
    AVPacketQueue *packet_queue_ = NULL;
    AVFrameQueue *frame_queue_ = NULL;

};


#endif //PLAYER_DECODECTHREAD_H
