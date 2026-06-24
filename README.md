# mediaforge

`mediaforge` 是第二版实用项目：把输入媒体规范化成网页友好的 MP4，并生成封面图和 JSON 报告。

```text
input media
  -> libavformat 读取容器和 packet
  -> libavcodec 解码/编码
  -> libswscale 缩放视频和转像素格式
  -> libswresample 重采样音频
  -> output.mp4 + cover.ppm + report.json
```

## 构建

```bash
cmake -S . -B build
cmake --build build
```

## 使用

```bash
./build/mediaforge normalize demo.mp4 normalized.mp4 \
  --width 640 --cover cover.ppm --report report.json
```

输出规格：

- 视频：H.264 / yuv420p
- 音频：AAC / stereo / 48 kHz
- 封面：RGB PPM
- 报告：JSON
