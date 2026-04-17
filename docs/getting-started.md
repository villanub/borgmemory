# Getting Started

Borg is a no-auth, single-user deployment for local use. Just a standard OpenAI API key and Docker.

## Prerequisites

- Docker with Compose v2
- An OpenAI API key

## Setup (3 commands)

```bash
cp .env.basic.example .env.basic
# Edit .env.basic and set OPENAI_API_KEY=sk-...
docker compose -f docker-compose.basic.yml --env-file .env.basic up -d
```

Verify it's running:

```bash
curl http://localhost:8080/health
# {"status":"ok","profile":"basic"}
```

## Connect Claude Desktop (MCP)

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "borg": {
      "url": "http://localhost:8080/mcp"
    }
  }
}
```

No auth header needed — Borg accepts all local connections.

## First use

In Claude Desktop, Borg's four tools are available immediately:

- **borg_learn** — save a decision or discovery
- **borg_think** — retrieve compiled context before a complex task
- **borg_recall** — search memory directly
- **borg_get_episode** — fetch a full stored episode by ID

Example prompt:
> "Use borg_learn to record: we decided to use SQLite for the local cache because the data volume is small and we want zero external dependencies."

## Namespaces

Borg has no namespace restrictions — use any namespace string you like:

```
namespace="project-alpha"
namespace="personal"
namespace="work"
```

## Stopping

```bash
docker compose -f docker-compose.basic.yml down
```

Data is persisted in the `borg-basic-data` Docker volume. To reset completely:

```bash
docker compose -f docker-compose.basic.yml down -v
```
