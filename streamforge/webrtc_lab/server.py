from __future__ import annotations

import argparse
import asyncio
import json
import logging
import math
from pathlib import Path


LOGGER = logging.getLogger("streamforge.webrtc_lab")


def _load_aiortc():
    try:
        from aiohttp import web
        from av import VideoFrame
        from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
    except ModuleNotFoundError as exc:
        missing = exc.name or "aiortc/aiohttp"
        raise RuntimeError(
            "WebRTC Learning Mode 需要额外依赖。\n"
            f"缺少模块：{missing}\n"
            "安装方式：python3 -m pip install '.[webrtc]'\n"
            "或：python3 -m pip install aiortc aiohttp"
        ) from exc
    return web, VideoFrame, RTCPeerConnection, RTCSessionDescription, VideoStreamTrack


def build_index_html() -> str:
    return """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>StreamForge WebRTC Learning Mode</title>
  <style>
    body { margin: 0; font-family: system-ui, sans-serif; background: #f5f7f9; color: #172026; }
    main { max-width: 1080px; margin: 0 auto; padding: 28px 18px; }
    h1 { margin: 0 0 8px; font-size: 30px; }
    p { color: #5e6973; }
    video { width: 100%; aspect-ratio: 16 / 9; background: #111820; border-radius: 8px; }
    button { height: 38px; padding: 0 14px; border: 0; border-radius: 6px; background: #145c9e; color: white; }
    pre { overflow: auto; background: #101820; color: #d9e7f2; padding: 12px; border-radius: 8px; }
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 16px; }
    .panel { background: white; border: 1px solid #dce2e8; border-radius: 8px; padding: 16px; margin-top: 16px; }
    @media (max-width: 760px) { .grid { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
<main>
  <h1>WebRTC Learning Mode</h1>
  <p>这个页面直接使用浏览器 RTCPeerConnection，与 Python aiortc 服务交换 SDP offer/answer。</p>
  <button id="start">Start PeerConnection</button>
  <button id="stop">Stop</button>
  <div class="panel"><video id="video" autoplay playsinline muted controls></video></div>
  <div class="grid">
    <div class="panel"><h2>Offer</h2><pre id="offer"></pre></div>
    <div class="panel"><h2>Answer</h2><pre id="answer"></pre></div>
  </div>
  <div class="panel"><h2>Events</h2><pre id="events"></pre></div>
</main>
<script>
let pc;
const video = document.getElementById("video");
const events = document.getElementById("events");

function log(line) {
  events.textContent += `${new Date().toISOString()} ${line}\\n`;
}

async function start() {
  pc = new RTCPeerConnection({
    iceServers: [{ urls: "stun:stun.l.google.com:19302" }]
  });

  pc.addTransceiver("video", { direction: "recvonly" });

  pc.oniceconnectionstatechange = () => log(`iceConnectionState=${pc.iceConnectionState}`);
  pc.onconnectionstatechange = () => log(`connectionState=${pc.connectionState}`);
  pc.onsignalingstatechange = () => log(`signalingState=${pc.signalingState}`);
  pc.ontrack = (event) => {
    log(`track kind=${event.track.kind}`);
    video.srcObject = event.streams[0];
  };

  const offer = await pc.createOffer();
  await pc.setLocalDescription(offer);
  await waitForIceGatheringComplete(pc);

  document.getElementById("offer").textContent = pc.localDescription.sdp;
  const response = await fetch("/offer", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      sdp: pc.localDescription.sdp,
      type: pc.localDescription.type
    })
  });
  const answer = await response.json();
  document.getElementById("answer").textContent = answer.sdp;
  await pc.setRemoteDescription(answer);
}

function waitForIceGatheringComplete(pc) {
  if (pc.iceGatheringState === "complete") return Promise.resolve();
  return new Promise((resolve) => {
    function checkState() {
      if (pc.iceGatheringState === "complete") {
        pc.removeEventListener("icegatheringstatechange", checkState);
        resolve();
      }
    }
    pc.addEventListener("icegatheringstatechange", checkState);
  });
}

async function stop() {
  if (!pc) return;
  pc.getSenders().forEach((sender) => sender.track && sender.track.stop());
  pc.getReceivers().forEach((receiver) => receiver.track && receiver.track.stop());
  pc.close();
  pc = undefined;
  log("closed");
}

document.getElementById("start").addEventListener("click", start);
document.getElementById("stop").addEventListener("click", stop);
</script>
</body>
</html>
"""


