//
// Created by bbs on 24-4-14.
//

#ifndef PLAYER_DEMUXTHREAD_H
#define PLAYER_DEMUXTHREAD_H

#include <string>
#include <iostream>
#include "Thread.h"
#include "AVPacketQueue.h"

extern "C"{
#include <libavformat/avformat.h>
#include <libavcodec/avcodec.h>
#include <libavutil/avutil.h>
#include <libavutil/mem.h>
#include <libavutil/rational.h>
#include <libavutil/timestamp.h>
#include <libavutil/mathematics.h>
}

class DemuxThread :public Thread{

public:
        DemuxThread(AVPacketQueue *audio_queue, AVPacketQueue *video_queue);
        ~DemuxThread();
        int Start();
        int Stop();
        int Init(const char *url);
        void Run();
        AVCodecParameters* AudioCodecParameters();
        AVCodecParameters* VideoCodecParameters();
        AVRational AudioStreamTimebase();
        AVRational VideoStreamTimebase();





private:
    char err[256]={0};
    std::string url_;
    AVPacketQueue *audio_queue_ = NULL;
    AVPacketQueue *video_queue_ = NULL;
    AVFormatContext *i_fmt= nullptr;
    int audio_index=-1;
    int video_index=-1;




};


#endif //PLAYER_DEMUXTHREAD_H
