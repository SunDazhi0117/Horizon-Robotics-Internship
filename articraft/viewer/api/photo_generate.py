from __future__ import annotations

import base64
import binascii
import json
import os
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from viewer.api.feedback_memory import render_feedback_memory, select_relevant_feedback

IMAGE_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
MAX_IMAGE_BYTES = 12 * 1024 * 1024
MAX_REFERENCE_IMAGES = 8
DEFAULT_PHOTO_PROVIDER = "codex-cli"
DEFAULT_CODEX_PHOTO_MODEL = "gpt-5.5"
DEFAULT_PROMPT_ENHANCEMENT_TIMEOUT_SECONDS = 120.0
PHOTO_PROVIDER_ENV_VAR = "ARTICRAFT_PHOTO_PROVIDER"
PHOTO_MODEL_ENV_VAR = "ARTICRAFT_PHOTO_MODEL"
CODEX_MODEL_ENV_VAR = "ARTICRAFT_CODEX_MODEL"
PROMPT_ENHANCEMENT_ENV_VAR = "ARTICRAFT_PHOTO_ENHANCE_PROMPT"
PROMPT_ENHANCEMENT_TIMEOUT_ENV_VAR = "ARTICRAFT_PHOTO_ENHANCE_TIMEOUT_SECONDS"
DEFAULT_PHOTO_ONLY_PROMPT = (
    "Infer a simple, plausible articulation plan from the reference photo. Identify the main "
    "movable part or parts that a real version of this object would have, such as lids, doors, "
    "hinges, drawers, sliders, knobs, buttons, rotating caps, or removable components. If the "
    "object appears to have no obvious moving part, add one clear educational articulation that "
    "fits the object without changing its visual identity."
)


@dataclass(frozen=True, slots=True)
class ReferencePhotoInput:
    image_data: str
    image_filename: str | None
    image_content_type: str


@dataclass(frozen=True, slots=True)
class PhotoGenerationResult:
    request_id: str
    prompt_path: Path
    image_path: Path
    image_paths: list[Path]
    log_path: Path
    enhanced_prompt_path: Path | None = None
    prompt_memory_path: Path | None = None


def build_reference_photo_prompt(user_prompt: str, *, image_count: int = 1) -> str:
    cleaned_prompt = user_prompt.strip() or DEFAULT_PHOTO_ONLY_PROMPT
    photo_description = (
        "the attached real-world reference photo"
        if image_count == 1
        else (
            f"the {image_count} attached real-world reference photos. Treat them as ordered "
            "views of the same object; they may show different angles, close-up details, or "
            "different articulation states such as closed, half-open, and fully open"
        )
    )
    return (
        f"Create an articulated 3D object using {photo_description} as the primary visual "
        "reference.\n\n"
        "Use the image set to infer the object's proportions, silhouette, visible parts, materials, "
        "colors, panel layout, handles, hinges, rails, knobs, and other visible details. "
        "If multiple photos show different motion states, infer the joint type, axis, range, "
        "and moving parts from the change between those states. "
        "If a part is hidden or ambiguous in the image, make a plausible simple mechanical "
        "interpretation instead of inventing unnecessary complexity.\n\n"
        "The generated object must be suitable for Articraft: represent fixed parts as rigid "
        "links, represent movable parts as explicit joints, and make the articulation visually "
        "clear in the viewer. Add visible hinges, pivots, rails, handles, or axes wherever they "
        "help explain how the object moves.\n\n"
        "User motion and design instructions:\n"
        f"{cleaned_prompt}\n\n"
        "Important: preserve the real object's overall visual style from the photo, but prioritize "
        "clean geometry, robust compilation, and clear articulation over photorealistic detail."
    )


def _safe_image_extension(content_type: str, filename: str | None) -> str:
    normalized_type = content_type.strip().lower()
    if normalized_type in IMAGE_EXTENSIONS:
        return IMAGE_EXTENSIONS[normalized_type]

    suffix = Path(filename or "").suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        return ".jpg"
    if suffix in {".png", ".webp"}:
        return suffix
    raise ValueError("Reference image must be a JPEG, PNG, or WEBP file.")


