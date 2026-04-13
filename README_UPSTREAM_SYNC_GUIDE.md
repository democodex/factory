# Upstream Sync Guide

How to merge changes from the upstream Google ADK Agent Starter Pack into
our fork without breaking XybOrg customizations.

**Upstream:** https://github.com/GoogleCloudPlatform/agent-starter-pack
**Our fork:** https://github.com/democodex/factory
**Submodule path:** `scripts/factory/` in the xyborg monorepo

---

## Core Principle

> **All merges from upstream MUST happen locally first.**
> Local = decision point. GitHub fork = storage/output only.

```
Upstream (Google)
       |
    fetch
       |
  Local Repo  <-- pull <-- Origin (your fork)
       |
    merge (decide here)
       |
    push
       |
  Origin (your fork)
```

---

## Repo Roles

| Repo | URL | Role |
|------|-----|------|
| **Upstream** | `GoogleCloudPlatform/agent-starter-pack` | Source of truth (Google) |
| **Origin** | `democodex/factory` | Our persistent fork on GitHub |
| **Local** | `scripts/factory/` | The ONLY place merges and conflict resolution happen |

---

## 1. Repository Setup

The fork should have two remotes configured:

```bash
cd scripts/factory
git remote -v
# origin   https://github.com/democodex/factory (our fork)
# upstream https://github.com/GoogleCloudPlatform/agent-starter-pack (source)
```

If `upstream` is missing:

```bash
git remote add upstream https://github.com/GoogleCloudPlatform/agent-starter-pack.git
```

---

## 2. Full Sync Workflow

### Step 0 -- Preflight (clean state)

```bash
cd scripts/factory
git status
```

Must be clean. If not: commit or stash before proceeding.

### Step 1 -- Fetch upstream (Google -> Local)

```bash
git fetch upstream
```

Downloads latest upstream commits. Does NOT modify your code.

### Step 2 -- Sync local with your fork (Origin -> Local)

```bash
git checkout main
git pull origin main
```

Ensures your local repo reflects your latest work from your fork.

### Step 3 -- Inspect incoming changes

```bash
# How far behind are we?
echo "Behind: $(git rev-list --count HEAD..upstream/main) commits"

# What's coming in?
git log HEAD..upstream/main --oneline
git diff HEAD..upstream/main --stat
```

### Step 4 -- Guardrail check (protected files)

```bash
git diff HEAD..upstream/main --name-only | grep -E \
  'expose_app\.py|agent_engine_app\.py|Makefile|pyproject\.toml'
```

**If output is NOT empty:** Upstream touched files we override. This is a
HIGH RISK merge requiring careful line-by-line review. See Section 3 for
per-file resolution recipes.

**Optional enforcement (recommended for scripts):**

```bash
CHANGED=$(git diff HEAD..upstream/main --name-only | \
  grep -E 'expose_app\.py|agent_engine_app\.py')

if [ -n "$CHANGED" ]; then
  echo "WARNING: Upstream modified protected files:"
  echo "$CHANGED"
  echo "Manual review required before merging."
fi
```

### Step 5 -- Dry-run merge (preview only)

```bash
git merge --no-commit --no-ff upstream/main
git diff --cached --name-only   # files that will change
git diff --name-only            # conflicted files
git merge --abort               # back out — just previewing
```

### Step 6 -- Perform actual merge (local only)

```bash
git merge upstream/main
```

This is where conflicts surface and decisions are made.

### Step 7 -- Resolve conflicts

For each conflicted file, open it, find the `<<<<<<<` markers, and apply
the resolution recipe from Section 3.

**Special rule for overridden core files** (`expose_app.py`,
`agent_engine_app.py`, `Makefile`, `pyproject.toml`):

1. Review upstream changes line-by-line
2. Identify: bug fixes, security changes, lifecycle changes
3. Reapply your custom logic deliberately — do not blindly accept either side

```bash
# After resolving each file:
git add <resolved-file>
```

### Step 8 -- Finalize merge

```bash
git commit   # merge commit message is auto-generated
```

### Step 9 -- Regenerate lock files

```bash
uv run python -m agent_starter_pack.utils.generate_locks
git add agent_starter_pack/resources/locks/
git commit -m "Regenerate lock files after upstream merge"
```

### Step 10 -- Validate (see Section 4)

### Step 11 -- Push to fork (Local -> Origin)

```bash
git push origin main
```

### Step 12 -- Update parent repo submodule

