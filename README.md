# StreamForge Gateway

StreamForge Gateway 是一个把 **FFmpeg + RTSP + RTMP + HLS + WebRTC** 串起来的本地流媒体网关项目。

它的目标不是写几个命令示例，而是做一个可运行、可扩展的流媒体实验台：

```text
RTSP / RTMP / file input
  -> FFmpeg probe / transcode / remux
  -> HLS segment output
  -> RTMP push
  -> RTSP publish to MediaMTX
  -> MediaMTX exposes RTSP / RTMP / HLS / WebRTC playback
  -> local dashboard for preview links and channel status
```

## 架构

```text
Camera / OBS / file
        |
        v
   streamctl
        |
        +-- ffprobe: inspect input
        |
        +-- FFmpeg process per channel
              |
              +-- local HLS: runtime/hls/<channel>/index.m3u8
              +-- RTMP push: rtmp://localhost:1935/<channel>
              +-- RTSP publish: rtsp://localhost:8554/<channel>
                                   |
                                   v
                                MediaMTX
                                   |
              +--------------------+--------------------+
              |                    |                    |
             RTSP                 HLS                WebRTC
    rtsp://localhost:8554/x  http://localhost:8888/x  http://localhost:8889/x
```

## 为什么这样设计

- **FFmpeg**：负责协议输入、转码、切片、推流，是真正的数据处理核心。
- **RTSP**：适合摄像头和局域网低延迟拉流。
- **RTMP**：适合 OBS 推流和老直播工作流。
- **HLS**：适合浏览器和点播式预览，延迟高但兼容性好。
- **WebRTC**：适合浏览器低延迟预览，不建议从零实现，交给 MediaMTX。

## 安装依赖

系统需要：

```bash
sudo apt-get install -y ffmpeg
```

推荐安装 MediaMTX：

```bash
docker compose up -d mediamtx
```

如果不用 Docker，也可以下载 MediaMTX 二进制，然后使用本项目的配置：

```bash
mediamtx configs/mediamtx.yml
```

## 快速开始

生成测试视频流：

```bash
ffmpeg -re -stream_loop -1 -i demo.mp4 \
  -c:v libx264 -preset veryfast -tune zerolatency \
  -c:a aac -f flv rtmp://localhost:1935/live/demo
```

探测输入：

```bash
python3 -m streamforge.cli probe demo.mp4
```

把文件或 RTSP/RTMP 输入转成本地 HLS：

```bash
python3 -m streamforge.cli run-channel demo demo.mp4 --hls
```

同时输出 HLS 并发布到 MediaMTX，获得 WebRTC 预览：

```bash
python3 -m streamforge.cli run-channel demo demo.mp4 --hls --publish-rtsp
```

浏览器打开：

```text
http://localhost:8080
```

MediaMTX WebRTC 播放地址：

```text
http://localhost:8889/demo
```

MediaMTX HLS 播放地址：

```text
http://localhost:8888/demo/index.m3u8
```

RTSP 播放地址：

```text
rtsp://localhost:8554/demo
```

## 配置式运行

编辑 [configs/channels.json](/home/bs/code/ffmpeg/configs/channels.json)：

```json
{
  "channels": [
    {
      "name": "demo",
      "input": "demo.mp4",
      "rtsp_transport": "tcp",
      "hls": true,
      "publish_rtsp": true,
      "push_rtmp": null
    }
  ]
}
```

运行：

```bash
python3 -m streamforge.cli run-config configs/channels.json
```

## Dashboard

启动静态页面服务：

```bash
python3 -m streamforge.cli serve --port 8080
```

页面会展示常用播放地址、HLS 播放器和 WebRTC 跳转入口。

## 目录

```text
.
├── configs/
│   ├── channels.json
│   └── mediamtx.yml
├── docs/
│   └── ARCHITECTURE.md
├── runtime/
│   └── hls/
├── streamforge/
│   ├── cli.py
│   ├── core/
│   └── web/
└── tests/
```

## 说明

WebRTC 不是 FFmpeg 直接输出给浏览器，而是 FFmpeg 发布到 MediaMTX，再由 MediaMTX 提供 WebRTC。这个组合更稳定，也更贴近真实项目。

## 学习文档

如果你的目标是熟悉 FFmpeg、RTSP、RTMP、HLS、WebRTC，先读：

- [docs/LEARNING_GUIDE.md](/home/bs/code/ffmpeg/docs/LEARNING_GUIDE.md)
- [docs/ARCHITECTURE.md](/home/bs/code/ffmpeg/docs/ARCHITECTURE.md)
- [docs/WEBRTC_LEARNING_MODE.md](/home/bs/code/ffmpeg/docs/WEBRTC_LEARNING_MODE.md)
- [docs/CPP_WEBRTC_LEARNING.md](/home/bs/code/ffmpeg/docs/CPP_WEBRTC_LEARNING.md)

启动 WebRTC 原理学习模式：

```bash
python3 -m pip install '.[webrtc]'
python3 -m streamforge.cli webrtc-lab --port 8090
```

启动 C++ WebRTC DataChannel 学习模式：

```bash
cmake -S cpp/webrtc_datachannel_lab -B build/webrtc-cpp
cmake --build build/webrtc-cpp

./build/webrtc-cpp/webrtc_manual_peer --role offer --signal-dir runtime/webrtc-signal
./build/webrtc-cpp/webrtc_manual_peer --role answer --signal-dir runtime/webrtc-signal
```
