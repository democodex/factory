# {{cookiecutter.agent_directory}}

XybOrg ADK agent scaffold — root agent, sub-agents directory, plugins, awareness events, and bootstrap.

## Quick Start

```bash
make install       # Install dependencies
make run           # Run agent locally via `adk run`
make playground    # ADK web playground
make test          # Run unit + integration tests
```

## Development

| Command | Description |
|---------|-------------|
| `make run` | Run agent locally via `adk run` |
| `make playground` | ADK web playground |
| `make test` | Run unit + integration tests |
| `make deploy` | Deploy via factory deployment system |
| `make analyze` | Analyze internal/external dependencies |
| `make logs` | Fetch recent deployment logs |

## Customization

| What | How |
|------|-----|
| Agent instructions | Edit `app/prompts.py` |
| Add domain tools | Add to `app/tools.py`, import in `app/agent.py` tools list |
| Add sub-agents | Add to `app/sub_agents/`, wire in `app/agent.py` |
| Slack channels | Set `SLACK_SUCCESS_CHANNEL` / `SLACK_ERROR_CHANNEL` env vars |
| Disable Slack | Set `ENABLE_SLACK_PLUGIN=false` |

## Visibility & Data Safety (views.py)

If your agent surfaces data sourced from `common/entities/` (e.g. `CompanyRecord`) to the LLM via a tool result, you **must** project that data through a visibility tier first. Raw canonical entities carry audit/lineage/internal fields (`date_enriched`, `legitimacy_*`, HubSpot system timestamps) that don't belong in a model's awareness context.

### When you need a `views.py`

| Your agent's tools return … | Action |
|-----------------------------|--------|
| Only data from this app (no `common/entities/` imports) | Skip — no `views.py` needed. |
| `CompanyRecord` (or other canonical entity) data | Add `app/views.py` and apply at every tool boundary that surfaces entity data. |

### How to add one

1. Pick a tier from `common/views/` — `CompanyPublicView` (customer-facing default) or `CompanyConfidentialView` (trusted internal).
2. Create `app/views.py`:

   ```python
   """Domain-safe views — apply at every LLM-facing tool result that returns
   data sourced from common/entities.
   """
   from collections.abc import Mapping
   from typing import Any

   from common.views import CompanyPublicView, project_to_view


   def to_{{cookiecutter.agent_directory}}_company_view(raw: Mapping[str, Any]) -> dict[str, Any]:
       return project_to_view(raw, CompanyPublicView)
   ```

3. Apply it at every tool boundary in `app/tools.py`:

   ```python
   from {{cookiecutter.agent_directory}}.views import to_{{cookiecutter.agent_directory}}_company_view

   async def get_company(...):
       ...
       result = await _get_company(company_identifier)
       if not result:
           return {"error": "Company not found."}
       return to_{{cookiecutter.agent_directory}}_company_view(result)
   ```

4. Add a tool-boundary regression test that mocks the underlying CRM call with a leaky dict and asserts no audit field appears in the result. The real failure mode is "someone forgot to call the projection at the boundary" — unit tests on the projection alone won't catch it.

See `common/views/README.md` and `common/entities/README.md` for the full architectural rule and an SDR reference implementation in `factory/sdr/sdr/views.py`.
