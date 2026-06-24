# AutoSub Studio 项目开发文档

## 1. 项目名称

**AutoSub Studio**

基于 FFmpeg 和 Whisper 的本地视频字幕生成、编辑、烧录与批量处理工具。

---

## 2. 项目定位

本项目不是简单调用 Whisper 和 FFmpeg 的脚本，而是一个完整的 **视频字幕生产工作流工具**。

它要解决的问题是：

* 视频自动生成字幕
* 字幕文本清洗和格式优化
* 字幕时间轴修正
* 字幕样式配置
* 硬字幕烧录
* 软字幕封装
* 多视频批量处理
* 失败重试和日志追踪
* 输出处理报告

最终目标是做成一个可以真实使用、可以写进简历、可以展示 Demo 的本地工具。

---

## 3. 项目核心流程

```text
输入视频
  ↓
检查视频信息
  ↓
提取音频
  ↓
调用 Whisper 识别语音
  ↓
生成字幕片段
  ↓
字幕后处理
  ↓
导出 SRT / ASS / VTT
  ↓
烧录硬字幕 或 封装软字幕
  ↓
生成最终视频
  ↓
输出任务报告
```

---

## 4. 技术栈

### 4.1 基础技术

* Python 3.10+
* FFmpeg
* FFprobe
* OpenAI Whisper / faster-whisper
* argparse / typer
* pathlib
* subprocess
* dataclasses
* json
* logging

### 4.2 可选技术

第一版先做 CLI，后续可以扩展 GUI。

CLI 版：

* Typer
* Rich
* tqdm

GUI 版：

* PySide6
* Qt Designer
* QThread
* SQLite

Web 版：

* FastAPI
* React
* Celery
* Redis

---

## 5. 项目目录结构

```text
autosub-studio/
├── README.md
├── PROJECT_PLAN.md
├── requirements.txt
├── pyproject.toml
├── main.py
├── autosub/
│   ├── __init__.py
│   ├── cli.py
│   ├── config.py
│   ├── constants.py
│   │
│   ├── core/
│   │   ├── ffmpeg_runner.py
│   │   ├── ffprobe.py
│   │   ├── audio_extractor.py
│   │   ├── transcriber.py
│   │   ├── subtitle_writer.py
│   │   ├── subtitle_cleaner.py
│   │   ├── subtitle_burner.py
│   │   ├── subtitle_muxer.py
│   │   └── progress_parser.py
│   │
│   ├── models/
│   │   ├── media_info.py
│   │   ├── subtitle_segment.py
│   │   ├── subtitle_style.py
│   │   └── task.py
│   │
│   ├── services/
│   │   ├── pipeline.py
│   │   ├── task_queue.py
│   │   ├── report_service.py
│   │   └── file_service.py
│   │
│   ├── presets/
│   │   ├── classic.json
│   │   ├── short_video.json
│   │   ├── course.json
│   │   └── bilingual.json
│   │
│   └── utils/
│       ├── time_format.py
│       ├── path_utils.py
│       ├── logger.py
│       └── validators.py
│
├── tests/
│   ├── test_ffprobe.py
│   ├── test_srt_writer.py
│   ├── test_subtitle_cleaner.py
│   ├── test_time_format.py
│   └── test_pipeline.py
│
├── examples/
│   ├── sample.mp4
│   ├── sample.srt
│   └── sample.ass
│
├── output/
└── logs/
```

---

## 6. 第一阶段目标：最小可行版本

### 6.1 第一阶段必须完成的功能

第一阶段只做最小闭环：

```text
输入一个视频
→ 提取音频
→ Whisper 识别
→ 生成 SRT
→ FFmpeg 烧录字幕
→ 输出带字幕的视频
```

### 6.2 命令行目标

最终可以执行：

```bash
python main.py transcribe input.mp4
```

生成：

```text
output/input.srt
```

执行：

```bash
python main.py burn input.mp4
```

生成：

```text
output/input_subtitled.mp4
```

执行：

```bash
python main.py all input.mp4
```

生成：

```text
output/input.srt
output/input_subtitled.mp4
output/input_report.json
```

---

## 7. CLI 命令设计