def _decode_image_data(image_data: str) -> bytes:
    raw = image_data.strip()
    data_url_match = re.match(r"^data:[^;]+;base64,(?P<data>.+)$", raw, flags=re.DOTALL)
    if data_url_match:
        raw = data_url_match.group("data")

    try:
        image_bytes = base64.b64decode(raw, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("Reference image data is not valid base64.") from exc

    if not image_bytes:
        raise ValueError("Reference image is empty.")
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise ValueError("Reference image is too large. Use an image smaller than 12 MB.")
    return image_bytes


def _python_executable(repo_root: Path) -> str:
    venv_python = repo_root / ".venv" / "bin" / "python"
    if venv_python.exists():
        return str(venv_python)
    return sys.executable


def _photo_generation_provider() -> str:
    return os.environ.get(PHOTO_PROVIDER_ENV_VAR, DEFAULT_PHOTO_PROVIDER).strip() or DEFAULT_PHOTO_PROVIDER


def _photo_generation_model(provider: str) -> str | None:
    explicit_model = os.environ.get(PHOTO_MODEL_ENV_VAR, "").strip()
    if explicit_model:
        return explicit_model
    if provider == "codex-cli":
        return os.environ.get(CODEX_MODEL_ENV_VAR, "").strip() or DEFAULT_CODEX_PHOTO_MODEL
    return None


def _env_flag(name: str, *, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    normalized = raw.strip().lower()
    if normalized in {"0", "false", "off", "no"}:
        return False
    if normalized in {"1", "true", "on", "yes"}:
        return True
    return default


def _env_float(name: str, *, default: float) -> float:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        value = float(raw)
    except ValueError:
        return default
    return value if value > 0 else default


def _codex_binary() -> str:
    return os.environ.get("ARTICRAFT_CODEX_CLI_BIN", "codex").strip() or "codex"


def _build_prompt_enhancement_instruction(
    user_prompt: str,
    *,
    image_count: int,
    feedback_memory_text: str = "",
) -> str:
    cleaned_prompt = user_prompt.strip()
    brief = cleaned_prompt or (
        "Infer the object identity and a clear plausible articulation from the attached photos."
    )
    photo_description = (
        "one attached reference photo"
        if image_count == 1
        else (
            f"{image_count} attached reference photos in upload order. They may show different "
            "views, close-up details, or motion states of the same object."
        )
    )
    memory_section = (
        "\n\nFeedback memory to apply when relevant:\n"
        f"{feedback_memory_text.strip()}"
        if feedback_memory_text.strip()
        else ""
    )
    return (
        "You are writing an Articraft generation prompt, not creating code.\n"
        f"Use the {photo_description} and the user's short instruction to produce one detailed "
        "prompt for a future 3D articulated-object generation run.\n\n"
        "The prompt should name the likely object, describe its silhouette, proportions, visible "
        "parts, materials, colors, seams, buttons, handles, surface details, and construction. "
        "It must also specify a clean articulation plan: fixed base/body, moving parts, joint "
        "type, joint axis or travel direction, plausible range of motion, visible hinges/rails/"
        "pivots/stops, and how multiple photo states should map to the generated movement. "
        "Keep the plan implementable with robust simple geometry. Do not invent logos, text, "
        "unseen electronics, or excessive hidden complexity. If the images are ambiguous, choose "
        "the simplest plausible mechanism that preserves the object's visual identity.\n\n"
        "Return JSON matching the schema with only a `prompt` string. The prompt itself should "
        "be concise but specific, about 250-500 words, and ready to paste into Articraft.\n\n"
        "User short instruction:\n"
        f"{brief}"
        f"{memory_section}"
    )


def _prompt_from_enhancement_output(raw_text: str) -> str | None:
    text = raw_text.strip()
    if not text:
        return None
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text).strip()

    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        payload = None

    if isinstance(payload, dict):
        prompt = payload.get("prompt")
        if isinstance(prompt, str):
            text = prompt.strip()

    text = text.replace("\r\n", "\n").strip()
    return text if len(text) >= 40 else None


def _enhance_photo_prompt(
    *,
    repo_root: Path,
    request_dir: Path,
    user_prompt: str,
    image_paths: list[Path],
    model: str | None,
    feedback_memory_text: str = "",
) -> Path | None:
    if not _env_flag(PROMPT_ENHANCEMENT_ENV_VAR, default=True):
        return None
    if not image_paths:
        return None

    schema_path = request_dir / "enhanced_prompt.schema.json"
    raw_output_path = request_dir / "enhanced_prompt.raw.txt"
    enhanced_prompt_path = request_dir / "enhanced_prompt.txt"
    enhancement_log_path = request_dir / "prompt_enhancement.log"
    schema = {
        "type": "object",
        "additionalProperties": False,
        "required": ["prompt"],
        "properties": {
            "prompt": {
                "type": "string",
                "minLength": 40,
            }
        },
    }
    schema_path.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")

    cmd = [
        _codex_binary(),
        "exec",
        "--skip-git-repo-check",
        "--ephemeral",
        "--ignore-rules",
        "--sandbox",
        os.environ.get("ARTICRAFT_CODEX_CLI_SANDBOX", "read-only").strip() or "read-only",
        "--color",
        "never",
        "--output-schema",
        str(schema_path),
        "--output-last-message",
        str(raw_output_path),
        "-C",
        str(repo_root),
    ]
    if model:
        cmd.extend(["--model", model])
    for image_path in image_paths:
        cmd.extend(["--image", str(image_path)])
    extra_args = os.environ.get("ARTICRAFT_CODEX_CLI_EXTRA_ARGS", "").strip()
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    cmd.append("-")

    instruction = _build_prompt_enhancement_instruction(
        user_prompt,
        image_count=len(image_paths),
        feedback_memory_text=feedback_memory_text,
    )
    with enhancement_log_path.open("w", encoding="utf-8") as log_file:
        log_file.write("$ " + " ".join(cmd) + "\n\n")
        log_file.flush()
        try:
            completed = subprocess.run(
                cmd,
                cwd=repo_root,
                input=instruction,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=_env_float(
                    PROMPT_ENHANCEMENT_TIMEOUT_ENV_VAR,
                    default=DEFAULT_PROMPT_ENHANCEMENT_TIMEOUT_SECONDS,
                ),
                check=False,
            )
        except (FileNotFoundError, subprocess.SubprocessError, OSError) as exc:
            log_file.write(f"\nPrompt enhancement failed, falling back: {exc}\n")
            return None

        if completed.returncode != 0:
            log_file.write(
                f"\nPrompt enhancement exited with status {completed.returncode}; falling back.\n"
            )
            return None

    if not raw_output_path.exists():
        return None
    enhanced_prompt = _prompt_from_enhancement_output(
        raw_output_path.read_text(encoding="utf-8")
    )
    if enhanced_prompt is None:
        return None

    enhanced_prompt_path.write_text(enhanced_prompt + "\n", encoding="utf-8")
    return enhanced_prompt_path


def start_photo_generation(
    *,
    repo_root: Path,
    prompt: str,
    images: list[ReferencePhotoInput] | None = None,
    image_data: str | None = None,
    image_filename: str | None = None,
    image_content_type: str = "application/octet-stream",
) -> PhotoGenerationResult:
    cleaned_prompt = prompt.strip()

    reference_images = list(images or [])
    if image_data is not None:
        reference_images.append(
            ReferencePhotoInput(
                image_data=image_data,
                image_filename=image_filename,
                image_content_type=image_content_type,
            )
        )
    if not reference_images:
        raise ValueError("At least one reference image is required.")
    if len(reference_images) > MAX_REFERENCE_IMAGES:
        raise ValueError(f"Use at most {MAX_REFERENCE_IMAGES} reference images.")

    request_id = datetime.now(UTC).strftime("photo_%Y%m%d_%H%M%S_") + uuid4().hex[:8]
    request_dir = repo_root / "data" / "photo_requests" / request_id
    request_dir.mkdir(parents=True, exist_ok=False)

    image_paths: list[Path] = []
    for index, reference_image in enumerate(reference_images, start=1):
        image_bytes = _decode_image_data(reference_image.image_data)
        extension = _safe_image_extension(
            reference_image.image_content_type,
            reference_image.image_filename,
        )
        image_path = request_dir / f"reference_{index:02d}{extension}"
        image_path.write_bytes(image_bytes)
        image_paths.append(image_path)

    prompt_path = request_dir / "prompt.txt"
    user_prompt_path = request_dir / "user_prompt.txt"
    prompt_memory_path = request_dir / "prompt_memory.txt"
    log_path = request_dir / "generate.log"

    user_prompt_path.write_text(cleaned_prompt + "\n", encoding="utf-8")
    provider = _photo_generation_provider()
    model = _photo_generation_model(provider)
    feedback_memory_text = render_feedback_memory(
        select_relevant_feedback(
            repo_root=repo_root,
            prompt=cleaned_prompt,
            limit=6,
        )
    )
    effective_prompt_memory_path: Path | None = None
    if feedback_memory_text.strip():
        prompt_memory_path.write_text(feedback_memory_text + "\n", encoding="utf-8")
        effective_prompt_memory_path = prompt_memory_path
    enhanced_prompt_path = (
        _enhance_photo_prompt(
            repo_root=repo_root,
            request_dir=request_dir,
            user_prompt=cleaned_prompt,
            image_paths=image_paths,
            model=model,
            feedback_memory_text=feedback_memory_text,
        )
        if provider == "codex-cli"
        else None
    )
    prompt_for_generation = (
        enhanced_prompt_path.read_text(encoding="utf-8").strip()
        if enhanced_prompt_path is not None
        else cleaned_prompt
    )
    if feedback_memory_text.strip() and enhanced_prompt_path is None:
        prompt_for_generation = (
            f"{prompt_for_generation}\n\n"
            "Relevant learned corrections from previous Articraft feedback:\n"
            f"{feedback_memory_text}"
        )
    final_prompt = build_reference_photo_prompt(
        prompt_for_generation,
        image_count=len(image_paths),
    )
    prompt_path.write_text(final_prompt, encoding="utf-8")

    cmd = [
        _python_executable(repo_root),
        "-m",
        "cli.main",
        "generate",
        "--provider",
        provider,
        "--repo-root",
        str(repo_root),
    ]
    for image_path in image_paths:
        cmd.extend(["--image", str(image_path)])
    if model:
        cmd.extend(["--model", model])
    cmd.append(final_prompt)

    with log_path.open("w", encoding="utf-8") as log_file:
        log_file.write("$ " + " ".join(cmd) + "\n\n")
        log_file.flush()
        subprocess.Popen(
            cmd,
            cwd=repo_root,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )

    return PhotoGenerationResult(
        request_id=request_id,
        prompt_path=prompt_path,
        image_path=image_paths[0],
        image_paths=image_paths,
        log_path=log_path,
        enhanced_prompt_path=enhanced_prompt_path,
        prompt_memory_path=effective_prompt_memory_path,
    )
