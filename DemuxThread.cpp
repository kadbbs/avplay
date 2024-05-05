//
// Created by bbs on 24-4-14.
//

#include "DemuxThread.h"
#include <thread>
int DemuxThread::Init(const char *url) {
    url_=url;
    int ret;
    std::cout<<"url = "<<url_<<std::endl;
    i_fmt=avformat_alloc_context();

    ret= avformat_open_input(&i_fmt,url_.c_str(),NULL,NULL);
    if(ret<0){

        av_strerror(ret,err,sizeof(err));
        std::cout<<"avformat_open_input failed,"<<err<<std::endl;
        return -1;
    }

    ret= avformat_find_stream_info(i_fmt,NULL);
    if(ret<0){
        av_strerror(ret,err,sizeof(err));
        std::cout<<"avformat_find_stream_info failed,"<<err<<std::endl;
        return -1;
    }
    av_dump_format(i_fmt,0,url_.c_str(),0);
    audio_index= av_find_best_stream(i_fmt,AVMEDIA_TYPE_AUDIO,-1,-1,NULL,0);
    video_index= av_find_best_stream(i_fmt,AVMEDIA_TYPE_VIDEO,-1,-1,NULL,0);
    if(audio_index<0||video_index<0){
        std::cout<<"no av stream"<<std::endl;
        return -1;
    }
    std::cout<<"audio_index="<<audio_index<<std::endl;
    std::cout<<"video_index="<<video_index<<std::endl;

    return 0;
}

DemuxThread::DemuxThread(AVPacketQueue *audio_queue, AVPacketQueue *video_queue):audio_queue_(audio_queue), video_queue_(video_queue) {
    std::cout<<"DemuxThread"<<std::endl;
}

DemuxThread::~DemuxThread() {
    std::cout<<"~DemuxThread"<<std::endl;

    if(thread_) {
        Stop();
    }
}


int DemuxThread::Start() {
    thread_ =new std::thread(&DemuxThread::Run,this);
    if(!thread_) {
        printf("new std::thread(&DemuxThread::Run, this) failed");
        return -1;
    }

    return 0;
}

int DemuxThread::Stop()
{
    Thread::Stop();
    avformat_close_input(&i_fmt);
}

AVCodecParameters *DemuxThread::AudioCodecParameters() {
    if(audio_index!=-1){
        return i_fmt->streams[audio_index]->codecpar;
    }else{
        return NULL;
    }
}

AVCodecParameters *DemuxThread::VideoCodecParameters() {
    if(video_index!=-1){
        return i_fmt->streams[video_index]->codecpar;
    }else{
        return NULL;
    }
}

void DemuxThread::Run() {
    printf("Run into\n");
    int ret=0;
    AVPacket pkt;

    while(abort_!=1){
        if(audio_queue_->Size()>100||video_queue_->Size()>100){
            std::this_thread::sleep_for(std::chrono::milliseconds(10));
            continue;
        }
        ret = av_read_frame(i_fmt, &pkt); //  fread
        if(ret < 0) {
            av_strerror(ret, err, sizeof(err));
            printf("av_read_frame failed, ret:%d, err2str:%s", ret, err);
            break;
        }
        if(pkt.stream_index==audio_index){
            ret=audio_queue_->Push(&pkt);
            printf("audio_packet_queue size:%d\n",audio_queue_->Size());

        }else if(pkt.stream_index==video_index){
            ret=video_queue_->Push(&pkt);
            printf("video_packet_queue size %d\n",video_queue_->Size());

        }else{
            av_packet_unref(&pkt);
        }
    }
    printf("Run finish");
}


AVRational DemuxThread::AudioStreamTimebase()
{
    if(audio_index != -1) {
        return i_fmt->streams[audio_index]->time_base;
    } else {
        return AVRational{0, 0};
    }
}

AVRational DemuxThread::VideoStreamTimebase()
{
    if(video_index!= -1) {
        return i_fmt->streams[video_index]->time_base;
    } else {
        return AVRational{0, 0};
    }
}