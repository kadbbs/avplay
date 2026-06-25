# FFmpeg / RTSP / RTMP / HLS / WebRTC 学习指南

这份文档围绕 StreamForge Gateway 写，不是百科式定义。目标是：你能看懂本项目每条命令为什么这么写，并能自己改输入、改输出、改协议。

## 1. 先建立一张地图

流媒体项目里最容易混乱的是：协议、编码、容器、传输方向经常混在一起说。

先记住这四层：

```text
画面/声音
  -> 编码：H.264 / H.265 / AAC / Opus
  -> 封装：FLV / MPEG-TS / fMP4 / RTP payload
  -> 协议：RTSP / RTMP / HTTP-HLS / WebRTC
  -> 播放端：VLC / OBS / 浏览器 / 移动端播放器
```

FFmpeg 最擅长的是中间三层：读协议、解封装、解码、编码、重新封装、再写协议。

本项目的角色分工：

```text
streamforge.cli       接收你的命令
Channel               描述一个流：名字、输入、输出开关
ffmpeg_commands.py    生成真正的 FFmpeg 命令
process_manager.py    启动和看守 FFmpeg 子进程
MediaMTX              把 RTSP/RTMP 转成浏览器可用的 HLS/WebRTC
web/                  本地预览页面
```

## 2. FFmpeg 是什么

FFmpeg 不是一个“播放器”，更像一把媒体瑞士刀。它常见工作有三种：

### 2.1 probe：看清输入

```bash
python3 -m streamforge.cli probe demo.mp4
```

底层是：

```bash
ffprobe -v error -print_format json -show_format -show_streams demo.mp4
```

你能拿到：

- 是否有视频流
- 是否有音频流
- 视频编码，比如 `h264`
- 音频编码，比如 `aac`
- 分辨率
- 时长

代码入口：

```text
streamforge/core/probe.py
```

### 2.2 transcode：转码

项目里的核心编码参数：

```bash
-c:v libx264
-preset veryfast
-tune zerolatency
-pix_fmt yuv420p
-g 50
-sc_threshold 0
-c:a aac
-ar 48000
-ac 2
```

逐项理解：

| 参数 | 含义 |
| --- | --- |
| `-c:v libx264` | 视频编码成 H.264 |
| `-preset veryfast` | 编码速度优先，适合实时流 |
| `-tune zerolatency` | 减少编码器内部缓存 |
| `-pix_fmt yuv420p` | 浏览器和播放器最兼容的像素格式 |
| `-g 50` | GOP 大小，关键帧间隔 |
| `-sc_threshold 0` | 避免场景切换导致额外关键帧 |
| `-c:a aac` | 音频编码成 AAC |
| `-ar 48000` | 音频采样率 48 kHz |
| `-ac 2` | 双声道 |

代码入口：

```text
streamforge/core/ffmpeg_commands.py::_low_latency_encode_args
```

### 2.3 remux：只换封装不重编码

本项目第一版偏学习稳定性，所以默认重编码。真实生产里，如果输入已经是 H.264/AAC，可以优化成：

```bash
-c copy
```

这叫 remux，CPU 很省，但要求输入编码和输出容器兼容。

## 3. RTSP

RTSP 常见于摄像头。

典型输入：

```text
rtsp://user:password@192.168.1.10:554/stream1
```

项目命令：

```bash
python3 -m streamforge.cli run-channel cam1 \
  rtsp://user:pass@192.168.1.10:554/stream1 \
  --hls
```

底层命令会包含：

```bash
-rtsp_transport tcp -i rtsp://...
```

为什么用 TCP：

- UDP 延迟可能更低，但更容易丢包。
- TCP 更稳，适合先把项目跑通。
- 摄像头、内网、NAT 场景下 TCP 更少惊喜。

代码入口：

```text
streamforge/core/ffmpeg_commands.py::_input_args
```

练习：

1. 把 `--rtsp-transport tcp` 改成 `udp`。
2. 用 VLC 打开同一个 RTSP 地址。
3. 比较 FFmpeg 日志里是否有丢包或重连问题。

## 4. RTMP

RTMP 常见于推流，例如 OBS 推到服务器。

典型地址：

