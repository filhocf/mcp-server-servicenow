# AGENTS.md — mcp-server-servicenow

## Projeto

MCP server para ServiceNow com 29 tools (Table API genérica + ITSM domain-specific + CMDB + Update Sets + System).
Fork de `jschuller/mcp-server-servicenow`, evoluído com tools ergonômicas para operação ITSM real.

## Stack

- Python 3.11+, FastMCP 3.1, Pydantic v2
- Auth: Basic, OAuth 2.1 (password + client_credentials), API Key
- Transport: stdio + Streamable HTTP
- Testes: pytest + pytest-asyncio + pytest-mock
- Lint: ruff
- CI: GitHub Actions (matrix 3.11/3.12/3.13)

## Instância alvo

- **Pronto Dataprev**: `https://pronto.dataprev.gov.br`
- Auth: OAuth client_credentials (client_id + client_secret)
- Versão: Tokyo+

## Comandos

```bash
# Testes
uv run pytest -q

# Lint
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/

# Rodar local (stdio)
SERVICENOW_INSTANCE_URL=https://pronto.dataprev.gov.br \
SERVICENOW_AUTH_TYPE=oauth \
SERVICENOW_CLIENT_ID=... \
SERVICENOW_CLIENT_SECRET=... \
uv run mcp-server-servicenow
```

## Convenções

- Tools: `@mcp.tool(tags={"read"|"write", "itsm"|"catalog"|"cmdb"|"system"})`
- Params: `Annotated[type, Field(description=...)]`
- Returns: `Dict[str, Any]` — search → `{count, items}`, create → `{sys_id, number, record}`
- Null safety: `data.get("result") or []` (nunca `data.get("result", [])`)
- HTTP: `make_sn_request()` + `parse_json_response()` centralizados

## Upstream

- Repo: `jschuller/mcp-server-servicenow`
- Issue #2 aberta oferecendo nossas ITSM tools como PR
- PyPI: `mcp-server-servicenow` (publicado pelo upstream)