### 7.1 查看视频信息

```bash
autosub info input.mp4
```

输出示例：

```text
文件名: input.mp4
时长: 00:12:35
分辨率: 1920x1080
视频编码: h264
音频编码: aac
音轨数量: 1
字幕轨数量: 0
```

---

### 7.2 只生成字幕

```bash
autosub transcribe input.mp4 --lang zh --model small
```

参数说明：

| 参数             | 说明         | 默认值    |
| -------------- | ---------- | ------ |
| `--lang`       | 识别语言       | auto   |
| `--model`      | Whisper 模型 | small  |
| `--format`     | 字幕格式       | srt    |
| `--output-dir` | 输出目录       | output |

---

### 7.3 烧录已有字幕

```bash
autosub burn input.mp4 --subtitle input.srt
```

参数说明：

| 参数           | 说明     | 默认值     |
| ------------ | ------ | ------- |
| `--subtitle` | 字幕文件路径 | 必填      |
| `--style`    | 字幕样式模板 | classic |
| `--crf`      | 视频质量参数 | 20      |
| `--preset`   | 编码速度   | medium  |
| `--output`   | 输出视频路径 | 自动生成    |

---

### 7.4 生成字幕并烧录

```bash
autosub all input.mp4 --lang zh --model small --style classic
```

完整流程：

```text
检查视频
提取音频
识别字幕
清洗字幕
导出 SRT
生成 ASS
烧录字幕
输出报告
```

---

### 7.5 批量处理

```bash
autosub batch ./videos --lang zh --model small --style short_video
```

功能要求：

* 扫描目录下所有视频文件
* 支持 mp4 / mov / mkv / webm
* 每个视频单独生成字幕
* 每个视频单独生成输出文件
* 失败的视频写入报告
* 已完成的视频可以跳过

---

## 8. 核心数据模型

### 8.1 SubtitleSegment

```python
from dataclasses import dataclass

@dataclass
class SubtitleSegment:
    index: int
    start: float
    end: float
    text: str
```

字段说明：

| 字段      | 类型    | 说明       |
| ------- | ----- | -------- |
| `index` | int   | 字幕序号     |
| `start` | float | 开始时间，单位秒 |
| `end`   | float | 结束时间，单位秒 |
| `text`  | str   | 字幕文本     |

---

### 8.2 MediaInfo

```python
from dataclasses import dataclass

@dataclass
class MediaInfo:
    path: str
    duration: float
    width: int
    height: int
    video_codec: str
    audio_codec: str | None
    has_audio: bool
    has_subtitle: bool
```

字段说明：

| 字段             | 类型          | 说明     |
| -------------- | ----------- | ------ |
| `path`         | str         | 视频路径   |
| `duration`     | float       | 视频时长   |
| `width`        | int         | 视频宽度   |
| `height`       | int         | 视频高度   |
| `video_codec`  | str         | 视频编码   |
| `audio_codec`  | str or None | 音频编码   |
| `has_audio`    | bool        | 是否有音频  |
| `has_subtitle` | bool        | 是否已有字幕 |

---

### 8.3 SubtitleStyle

```python
from dataclasses import dataclass

@dataclass
class SubtitleStyle:
    name: str
    font_name: str
    font_size: int
    primary_color: str
    outline_color: str
    outline: int
    shadow: int
    alignment: int
    margin_v: int
```

字段说明：

| 字段              | 说明    |
| --------------- | ----- |
| `name`          | 样式名称  |
| `font_name`     | 字体名称  |
| `font_size`     | 字号    |
| `primary_color` | 主文字颜色 |
| `outline_color` | 描边颜色  |
| `outline`       | 描边粗细  |
| `shadow`        | 阴影大小  |
| `alignment`     | 字幕位置  |
| `margin_v`      | 底部距离  |

---

### 8.4 SubtitleTask

```python
from dataclasses import dataclass

@dataclass
class SubtitleTask:
    input_path: str
    output_dir: str
    language: str
    model: str
    subtitle_format: str
    style_name: str
    burn_subtitle: bool
    soft_subtitle: bool
    status: str
```

任务状态：

