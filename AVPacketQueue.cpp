//
// Created by bbs on 24-5-4.
//

#include "AVPacketQueue.h"
AVPacketQueue::AVPacketQueue() {

}
AVPacketQueue::~AVPacketQueue() {
    AVPacket *pkt=NULL;
    int ret=queue_.Pop(pkt,1);
    if(ret>0){

    }
    av_packet_free(&pkt);
}


int AVPacketQueue::Push(AVPacket *val) {


    AVPacket *tmp_pkt=av_packet_alloc();
    av_packet_move_ref(tmp_pkt,val);
    return queue_.Push(tmp_pkt);
}

AVPacket *AVPacketQueue::Pop(const int timeout){
    AVPacket *tmp_pkt= nullptr;
    int ret=queue_.Pop(tmp_pkt,timeout);
    if(ret<0){
        return NULL;
    }

    return tmp_pkt;
}

int AVPacketQueue::Size() {
    return queue_.Size();
}
