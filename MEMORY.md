# MEMORY.md — mcp-server-servicenow

## Estado Atual

- **Versão**: 0.5.1 (bump pendente)
- **Branch**: feat/oauth-client-credentials (PR pendente)
- **Testes**: 114 passed, 13 skipped (integração)
- **CI**: GitHub Actions ativo + Gemini Code Assist

## Histórico

### 03/jun/2026 — Fork + ITSM tools + OAuth client_credentials
- Fork de jschuller/mcp-server-servicenow (substituiu asklokesh abandonado)
- 10 tools ITSM domain-specific (incident, change, catalog) — PR #2 mergeado
- OAuth client_credentials grant — branch feat/oauth-client-credentials (PR pendente)
- Issue #2 no upstream oferecendo PR com as tools
- Repo antigo (servicenow-mcp-server, fork asklokesh) arquivado

## Decisões

- **Base**: jschuller > asklokesh > echelon. Motivo: FastMCP 3.1, OAuth 2.1, Resources, PyPI.
- **Nosso diferencial**: tools domain-specific ergonômicas (agente acerta de primeira sem encoded query)
- **Instalação**: via git (`uvx --from git+...`), não PyPI próprio (nome conflita com upstream)
- **Auth produção**: OAuth client_credentials (Pronto Dataprev)

## Pendente

- [ ] PR #3 (oauth client_credentials) — criar + CI + merge
- [ ] Remover username/password do mcp.json (não precisa com client_credentials)
- [ ] Testar end-to-end via Kiro CLI (reiniciar CLI após merge)
- [ ] Bump versão para 0.6.0
- [ ] Oferecer PR upstream (client_credentials + ITSM tools)
