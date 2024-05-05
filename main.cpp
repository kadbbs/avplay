#include <iostream>
#include "DemuxThread.h"
#include "AVFrameQueue.h"
#include "decodecthread.h"

int main(int argc ,char **argv) {
    std::cout << "Hello, World!" << std::endl;
    AVPacketQueue audio_packet_queue;
    AVPacketQueue video_packet_queue;

    AVFrameQueue audio_frame_queue;
    AVFrameQueue video_frame_queue;
    DemuxThread *demuxThread=new DemuxThread(&audio_packet_queue,&video_packet_queue);
    demuxThread->Init(argv[1]);
    demuxThread->Start();

//    std::this_thread::sleep_for(std::chrono::milliseconds(50*1000));

    printf("audio_packet_queue size:%d",audio_packet_queue.Size());
    printf("video_packet_queue size %d",video_packet_queue.Size());


    //解码线程
    decodecthread *audio_decodecthread=new decodecthread(&audio_packet_queue,&audio_frame_queue);
    decodecthread *video_decodecthread=new decodecthread(&video_packet_queue,&video_frame_queue);

    audio_decodecthread->Init(demuxThread->AudioCodecParameters());
    audio_decodecthread->Start();


    video_decodecthread->Init(demuxThread->VideoCodecParameters());
    video_decodecthread->Start();


//    demuxThread->Stop();
//    delete demuxThread;
//    audio_decodecthread->Stop();
//    delete audio_decodecthread;
//    video_decodecthread->Stop();
//    delete video_decodecthread;


    //
    return 0;
}
