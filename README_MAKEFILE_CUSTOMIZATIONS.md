# Makefile Customizations for Factory Deployment System

This document details all modifications made to the agent-starter-pack library templates to support the XybOrg factory deployment system.

## Overview

The XybOrg factory uses a centralized deployment orchestration system (`factory_deployment_agent.py`) that:
- Analyzes both internal (common/config) and external (PyPI) dependencies
- Automatically updates `pyproject.toml` with missing packages
- Creates staging bundles with selective dependency copying
- Auto-detects and passes required environment variables based on integrations

**Factory deployment is now the DEFAULT behavior.** The Makefile template generates factory deployment targets unless explicitly disabled with `use_original_deployment: true`.

---

## Modified Files

### 1. `agent_starter_pack/base_template/Makefile`

**Location:** Lines 231-297
**Section:** Backend Deployment Targets

### 2. `pyproject.toml`

**Location:** Line 119
**Section:** Project Scripts

#### Change Made

Renamed the CLI entry point from `agent-starter-pack` to `xyborg-agent`:

```toml
[project.scripts]
xyborg-agent = "agent_starter_pack.cli.main:cli"
```

This allows the command to be branded specifically for the XybOrg factory fork.

### 3. `~/.zshrc`

**Location:** Shell configuration file (user home directory)
**Section:** Aliases (appended to end of file)

#### Change Made

Added shell alias to always use the local modified template:

```bash
alias xyborg-agent='uvx --from /Users/democodex/code/xyborg/scripts/factory xyborg-agent'
```

**Why this is needed:** Without the alias, `uvx xyborg-agent` would try to fetch from PyPI. The alias ensures the local fork at `/Users/democodex/code/xyborg/scripts/factory` is always used, which includes the factory deployment modifications.

**To activate:** Run `source ~/.zshrc` or open a new terminal.

---

### Summary of File Changes

| File | Lines Changed | Purpose |
|------|---------------|---------|
| `agent_starter_pack/base_template/Makefile` | ~67 lines (231-297) | Enable factory deployment by default |
| `pyproject.toml` | 1 line (119) | Rename CLI command to `xyborg-agent` |
| `~/.zshrc` | 1 line (appended) | Alias to use local modified template |

#### Changes Made (Makefile)

Added conditional logic that checks for `cookiecutter.settings.get("use_original_deployment")` flag:

**DEFAULT (when `use_original_deployment` is not set or false):**
- Uses factory deployment agent (the new default)
- Includes four Make targets:
  - `analyze`: Analyzes dependencies only
  - `prepare`: Analyzes, updates TOML, creates staging bundle
  - `deploy`: Full deployment pipeline (analyze → prepare → deploy)
  - `deploy-verbose`: Same as deploy with verbose logging
- All targets delegate to `scripts.deployment.cli`
- Targets navigate to project root before executing

**When `use_original_deployment: true`:**
- Uses standard agent-starter-pack deployment (original behavior)
- Supports both `cloud_run` and `agent_engine` deployment targets
- Backward compatible for agents that need the original deployment flow

#### Modified Code Block (Makefile)

```jinja2
# ==============================================================================
# Backend Deployment Targets{% if not cookiecutter.settings.get("use_original_deployment") %} (Delegated to Factory Deployment Agent){% endif %}
# ==============================================================================

{% if not cookiecutter.settings.get("use_original_deployment") -%}
# Analyze dependencies (internal common/config + external PyPI packages)
analyze:
	@PROJECT_ROOT=$$(git rev-parse --show-toplevel 2>/dev/null || echo "../..") && \
	cd $$PROJECT_ROOT && \
	uv run python -m scripts.deployment.cli analyze {{cookiecutter.project_name}}

# Prepare deployment (analyze deps, update toml with confirmation, create staging)
prepare:
	@PROJECT_ROOT=$$(git rev-parse --show-toplevel 2>/dev/null || echo "../..") && \
	cd $$PROJECT_ROOT && \
	uv run python -m scripts.deployment.cli prepare {{cookiecutter.project_name}}

# Full deployment (analyze + prepare + deploy to Vertex AI)
deploy:
	@PROJECT_ROOT=$$(git rev-parse --show-toplevel 2>/dev/null || echo "../..") && \
	cd $$PROJECT_ROOT && \
	uv run python -m scripts.deployment.cli deploy {{cookiecutter.project_name}} --yes

# Verbose deployment with detailed logging
deploy-verbose:
	@PROJECT_ROOT=$$(git rev-parse --show-toplevel 2>/dev/null || echo "../..") && \
	cd $$PROJECT_ROOT && \
	uv run python -m scripts.deployment.cli deploy {{cookiecutter.project_name}} --yes --verbose

{%- else -%}
# [Standard deployment logic remains unchanged]
{%- endif %}

# Alias for 'make deploy' for backward compatibility
backend: deploy
```