```text
PENDING
PROBING
EXTRACTING_AUDIO
TRANSCRIBING
POST_PROCESSING
EXPORTING_SUBTITLE
RENDERING
MUXING
DONE
FAILED
```

---

## 9. FFmpeg 模块设计

### 9.1 ffmpeg_runner.py

职责：

* 统一执行 FFmpeg 命令
* 捕获 stdout
* 捕获 stderr
* 返回执行结果
* 处理错误信息
* 支持进度回调

函数设计：

```python
def run_ffmpeg(command: list[str]) -> subprocess.CompletedProcess:
    pass
```

```python
def run_ffmpeg_with_progress(
    command: list[str],
    duration: float,
    on_progress: callable
) -> int:
    pass
```

---

### 9.2 ffprobe.py

职责：

* 获取视频基础信息
* 判断是否有音轨
* 判断是否有字幕轨
* 输出 MediaInfo

命令：

```bash
ffprobe -v error -print_format json -show_format -show_streams input.mp4
```

函数设计：

```python
def probe_media(input_path: str) -> MediaInfo:
    pass
```

需要解析的信息：

```text
format.duration
streams[].codec_type
streams[].codec_name
streams[].width
streams[].height
```

---

### 9.3 audio_extractor.py

职责：

* 从视频中提取适合语音识别的音频
* 输出 wav 文件

命令：

```bash
ffmpeg -y -i input.mp4 -vn -ac 1 -ar 16000 -c:a pcm_s16le output.wav
```

函数设计：

```python
def extract_audio(input_path: str, output_audio_path: str) -> str:
    pass
```

验收标准：

* 输入 mp4 后可以生成 wav
* 没有音轨时抛出清晰错误
* 输出文件存在且大小大于 0
* 支持中文路径和空格路径

---

### 9.4 subtitle_burner.py

职责：

* 使用 FFmpeg 将字幕烧录进视频
* 支持 SRT
* 支持 ASS
* 支持样式模板

基础命令：

```bash
ffmpeg -y -i input.mp4 -vf "subtitles=input.srt" -c:v libx264 -crf 20 -preset medium -c:a copy output.mp4
```

函数设计：

```python
def burn_subtitle(
    video_path: str,
    subtitle_path: str,
    output_path: str,
    crf: int = 20,
    preset: str = "medium"
) -> str:
    pass
```

验收标准：

* 输出视频可以正常播放
* 字幕已经压进画面
* 音频没有丢失
* 输出文件时长接近原视频
* FFmpeg 报错时能够显示明确错误

---

### 9.5 subtitle_muxer.py

职责：

* 将字幕作为软字幕封装进视频
* MP4 使用 mov_text
* MKV 使用 srt 或 ass

MP4 命令：

```bash
ffmpeg -y -i input.mp4 -i subtitle.srt -c:v copy -c:a copy -c:s mov_text output.mp4
```

MKV 命令：

```bash
ffmpeg -y -i input.mp4 -i subtitle.srt -c copy -c:s srt output.mkv
```

函数设计：

```python
def mux_soft_subtitle(
    video_path: str,
    subtitle_path: str,
    output_path: str
) -> str:
    pass
```

---

## 10. Whisper 模块设计

### 10.1 transcriber.py

职责：

* 调用 Whisper
* 输入音频文件
* 输出字幕片段列表
* 支持指定语言
* 支持指定模型

函数设计：

```python
def transcribe_audio(
    audio_path: str,
    model_name: str = "small",
    language: str | None = None
) -> list[SubtitleSegment]:
    pass
```

输出示例：

```python
[
    SubtitleSegment(
        index=1,
        start=1.2,
        end=3.8,
        text="大家好，欢迎来到这个视频。"
    ),
    SubtitleSegment(
        index=2,
        start=4.1,
        end=6.5,
        text="今天我们来讲 FFmpeg。"
    )
]
```

验收标准：

* 可以识别中文视频
* 可以识别英文视频
* 输出结果包含 start、end、text
* 识别失败时有明确错误
* 模型不存在时有提示
* GPU 不可用时可以回退 CPU

---

## 11. 字幕导出模块

### 11.1 subtitle_writer.py

需要支持：

* SRT
* VTT
* ASS