```text
rtmp://127.0.0.1:1935/live/demo
```

RTMP 的常见封装是 FLV，所以 FFmpeg 输出时用：

```bash
-f flv rtmp://...
```

项目里打印 RTMP 推流命令：

```bash
python3 -m streamforge.cli command demo demo.mp4 --kind rtmp
```

你会看到：

```bash
ffmpeg ... -f flv rtmp://127.0.0.1:1935/demo
```

注意：MediaMTX 的路径配置会影响 RTMP URL 形式。OBS 常用：

```text
server: rtmp://127.0.0.1:1935/live
stream key: demo
```

对应完整 URL：

```text
rtmp://127.0.0.1:1935/live/demo
```

本项目默认 `rtmp://127.0.0.1:1935/<channel>`，你也可以通过 `push_rtmp` 指定完整地址。

## 5. HLS

HLS 本质是 HTTP 文件播放：

```text
index.m3u8
segment_00000.ts
segment_00001.ts
segment_00002.ts
```

项目启动本地 HLS：

```bash
python3 -m streamforge.cli run-channel demo demo.mp4 --hls
```

输出目录：

```text
runtime/hls/demo/index.m3u8
runtime/hls/demo/segment_00000.ts
```

底层关键参数：

```bash
-f hls
-hls_time 2
-hls_list_size 6
-hls_flags delete_segments+append_list+program_date_time
-hls_segment_filename runtime/hls/demo/segment_%05d.ts
runtime/hls/demo/index.m3u8
```

逐项理解：

| 参数 | 含义 |
| --- | --- |
| `-f hls` | 输出 HLS |
| `-hls_time 2` | 每个 ts 分片目标 2 秒 |
| `-hls_list_size 6` | 播放列表保留最近 6 个分片 |
| `delete_segments` | 删除旧分片，避免磁盘爆掉 |
| `append_list` | 持续追加播放列表 |
| `program_date_time` | 给分片写入墙钟时间，方便排查延迟 |

HLS 的重要直觉：

- 分片越小，延迟越低，但 HTTP 请求更多。
- 播放器通常要缓冲多个分片。
- 普通 HLS 延迟常见是 6 到 20 秒。
- 它很稳、很兼容，但不是最低延迟方案。

## 6. WebRTC

WebRTC 是浏览器低延迟播放的主角，但它不是一个 FFmpeg 简单 `-f webrtc` 就能输出的协议。

WebRTC 涉及：

- signaling
- ICE
- STUN / TURN
- DTLS
- SRTP
- RTP packetization
- browser SDP negotiation

所以本项目的设计是：

```text
FFmpeg -> RTSP publish -> MediaMTX -> WebRTC browser playback
```

这条是实用路线。项目还提供了 WebRTC Learning Mode：

```text
Browser RTCPeerConnection -> Python aiortc -> generated video track
```

如果你想看 SDP offer/answer、ICE 状态和 `RTCPeerConnection` API，继续读：

```text
docs/WEBRTC_LEARNING_MODE.md
```

启动 MediaMTX：

```bash
docker compose up -d mediamtx
```

发布一个通道：

```bash
python3 -m streamforge.cli run-channel demo demo.mp4 --publish-rtsp
```

打开：

```text
http://127.0.0.1:8889/demo
```

这里的关键理解：

- FFmpeg 负责把媒体推到 MediaMTX。
- MediaMTX 负责和浏览器谈 WebRTC。
- 浏览器不直接吃 RTSP，也不直接吃 RTMP。

## 7. 把四种协议串起来

### 7.1 RTSP 摄像头转 HLS

```bash
python3 -m streamforge.cli run-channel cam1 \
  rtsp://user:pass@192.168.1.10:554/stream1 \
  --hls
```

本地预览：

```bash
python3 -m streamforge.cli serve --port 8080
```

打开：

```text
http://127.0.0.1:8080
```

### 7.2 文件模拟直播转 WebRTC

```bash
docker compose up -d mediamtx

python3 -m streamforge.cli run-channel demo demo.mp4 --publish-rtsp
```

打开：

```text
http://127.0.0.1:8889/demo
```

### 7.3 文件同时输出 HLS 和 WebRTC

