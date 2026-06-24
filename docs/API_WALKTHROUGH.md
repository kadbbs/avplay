# FFmpeg 五库走读

这个分支是第一版学习项目，重点是把五个常见 FFmpeg 库连成可运行的小闭环。

数据流：

```text
AVFormatContext -> AVPacket -> AVCodecContext -> AVFrame
```

视频缩略图路径：

```text
decode video frame -> sws_scale -> RGB24 PPM
```

音频导出路径：

```text
decode audio frame -> swr_convert -> stereo 48kHz s16le
```
