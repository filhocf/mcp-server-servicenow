"""ServiceNow Service Catalog tools."""

from typing import Annotated, Any, Dict, List, Optional

from pydantic import Field

from servicenow_mcp.server import mcp, get_config, make_sn_request
from servicenow_mcp.utils.http import parse_json_response


@mcp.tool(tags={"read", "catalog"})
def catalog_items(
    category: Annotated[Optional[str], Field(description="Category title")] = None,
    query: Annotated[Optional[str], Field(description="Text search on name")] = None,
    limit: Annotated[int, Field(description="Max results")] = 50,
) -> Dict[str, Any]:
    """List service catalog items."""
    config = get_config()
    query_parts = ["active=true"]
    if category:
        query_parts.append(f"category.title={category}")
    if query:
        query_parts.append(f"nameLIKE{query}")
    query_parts.append("ORDERBYDESCsys_created_on")
    encoded_query = "^".join(query_parts)

    params = {
        "sysparm_query": encoded_query,
        "sysparm_display_value": "true",
        "sysparm_limit": limit,
    }
    url = f"{config.api_url}/table/sc_cat_item"
    response = make_sn_request("GET", url, config.timeout, params=params)
    data = parse_json_response(response, url)
    result = data.get("result") or []
    return {"count": len(result), "items": result}


@mcp.tool(tags={"read", "catalog"})
def ritm_search(
    requested_for: Annotated[
        Optional[str], Field(description="Requested for username")
    ] = None,
    assignment_group: Annotated[
        Optional[str], Field(description="Assignment group name")
    ] = None,
    state: Annotated[
        Optional[List[int]], Field(description="List of state values")
    ] = None,
    cat_item: Annotated[Optional[str], Field(description="Catalog item name")] = None,
    text_search: Annotated[Optional[str], Field(description="Text search")] = None,
    limit: Annotated[int, Field(description="Max results")] = 50,
) -> Dict[str, Any]:
    """Search requested items (RITMs)."""
    config = get_config()
    query_parts = []
    if requested_for:
        query_parts.append(f"requested_for.user_name={requested_for}")
    if assignment_group:
        query_parts.append(f"assignment_group.name={assignment_group}")
    if state:
        query_parts.append(f"stateIN{','.join(str(s) for s in state)}")
    if cat_item:
        query_parts.append(f"cat_item.name={cat_item}")
    if text_search:
        query_parts.append(f"short_descriptionLIKE{text_search}")
    query_parts.append("ORDERBYDESCsys_created_on")
    encoded_query = "^".join(query_parts)

    params = {
        "sysparm_query": encoded_query,
        "sysparm_display_value": "true",
        "sysparm_limit": limit,
    }
    url = f"{config.api_url}/table/sc_req_item"
    response = make_sn_request("GET", url, config.timeout, params=params)
    data = parse_json_response(response, url)
    result = data.get("result") or []
    return {"count": len(result), "ritms": result}


@mcp.tool(tags={"write", "catalog"})
def ritm_create(
    cat_item_sys_id: Annotated[str, Field(description="Catalog item sys_id")],
    requested_for: Annotated[
        Optional[str], Field(description="Requested for username")
    ] = None,
    quantity: Annotated[int, Field(description="Quantity")] = 1,
    variables: Annotated[
        Optional[Dict[str, Any]], Field(description="Item variables")
    ] = None,
) -> Dict[str, Any]:
    """Order a service catalog item."""
    config = get_config()
    vars_dict = dict(variables) if variables else {}
    if requested_for:
        vars_dict["requested_for"] = requested_for

    payload: Dict[str, Any] = {"sysparm_quantity": quantity, "variables": vars_dict}
    url = f"{config.instance_url}/api/sn_sc/servicecatalog/items/{cat_item_sys_id}/order_now"
    response = make_sn_request("POST", url, config.timeout, json_data=payload)
    data = parse_json_response(response, url)
    result = data.get("result") or {}
    return {
        "request_number": result.get("request_number"),
        "request_id": result.get("request_id"),
        "result": result,
    }