```bash
docker compose up -d mediamtx

python3 -m streamforge.cli run-channel demo demo.mp4 --hls --publish-rtsp
```

本地 HLS：

```text
runtime/hls/demo/index.m3u8
```

MediaMTX WebRTC：

```text
http://127.0.0.1:8889/demo
```

### 7.4 RTMP 推流到 MediaMTX

```bash
python3 -m streamforge.cli run-channel demo demo.mp4 \
  --push-rtmp rtmp://127.0.0.1:1935/live/demo
```

然后你可以在 MediaMTX 侧用 HLS/WebRTC 播放它，具体路径取决于 MediaMTX 的 path 配置。

## 8. 读代码路线

按这个顺序读，不容易乱：

1. `streamforge/core/channel.py`

   看一个通道如何定义：`name`、`input`、`hls`、`publish_rtsp`、`push_rtmp`。

2. `streamforge/core/ffmpeg_commands.py`

   看每种输出如何变成 FFmpeg 命令。

3. `streamforge/core/probe.py`

   看 ffprobe 如何拿到媒体信息。

4. `streamforge/core/pipeline.py`

   看一个通道会启动哪些 FFmpeg 子进程。

5. `streamforge/core/process_manager.py`

   看 Python 如何管理长期运行的 FFmpeg。

6. `streamforge/cli.py`

   看命令行如何把用户输入变成 Channel 和 Pipeline。

7. `streamforge/web/`

   看 HLS 和 WebRTC 播放入口怎么组织。

## 9. 最小实验清单

### 实验 1：只看命令，不执行

```bash
python3 -m streamforge.cli command demo demo.mp4 --kind hls
python3 -m streamforge.cli command demo demo.mp4 --kind rtsp
python3 -m streamforge.cli command demo demo.mp4 --kind rtmp
```

把输出复制出来，逐个参数查清楚。

### 实验 2：生成 HLS

```bash
python3 -m streamforge.cli run-channel demo demo.mp4 --hls
```

另开终端：

```bash
ls runtime/hls/demo
sed -n '1,40p' runtime/hls/demo/index.m3u8
```

观察 `.m3u8` 文件如何随着时间更新。

### 实验 3：启动 dashboard

```bash
python3 -m streamforge.cli serve --port 8080
```

打开：

```text
http://127.0.0.1:8080
```

### 实验 4：接入 MediaMTX

```bash
docker compose up -d mediamtx
python3 -m streamforge.cli run-channel demo demo.mp4 --publish-rtsp
```

打开：

```text
http://127.0.0.1:8889/demo
```

### 实验 5：改 HLS 延迟

改 `streamforge/core/ffmpeg_commands.py`：

```python
"-hls_time", "2"
```

改成：

```python
"-hls_time", "1"
```

重新运行，观察分片数量和播放延迟。

## 10. 常见问题

### 浏览器为什么不能直接播放 RTSP

浏览器没有原生 RTSP 播放能力。你需要把 RTSP 转成 HLS 或 WebRTC。

### 浏览器为什么不能直接播放 RTMP

现代浏览器已经不支持 Flash，RTMP 主要作为推流协议，不适合作为网页播放协议。

### HLS 为什么延迟高

因为 HLS 是分片播放，播放器通常等几个分片再播。它追求兼容性和稳定性，不追求最低延迟。

### WebRTC 为什么不用 FFmpeg 直接做

FFmpeg 可以处理 RTP/编码/封装，但完整 WebRTC 需要浏览器协商和网络穿透。用 MediaMTX 更现实。

### 为什么文件输入要 `-stream_loop -1 -re`

文件默认会被 FFmpeg 尽快读完。模拟直播时要：

- `-stream_loop -1`：无限循环文件。
- `-re`：按真实时间速度读取，不要瞬间跑完。

## 11. 你应该形成的判断

如果你要做摄像头预览：

```text
RTSP input -> FFmpeg -> HLS/WebRTC
```

如果你要做 OBS 推流：

```text
OBS RTMP -> MediaMTX -> HLS/WebRTC
```

如果你要做浏览器低延迟：

```text
WebRTC
```

如果你要做最大兼容：

```text
HLS
```

如果你要做后端转码：

```text
FFmpeg
```
