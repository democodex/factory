# {{cookiecutter.agent_directory}}

XybOrg Live voice agent with Gemini Live API, WebSocket backend, and React frontend.

## Quick Start

```bash
make install       # Install Python + frontend dependencies
make live          # Start WebSocket backend (port 8000)
make frontend-dev  # Start frontend dev server (port 3000, separate terminal)
```

## Development

| Command | Description |
|---------|-------------|
| `make live` | Start Live API backend (WebSocket server) |
| `make frontend-dev` | Start frontend dev server (hot reload) |
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
| Change live model | Set `LIVE_MODEL` env var (default: `gemini-live-2.5-flash-native-audio`) |
| Slack channels | Set `SLACK_SUCCESS_CHANNEL` / `SLACK_ERROR_CHANNEL` env vars |
| Disable Slack | Set `ENABLE_SLACK_PLUGIN=false` |
