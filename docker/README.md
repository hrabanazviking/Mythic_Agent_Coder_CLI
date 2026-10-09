# Mythic Agent Docker support (Slice 40)

## Quick start

```bash
# Build the image
docker build -t mythic-agent .

# Run with your workspace mounted
docker run -it --rm \
  -v $(pwd):/workspace \
  -v mythic-config:/root/.config/mythic \
  mythic-agent run "explain this codebase"

# Interactive chat
docker run -it --rm \
  -v $(pwd):/workspace \
  -v mythic-config:/root/.config/mythic \
  mythic-agent chat
```

## Configuration

The container uses `/root/.config/mythic` for configuration. Mount a named
volume to persist settings, sessions, and API keys across runs.

Set your provider via environment variables:
```bash
docker run -it --rm \
  -e OPENAI_API_KEY="sk-..." \
  -v $(pwd):/workspace \
  mythic-agent run "refactor this"
```

Or configure interactively on first run (settings persist in the volume).

## Volumes

| Volume | Purpose |
|--------|---------|
| `/workspace` | Your project directory (mount your code here) |
| `/root/.config/mythic` | Config, sessions, memory (use named volume) |

## Security notes

- The container runs as root by default. For untrusted code, use `--user`
  and read-only mounts: `-v $(pwd):/workspace:ro`.
- API keys passed via `-e` are visible in `docker inspect`. Prefer the
  config file in the named volume for long-term use.
- Network access is required for hosted LLM providers. Use
  `--network none` with a local provider (e.g. Ollama on host via
  `--add-host host.docker.internal:host-gateway`).