```bash
cd /path/to/xyborg
git add scripts/factory
git commit -m "Sync factory submodule with upstream agent-starter-pack vX.X.X"
git push
```

---

## 2b. PR-Based Sync (safer for large updates)

For larger upstream syncs, use a branch instead of merging directly to main:

```bash
cd scripts/factory
git fetch upstream
git checkout -b sync/upstream-$(date +%Y%m%d) main
git merge upstream/main

# Resolve conflicts, regenerate locks, validate...
git push origin sync/upstream-$(date +%Y%m%d)

# Create PR on our fork
gh pr create \
  --repo democodex/factory \
  --title "Sync upstream agent-starter-pack" \
  --body "Merging latest from GoogleCloudPlatform/agent-starter-pack.

## Checklist
- [ ] Makefile override hooks preserved
- [ ] pyproject.toml pythonpath + asyncio_mode preserved
- [ ] CLI entrypoint name preserved
- [ ] Lock files regenerated
- [ ] Template generation tested (xyborg, xyborg_live, xyborg_a2a)
- [ ] Upstream changes to agent_engine_app.py / expose_app.py reviewed against our xyborg_live overrides"
```

---

## 3. Conflict Resolution Recipes

We modify exactly 3 core files. These are the only files that should
produce merge conflicts. Each has a deterministic resolution.

### 3a. `agent_starter_pack/base_templates/python/Makefile`

**Our change:** `commands.override` Jinja hooks for `deploy` and `test`
targets (+9 lines). Also `us-west1` -> `us-central1` in several places.

**Resolution:**
1. Keep our `{%- if commands.override.deploy %}` wrapper around the deploy target
2. Keep our `{%- if commands.override.test %}` wrapper around the test target
3. Accept upstream changes to the logic INSIDE the `{%- else %}` blocks
4. Region changes: accept either — our templates override the entire deploy target

**Verify:**
```bash
grep -c 'commands.*override.*deploy' agent_starter_pack/base_templates/python/Makefile
grep -c 'commands.*override.*test' agent_starter_pack/base_templates/python/Makefile
# Both should return 2
```

### 3b. `agent_starter_pack/base_templates/python/pyproject.toml`

**Our change:** 2 lines in `[tool.pytest.ini_options]`:
```toml
pythonpath = [".", "../.."]   # was "."
asyncio_mode = "auto"         # added
```

**Resolution:**
1. Keep our `pythonpath = [".", "../.."]`
2. Keep our `asyncio_mode = "auto"`
3. Accept any other upstream additions to the section

**Verify:**
```bash
grep -A3 'tool.pytest' agent_starter_pack/base_templates/python/pyproject.toml
```

### 3c. `pyproject.toml` (root)

**Our change:** CLI entrypoint rename.

**Resolution:**
1. Accept upstream version bumps
2. Keep our `xyborg-agent = "agent_starter_pack.cli.main:cli"`

### 3d. Files we OVERRIDE via xyborg_live template

Our `xyborg_live` template ships its own copies of `agent_engine_app.py`
and `expose_app.py` that overwrite the deployment template versions during
generation. These won't cause git conflicts, but upstream changes to the
originals may contain bug fixes or features we should port.

**After every merge, check:**
```bash
# Did upstream change the files we override?
git diff HEAD~1..HEAD --name-only | grep -E \
  'deployment_targets.*agent_engine_app\.py|deployment_targets.*expose_app\.py'

# If yes: diff upstream's version against our override
diff \
  agent_starter_pack/deployment_targets/agent_engine/python/\{\{cookiecutter.agent_directory\}\}/agent_engine_app.py \
  agent_starter_pack/agents/xyborg_live/app/agent_engine_app.py

diff \
  agent_starter_pack/deployment_targets/agent_engine/python/\{\{cookiecutter.agent_directory\}\}/app_utils/expose_app.py \
  agent_starter_pack/agents/xyborg_live/app/app_utils/expose_app.py
```

If upstream added meaningful changes (bug fixes, security patches, new ADK
compatibility), port them into our overrides.

---

## 4. Post-Merge Validation