---

## How to Use

### Factory Deployment (DEFAULT)

**Factory deployment is now the default.** Simply run:

```bash
cd /path/to/xyborg/factory
xyborg-agent create
```

All generated agents will use factory deployment automatically.

### Original Deployment (Opt-in)

If you need the original agent-starter-pack deployment for a specific agent, add this to `.template/templateconfig.yaml`:

```yaml
name: "your-agent"
description: "Your agent description"
example_question: "What can you help me with?"

settings:
  deployment_targets:
    - agent_engine
  agent_directory: "app"
  use_original_deployment: true  # ← Use original deployment instead of factory

tags:
  - adk
```

### Generated Makefile Targets

**Default (Factory Deployment):**

```makefile
# Analyze dependencies
make analyze

# Prepare deployment bundle
make prepare

# Full deployment
make deploy

# Verbose deployment
make deploy-verbose

# Backward compatibility alias
make backend
```

**With `use_original_deployment: true`:**

```makefile
# Standard deployment (exports deps, runs deploy.py)
make deploy

# Backward compatibility alias
make backend
```

---

## Architecture Comparison

### Standard Agent-Starter-Pack Deployment

```
make deploy
  ↓
  1. uv export → .requirements.txt
  2. uv run app.app_utils.deploy
  3. Direct deployment to Vertex AI
```

### Factory Deployment System

```
make deploy
  ↓
  1. Navigate to project root
  2. Run factory_deployment_agent.py
     ↓
     a. Analyze internal deps (common/config modules)
     b. Analyze external deps (PyPI packages)
     c. Check pyproject.toml for missing packages
     d. Update pyproject.toml (with confirmation)
     e. Create staging bundle
     f. Copy selective dependencies
     g. Auto-detect required env vars
     h. Export requirements
     i. Deploy to Vertex AI
```

---

## Benefits of This Approach

1. **No Core Library Breakage**: Standard agent-starter-pack functionality remains intact
2. **Backward Compatible**: Existing agents without the flag continue working normally
3. **Clean Separation**: Factory-specific logic stays in your project, not upstream
4. **Easy Maintenance**: Only the Makefile template needs updates when agent-starter-pack changes
5. **Flexible**: Can switch deployment systems per-agent by toggling the flag

---

## Testing

To verify the modifications work correctly:

```bash
# Test with factory deployment enabled
cd /path/to/xyborg/factory
xyborg-agent create

# When prompted:
# - Select an agent template
# - Factory deployment is now the default (no config changes needed)
# - Check the generated Makefile has analyze/prepare/deploy/deploy-verbose targets

# Test deployment
cd generated-agent
make analyze    # Should call factory_deployment_agent.py
make prepare    # Should create staging bundle
make deploy     # Should run full deployment pipeline
```

---

## Rollback Plan

If issues arise, you can revert by:

1. Restore the original Makefile template from git:
   ```bash
   cd scripts/factory
   git checkout HEAD -- agent_starter_pack/base_template/Makefile
   ```

2. Remove the `use_factory_deployment` flag from agent templates

3. Existing deployed agents continue working unchanged

---

## Future Enhancements

Potential improvements to consider:

1. **Add `make status`**: Check deployment status and show current version
2. **Add `make rollback`**: Rollback to previous deployment
3. **Add `make logs`**: Stream logs from deployed agent
4. **Add `make test-remote`**: Run integration tests against deployed agent
5. **Environment-specific deployments**: Support dev/staging/prod environments
6. **Dry-run mode**: Preview deployment changes without executing

---

## Maintenance Notes

### When Updating Agent-Starter-Pack

If you pull upstream changes from agent-starter-pack:

1. Check if `base_template/Makefile` has conflicts
2. Ensure the conditional logic around lines 231-297 is preserved
3. Test with both `use_factory_deployment: true` and `false`
4. Update this document if new deployment features are added

### Adding New Factory Targets

To add new deployment targets (e.g., `make validate`):

1. Add the target inside the `{% if cookiecutter.settings.get("use_factory_deployment") -%}` block
2. Follow the same pattern: navigate to project root, call factory_deployment_agent
3. Update this document with the new target

---

## Questions or Issues?

If you encounter problems with these customizations:

1. Check that `use_factory_deployment: true` is set in your template config
2. Verify `scripts/deployment/make/factory_deployment_agent.py` exists and is executable
3. Ensure you're running from within a git repository (for `git rev-parse --show-toplevel`)
4. Check the factory deployment agent logs for detailed error messages

For standard agent-starter-pack issues (without factory deployment), refer to the official documentation:
https://googlecloudplatform.github.io/agent-starter-pack/

---

## Deployment Configuration Tracking

### Overview

