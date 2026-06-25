from __future__ import annotations

import signal
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

from streamforge.core.errors import ProcessFailedError
from streamforge.core.probe import require_binary


@dataclass(slots=True)
class ManagedProcess:
    name: str
    command: list[str]
    log_path: Path
    process: subprocess.Popen[str] | None = field(default=None)

    def start(self) -> None:
        require_binary(self.command[0])
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

        # FFmpeg is a long-running child process in streaming projects. We send
        # all output to a per-channel log file so the CLI stays readable and the
        # real FFmpeg diagnostics are still available when something fails.
        log_file = self.log_path.open("a", encoding="utf-8")
        self.process = subprocess.Popen(
            self.command,
            text=True,
            stdout=log_file,
            stderr=subprocess.STDOUT,
        )

    def stop(self, timeout: float = 8.0) -> None:
        if not self.process or self.process.poll() is not None:
            return

        # Give FFmpeg a chance to close playlists, files and network sockets
        # cleanly before falling back to SIGKILL.
        self.process.send_signal(signal.SIGTERM)
        try:
            self.process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()

    @property
    def running(self) -> bool:
        return self.process is not None and self.process.poll() is None


class ProcessGroup:
    def __init__(self, processes: list[ManagedProcess]):
        self.processes = processes

    def run_forever(self) -> None:
        for process in self.processes:
            process.start()
            time.sleep(0.5)
            if not process.running:
                raise ProcessFailedError(f"进程启动失败：{process.name}，请查看日志 {process.log_path}")

        try:
            while True:
                # A streaming gateway should notice when one FFmpeg worker dies.
                # This first version stops the group and surfaces the failure;
                # a production supervisor could restart failed workers here.
                failed = [p for p in self.processes if not p.running]
                if failed:
                    names = ", ".join(p.name for p in failed)
                    raise ProcessFailedError(f"进程退出：{names}")
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            for process in self.processes:
                process.stop()
