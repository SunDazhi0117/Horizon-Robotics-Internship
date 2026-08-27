from __future__ import annotations

import asyncio
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

DEFAULT_DURATION_SECONDS = 8.0
DEFAULT_FPS = 15
DEFAULT_WIDTH = 960
DEFAULT_HEIGHT = 540
DEFAULT_ANIMATION_SPEED = 0.35
DEFAULT_PER_JOINT_SECONDS = 2.4
DEFAULT_PAUSE_SECONDS = 0.35


@dataclass(frozen=True, slots=True)
class VideoExportResult:
    output_path: Path
    file_url: str


def record_viewer_url(record_id: str) -> str:
    return f"http://127.0.0.1:8765/viewer?record={quote(record_id)}"


def staging_viewer_url(run_id: str, record_id: str) -> str:
    return (
        "http://127.0.0.1:8765/viewer?"
        f"staging={quote(run_id)}:{quote(record_id)}&browser=staging&run={quote(run_id)}"
    )


def _format_export_error(details: str, returncode: int) -> str:
    if "No module named playwright" in details:
        return "Playwright is not installed. Run `uv sync` from the repository root."
    if "Executable doesn't exist" in details and "playwright install" in details:
        return "Playwright Chromium is not installed. Run `uv run python -m playwright install chromium`."
    if "Failed to download" in details and "playwright" in details:
        return (
            "Playwright Chromium could not be downloaded in this environment. "
            "Install Chrome/Chromium locally or run `uv run python -m playwright install chromium` "
            "from a network that can access the Playwright browser archive."
        )
    return details or f"MP4 export failed with exit code {returncode}."


async def export_viewer_mp4(
    *,
    repo_root: Path,
    viewer_url: str,
    output_path: Path,
    file_url: str,
    duration: float = DEFAULT_DURATION_SECONDS,
    fps: int = DEFAULT_FPS,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
    animation_speed: float = DEFAULT_ANIMATION_SPEED,
) -> VideoExportResult:
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg is required to export MP4 files, but it was not found in PATH.")

    script_path = repo_root / "scripts" / "export_viewer_mp4.py"
    if not script_path.exists():
        raise RuntimeError(f"MP4 export script not found: {script_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        str(script_path),
        "--url",
        viewer_url,
        "--out",
        str(output_path),
        "--duration",
        str(duration),
        "--fps",
        str(fps),
        "--width",
        str(width),
        "--height",
        str(height),
        "--animation-mode",
        "sequence",
        "--animation-speed",
        str(animation_speed),
        "--per-joint-seconds",
        str(DEFAULT_PER_JOINT_SECONDS),
        "--pause-seconds",
        str(DEFAULT_PAUSE_SECONDS),
        "--capture-target",
        "canvas",
        "--wait",
        "2.0",
    ]

    try:
        await asyncio.to_thread(
            subprocess.run,
            cmd,
            cwd=str(repo_root),
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("Python executable was not found while exporting MP4.") from exc
    except subprocess.CalledProcessError as exc:
        details = "\n".join(part for part in (exc.stdout, exc.stderr) if part.strip()).strip()
        raise RuntimeError(_format_export_error(details, exc.returncode)) from exc

    return VideoExportResult(output_path=output_path, file_url=file_url)
