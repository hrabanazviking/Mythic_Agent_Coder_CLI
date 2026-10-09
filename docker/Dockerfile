# Mythic Agent Docker image (Slice 40)
# Build: docker build -t mythic-agent .
# Run: docker run -it --rm -v $(pwd):/workspace mythic-agent run "task"

FROM python:3.12-slim

LABEL maintainer="hrabanazviking"
LABEL description="Mythic Agent - Viking-themed AI coding assistant"

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy package files
COPY pyproject.toml LICENSE NOTICE ./
COPY mythic_agent/ ./mythic_agent/
COPY default_agent_characters/ ./default_agent_characters/
COPY Mythic-Engineering/ ./Mythic-Engineering/

# Install (core only - TUI/voice are optional)
RUN pip install --no-cache-dir -e .

# Workspace mount point
VOLUME ["/workspace", "/root/.config/mythic"]
WORKDIR /workspace

# Default: show help
ENTRYPOINT ["mythic"]
CMD ["--help"]
