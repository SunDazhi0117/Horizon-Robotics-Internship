# SceneSmith Codex Guide

## Environment

- Use Python 3.11 through the repository's `uv` environment.
- Install dependencies with `uv sync --no-dev`.
- Never commit API keys. For local runs, `scripts/run_simple_scene.sh` loads
  `OPENAI_API_KEY` from the environment or from a separate env file.
- SceneSmith uses the OpenAI Agents SDK. Codex CLI login credentials are not an
  OpenAI API key and cannot be passed directly to the SDK.

## First Verification

Run the lightweight floor-plan smoke test before downloading 3D asset datasets:

```bash
scripts/run_simple_scene.sh
```

This generates one simple room and stops after the `floor_plan` stage. It does
not require SAM3D, HSSD, ArtVIP, Objaverse, or AmbientCG data.

## Full Generation

The full pipeline requires the datasets and checkpoints documented in
`README.md`. Do not start a full generation unless those inputs exist.

## Checks

```bash
uv run pytest tests/unit -x
uv run python main.py --cfg job +name=config_check
```