第一版必须支持 SRT。

---

### 11.2 SRT 格式

SRT 示例：

```text
1
00:00:01,200 --> 00:00:03,800
大家好，欢迎来到这个视频。

2
00:00:04,100 --> 00:00:06,500
今天我们来讲 FFmpeg。
```

函数设计：

```python
def write_srt(segments: list[SubtitleSegment], output_path: str) -> str:
    pass
```

时间格式函数：

```python
def format_srt_time(seconds: float) -> str:
    pass
```

验收标准：

* 时间格式必须是 `00:00:01,200`
* 字幕序号从 1 开始
* 每条字幕之间有一个空行
* 输出 UTF-8 编码
* 中文不会乱码

---

### 11.3 VTT 格式

VTT 示例：

```text
WEBVTT

00:00:01.200 --> 00:00:03.800
大家好，欢迎来到这个视频。

00:00:04.100 --> 00:00:06.500
今天我们来讲 FFmpeg。
```

函数设计：

```python
def write_vtt(segments: list[SubtitleSegment], output_path: str) -> str:
    pass
```

---

### 11.4 ASS 格式

ASS 适合做样式。

ASS 示例：

```text
[Script Info]
Title: AutoSub Studio
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,36,&H00FFFFFF,&H00000000,1,2,1,2,10,10,40,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:01.20,0:00:03.80,Default,,0,0,0,,大家好，欢迎来到这个视频。
```

函数设计：

```python
def write_ass(
    segments: list[SubtitleSegment],
    output_path: str,
    style: SubtitleStyle
) -> str:
    pass
```

---

## 12. 字幕后处理模块

### 12.1 subtitle_cleaner.py

职责：

* 清理字幕文本
* 自动断行
* 合并过短字幕
* 拆分过长字幕
* 修正时间轴
* 过滤无意义语气词

---

### 12.2 自动断行

规则：

```text
中文每行最多 18 个字
英文每行最多 42 个字符
每条字幕最多 2 行
优先在标点处分割
其次在空格处分割
最后按长度硬切
```

函数设计：

```python
def wrap_subtitle_text(
    text: str,
    max_chars_per_line: int = 18,
    max_lines: int = 2
) -> str:
    pass
```

示例：

```text
原始：
今天我们来讲一下如何使用 FFmpeg 和 Whisper 做一个自动字幕生成工具

处理后：
今天我们来讲一下如何使用
FFmpeg 和 Whisper 做一个自动字幕生成工具
```

---

### 12.3 时间轴偏移

功能：

```bash
autosub all input.mp4 --offset 0.3
```

含义：

```text
所有字幕整体延后 0.3 秒
```

函数设计：

```python
def apply_offset(
    segments: list[SubtitleSegment],
    offset: float
) -> list[SubtitleSegment]:
    pass
```

要求：

* start 不能小于 0
* end 必须大于 start
* 偏移后仍然保持顺序

---

### 12.4 最短显示时间

问题：

```text
有些字幕只有 0.2 秒，用户看不清
```

规则：

```text
每条字幕最少显示 1.0 秒
如果太短，自动延长 end
不能和下一条字幕严重重叠
```

函数设计：

```python
def ensure_min_duration(
    segments: list[SubtitleSegment],
    min_duration: float = 1.0
) -> list[SubtitleSegment]:
    pass
```

---

### 12.5 语气词过滤

可配置过滤词：

```text
嗯
啊
呃
额
就是
然后然后
```

函数设计：

```python
def remove_filler_words(text: str, filler_words: list[str]) -> str:
    pass
```

注意：

* 不要过度清理
* 默认关闭
* 用户显式开启才过滤

---

### 12.6 标点修正

处理规则：

```text
中文句子使用中文标点
连续多个标点合并
去掉字幕首尾空格
英文和数字之间保留空格
FFmpeg、Whisper 等技术词保留英文
```

函数设计：

```python
def normalize_punctuation(text: str, language: str) -> str:
    pass
```

---

## 13. 字幕样式模板

### 13.1 classic.json

