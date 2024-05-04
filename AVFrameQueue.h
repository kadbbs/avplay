//
// Created by bbs on 24-5-5.
//

#ifndef PLAYER_AVFRAMEQUEUE_H
#define PLAYER_AVFRAMEQUEUE_H
#include "queue.h"

extern "C"{
#include <libavutil/frame.h>

};

class AVFrameQueue {
public:

    AVFrameQueue();
    ~AVFrameQueue();
    void Abort();
    int Push(AVFrame *val);
    AVFrame *Pop(const int timeout);
    AVFrame *Front();
    int Size();
private:
    void release();
    queue<AVFrame *> queue_;
};


#endif //PLAYER_AVFRAMEQUEUE_H
