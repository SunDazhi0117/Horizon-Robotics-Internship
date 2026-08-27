from __future__ import annotations

import argparse
import asyncio
import math
import shutil
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from playwright.async_api import async_playwright

AUTO_ANIMATE_RENDER_QUERY = "100011000"
SEQUENCE_RENDER_QUERY = "100010000"
DEFAULT_ANIMATION_SPEED = 0.35
DEFAULT_PER_JOINT_SECONDS = 2.4
DEFAULT_PAUSE_SECONDS = 0.35


def with_export_query(
    url: str,
    *,
    animation_mode: str,
    animation_speed: float,
) -> str:
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query.setdefault(
        "render",
        AUTO_ANIMATE_RENDER_QUERY if animation_mode == "auto" else SEQUENCE_RENDER_QUERY,
    )
    query.setdefault("animation_speed", f"{animation_speed:g}")
    query.setdefault("export_canvas", "1")
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:5173")
    parser.add_argument("--record-text", default="")
    parser.add_argument("--out", required=True)
    parser.add_argument("--duration", type=float, default=8.0)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--wait", type=float, default=2.0)
    parser.add_argument(
        "--animation-mode", choices=("sequence", "auto", "sliders"), default="sequence"
    )
    parser.add_argument("--animation-speed", type=float, default=DEFAULT_ANIMATION_SPEED)
    parser.add_argument("--per-joint-seconds", type=float, default=DEFAULT_PER_JOINT_SECONDS)
    parser.add_argument("--pause-seconds", type=float, default=DEFAULT_PAUSE_SECONDS)
    parser.add_argument("--capture-target", choices=("canvas", "page"), default="canvas")
    args = parser.parse_args()

    out_path = Path(args.out).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    frame_dir = Path(tempfile.mkdtemp(prefix="articraft_mp4_frames_"))

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
            viewport={"width": args.width, "height": args.height},
            device_scale_factor=1,
        )

        viewer_url = with_export_query(
            args.url,
            animation_mode=args.animation_mode,
            animation_speed=args.animation_speed,
        )
        print(f"[1/5] Opening Viewer: {viewer_url}")
        await page.goto(viewer_url, wait_until="domcontentloaded", timeout=60_000)
        await page.wait_for_timeout(3000)

        try:
            await page.wait_for_selector("canvas", timeout=30_000)
        except Exception:
            print("Warning: canvas not found after 30s; continuing anyway")

        if args.record_text:
            print(f"[2/5] Trying to open record containing text: {args.record_text}")
            try:
                await page.get_by_text(args.record_text, exact=False).first.click(timeout=10_000)
                await page.wait_for_timeout(int(args.wait * 1000))
            except Exception as exc:
                print(f"Warning: could not click record text automatically: {exc}")
                print(
                    "The script will continue. Make sure the Viewer URL already opens the target record."
                )

        print("[3/5] Waiting for Viewer canvas / page content")
        canvas = page.locator("canvas").first
        if args.capture_target == "canvas":
            await canvas.wait_for(state="visible", timeout=60_000)
        await page.wait_for_timeout(int(args.wait * 1000))

        slider_count = 0
        if args.animation_mode == "sliders":
            slider_count = await page.locator('input[type="range"]').count()
            print(f"Found {slider_count} slider(s).")

        sequence_joints: list[str] = []
        if args.animation_mode == "sequence":
            print("Waiting for sequential joint export controller")
            await page.wait_for_function(
                "() => window.__ARTICRAFT_EXPORT__?.ready === true",
                timeout=60_000,
            )
            sequence_joints = await page.evaluate(
                "() => window.__ARTICRAFT_EXPORT__.joints.map((joint) => joint.name)"
            )
            print(f"Found {len(sequence_joints)} sequential joint(s).")

        if args.animation_mode == "sliders" and slider_count == 0:
            await page.screenshot(path=str(frame_dir / "debug_no_sliders.png"), full_page=True)
            await browser.close()
            raise RuntimeError(
                "No joint sliders found. The record may not be open, or the Viewer uses a different slider element."
            )
        if args.animation_mode == "sequence" and len(sequence_joints) == 0:
            await page.screenshot(path=str(frame_dir / "debug_no_joints.png"), full_page=True)
            await browser.close()
            raise RuntimeError("No movable joints found for sequential MP4 export.")

        print("[4/5] Animating joints and capturing frames")

        if args.animation_mode == "sequence":
            sequence_duration = len(sequence_joints) * max(args.per_joint_seconds, 0.25)
            pause_duration = max(len(sequence_joints) - 1, 0) * max(args.pause_seconds, 0)
            total_frames = max(
                int(args.duration * args.fps),
                int(math.ceil((sequence_duration + pause_duration) * args.fps)),
            )
        else:
            total_frames = int(args.duration * args.fps)

        for frame_idx in range(total_frames):
            t = frame_idx / max(total_frames - 1, 1)

            if args.animation_mode == "sequence":
                segment_seconds = max(args.per_joint_seconds, 0.25) + max(args.pause_seconds, 0)
                time_seconds = frame_idx / args.fps
                joint_index = min(int(time_seconds / segment_seconds), len(sequence_joints) - 1)
                segment_time = time_seconds - (joint_index * segment_seconds)
                phase = min(segment_time / max(args.per_joint_seconds, 0.25), 1)
                await page.evaluate(
                    """
                    ({ jointIndex, phase }) => {
                        window.__ARTICRAFT_EXPORT__.setSequentialJointPhase(jointIndex, phase);
                    }
                    """,
                    {"jointIndex": joint_index, "phase": phase},
                )

            elif args.animation_mode == "sliders":
                # ping-pong motion: 0 -> 1 -> 0
                phase = 0.5 - 0.5 * math.cos(2 * math.pi * t)

                await page.evaluate(
                    """
                    ({ phase }) => {
                        const sliders = Array.from(document.querySelectorAll('input[type="range"]'));

                        for (const slider of sliders) {
                            const min = Number.parseFloat(slider.min || "0");
                            const max = Number.parseFloat(slider.max || "1");

                            if (!Number.isFinite(min) || !Number.isFinite(max)) {
                                continue;
                            }

                            const value = min + (max - min) * phase;
                            slider.value = String(value);

                            slider.dispatchEvent(new Event("input", { bubbles: true }));
                            slider.dispatchEvent(new Event("change", { bubbles: true }));
                        }
                    }
                    """,
                    {"phase": phase},
                )

            await page.wait_for_timeout(int(1000 / args.fps))

            frame_path = frame_dir / f"frame_{frame_idx:05d}.png"
            if args.capture_target == "canvas":
                await canvas.screenshot(path=str(frame_path))
            else:
                await page.screenshot(path=str(frame_path), full_page=False)

            if frame_idx % args.fps == 0:
                print(f"Captured frame {frame_idx}/{total_frames}")

        await browser.close()

    print("[5/5] Encoding MP4 with ffmpeg")

    cmd = [
        "ffmpeg",
        "-y",
        "-framerate",
        str(args.fps),
        "-i",
        str(frame_dir / "frame_%05d.png"),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(out_path),
    ]

    subprocess.run(cmd, check=True)

    print()
    print("MP4 exported successfully:")
    print(out_path)

    shutil.rmtree(frame_dir, ignore_errors=True)


if __name__ == "__main__":
    asyncio.run(main())