```json
{
  "name": "classic",
  "font_name": "Arial",
  "font_size": 36,
  "primary_color": "&H00FFFFFF",
  "outline_color": "&H00000000",
  "outline": 2,
  "shadow": 1,
  "alignment": 2,
  "margin_v": 40
}
```

说明：

```text
白字黑边，适合大多数视频
```

---

### 13.2 short_video.json

```json
{
  "name": "short_video",
  "font_name": "Arial",
  "font_size": 48,
  "primary_color": "&H0000FFFF",
  "outline_color": "&H00000000",
  "outline": 3,
  "shadow": 1,
  "alignment": 2,
  "margin_v": 80
}
```

说明：

```text
大号黄字黑边，适合短视频
```

---

### 13.3 course.json

```json
{
  "name": "course",
  "font_name": "Arial",
  "font_size": 30,
  "primary_color": "&H00FFFFFF",
  "outline_color": "&H00000000",
  "outline": 2,
  "shadow": 0,
  "alignment": 2,
  "margin_v": 30
}
```

说明：

```text
字号较小，适合课程和教程视频
```

---

## 14. 任务流水线设计

### 14.1 pipeline.py

职责：

* 串联完整处理流程
* 统一管理任务状态
* 统一处理异常
* 统一写入报告

核心函数：

```python
def run_pipeline(task: SubtitleTask) -> dict:
    pass
```

处理流程：

```text
1. 校验输入文件
2. 创建工作目录
3. 使用 ffprobe 获取媒体信息
4. 检查是否存在音轨
5. 提取 wav 音频
6. 调用 Whisper 识别
7. 字幕清洗
8. 导出 SRT
9. 如果需要，导出 ASS
10. 如果需要，烧录硬字幕
11. 如果需要，封装软字幕
12. 删除临时文件
13. 生成 report.json
```

---

### 14.2 工作目录设计

假设输入：

```text
videos/lesson01.mp4
```

输出目录：

```text
output/lesson01/
├── audio.wav
├── lesson01.raw.srt
├── lesson01.cleaned.srt
├── lesson01.ass
├── lesson01_subtitled.mp4
└── report.json
```

---

## 15. 进度显示设计

### 15.1 阶段进度

整体阶段：

```text
PROBING              5%
EXTRACTING_AUDIO     15%
TRANSCRIBING         55%
POST_PROCESSING      65%
EXPORTING_SUBTITLE   75%
RENDERING            95%
DONE                 100%
```

---

### 15.2 FFmpeg 进度解析

FFmpeg 输出中会出现：

```text
time=00:01:23.45
```

可以根据视频总时长计算渲染进度：

```text
当前进度 = 当前处理时间 / 视频总时长
```

函数设计：

```python
def parse_ffmpeg_time(line: str) -> float | None:
    pass
```

---

## 16. 错误处理要求

### 16.1 常见错误

需要处理：

```text
FFmpeg 未安装
ffprobe 未安装
输入文件不存在
输入文件不是视频
视频没有音轨
Whisper 模型下载失败
识别过程中断
字幕文件不存在
字幕路径包含特殊字符
字体不存在
输出目录没有权限
磁盘空间不足
FFmpeg 烧录失败
```

---

### 16.2 错误信息要求

错误信息不要只显示：

```text
error
```

应该显示：

```text
处理失败：当前视频没有检测到音轨，无法生成字幕。
文件：input.mp4
建议：请确认视频是否包含声音。
```

---

## 17. 日志设计

### 17.1 日志文件

每次处理生成：

```text
logs/autosub_2026-06-25.log
```

日志内容：

```text
[INFO] Start task: input.mp4
[INFO] Probe media success: duration=735.2
[INFO] Extract audio success: output/audio.wav
[INFO] Transcribe success: segments=128
[INFO] Export SRT success: output/input.srt
[INFO] Burn subtitle success: output/input_subtitled.mp4
[INFO] Task done
```

---

### 17.2 失败日志

```text
[ERROR] Task failed: input.mp4
[ERROR] Stage: EXTRACTING_AUDIO
[ERROR] Reason: no audio stream found
```

---

## 18. 报告文件设计

每个视频输出一个 `report.json`。

示例：

