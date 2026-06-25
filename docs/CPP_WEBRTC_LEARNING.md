# C++ WebRTC 学习路线

你想用 C++ 学 WebRTC，我建议分两步：

```text
第一步：C++ PeerConnection + DataChannel
第二步：C++ PeerConnection + FFmpeg/RTP video track
```

当前项目已经加入第一步：`cpp/webrtc_datachannel_lab`。

## 为什么先学 DataChannel

WebRTC 里真正难的第一层不是视频，而是：

- signaling
- SDP offer / answer
- ICE candidate
- DTLS/SRTP 连接建立
- PeerConnection 状态

DataChannel 不需要摄像头、编码器和 RTP packetization，所以最适合先把 WebRTC 连接过程看清楚。

## 为什么用 libdatachannel

C++ 有两条路线：

| 路线 | 优点 | 缺点 |
| --- | --- | --- |
| Google libWebRTC | 最完整，Chrome 同源实现 | 构建巨大，依赖复杂，初学容易卡在工程环境 |
| libdatachannel | C++17、CMake、轻量、能和浏览器互通 | 功能不如 libWebRTC 全 |

本项目用 `libdatachannel` 做学习层。它是 C++ WebRTC network library，提供 DataChannel、Media Transport、WebSocket 等能力，API 也接近浏览器 WebRTC。

## 构建

```bash
cmake -S cpp/webrtc_datachannel_lab -B build/webrtc-cpp
cmake --build build/webrtc-cpp
```

首次构建会下载：

- `libdatachannel`

`nlohmann/json` 会由 `libdatachannel` 的依赖树提供，本项目直接复用它。

## 运行

开第一个终端：

```bash
./build/webrtc-cpp/webrtc_manual_peer \
  --role offer \
  --signal-dir runtime/webrtc-signal
```

开第二个终端：

```bash
./build/webrtc-cpp/webrtc_manual_peer \
  --role answer \
  --signal-dir runtime/webrtc-signal
```

两个 C++ peer 会通过文件交换信令：

```text
runtime/webrtc-signal/
├── offer_description.json
├── answer_description.json
├── offer_candidates.jsonl
└── answer_candidates.jsonl
```

连接成功后，在一边输入文字，另一边会收到 DataChannel 消息。

## 你应该观察的日志

### Local description ready

本端生成 SDP。

### Remote description applied

本端读取并应用对端 SDP。

### Local candidate

本端发现一个 ICE candidate。

### Remote candidate applied

本端读取并应用对端 ICE candidate。

### PeerConnection state

常见变化：

```text
New -> Connecting -> Connected
```

### DataChannel open

DataChannel 已经建立，可以发消息。

## 代码阅读顺序

1. `Options`

   看命令行参数如何决定角色：`offer` 或 `answer`。

2. `makeConfiguration`

   看 STUN server 如何进入 WebRTC 配置。

3. `pc->onLocalDescription`

   看本端 SDP 如何写入文件。

4. `pc->onLocalCandidate`

   看 ICE candidate 如何写入 JSONL。

5. `pc->setRemoteDescription`

   看远端 SDP 如何被应用。

6. `pc->addRemoteCandidate`

   看远端 candidate 如何被应用。

7. `createDataChannel`

   看 offer 方如何主动创建 DataChannel。

8. `pc->onDataChannel`

   看 answer 方如何接收远端创建的 DataChannel。

## 和 FFmpeg 的下一步结合

DataChannel 学会后，再接视频：

```text
FFmpeg encode H.264
  -> RTP packetization
  -> libdatachannel media track
  -> Browser WebRTC playback
```

更完整的后续任务：

1. 用 FFmpeg 生成 H.264 Annex B。
2. 在 C++ 中读 H.264 NALU。
3. 用 libdatachannel 创建 video track。
4. 把 H.264 packetize 成 RTP。
5. 浏览器通过 WebRTC 播放。

这一步比 DataChannel 难很多，因为它涉及 codec、RTP timestamp、payload type、RTCP feedback、keyframe 请求等内容。

所以当前 C++ lab 先把 WebRTC 连接本身吃透，是更稳的路径。
