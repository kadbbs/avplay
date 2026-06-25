# C++ WebRTC DataChannel Lab

这个子项目是 StreamForge 的 **C++ WebRTC 学习模式**。

它不走 MediaMTX，也不走 Python `aiortc`。它使用 C++ 库 `libdatachannel` 直接创建：

- `rtc::PeerConnection`
- SDP offer / answer
- ICE candidates
- `rtc::DataChannel`

第一阶段先学 DataChannel，因为这是 WebRTC C++ 最小闭环。等你理解信令、ICE、PeerConnection 状态后，再接视频轨道会顺很多。

## 为什么不用 Google 原生 WebRTC

Google 原生 WebRTC 很完整，但构建巨大，初学容易把时间花在 depot_tools、gn、ninja、依赖和符号冲突上。

本项目用 `libdatachannel` 的原因：

- C++17 API 简洁
- CMake 友好
- 能和浏览器互通
- 适合学习 SDP、ICE、DataChannel、Media Track

## 构建

```bash
cmake -S cpp/webrtc_datachannel_lab -B build/webrtc-cpp
cmake --build build/webrtc-cpp
```

首次构建会通过 CMake `FetchContent` 下载：

- `libdatachannel`

`nlohmann/json` 由 `libdatachannel` 的依赖树提供，本项目直接复用它。

## 运行两个 C++ peer

开第一个终端：

```bash
./build/webrtc-cpp/webrtc_manual_peer --role offer --signal-dir runtime/webrtc-signal
```

开第二个终端：

```bash
./build/webrtc-cpp/webrtc_manual_peer --role answer --signal-dir runtime/webrtc-signal
```

两个进程会用 `runtime/webrtc-signal` 里的 JSON 文件交换：

```text
offer_description.json
answer_description.json
offer_candidates.jsonl
answer_candidates.jsonl
```

连接成功后，在任意一边输入文字，对端会通过 WebRTC DataChannel 收到消息。

## 你要观察什么

1. `Local description ready`

   本端生成 SDP。

2. `Remote description applied`

   本端接收并应用对端 SDP。

3. `Local candidate`

   本端发现 ICE candidate。

4. `Remote candidate applied`

   本端应用对端 candidate。

5. `PeerConnection state`

   看连接从 `Connecting` 到 `Connected`。

6. `DataChannel open`

   DataChannel 已经可用，可以收发消息。

## 和现有项目的关系

```text
MediaMTX WebRTC path
  FFmpeg -> RTSP -> MediaMTX -> Browser
  工程实用，WebRTC 细节被 MediaMTX 封装

Python aiortc Learning Mode
  Browser -> Python -> generated video track
  适合看浏览器 RTCPeerConnection 和 SDP

C++ libdatachannel Lab
  C++ PeerConnection <-> C++ PeerConnection
  适合学习 C++ WebRTC API、ICE、DataChannel
```

下一步可以从这个 lab 往两个方向扩展：

- C++ peer 对接浏览器页面。
- FFmpeg 输出 RTP/H.264，C++ peer 用 libdatachannel 发 video track。