```json
{
  "input_path": "videos/lesson01.mp4",
  "output_dir": "output/lesson01",
  "status": "success",
  "duration": 735.2,
  "media": {
    "width": 1920,
    "height": 1080,
    "video_codec": "h264",
    "audio_codec": "aac"
  },
  "subtitle": {
    "segments": 128,
    "language": "zh",
    "format": ["srt", "ass"],
    "style": "classic"
  },
  "outputs": {
    "srt": "output/lesson01/lesson01.cleaned.srt",
    "ass": "output/lesson01/lesson01.ass",
    "video": "output/lesson01/lesson01_subtitled.mp4"
  },
  "time_cost": {
    "extract_audio": 8.2,
    "transcribe": 95.4,
    "render": 41.7,
    "total": 151.3
  }
}
```

---

## 19. 批量处理设计

### 19.1 输入

```bash
autosub batch ./videos --recursive --lang zh --model small
```

### 19.2 扫描规则

支持的视频格式：

```text
.mp4
.mov
.mkv
.webm
.avi
.m4v
```

### 19.3 批量报告

输出：

```text
output/batch_report.json
```

示例：

```json
{
  "total": 10,
  "success": 8,
  "failed": 2,
  "skipped": 0,
  "items": [
    {
      "input": "lesson01.mp4",
      "status": "success",
      "output": "output/lesson01/lesson01_subtitled.mp4"
    },
    {
      "input": "lesson02.mp4",
      "status": "failed",
      "reason": "no audio stream found"
    }
  ]
}
```

---

## 20. 测试用例

### 20.1 单元测试

需要测试：

```text
format_srt_time
write_srt
wrap_subtitle_text
apply_offset
ensure_min_duration
remove_filler_words
parse_ffmpeg_time
probe_media
```

---

### 20.2 集成测试

需要测试：

```text
输入正常 mp4，可以生成 srt
输入正常 mp4，可以生成硬字幕视频
输入无音轨视频，会报明确错误
输入不存在文件，会报明确错误
输入中文路径视频，可以正常处理
输入带空格路径视频，可以正常处理
批量处理时，一个失败不会影响其他任务
```

---

### 20.3 测试样例

准备这些测试文件：

```text
sample_chinese.mp4
sample_english.mp4
sample_no_audio.mp4
sample_with_space name.mp4
中文路径测试.mp4
sample_long_video.mp4
```

---

## 21. 第一版开发任务清单

### 21.1 项目初始化

* [ ] 创建项目目录
* [ ] 创建虚拟环境
* [ ] 创建 `requirements.txt`
* [ ] 创建 `README.md`
* [ ] 创建 `main.py`
* [ ] 创建 `autosub/` 包
* [ ] 配置日志目录
* [ ] 配置输出目录

---

### 21.2 FFprobe 模块

* [ ] 编写 `MediaInfo` 数据类
* [ ] 编写 `probe_media()` 函数
* [ ] 调用 ffprobe 获取 JSON
* [ ] 解析视频流
* [ ] 解析音频流
* [ ] 判断是否有音轨
* [ ] 判断是否有字幕轨
* [ ] 处理 ffprobe 不存在的错误
* [ ] 处理文件不存在的错误
* [ ] 编写测试用例

---

### 21.3 音频提取模块

* [ ] 编写 `extract_audio()` 函数
* [ ] 使用 FFmpeg 提取 wav
* [ ] 设置单声道
* [ ] 设置 16000Hz
* [ ] 检查输出文件是否存在
* [ ] 检查输出文件大小
* [ ] 处理无音轨错误
* [ ] 编写测试用例

---

### 21.4 Whisper 识别模块

* [ ] 安装 Whisper 或 faster-whisper
* [ ] 编写 `SubtitleSegment` 数据类
* [ ] 编写 `transcribe_audio()` 函数
* [ ] 支持模型参数
* [ ] 支持语言参数
* [ ] 输出字幕片段列表
* [ ] 处理模型加载失败
* [ ] 处理识别失败
* [ ] 编写测试用例

---

### 21.5 SRT 导出模块

* [ ] 编写 `format_srt_time()` 函数
* [ ] 编写 `write_srt()` 函数
* [ ] 支持 UTF-8 编码
* [ ] 确保序号正确
* [ ] 确保时间格式正确
* [ ] 确保空行正确
* [ ] 编写测试用例