The factory deployment system tracks deployment configuration in `deployment_metadata.json` by enhancing the metadata file after successful deployment.

### Architecture

```
deploy.py (Google's template)
  ↓ Writes basic metadata
  {
    "remote_agent_engine_id": "...",
    "deployment_target": "agent_engine",
    "is_a2a": false,
    "deployment_timestamp": "..."
  }

factory_deployment_agent.py
  ↓ Enhances with factory config
  {
    ... (original metadata) ...,
    "factory_deployment": {
      "deployed_by": "factory_deployment_agent",
      "version": "1.0",
      "config": { ... },
      "dependencies": { ... },
      "environment": { ... },
      "staging": { ... }
    }
  }
```

### Enhanced Metadata Structure

**`factory_deployment.config`** - Deployment resource configuration:
- `display_name`: Agent display name
- `description`: Agent description
- `cpu`: CPU limit (e.g., "4")
- `memory`: Memory limit (e.g., "8Gi")
- `min_instances`: Minimum instances
- `max_instances`: Maximum instances
- `container_concurrency`: Container concurrency setting
- `num_workers`: Number of worker processes
- `labels`: Key-value labels applied to agent

**`factory_deployment.dependencies`** - Dependency tracking:
- `internal_modules`: Count of internal modules bundled
- `internal_packages`: List of internal packages (common, config)
- `external_packages`: Count of external PyPI packages

**`factory_deployment.environment`** - Environment variable tracking:
- `variables_passed`: Count of env vars passed
- `variable_keys`: List of env var names (not values, for security)

**`factory_deployment.staging`** - Staging information:
- `location`: Path to staging directory
- `bundle_created`: Whether staging bundle was successfully created

### Example Enhanced Metadata

```json
{
  "remote_agent_engine_id": "projects/1043474131598/locations/us-central1/reasoningEngines/6944701258498310144",
  "deployment_target": "agent_engine",
  "is_a2a": false,
  "deployment_timestamp": "2026-01-02T16:30:45.123456",
  "factory_deployment": {
    "deployed_by": "factory_deployment_agent",
    "version": "1.0",
    "config": {
      "display_name": "sales",
      "description": "Factory-deployed sales agent",
      "cpu": "4",
      "memory": "8Gi",
      "min_instances": 1,
      "max_instances": 10,
      "container_concurrency": 9,
      "num_workers": 1,
      "labels": {
        "managed_by": "factory",
        "agent": "sales"
      }
    },
    "dependencies": {
      "internal_modules": 11,
      "internal_packages": ["common"],
      "external_packages": 12
    },
    "environment": {
      "variables_passed": 8,
      "variable_keys": [
        "HUBSPOT_ACCESS_TOKEN",
        "GOOGLE_CLOUD_PROJECT",
        "GOOGLE_CLOUD_REGION"
      ]
    },
    "staging": {
      "location": "/path/to/staging/sales",
      "bundle_created": true
    }
  }
}
```

### Benefits

1. **Audit Trail**: Track what configuration was used for each deployment
2. **Reproducibility**: Know exactly how an agent was deployed
3. **Debugging**: See what dependencies and env vars were included
4. **Configuration Drift Detection**: Compare current vs. previous deployments
5. **Team Visibility**: Everyone can see deployment settings

### Implementation Details

- **Method**: `factory_deployment_agent._enhance_deployment_metadata()`
- **File**: `scripts/deployment/make/factory_deployment_agent.py`
- **Called**: After successful deployment
- **Template Changes**: None required - `deploy.py` template remains unchanged
- **Compatibility**: Direct `deploy.py` calls still work (without enhancement)

---

## Quick Start

To create an agent with factory deployment (now the default):

```bash
cd /path/to/xyborg/factory
xyborg-agent create
```

That's it! Your agent will automatically use factory deployment with these targets:
- `make analyze` - Analyze dependencies
- `make prepare` - Prepare deployment bundle
- `make deploy` - Full deployment
- `make deploy-verbose` - Verbose deployment

### Setup

The `xyborg-agent` command is aliased in your shell configuration (`~/.zshrc`):

```bash
alias xyborg-agent='uvx --from /Users/democodex/code/xyborg/scripts/factory xyborg-agent'
```

This ensures you're always using your locally modified template with factory deployment enabled.

**Note:** The CLI entry point was renamed from `agent-starter-pack` to `xyborg-agent` in `pyproject.toml` line 119.

---

**Last Updated:** 2026-01-02
**Modified Files:** 3
- `agent_starter_pack/base_template/Makefile` (~67 lines - inverted conditional logic)
- `pyproject.toml` (line 119 - CLI entry point renamed to `xyborg-agent`)
- `~/.zshrc` (1 line - alias added for easy command access)

**Breaking Changes:** None (100% backward compatible)