def make_synthetic_track(VideoFrame, VideoStreamTrack):
    class SyntheticVideoTrack(VideoStreamTrack):
        """A tiny generated video source so WebRTC can run without a camera.

        The goal is learning signaling and media flow. A later exercise can
        replace this generated track with frames decoded from FFmpeg/PyAV.
        """

        def __init__(self) -> None:
            super().__init__()
            self.counter = 0

        async def recv(self):
            pts, time_base = await self.next_timestamp()
            width, height = 640, 360
            frame = VideoFrame(width=width, height=height, format="yuv420p")
            t = self.counter
            self.counter += 1

            # Fill YUV420P planes manually. This keeps the learning mode free
            # of numpy while still producing visible moving video.
            y_plane = bytearray()
            y_stride = frame.planes[0].line_size
            for y in range(height):
                row = bytearray()
                for x in range(width):
                    row.append((x + y + t * 4) % 256)
                row.extend(b"\x00" * (y_stride - width))
                y_plane.extend(row)

            chroma_w = width // 2
            chroma_h = height // 2
            chroma_stride = frame.planes[1].line_size
            u_value = int((math.sin(t / 20.0) + 1) * 60 + 60) % 256
            v_value = int((math.cos(t / 25.0) + 1) * 60 + 90) % 256
            u_row = bytes([u_value]) * chroma_w + b"\x00" * (chroma_stride - chroma_w)
            v_row = bytes([v_value]) * chroma_w + b"\x00" * (chroma_stride - chroma_w)
            u_plane = u_row * chroma_h
            v_plane = v_row * chroma_h

            frame.planes[0].update(bytes(y_plane))
            frame.planes[1].update(u_plane)
            frame.planes[2].update(v_plane)

            frame.pts = pts
            frame.time_base = time_base
            return frame

    return SyntheticVideoTrack


async def run_webrtc_lab(host: str = "0.0.0.0", port: int = 8090) -> None:
    web, VideoFrame, RTCPeerConnection, RTCSessionDescription, VideoStreamTrack = _load_aiortc()
    SyntheticVideoTrack = make_synthetic_track(VideoFrame, VideoStreamTrack)
    pcs: set[RTCPeerConnection] = set()

    async def index(_request):
        return web.Response(text=build_index_html(), content_type="text/html")

    async def offer(request):
        params = await request.json()
        offer_desc = RTCSessionDescription(sdp=params["sdp"], type=params["type"])
        pc = RTCPeerConnection()
        pcs.add(pc)

        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
            LOGGER.info("connectionState=%s", pc.connectionState)
            if pc.connectionState in {"failed", "closed"}:
                await pc.close()
                pcs.discard(pc)

        await pc.setRemoteDescription(offer_desc)
        pc.addTrack(SyntheticVideoTrack())
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)

        return web.Response(
            content_type="application/json",
            text=json.dumps({"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}),
        )

    async def on_shutdown(_app):
        await asyncio.gather(*(pc.close() for pc in pcs), return_exceptions=True)
        pcs.clear()

    app = web.Application()
    app.router.add_get("/", index)
    app.router.add_post("/offer", offer)
    app.on_shutdown.append(on_shutdown)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    print(f"WebRTC Learning Mode: http://127.0.0.1:{port}")
    print("Open the page, click Start, then inspect Offer/Answer and connection events.")
    try:
        while True:
            await asyncio.sleep(3600)
    finally:
        await runner.cleanup()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="StreamForge WebRTC Learning Mode")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8090)
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_webrtc_lab(args.host, args.port))


if __name__ == "__main__":
    main()
