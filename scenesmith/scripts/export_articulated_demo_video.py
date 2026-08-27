#!/usr/bin/env python3
"""Record a safe sequential articulation demo from the SceneSmith viewer."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import shutil
import subprocess
import tempfile

from pathlib import Path

from playwright.async_api import Page, async_playwright


SEQUENCE = [
    ("closed hold", 0.8, {}),
    ("open entry door", 1.2, {"frame_to_door": 1.2}),
    (
        "open cabinet",
        1.5,
        {"left_hinge": 1.2, "right_hinge": 1.2},
    ),
    ("open microwave door", 1.5, {"body_to_front_door": 1.5}),
    ("extend microwave tray", 1.2, {"body_to_sliding_tray": 0.22}),
    (
        "turn microwave controls",
        1.0,
        {
            "tray_to_turntable": 2.4,
            "body_to_upper_knob": 1.2,
            "body_to_lower_knob": -1.2,
        },
    ),
    ("open hold", 0.8, {}),
    (
        "reset controls and retract tray",
        1.1,
        {
            "body_to_sliding_tray": 0.0,
            "tray_to_turntable": 0.0,
            "body_to_upper_knob": 0.0,
            "body_to_lower_knob": 0.0,
        },
    ),
    ("close microwave door", 1.3, {"body_to_front_door": 0.0}),
    (
        "close cabinet",
        1.3,
        {"left_hinge": 0.0, "right_hinge": 0.0},
    ),
    ("close entry door", 1.0, {"frame_to_door": 0.0}),
    ("final hold", 0.8, {}),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--update-hz", type=int, default=24)
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--browser-executable", type=Path)
    return parser.parse_args()


async def set_joint(page: Page, name: str, value: float) -> None:
    await page.locator(f"#joint-{name}").evaluate(
        """
        (input, amount) => {
          input.value = String(amount);
          input.dispatchEvent(new Event("input", {bubbles: true}));
        }
        """,
        value,
    )


def smoothstep(value: float) -> float:
    return value * value * (3.0 - 2.0 * value)


async def animate_segment(
    page: Page,
    current: dict[str, float],
    duration: float,
    targets: dict[str, float],
    update_hz: int,
) -> int:
    updates = max(round(duration * update_hz), 2)
    start_values = dict(current)
    delay_ms = max(round(duration * 1000 / updates), 1)
    for index in range(updates):
        phase = smoothstep(index / max(updates - 1, 1))
        for name, target in targets.items():
            start = start_values[name]
            await set_joint(page, name, start + (target - start) * phase)
        await page.wait_for_timeout(delay_ms)
    current.update(targets)
    return updates


def probe_video(path: Path) -> dict:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration:stream=codec_name,width,height,r_frame_rate,nb_frames",
        "-of",
        "json",
        str(path),
    ]
    result = subprocess.run(
        command, check=True, capture_output=True, text=True
    )
    return json.loads(result.stdout)


async def main() -> None:
    args = parse_args()
    output = args.out.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix="scenesmith_demo_video_"))
    webm = temporary / "capture.webm"
    browser_executable = (
        args.browser_executable.expanduser().resolve()
        if args.browser_executable
        else None
    )
    current = {
        "frame_to_door": 0.0,
        "left_hinge": 0.0,
        "right_hinge": 0.0,
        "body_to_front_door": 0.0,
        "body_to_sliding_tray": 0.0,
        "tray_to_turntable": 0.0,
        "body_to_upper_knob": 0.0,
        "body_to_lower_knob": 0.0,
    }
    update_count = 0

    try:
        async with async_playwright() as playwright:
            launch_options = {"headless": True}
            if browser_executable:
                launch_options["executable_path"] = str(browser_executable)
            browser = await playwright.chromium.launch(**launch_options)
            context = await browser.new_context(
                viewport={"width": args.width, "height": args.height},
                device_scale_factor=1,
                record_video_dir=str(temporary),
                record_video_size={
                    "width": args.width,
                    "height": args.height,
                },
            )
            page = await context.new_page()
            video = page.video
            errors = []
            page.on(
                "console",
                lambda message: (
                    errors.append(message.text)
                    if message.type == "error"
                    else None
                ),
            )
            await page.goto(
                args.url, wait_until="domcontentloaded", timeout=60_000
            )
            await page.wait_for_function(
                "document.querySelector('#status').textContent === 'Ready'",
                timeout=60_000,
            )
            await page.wait_for_function(
                "window.viewerJoints?.length === 8 "
                "&& window.viewerInterlocks?.microwave",
                timeout=30_000,
            )

            tray = page.locator("#joint-body_to_sliding_tray")
            if not await tray.is_disabled():
                raise RuntimeError("Microwave tray is not initially locked")

            # Keep the room and all eight controls visible.
            await page.mouse.move(640, 360)
            await page.mouse.down()
            await page.mouse.move(810, 430, steps=30)
            await page.mouse.up()
            await page.mouse.wheel(0, -1650)
            await page.wait_for_timeout(500)

            for label, duration, targets in SEQUENCE:
                print(label, flush=True)
                update_count += await animate_segment(
                    page,
                    current,
                    duration,
                    targets,
                    args.update_hz,
                )

            if errors:
                raise RuntimeError(f"Viewer console errors: {errors}")
            if float(await tray.input_value()) != 0.0:
                raise RuntimeError("Video sequence did not finish retracted")
            if not await tray.is_disabled():
                raise RuntimeError("Tray interlock was not restored")

            await page.close()
            await video.save_as(str(webm))
            await context.close()
            await browser.close()

        recording_probe = probe_video(webm)
        recorded_duration = float(recording_probe["format"]["duration"])
        planned_duration = sum(seconds for _, seconds, _ in SEQUENCE)
        speed_factor = recorded_duration / planned_duration
        command = [
            "ffmpeg",
            "-y",
            "-i",
            str(webm),
            "-vf",
            f"setpts=PTS/{speed_factor:.9f}",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "20",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            "-an",
            str(output),
        ]
        subprocess.run(command, check=True)
        probe = probe_video(output)
        digest = hashlib.sha256(output.read_bytes()).hexdigest()
        metadata = {
            "video": str(output),
            "bytes": output.stat().st_size,
            "sha256": digest,
            "viewer_url": args.url,
            "animation_update_hz": args.update_hz,
            "animation_updates": update_count,
            "source_recording_duration_seconds": round(
                recorded_duration, 3
            ),
            "planned_duration_seconds": planned_duration,
            "speed_factor": round(speed_factor, 6),
            "probe": probe,
            "microwave_interlock": {
                "safe_door_angle_rad": 1.5,
                "tray_locked_below_safe_angle": True,
                "sequence_opens_door_before_tray": True,
                "sequence_retracts_tray_before_closing_door": True,
            },
            "segments": [
                {"name": name, "seconds": seconds, "targets": targets}
                for name, seconds, targets in SEQUENCE
            ],
        }
        output.with_suffix(".json").write_text(
            json.dumps(metadata, indent=2) + "\n"
        )
        print(json.dumps(metadata, indent=2))
    finally:
        shutil.rmtree(temporary, ignore_errors=True)


if __name__ == "__main__":
    asyncio.run(main())
