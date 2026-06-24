# ffmpeg-five-lab

一个用于学习 FFmpeg 五个常用 C API 模块的小项目。

它提供三个命令：

```bash
./build/ff5lab info input.mp4
./build/ff5lab thumbnail input.mp4 frame.ppm 480
./build/ff5lab audio-pcm input.mp4 audio.s16le 3
```

覆盖的模块：

- `libavformat`：打开容器、读取流信息、解封装 packet。
- `libavcodec`：打开 decoder，把 packet 解成 frame。
- `libavutil`：错误处理、内存、图片 buffer、声道布局。
- `libswscale`：视频缩放和像素格式转换。
- `libswresample`：音频重采样和采样格式转换。

## 构建

```bash
sudo apt-get install -y build-essential cmake pkg-config \
  libavformat-dev libavcodec-dev libavutil-dev libswscale-dev libswresample-dev

cmake -S . -B build
cmake --build build
```

## 生成测试素材

```bash
ffmpeg -y \
  -f lavfi -i testsrc2=size=1280x720:rate=30 \
  -f lavfi -i sine=frequency=880:sample_rate=44100 \
  -t 5 -c:v libx264 -pix_fmt yuv420p -c:a aac demo.mp4
```
