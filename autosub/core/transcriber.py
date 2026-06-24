from __future__ import annotations

from pathlib import Path

from autosub.models.subtitle_segment import SubtitleSegment


class TranscriptionError(RuntimeError):
    pass


def _transcribe_with_faster_whisper(
    audio_path: Path,
    model_name: str,
    language: str | None,
) -> list[SubtitleSegment]:
    from faster_whisper import WhisperModel

    model = WhisperModel(model_name, device="auto", compute_type="auto")
    segments, _info = model.transcribe(str(audio_path), language=language or None)
    return [
        SubtitleSegment(index=i, start=float(seg.start), end=float(seg.end), text=seg.text.strip())
        for i, seg in enumerate(segments, start=1)
        if seg.text.strip()
    ]


def _transcribe_with_openai_whisper(
    audio_path: Path,
    model_name: str,
    language: str | None,
) -> list[SubtitleSegment]:
    import whisper

    model = whisper.load_model(model_name)
    result = model.transcribe(str(audio_path), language=None if language == "auto" else language)
    return [
        SubtitleSegment(
            index=i,
            start=float(seg["start"]),
            end=float(seg["end"]),
            text=str(seg["text"]).strip(),
        )
        for i, seg in enumerate(result.get("segments", []), start=1)
        if str(seg.get("text", "")).strip()
    ]


def transcribe_audio(
    audio_path: str | Path,
    model_name: str = "small",
    language: str | None = None,
) -> list[SubtitleSegment]:
    path = Path(audio_path)
    if not path.exists():
        raise FileNotFoundError(f"处理失败：音频文件不存在。\n文件：{path}")

    lang = None if language in (None, "", "auto") else language
    try:
        return _transcribe_with_faster_whisper(path, model_name, lang)
    except ModuleNotFoundError:
        pass
    except Exception as exc:  # Whisper backends raise diverse model/runtime errors.
        raise TranscriptionError(f"Whisper 识别失败：{exc}") from exc

    try:
        return _transcribe_with_openai_whisper(path, model_name, lang)
    except ModuleNotFoundError as exc:
        raise TranscriptionError(
            "处理失败：未安装 Whisper 后端。\n"
            "建议：执行 `pip install faster-whisper` 或 `pip install openai-whisper`。"
        ) from exc
    except Exception as exc:
        raise TranscriptionError(f"Whisper 识别失败：{exc}") from exc