```bash
cd scripts/factory

# 1. Core modifications intact
grep -c 'commands.*override.*deploy' agent_starter_pack/base_templates/python/Makefile  # expect: 2
grep 'pythonpath.*\.\./\.\.' agent_starter_pack/base_templates/python/pyproject.toml    # expect: 1 match
grep 'xyborg-agent' pyproject.toml                                                      # expect: 1 match

# 2. Template generation
printf '1\nus-central1\n' | uv run xyborg-agent create /tmp/test-xyborg --agent xyborg
printf '1\nus-central1\n' | uv run xyborg-agent create /tmp/test-xyborg-live --agent xyborg_live
printf '1\nus-central1\n' | uv run xyborg-agent create /tmp/test-xyborg-a2a --agent xyborg_a2a

# 3. Verify xyborg_live customizations survived
grep 'bootstrap' /tmp/test-xyborg-live/*/agent.py
grep 'session_service_builder' /tmp/test-xyborg-live/*/agent.py
grep 'bidi_stream_query' /tmp/test-xyborg-live/*/agent_engine_app.py
grep 'sessionInfo' /tmp/test-xyborg-live/*/app_utils/expose_app.py

# 4. Cleanup
rm -rf /tmp/test-xyborg /tmp/test-xyborg-live /tmp/test-xyborg-a2a
```

---

## 5. Evaluating Upstream Features

When reviewing incoming commits, flag anything in these areas:

### High-Priority (directly relevant)

| Area | Why | What to look for |
|------|-----|-----------------|
| `agent_engine_app.py` template | We override this for `xyborg_live` | Changes to `bidi_stream_query`, `set_up()`, session handling |
| `expose_app.py` template | We override this for `xyborg_live` | WebSocket adapter changes, new message types |
| Session management | We added `DatabaseSessionService` | Upstream adding `session_service_builder`, `session_type` options |
| ADK version bumps | May add features we can leverage | New `google-adk` versions |
| `adk_live` agent template | Base for `xyborg_live` | New patterns, model changes |
| Frontend (`adk_live_react`) | Base for `xyborg_live_react` | WebSocket protocol changes, audio handling |

### Medium-Priority

| Area | Why |
|------|-----|
| Deployment targets | Cloud Run / GKE improvements |
| CI/CD templates | CloudBuild / GitHub Actions |
| Testing patterns | New eval frameworks |
| CLI improvements | New flags, `enhance` command |

**If upstream adds session persistence natively,** evaluate whether their
implementation supersedes ours. If so, we can remove our `xyborg_live`
overrides — reducing maintenance surface.

### Review commands

```bash
# Focus on high-priority areas
git diff HEAD..upstream/main -- \
  agent_starter_pack/deployment_targets/agent_engine/ \
  agent_starter_pack/agents/adk_live/ \
  agent_starter_pack/frontends/adk_live_react/

# Upstream commits touching our override targets
git log HEAD..upstream/main --oneline -- \
  agent_starter_pack/deployment_targets/agent_engine/
```

---

## Anti-Patterns

### Do NOT sync via GitHub UI or `gh repo sync`

```bash
# NEVER do this:
gh repo sync democodex/factory --source GoogleCloudPlatform/agent-starter-pack
```

This bypasses your local control layer and is dangerous with overridden
files. If upstream changed `expose_app.py` and you auto-sync, your fork
silently accepts their version — but your `xyborg_live` template still
ships your override. The two diverge without any conflict warning.

### Do NOT resolve conflicts in multiple places

All conflict resolution happens ONLY in your local repo. Never use GitHub's
web conflict editor for this fork.

### Do NOT skip the guardrail check (Step 4)

Even if the merge looks clean, always verify protected files weren't
touched. A clean merge does not mean a safe merge — upstream can change
the parent file that your `xyborg_live` template overrides without
producing a git conflict.

---

## Quick Reference

```bash
cd scripts/factory

# Check position
git fetch upstream
echo "Ahead: $(git rev-list --count upstream/main..HEAD)"
echo "Behind: $(git rev-list --count HEAD..upstream/main)"

# Inspect before merging
git log HEAD..upstream/main --oneline
git diff HEAD..upstream/main --name-only | grep -E 'expose_app|agent_engine_app|Makefile|pyproject'

# Full sync (no conflicts expected)
git fetch upstream && git pull origin main && git merge upstream/main && \
  uv run python -m agent_starter_pack.utils.generate_locks && \
  git add -A && git commit -m "Regenerate lock files after upstream merge" && \
  git push origin main

# Then in parent repo:
cd /path/to/xyborg && git add scripts/factory && \
  git commit -m "Sync factory submodule with upstream" && git push
```

---

## Strategic Note

The current model relies on manual reconciliation of overwritten upstream
files. This is workable short-term but does not scale. If upstream begins
actively developing session persistence or live agent features, consider
evolving to an extension/patch architecture that eliminates direct file
overwrites.
