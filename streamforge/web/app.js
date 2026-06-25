function urls(channel) {
  return {
    localHls: `/hls/${channel}/index.m3u8`,
    mediamtxHls: `http://127.0.0.1:8888/${channel}/index.m3u8`,
    webrtc: `http://127.0.0.1:8889/${channel}`,
    rtsp: `rtsp://127.0.0.1:8554/${channel}`,
    rtmp: `rtmp://127.0.0.1:1935/${channel}`,
  };
}

let hls;

function loadChannel() {
  const channel = document.getElementById("channel").value.trim() || "demo";
  const u = urls(channel);
  const video = document.getElementById("video");

  document.getElementById("localHls").href = u.localHls;
  document.getElementById("mediamtxHls").href = u.mediamtxHls;
  document.getElementById("webrtc").href = u.webrtc;
  document.getElementById("rtsp").textContent = u.rtsp;
  document.getElementById("rtmp").textContent = u.rtmp;

  if (hls) {
    hls.destroy();
    hls = undefined;
  }

  if (window.Hls && Hls.isSupported()) {
    hls = new Hls({ lowLatencyMode: true });
    hls.loadSource(u.localHls);
    hls.attachMedia(video);
  } else {
    video.src = u.localHls;
  }
}

document.getElementById("apply").addEventListener("click", loadChannel);
loadChannel();
