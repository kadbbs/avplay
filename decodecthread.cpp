//
// Created by bbs on 24-4-14.
//

#include "decodecthread.h"
#include <stdio.h>

decodecthread::~decodecthread() {
    if(thread_){
        Stop();
    }
    if(codec_ctx_){
        avcodec_close(codec_ctx_);
    }
}

decodecthread::decodecthread(AVPacketQueue *packetQueue, AVFrameQueue *frameQueue) : packet_queue_(packetQueue), frame_queue_(frameQueue){

}

int decodecthread::Init(AVCodecParameters *par) {
    printf("decodecthread::Init\n");
    if(!par){
        printf("init par is null");
        return-1;
    }
    codec_ctx_= avcodec_alloc_context3(NULL);
    int ret= avcodec_parameters_to_context(codec_ctx_,par);
    if(ret<0){
        av_strerror(ret,err2str,sizeof(err2str));
        printf("avcodec_parameters_to_context,ret%d,err:%s",ret,err2str);

        return -1;
    }
    printf("codec_ctx_->codec_id %d\n",codec_ctx_->codec_id);
    const AVCodec *codec= avcodec_find_decoder(codec_ctx_->codec_id);
    if(!codec) {
        printf("avcodec_find_decoder failed\n");
        return -1;
    }
    ret= avcodec_open2(codec_ctx_,codec,NULL);
    if(ret < 0) {
        av_strerror(ret, err2str, sizeof(err2str));
        printf("avcodec_open2 failed, ret:%d, err2str:%s\n", ret, err2str);
        return -1;
    }

    return 0;
}

int decodecthread::Start() {
    thread_=new std::thread(&decodecthread::Run,this);
    if(!thread_){
        printf("new decodecthread thread!!!\n");
        return -2;
    }
    return 0;
}

int decodecthread::Stop() {

    return 0;
}

void decodecthread::Run() {
    printf("decodecthread::Running !!!\n");
    AVFrame *frame=av_frame_alloc();
    while(abort_!=1){
        AVPacket *pkt = packet_queue_->Pop(10);
        if(pkt){

            int ret = avcodec_send_packet(codec_ctx_,pkt);
            if(!codec_ctx_){
                printf("codec_ctx_ is null\n");
            }
            if(ret<0){
                av_strerror(ret,err2str,sizeof(err2str));
                printf("avcodec_send_packet,ret%d,err:%s\n",ret,err2str);

                return ;
            }
            while(true){
                ret= avcodec_receive_frame(codec_ctx_,frame);
                if(ret==0){
                    frame_queue_->Push(frame);
                    printf("frame_queue_ size: %d\n",frame_queue_->Size());

                    continue;
                }else if(AVERROR(EAGAIN)==ret){
                    break;
                }else{
                    abort_=1;
                    av_strerror(ret,err2str,sizeof(err2str));
                    printf("avcodec_receive_frame,ret%d,err:%s\n",ret,err2str);
                    break;
                }
            }
        }else{
            printf("not got packet!!!\n");

        }
    }

}
