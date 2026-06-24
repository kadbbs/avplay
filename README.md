# AutoSub Studio

AutoSub Studio 是一个基于 FFmpeg / FFprobe 和 Whisper 的本地视频字幕生产工作流工具。

第一版聚焦 CLI 闭环：

```text
输入视频
  -> ffprobe 检查媒体信息
  -> FFmpeg 提取 16 kHz mono wav
  -> Whisper / faster-whisper 语音识别
  -> 字幕清洗
  -> 导出 SRT / ASS / VTT
  -> FFmpeg 烧录硬字幕或封装软字幕
  -> 输出 report.json
```

## 功能

- 查看视频信息：`autosub info input.mp4`
- 生成字幕：`autosub transcribe input.mp4 --lang zh --model small`
- 烧录已有字幕：`autosub burn input.mp4 --subtitle input.srt`
- 完整流程：`autosub all input.mp4 --lang zh --model small --style classic`
- 批量处理：`autosub batch ./videos --recursive`
- 导出 SRT / VTT / ASS
- 支持 ASS 样式模板：`classic`、`short_video`、`course`
- 输出每个任务的 `report.json`

## 安装

需要 Python 3.10+。

系统依赖：

```bash
sudo apt-get update
sudo apt-get install -y ffmpeg
```

Python 依赖：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Whisper 后端二选一：

```bash
pip install faster-whisper
```

或：

```bash
pip install openai-whisper
```

## 快速开始

开发模式直接运行：

```bash
python3 main.py info demo.mp4
python3 main.py transcribe demo.mp4 --lang zh --model small
python3 main.py burn demo.mp4 --subtitle output/demo/demo.cleaned.srt
python3 main.py all demo.mp4 --lang zh --model small --style classic
```

安装成命令后：

```bash
autosub all ./examples/sample.mp4 --lang zh --model small --style classic
```

输出目录：

```text
output/sample/
├── audio.wav
├── sample.raw.srt
├── sample.cleaned.srt
├── sample.ass
├── sample_subtitled.mp4
└── report.json
```

## 常见问题

**提示找不到 ffmpeg / ffprobe**

安装 FFmpeg，并确认 `ffmpeg -version`、`ffprobe -version` 能运行。

**提示没有 Whisper 后端**

安装 `faster-whisper` 或 `openai-whisper`。推荐 `faster-whisper`，CPU 环境也比较友好。

**字幕路径含中文或空格**

项目使用 `subprocess` 参数列表执行命令，并对 FFmpeg subtitles filter 做了路径转义。

## 项目文档

完整需求见 [ass.md](/home/bs/code/ffmpeg/ass.md)。
