# ADK Starter Kit Customizations

Fork of [GoogleCloudPlatform/agent-starter-pack](https://github.com/GoogleCloudPlatform/agent-starter-pack) with XybOrg factory extensions.

**Repo:** `github.com/democodex/factory` (origin) | `github.com/GoogleCloudPlatform/agent-starter-pack` (upstream)

---

## Design Principle

**Do not modify core starter pack files.** Custom agent templates use auto-discovery (`agents/` directory) and built-in extension points (`commands.override`, `commands.extra`) to inject all XybOrg-specific behavior. This keeps upstream merges clean.

Three core files have minimal modifications (detailed below). Everything else is additive.

---

## Core File Modifications (3 files)

These are the only upstream files we've changed. Each diff is small and isolated.

### 1. `agent_starter_pack/base_templates/python/Makefile` (+9 lines)

Added `commands.override` hooks for `deploy` and `test` targets, matching the existing `install` and `playground` override patterns already in upstream:

```jinja2
{# deploy override (lines 266-269) #}
{%- if cookiecutter.settings.get("commands", {}).get("override", {}).get("deploy") %}
deploy:
	{{cookiecutter.settings.get("commands", {}).get("override", {}).get("deploy")}}
{%- else %}
{# ... standard deploy logic unchanged ... #}
{%- endif %}  {# closing endif at line 337 #}

{# test override (lines 413-416) #}
{%- if cookiecutter.settings.get("commands", {}).get("override", {}).get("test") %}
	{{cookiecutter.settings.get("commands", {}).get("override", {}).get("test")}}
{%- else %}
	uv run pytest tests/unit && uv run pytest tests/integration
{%- endif %}
```

**Why:** The upstream Makefile only had override hooks for `install` and `playground`. We need the same pattern for `deploy` (factory deployment system) and `test` (monorepo PYTHONPATH). Templates that don't use these overrides get standard behavior unchanged.

### 2. `agent_starter_pack/base_templates/python/pyproject.toml` (+2 lines)

```toml
[tool.pytest.ini_options]
pythonpath = [".", "../.."]   # was "." — added monorepo root for config.secrets
asyncio_mode = "auto"         # added — enables async test fixtures
```

**Why:** XybOrg agents import `config.secrets` and `common.*` from the monorepo root. Tests need `../..` on the Python path. `asyncio_mode = "auto"` is needed for async tool/service tests.

### 3. `pyproject.toml` (root, 1 line)

```toml
[project.scripts]
xyborg-agent = "agent_starter_pack.cli.main:cli"  # was agent-starter-pack
```

**Why:** Branded CLI command for the XybOrg fork.

---

## Custom Agent Templates (additive, no core changes)

The starter pack auto-discovers templates in `agents/` directories containing `.template/templateconfig.yaml`. Our two custom templates are invisible to upstream.

### `agents/xyborg/` — Standard XybOrg Agent

Production-ready agent with secrets, plugins, sessions, background tasks, and factory deployment.

```
agents/xyborg/
├── .template/
│   └── templateconfig.yaml    # Auto-discovery config + Makefile commands
└── app/
    ├── __init__.py             # Exports app
    ├── agent.py                # Pure composition — Agent + App wiring
    ├── bootstrap.py            # Infrastructure wiring (plugins, callbacks, task service)
    ├── settings.py             # config.secrets loader + DEFAULT_MODEL
    ├── plugins.py              # EventPlugin + SlackNotificationPlugin (env-configurable)
    ├── prompts.py              # ROOT_AGENT_INSTRUCTION template
    ├── tools/__init__.py       # Scaffold for domain tools
    └── sub_agents/__init__.py  # Scaffold for sub-agents
```

### `agents/xyborg_a2a/` — XybOrg Agent with A2A Protocol

Identical `app/` files as `xyborg`. Differences are in `templateconfig.yaml`:
- Extra dependencies: `a2a-sdk~=0.3.9`, `nest-asyncio>=1.6.0,<2.0.0`
- Tags: `["adk", "a2a"]` (triggers A2A code paths in `agent_engine_app.py` deployment overlay)

### Template File Details

| File | Purpose |
|------|---------|
| `agent.py` | Imports `bootstrap()` for infrastructure, composes `Agent` + `App`. Tools: `get_task_status`, `list_active_tasks`, `call_remote_agent` |
| `bootstrap.py` | Calls `get_plugins()`, initializes `get_background_task_service()`, returns `(plugins, before_agent_callback, before_model_callback)` |
| `settings.py` | Imports `config.secrets` (auto-loads `.env` + Google Secret Manager), exports `DEFAULT_MODEL` with env fallback |
| `plugins.py` | `CloudLoggingEventStreamingPlugin` + optional `SlackNotificationPlugin`. Configurable via env vars |
| `prompts.py` | `ROOT_AGENT_INSTRUCTION` — placeholder for domain-specific instructions |

### Customization After Creation

| What | How |
|------|-----|
| Agent instructions | Edit `prompts.py` |
| Add domain tools | Add to `tools/`, import in `agent.py` tools list |
| Add sub-agents | Add to `sub_agents/`, wire in `agent.py` |
| Slack channels | Set `SLACK_SUCCESS_CHANNEL` / `SLACK_ERROR_CHANNEL` env vars |
| Disable Slack | Set `ENABLE_SLACK_PLUGIN=false` |
| Change model | Set `DEFAULT_MODEL` env var |
| Task notifications | Uncomment `register_behavior()` in `bootstrap.py` |

---

## Custom Makefile Targets

Injected via `templateconfig.yaml` using two mechanisms:

- **`commands.override`** — Replaces existing base targets
- **`commands.extra`** — Adds new targets under "Agent-Specific Commands" section

| Target | Mechanism | Description |
|--------|-----------|-------------|
| `deploy` | override | Factory deployment via `scripts.deployment.cli` |
| `playground` | override | ADK web with monorepo PYTHONPATH |
| `test` | override | pytest with monorepo PYTHONPATH |
| `run` | extra | Run agent locally via `adk run` |
| `analyze` | extra | Analyze internal/external dependencies |
| `prepare` | extra | Prepare deployment bundle |
| `deploy-verbose` | extra | Full deployment with detailed logging |
| `logs` | extra | Fetch recent 50 logs via `gcloud logging read` |
| `logs-stream` | extra | Stream live logs via `gcloud alpha logging tail` |
| `status` | extra | Show `deployment_metadata.json` |
| `clean` | extra | Remove caches and build artifacts |
| `export-requirements` | extra | Export deps to `.requirements.txt` |

**Note on cookiecutter variables:** YAML string values in `commands.extra`/`commands.override` are injected as plain text — Jinja2 does not render `{{cookiecutter.*}}` inside them. All commands use runtime `awk` parsing from `pyproject.toml` instead:

```bash
AGENT_DIR=$$(awk -F'"' '/^agent_directory =/{print $$2}' pyproject.toml)
PROJECT_NAME=$$(awk -F'"' '/^name =/{print $$2}' pyproject.toml)
```

---

## Lock Files

Each template + deployment target combination requires a lock file in `resources/locks/`:

- `uv-xyborg-agent_engine.lock`
- `uv-xyborg_a2a-agent_engine.lock`

Generated by:

```bash
cd scripts/factory
uv run python -m agent_starter_pack.utils.generate_locks
```

Re-run after changing `extra_dependencies` in any `templateconfig.yaml`.

---

## Template Composition Order

When `xyborg-agent create` runs, files are layered in this order (later layers override earlier):

1. `base_templates/python/` — Makefile, pyproject.toml, app_utils/, tests/
2. `deployment_targets/agent_engine/` — agent_engine_app.py, deploy.py, telemetry.py
3. `agents/{template}/app/` — agent.py, bootstrap.py, settings.py, plugins.py, prompts.py

Cookiecutter then renders all `{{cookiecutter.*}}` variables across the merged result.

---

## Syncing with Upstream

### Fetch and merge upstream changes

```bash
cd scripts/factory

# Fetch latest upstream
git fetch upstream

# Merge (prefer merge over rebase to preserve our commit history)
git merge upstream/main

# Resolve conflicts if any — typically only in:
#   agent_starter_pack/base_templates/python/Makefile (our 9-line diff)
#   agent_starter_pack/base_templates/python/pyproject.toml (our 2-line diff)
#   pyproject.toml (our 1-line CLI rename)

# Regenerate lock files (upstream dependency changes)
uv run python -m agent_starter_pack.utils.generate_locks

# Test
printf '1\nus-central1\n' | uv run xyborg-agent create test_merge --agent xyborg --output-dir /tmp
rm -rf /tmp/test-merge

# Push
git push origin main
```

### What's safe during upstream merges

| Component | Risk | Notes |
|-----------|------|-------|
| `agents/xyborg/`, `agents/xyborg_a2a/` | None | Upstream never touches these |
| `resources/locks/uv-xyborg*.lock` | None | Our files, not upstream |
| `base_templates/python/Makefile` | Low | Our 9 lines follow existing patterns; conflicts are simple to resolve |
| `base_templates/python/pyproject.toml` | Low | 2 lines in `[tool.pytest.ini_options]` |
| Root `pyproject.toml` | Low | 1 line in `[project.scripts]` |
| Lock files for upstream templates | Auto | Re-run `generate_locks` after merge |

### After pushing the submodule

Update the parent repo's submodule pointer:

```bash
cd /path/to/xyborg
git add scripts/factory
git commit -m "Update factory submodule"
```

---

## CLI Setup

The `xyborg-agent` command requires a shell alias to use the local fork:

```bash
# In ~/.zshrc
alias xyborg-agent='uvx --from /Users/democodex/code/xyborg/scripts/factory xyborg-agent'
```

Without this, `uvx xyborg-agent` would try to install from PyPI.

---

## Deployment Architecture

### Factory Deployment (XybOrg templates)

```
make deploy
  → scripts/deployment/cli deploy $PROJECT_NAME $AGENT_DIR
    → Analyze internal deps (common/config modules)
    → Analyze external deps (PyPI packages)
    → Update pyproject.toml if needed
    → Create staging bundle with selective dep copying
    → Auto-detect required env vars
    → Export requirements
    → Deploy to Vertex AI Agent Engine
```

### Standard Deployment (upstream templates)

```
make deploy
  → uv export → .requirements.txt
  → uv run app.app_utils.deploy
  → Direct deployment to Vertex AI
```

Templates without `commands.override.deploy` get standard deployment unchanged.

---

## File Change Summary

| File | Type | Lines Changed |
|------|------|---------------|
| `agent_starter_pack/base_templates/python/Makefile` | Modified | +9 (deploy + test override hooks) |
| `agent_starter_pack/base_templates/python/pyproject.toml` | Modified | +2 (pythonpath, asyncio_mode) |
| `pyproject.toml` | Modified | 1 (CLI rename) |
| `agents/xyborg/` | Added | 9 files (template) |
| `agents/xyborg_a2a/` | Added | 9 files (template) |
| `resources/locks/uv-xyborg-agent_engine.lock` | Added | Generated |
| `resources/locks/uv-xyborg_a2a-agent_engine.lock` | Added | Generated |

**Last Updated:** 2026-03-13
