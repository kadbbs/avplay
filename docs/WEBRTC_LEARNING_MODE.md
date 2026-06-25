# WebRTC Learning Mode

StreamForge 现在有两条 WebRTC 路线：

```text
实用路线：FFmpeg -> MediaMTX -> WebRTC
学习路线：Browser RTCPeerConnection -> Python aiortc -> generated video track
```

MediaMTX 路线适合做工程。Learning Mode 适合学习 WebRTC 本身。

## 1. 你能学到什么

Learning Mode 会让你直接看到：

- 浏览器创建 `RTCPeerConnection`
- 浏览器创建 SDP offer
- Python 接收 offer
- Python 创建 SDP answer
- 浏览器设置 remote answer
- ICE / signaling / connection 状态变化
- Python 发送一条 video track 给浏览器

它不依赖摄像头，也不依赖 FFmpeg 输入。服务端会生成一条动态测试画面，这样你可以先专注 WebRTC 协商流程。

## 2. 安装依赖

WebRTC Learning Mode 是可选依赖，不影响主项目。

```bash
python3 -m pip install '.[webrtc]'
```

或者：

```bash
python3 -m pip install aiortc aiohttp
```

## 3. 启动

```bash
python3 -m streamforge.cli webrtc-lab --port 8090
```

打开：

```text
http://127.0.0.1:8090
```

点击 `Start PeerConnection`。页面会显示 offer SDP、answer SDP 和连接状态。

## 4. 核心数据流

```text
Browser
  create RTCPeerConnection
  addTransceiver("video", recvonly)
  createOffer()
  setLocalDescription()
  POST /offer
        |
        v
Python aiohttp server
  RTCPeerConnection()
  setRemoteDescription(offer)
  addTrack(SyntheticVideoTrack)
  createAnswer()
  setLocalDescription(answer)
        |
        v
Browser
  setRemoteDescription(answer)
  ontrack -> video.srcObject
```

代码入口：

```text
streamforge/webrtc_lab/server.py
```

## 5. SDP 看什么

SDP 是 WebRTC 协商的文本描述。你可以在页面里找这些内容：

```text
m=video
a=ice-ufrag
a=ice-pwd
a=fingerprint
a=setup
a=rtpmap
a=rtcp-mux
```

| 字段 | 作用 |
| --- | --- |
| `m=video` | 声明一条视频媒体 |
| `a=ice-ufrag` / `a=ice-pwd` | ICE 连通性检查凭据 |
| `a=fingerprint` | DTLS 证书指纹 |
| `a=setup` | DTLS 主被动角色 |
| `a=rtpmap` | RTP payload type 到 codec 的映射 |
| `a=rtcp-mux` | RTP 和 RTCP 复用同一个端口 |

## 6. ICE 看什么

浏览器页面会打印：

```text
iceConnectionState=checking
iceConnectionState=connected
```

常见状态：

| 状态 | 说明 |
| --- | --- |
| `new` | 还没开始检查 |
| `checking` | 正在做连通性检查 |
| `connected` | 找到可用网络路径 |
| `completed` | 检查完成 |
| `failed` | 找不到可用路径 |
| `disconnected` | 临时断开 |
| `closed` | 连接关闭 |

本地学习时通常很快进入 `connected`。

## 7. Track 是什么

WebRTC 不是只传“一个视频文件”，而是传媒体轨道：

```text
MediaStream
  -> video MediaStreamTrack
  -> audio MediaStreamTrack
```

本项目的 `SyntheticVideoTrack` 继承自 aiortc 的 `VideoStreamTrack`：

```python
class SyntheticVideoTrack(VideoStreamTrack):
    async def recv(self):
        ...
        return frame
```

`recv()` 每次返回一帧 PyAV `VideoFrame`。aiortc 会把它编码、打包进 RTP，再通过 WebRTC 发给浏览器。

## 8. 它和 MediaMTX 路线有什么区别

### MediaMTX 路线

```text
FFmpeg -> RTSP -> MediaMTX -> WebRTC
```

优点：

- 工程实用
- 支持真实 RTSP/RTMP 输入
- 少写复杂协议代码

缺点：

- 你看不到 SDP/ICE/PeerConnection 细节

### Learning Mode

```text
Browser -> Python signaling -> aiortc peer -> Browser video
```

优点：

- 能看到 offer/answer
- 能看到 ICE 状态
- 能理解 track 如何进入浏览器

缺点：

- 不是生产网关
- 默认没有接真实摄像头或 RTSP 输入

## 9. 下一步练习

1. 在页面里打印 `pc.getStats()`。
2. 给 Python 服务加一条 audio track。
3. 把 generated video track 换成摄像头或视频文件解码帧。
4. 增加 trickle ICE，逐个发送 candidate。
5. 加入 TURN 服务器配置，测试跨网络连接。

## 10. 和 FFmpeg 结合的扩展方向

当前 Learning Mode 先不用 FFmpeg，避免一次学太多。下一步可以做：

```text
FFmpeg/PyAV decode input
  -> aiortc VideoStreamTrack.recv()
  -> Browser WebRTC
```

或者：

```text
FFmpeg outputs RTP
  -> Python receives RTP
  -> aiortc forwards track
  -> Browser WebRTC
```

第一条更适合学习代码，第二条更接近媒体网关。
