from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class Channel:
    name: str
    input: str
    rtsp_transport: str = "tcp"
    hls: bool = True
    publish_rtsp: bool = False
    push_rtmp: str | None = None
    runtime_dir: Path = Path("runtime")

    @property
    def hls_dir(self) -> Path:
        return self.runtime_dir / "hls" / self.name

    @property
    def hls_playlist(self) -> Path:
        return self.hls_dir / "index.m3u8"

    @property
    def mediamtx_rtsp_url(self) -> str:
        return f"rtsp://127.0.0.1:8554/{self.name}"

    @property
    def mediamtx_rtmp_url(self) -> str:
        return f"rtmp://127.0.0.1:1935/{self.name}"

    @property
    def mediamtx_hls_url(self) -> str:
        return f"http://127.0.0.1:8888/{self.name}/index.m3u8"

    @property
    def mediamtx_webrtc_url(self) -> str:
        return f"http://127.0.0.1:8889/{self.name}"


def load_channels(path: str | Path) -> list[Channel]:
    config_path = Path(path)
    data = json.loads(config_path.read_text(encoding="utf-8"))
    channels: list[Channel] = []
    for item in data.get("channels", []):
        channels.append(
            Channel(
                name=item["name"],
                input=item["input"],
                rtsp_transport=item.get("rtsp_transport", "tcp"),
                hls=bool(item.get("hls", True)),
                publish_rtsp=bool(item.get("publish_rtsp", False)),
                push_rtmp=item.get("push_rtmp"),
                runtime_dir=Path(item.get("runtime_dir", "runtime")),
            )
        )
    return channels
