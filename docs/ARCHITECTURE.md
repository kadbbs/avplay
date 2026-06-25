# StreamForge Gateway Architecture

StreamForge 把复杂协议拆成两个职责边界：

- FFmpeg：负责输入、转码、封装、切片、推流。
- MediaMTX：负责 RTSP、RTMP、HLS、WebRTC 协议服务。

## 数据路径

### RTSP camera to HLS

```text
rtsp://camera/live
  -> ffmpeg -rtsp_transport tcp -i ...
  -> runtime/hls/camera/index.m3u8
  -> browser dashboard
```

### File to WebRTC

```text
demo.mp4
  -> ffmpeg -re -i demo.mp4 -f rtsp rtsp://127.0.0.1:8554/demo
  -> MediaMTX
  -> http://127.0.0.1:8889/demo
```

### RTMP ingest to WebRTC

```text
OBS -> rtmp://127.0.0.1:1935/live/demo
  -> MediaMTX path
  -> WebRTC / HLS / RTSP playback
```

## Latency expectations

- RTSP over TCP: low latency on LAN, but browser support requires a gateway.
- RTMP: useful for ingest, not a modern browser playback protocol.
- HLS: high compatibility, usually several seconds of latency.
- WebRTC: browser-native low-latency playback through MediaMTX.

## Why not implement WebRTC directly

WebRTC requires signaling, ICE, DTLS, SRTP, RTP packetization and browser negotiation.
For a practical FFmpeg-centered project, MediaMTX gives a proven WebRTC gateway while
keeping FFmpeg as the media processing engine.