---

### 21.6 字幕清洗模块

* [ ] 编写 `wrap_subtitle_text()` 函数
* [ ] 编写 `apply_offset()` 函数
* [ ] 编写 `ensure_min_duration()` 函数
* [ ] 编写 `remove_filler_words()` 函数
* [ ] 编写 `normalize_punctuation()` 函数
* [ ] 支持配置最大行长度
* [ ] 支持配置最短显示时间
* [ ] 编写测试用例

---

### 21.7 ASS 导出模块

* [ ] 编写 `SubtitleStyle` 数据类
* [ ] 编写样式模板 JSON
* [ ] 编写 `load_style()` 函数
* [ ] 编写 `write_ass()` 函数
* [ ] 支持 classic 样式
* [ ] 支持 short_video 样式
* [ ] 支持 course 样式
* [ ] 编写测试用例

---

### 21.8 字幕烧录模块

* [ ] 编写 `burn_subtitle()` 函数
* [ ] 支持 SRT 烧录
* [ ] 支持 ASS 烧录
* [ ] 支持 crf 参数
* [ ] 支持 preset 参数
* [ ] 保留原音频
* [ ] 输出 mp4
* [ ] 处理字幕文件不存在错误
* [ ] 处理 FFmpeg 渲染失败错误
* [ ] 编写测试用例

---

### 21.9 软字幕封装模块

* [ ] 编写 `mux_soft_subtitle()` 函数
* [ ] 支持 MP4 软字幕
* [ ] 支持 MKV 软字幕
* [ ] 处理字幕编码问题
* [ ] 编写测试用例

---

### 21.10 Pipeline 模块

* [ ] 编写 `run_pipeline()` 函数
* [ ] 串联 probe
* [ ] 串联 extract audio
* [ ] 串联 transcribe
* [ ] 串联 subtitle clean
* [ ] 串联 subtitle export
* [ ] 串联 burn subtitle
* [ ] 记录每一步耗时
* [ ] 记录每一步状态
* [ ] 失败时停止任务
* [ ] 生成 report.json

---

### 21.11 CLI 模块

* [ ] 实现 `autosub info`
* [ ] 实现 `autosub transcribe`
* [ ] 实现 `autosub burn`
* [ ] 实现 `autosub all`
* [ ] 实现 `autosub batch`
* [ ] 支持 `--lang`
* [ ] 支持 `--model`
* [ ] 支持 `--style`
* [ ] 支持 `--output-dir`
* [ ] 支持 `--offset`
* [ ] 支持 `--soft-subtitle`
* [ ] 支持 `--hard-subtitle`

---

### 21.12 批量处理模块

* [ ] 编写目录扫描函数
* [ ] 支持递归扫描
* [ ] 支持跳过已完成
* [ ] 支持单个失败继续执行
* [ ] 支持批量报告
* [ ] 支持显示总进度
* [ ] 支持失败列表输出

---

## 22. 第二版增强功能

### 22.1 字幕编辑

* [ ] 加载 SRT 文件
* [ ] 显示字幕列表
* [ ] 修改字幕文本
* [ ] 修改开始时间
* [ ] 修改结束时间
* [ ] 合并字幕
* [ ] 拆分字幕
* [ ] 搜索替换
* [ ] 保存修改后的字幕

---

### 22.2 双语字幕

* [ ] 支持识别原语言
* [ ] 支持翻译成目标语言
* [ ] 支持上下两行显示
* [ ] 支持中英双语 ASS
* [ ] 支持只导出双语字幕文件
* [ ] 支持烧录双语字幕

---

### 22.3 GUI 版本

* [ ] 支持拖拽导入视频
* [ ] 显示视频列表
* [ ] 显示视频基础信息
* [ ] 显示字幕列表
* [ ] 支持字幕编辑
* [ ] 支持样式选择
* [ ] 支持预览字幕效果
* [ ] 支持开始 / 暂停 / 取消任务
* [ ] 显示进度条
* [ ] 显示失败原因

---

### 22.4 字幕预览

