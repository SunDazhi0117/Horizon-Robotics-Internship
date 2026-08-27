# Codex Plugin Setup

You can use Codex with Articraft even when you do not have provider API keys configured in `.env`. The Codex plugin adds repo-local guidance for creating, checking, curating, and viewing articulated 3D assets.

There are two supported Codex paths:

- **Recommended:** use Articraft's internal `codex-cli` provider. Articraft owns the generation loop, compile feedback, record persistence, turn/tool metadata, and trajectory while Codex supplies model access.
- **Legacy external drafting:** ask Codex to manually author the active `model.py` for an external-agent record. This path follows [EXTERNAL_AGENT_DATA.md](../EXTERNAL_AGENT_DATA.md) and intentionally records `creator.mode=external_agent`, `creator.agent=codex`, and `creator.trace_available=false`.

Use the legacy external path only when you explicitly want Codex to edit `model.py` outside the Articraft harness. For normal no-key generation, prefer `--provider codex-cli`.

## Add The Codex Plugin

This repository includes a repo-local Codex plugin under `plugins/articraft/`.

After completing the Quickstart setup from the repository root:

1. Open this repository in Codex.
2. Restart or reload Codex so it can discover `.agents/plugins/marketplace.json`.
3. In the Codex plugin or marketplace UI, install **Articraft** from **Articraft Local**.
4. Allow Codex to run local repository commands when it creates, checks, compiles, or opens Articraft records.

The plugin itself adds Codex guidance and skills. It does not add Articraft provider credentials. For the recommended no-key path, make sure the local Codex CLI is installed and logged in, then pass an explicit Codex model or set `ARTICRAFT_CODEX_MODEL`.

## Recommended No-Key Generation

From Codex, ask for an Articraft-managed Codex CLI run:

```text
Create a realistic articulated [object name] with Articraft's codex-cli provider and add it to the dataset category [category slug].
```

For example:

```text
Create a realistic articulated microscope with a tilting head, rotating objective turret, adjustable stage, and focus knobs. Use Articraft's codex-cli provider and add it to the microscope dataset category.
```

Codex should run:

```bash
uv run articraft dataset run "<object prompt>" --category-slug <category-slug> --provider codex-cli --model <codex-model-id>
```

For a local workbench draft that is not being added to the dataset, use `generate` instead:

```bash
uv run articraft generate --provider codex-cli --model <codex-model-id> "<object prompt>"
```

You can set the model once and omit `--model` from later commands:

```bash
export ARTICRAFT_CODEX_MODEL=<codex-model-id>
uv run articraft dataset run "<object prompt>" --category-slug <category-slug> --provider codex-cli
```

Codex should create dataset records only when the prompt explicitly asks for a dataset contribution. Workbench records are local drafts.

## Legacy External Drafting

If you want Codex to manually write the record's active `model.py`, prompt it to follow the external-agent contract:

```text
Create a realistic articulated [object name] and add it to the Articraft dataset. Follow EXTERNAL_AGENT_DATA.md.
```

Codex should initialize the record with:

```bash
uv run articraft external init --agent codex --model-id <model-id> --thinking-level <low|med|high|xhigh> "<object prompt>"
```

If the model or thinking level is unknown, Codex should omit those flags rather than guessing. It must edit only the CLI-printed active `model=` path, usually:

```text
data/records/<record_id>/revisions/<revision_id>/model.py
```

During authoring, Codex should run:

```bash
uv run articraft external check data/records/<record_id>
```

Then it should finalize the record:

```bash
uv run articraft external finalize data/records/<record_id>
```

Use `--category-slug <slug>` only when adding the object to the dataset:

```bash
uv run articraft external finalize data/records/<record_id> --category-slug <slug>
```

## Before Opening A PR

Ask Codex to leave you with:

- the generated `record_id`
- whether it used `codex-cli` generation or legacy external drafting
- the category slug used for dataset promotion, if any
- the validation, compile, or finalize command it ran
- any warnings or known limitations

Then inspect the object in the viewer and rate it before committing dataset records. For dataset contributions, rebuild the record index before committing:

```bash
uv run articraft data build-record-index
```
