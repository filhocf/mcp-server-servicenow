# Code Review: itsm_tools.py & catalog_tools.py

**Verdict: PASS**

## Summary

All 16 tests pass. Both modules are well-implemented and consistent with the existing `cmdb_tools.py` pattern.

## Checklist

| Criterion | Status | Notes |
|-----------|--------|-------|
| No hardcoded credentials | ✅ | Auth delegated to `make_sn_request` / `get_config()` |
| Input validation | ✅ | Types enforced via Annotated+Field; None values excluded from payloads |
| Error handling | ✅ | `make_sn_request` raises on HTTP errors; `parse_json_response` raises `ServiceNowAPIError` on empty/HTML/invalid JSON — exceptions propagate to MCP framework |
| Consistent return types | ✅ | All return `Dict[str, Any]`; search tools return `{count, items}`, create tools return `{sys_id, number, record}`, update tools return `{sys_id, number, state}` |
| No None values in payload | ✅ | All create/update tools use `if val is not None` guard before adding to payload |
| Annotated + Field usage | ✅ | Every parameter uses `Annotated[type, Field(description=...)]` |
| Tags correctly set | ✅ | read/write paired with itsm/catalog as appropriate |
| cli.py imports | ✅ | Lines 271-272 import both modules |
| Pattern consistency with cmdb_tools | ✅ | Same import structure, same `get_config()` → build URL → `make_sn_request` → `parse_json_response` → extract result pattern |

## Minor Observations (informational, not blocking)

1. **No `limit` bounds validation** — `cmdb_tools.list_ci` uses `Field(ge=1, le=1000)` but the new tools don't constrain `limit`. Not a bug (ServiceNow will clamp server-side), but adding `ge=1, le=1000` would be more defensive and consistent.

2. **`change_create` uses `type` as parameter name** — shadows Python builtin. Harmless in this scope but worth noting.

3. **`ritm_create` uses service catalog API** (`/api/sn_sc/servicecatalog/items/.../order_now`) rather than the Table API used elsewhere — this is correct for catalog ordering and shows intentional design.

No security vulnerabilities, no credential leaks, no logic errors found.