* [ ] 截取视频某一帧
* [ ] 在截图上渲染字幕效果
* [ ] 预览字体大小
* [ ] 预览颜色
* [ ] 预览描边
* [ ] 预览位置
* [ ] 不必完整渲染视频即可看效果

---

## 23. 验收标准

### 23.1 基础验收

项目完成后，必须满足：

* [ ] 能输入一个视频文件
* [ ] 能成功提取音频
* [ ] 能成功识别语音
* [ ] 能生成 SRT 字幕
* [ ] 能烧录硬字幕
* [ ] 能输出最终视频
* [ ] 能输出 report.json
* [ ] 错误时有明确提示

---

### 23.2 工程验收

项目还应满足：

* [ ] 代码结构清晰
* [ ] 模块职责明确
* [ ] 不把所有逻辑写在一个文件里
* [ ] FFmpeg 命令有统一封装
* [ ] 路径处理兼容空格和中文
* [ ] 关键函数有类型注解
* [ ] 有基础测试
* [ ] 有 README 使用说明
* [ ] 有示例命令
* [ ] 有示例输出

---

### 23.3 简历验收

项目完成后，应该能够在简历里写：

```text
开发了一款基于 FFmpeg 与 Whisper 的本地视频字幕生产工具，设计 Media Probe → Audio Extract → ASR Transcribe → Subtitle Post-process → Render/Mux 的处理流水线，支持 SRT/ASS 字幕导出、硬字幕烧录、软字幕封装、字幕自动断行、样式模板、批量任务处理、失败重试和 JSON 报告导出。
```

---

## 24. README 需要包含的内容

最终 README 至少包含：

```text
项目简介
功能列表
技术栈
安装方式
FFmpeg 安装说明
Whisper 安装说明
快速开始
CLI 命令说明
输出目录说明
字幕样式说明
常见问题
项目截图或 Demo
未来计划
```

---

## 25. 推荐开发顺序

建议按下面顺序做：

```text
1. 先跑通 FFmpeg 和 ffprobe
2. 再跑通音频提取
3. 再接入 Whisper
4. 再生成 SRT
5. 再做字幕烧录
6. 再做字幕清洗
7. 再做 ASS 样式
8. 再做 pipeline
9. 再做 CLI
10. 最后做批量处理和报告
```

不要一开始就做 GUI。

---

## 26. 项目完成标准

当你可以执行下面命令时，第一版就算完成：

```bash
autosub all ./examples/sample.mp4 --lang zh --model small --style classic
```

并且成功生成：

```text
output/sample/sample.cleaned.srt
output/sample/sample.ass
output/sample/sample_subtitled.mp4
output/sample/report.json
```

同时满足：

```text
字幕可以正常显示
中文不乱码
视频可以正常播放
音频没有丢失
报告内容完整
失败时有明确错误提示
```

---

## 27. 后续可扩展方向

* 支持 faster-whisper 提高速度
* 支持 GPU / CPU 自动切换
* 支持字幕翻译
* 支持双语字幕
* 支持字幕编辑器
* 支持 GUI 桌面端
* 支持 Web 上传处理
* 支持视频预览
* 支持多任务并发
* 支持 Docker 部署
* 支持云端任务队列
* 支持字幕关键词高亮
* 支持短视频大字模板
* 支持自动生成封面图
* 支持从已有字幕重新烧录

---

## 28. 当前优先级

第一优先级：

* [ ] ffprobe 视频检查
* [ ] FFmpeg 音频提取
* [ ] Whisper 识别
* [ ] SRT 导出
* [ ] FFmpeg 字幕烧录

第二优先级：

* [ ] 字幕自动断行
* [ ] ASS 样式模板
* [ ] 任务报告
* [ ] CLI 参数完善

第三优先级：

* [ ] 批量处理
* [ ] 字幕编辑
* [ ] GUI
* [ ] 双语字幕

---

## 29. 最终目标

这个项目最终要体现的不是：

```text
我会调用 FFmpeg。
```

而是：

```text
我能把 FFmpeg、Whisper、字幕格式、任务队列、错误处理、批量处理和用户工作流整合成一个完整的工具。
```

这才是项目价值。

