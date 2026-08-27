"""OpenAI Agents SDK model adapter backed by an authenticated Codex CLI."""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import mimetypes
import os
import subprocess
import tempfile
import uuid

from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from agents import FunctionTool
from agents.agent_output import AgentOutputSchemaBase
from agents.handoffs import Handoff
from agents.items import TResponseStreamEvent
from agents.model_settings import ModelSettings
from agents.models.interface import Model, ModelResponse, ModelTracing
from agents.tool import Tool
from agents.usage import Usage
from openai.types.responses import (
    ResponseFunctionToolCall,
    ResponseOutputMessage,
    ResponseOutputText,
)
from openai.types.responses.response_prompt_param import ResponsePromptParam

console_logger = logging.getLogger(__name__)

_ENVELOPE_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {"type": "string", "enum": ["tool_calls", "final"]},
        "content": {"type": "string"},
        "tool_calls": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "arguments_json": {"type": "string"},
                },
                "required": ["name", "arguments_json"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["action", "content", "tool_calls"],
    "additionalProperties": False,
}


class CodexCLIModel(Model):
    """Run agent turns through Codex CLI while preserving SDK tool execution."""

    def __init__(
        self,
        model: str = "gpt-5.5",
        *,
        reasoning_effort: str = "high",
        timeout_seconds: float = 1800,
    ) -> None:
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.timeout_seconds = timeout_seconds

    async def get_response(
        self,
        system_instructions: str | None,
        input: str | list[Any],
        model_settings: ModelSettings,
        tools: list[Tool],
        output_schema: AgentOutputSchemaBase | None,
        handoffs: list[Handoff],
        tracing: ModelTracing,
        *,
        previous_response_id: str | None,
        conversation_id: str | None,
        prompt: ResponsePromptParam | None,
    ) -> ModelResponse:
        del handoffs, tracing, previous_response_id, conversation_id, prompt

        with tempfile.TemporaryDirectory(
            prefix="scenesmith-codex-", ignore_cleanup_errors=True
        ) as temp_dir_raw:
            temp_dir = Path(temp_dir_raw)
            image_paths: list[Path] = []
            normalized_input = _normalize_payload(input, temp_dir, image_paths)
            request = self._build_request(
                system_instructions=system_instructions,
                input=normalized_input,
                model_settings=model_settings,
                tools=tools,
                output_schema=output_schema,
            )
            payload = await asyncio.to_thread(
                self._run_codex,
                request,
                temp_dir,
                image_paths,
            )

        output: list[Any] = []
        if payload["action"] == "tool_calls":
            valid_tool_names = {
                tool.name for tool in tools if isinstance(tool, FunctionTool)
            }
            for call in payload["tool_calls"]:
                name = str(call["name"])
                if name not in valid_tool_names:
                    raise RuntimeError(
                        f"Codex requested unknown SceneSmith tool '{name}'. "
                        f"Available tools: {sorted(valid_tool_names)}"
                    )
                try:
                    arguments = json.loads(call["arguments_json"])
                except (TypeError, json.JSONDecodeError) as exc:
                    raise RuntimeError(
                        f"Codex returned invalid arguments for tool '{name}'"
                    ) from exc
                if not isinstance(arguments, dict):
                    raise RuntimeError(
                        f"Codex returned non-object arguments for tool '{name}'"
                    )
                output.append(
                    ResponseFunctionToolCall(
                        arguments=json.dumps(arguments, ensure_ascii=False),
                        call_id=f"call_{uuid.uuid4().hex}",
                        name=name,
                        type="function_call",
                        status="completed",
                    )
                )
        else:
            output.append(
                ResponseOutputMessage(
                    id=f"msg_{uuid.uuid4().hex}",
                    content=[
                        ResponseOutputText(
                            annotations=[],
                            text=payload["content"],
                            type="output_text",
                        )
                    ],
                    role="assistant",
                    status="completed",
                    type="message",
                )
            )

        return ModelResponse(
            output=output,
            usage=Usage(requests=1),
            response_id=None,
        )

    async def stream_response(
        self,
        system_instructions: str | None,
        input: str | list[Any],
        model_settings: ModelSettings,
        tools: list[Tool],
        output_schema: AgentOutputSchemaBase | None,
        handoffs: list[Handoff],
        tracing: ModelTracing,
        *,
        previous_response_id: str | None,
        conversation_id: str | None,
        prompt: ResponsePromptParam | None,
    ) -> AsyncIterator[TResponseStreamEvent]:
        del (
            system_instructions,
            input,
            model_settings,
            tools,
            output_schema,
            handoffs,
            tracing,
            previous_response_id,
            conversation_id,
            prompt,
        )
        raise NotImplementedError("CodexCLIModel does not support streaming")
        yield  # pragma: no cover

    def _build_request(
        self,
        *,
        system_instructions: str | None,
        input: Any,
        model_settings: ModelSettings,
        tools: list[Tool],
        output_schema: AgentOutputSchemaBase | None,
    ) -> str:
        function_tools = [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.params_json_schema,
            }
            for tool in tools
            if isinstance(tool, FunctionTool)
        ]
        final_output = (
            {
                "type": "json",
                "name": output_schema.name(),
                "schema": output_schema.json_schema(),
            }
            if output_schema is not None and not output_schema.is_plain_text()
            else {"type": "text"}
        )

        return (
            "You are the language model inside a SceneSmith agent loop. "
            "Follow the system instructions and conversation exactly. "
            "SceneSmith, not you, executes tools.\n\n"
            "Return one JSON envelope matching the provided output schema. "
            "To use tools, set action='tool_calls', content='', and include one or "
            "more calls with exact tool names and arguments_json containing a "
            "JSON-encoded argument object. To finish, set "
            "action='final', tool_calls=[], and put the final response in content. "
            "When final_output.type is 'json', content must itself be a JSON string "
            "matching final_output.schema. Never invent tool results.\n\n"
            f"SYSTEM INSTRUCTIONS:\n{system_instructions or ''}\n\n"
            f"MODEL SETTINGS:\n{_json_dump({'tool_choice': model_settings.tool_choice, 'parallel_tool_calls': model_settings.parallel_tool_calls})}\n\n"
            f"AVAILABLE TOOLS:\n{_json_dump(function_tools)}\n\n"
            f"FINAL OUTPUT REQUIREMENT:\n{_json_dump(final_output)}\n\n"
            f"CONVERSATION INPUT:\n{_json_dump(input)}"
        )

    def _run_codex(
        self,
        request: str,
        temp_dir: Path,
        image_paths: list[Path],
    ) -> dict[str, Any]:
        schema_path = temp_dir / "response.schema.json"
        result_path = temp_dir / "response.json"
        schema_path.write_text(json.dumps(_ENVELOPE_SCHEMA), encoding="utf-8")

        command = [
            "codex",
            "exec",
            "--ephemeral",
            "--ignore-user-config",
            "--skip-git-repo-check",
            "--sandbox",
            "read-only",
            "--model",
            self.model,
            "--config",
            f'model_reasoning_effort="{self.reasoning_effort}"',
            "--output-schema",
            str(schema_path),
            "--output-last-message",
            str(result_path),
            "--cd",
            str(temp_dir),
        ]
        for image_path in image_paths:
            command.extend(["--image", str(image_path)])
        command.append("-")

        env = os.environ.copy()
        env.pop("OPENAI_API_KEY", None)
        env.pop("OPENAI_API_KEYS", None)
        source_codex_home = Path(
            os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))
        )
        isolated_codex_home = temp_dir / "codex-home"
        isolated_codex_home.mkdir()
        auth_file = source_codex_home / "auth.json"
        if not auth_file.is_file():
            raise RuntimeError(f"Codex authentication not found: {auth_file}")
        (isolated_codex_home / "auth.json").symlink_to(auth_file)
        env["CODEX_HOME"] = str(isolated_codex_home)
        completed = subprocess.run(
            command,
            input=request,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=env,
            timeout=self.timeout_seconds,
            check=False,
        )
        if completed.returncode != 0 or not result_path.exists():
            log_tail = completed.stdout[-6000:]
            raise RuntimeError(
                f"Codex CLI model call failed with status {completed.returncode}:\n"
                f"{log_tail}"
            )

        try:
            payload = json.loads(result_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError("Codex CLI returned an invalid model envelope") from exc
        if payload.get("action") == "tool_calls" and not payload.get("tool_calls"):
            raise RuntimeError("Codex CLI selected tool_calls without any calls")
        return payload


def codex_cli_completion(
    messages: list[dict[str, Any]],
    *,
    model: str = "gpt-5.5",
    reasoning_effort: str = "high",
    require_json: bool = False,
) -> str:
    """Run a synchronous text or vision completion through Codex CLI."""

    adapter = CodexCLIModel(
        model=model,
        reasoning_effort=reasoning_effort,
    )
    with tempfile.TemporaryDirectory(prefix="scenesmith-codex-vlm-") as temp_dir_raw:
        temp_dir = Path(temp_dir_raw)
        image_paths: list[Path] = []
        normalized_messages = _normalize_payload(messages, temp_dir, image_paths)
        output_requirement = (
            "Return a valid JSON object as the content string."
            if require_json
            else "Return the requested answer as the content string."
        )
        request = (
            "You are the vision-language analysis service inside SceneSmith. "
            "Analyze the supplied conversation and attached images carefully. "
            f"{output_requirement} Return action='final' and tool_calls=[].\n\n"
            f"CONVERSATION:\n{_json_dump(normalized_messages)}"
        )
        payload = adapter._run_codex(request, temp_dir, image_paths)

    if payload.get("action") != "final":
        raise RuntimeError("Codex VLM completion returned a non-final action")
    content = str(payload.get("content", "")).strip()
    if not content:
        raise RuntimeError("Codex VLM completion returned empty content")
    if require_json:
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Codex VLM completion returned invalid JSON") from exc
        if not isinstance(parsed, dict):
            raise RuntimeError("Codex VLM completion must return a JSON object")
    return content


def model_from_config(openai_config: Any) -> str | CodexCLIModel:
    """Resolve a normal OpenAI model name or a Codex CLI model adapter."""

    provider = str(openai_config.get("provider", "openai"))
    if provider != "codex-cli":
        return str(openai_config.model)
    return CodexCLIModel(
        model=str(openai_config.get("codex_cli_model", "gpt-5.5")),
        reasoning_effort=str(openai_config.get("codex_cli_reasoning_effort", "high")),
    )


def _normalize_payload(
    value: Any,
    temp_dir: Path,
    image_paths: list[Path],
) -> Any:
    if hasattr(value, "model_dump"):
        value = value.model_dump(exclude_none=True)
    if isinstance(value, dict):
        normalized = {
            str(key): _normalize_payload(item, temp_dir, image_paths)
            for key, item in value.items()
        }
        image_url = normalized.get("image_url")
        if isinstance(image_url, str) and image_url.startswith("data:image/"):
            image_path = _write_data_image(image_url, temp_dir, len(image_paths))
            image_paths.append(image_path)
            normalized["image_url"] = f"[attached image: {image_path.name}]"
        elif isinstance(image_url, dict):
            url = image_url.get("url")
            if isinstance(url, str) and url.startswith("data:image/"):
                image_path = _write_data_image(url, temp_dir, len(image_paths))
                image_paths.append(image_path)
                image_url["url"] = f"[attached image: {image_path.name}]"
        return normalized
    if isinstance(value, (list, tuple)):
        return [_normalize_payload(item, temp_dir, image_paths) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _write_data_image(data_url: str, temp_dir: Path, index: int) -> Path:
    header, encoded = data_url.split(",", 1)
    mime_type = header.split(";", 1)[0].removeprefix("data:")
    extension = mimetypes.guess_extension(mime_type) or ".png"
    image_path = temp_dir / f"observation_{index:03d}{extension}"
    image_path.write_bytes(base64.b64decode(encoded))
    return image_path


def _json_dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, default=str)
