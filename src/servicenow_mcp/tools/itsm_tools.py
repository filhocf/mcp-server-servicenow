"""ServiceNow ITSM tools — Incidents and Changes."""

from typing import Annotated, Any, Dict, List, Optional

from pydantic import Field

from servicenow_mcp.server import mcp, get_config, make_sn_request
from servicenow_mcp.utils.http import parse_json_response


@mcp.tool(tags={"read", "itsm"})
def incident_search(
    assigned_to: Annotated[
        Optional[str], Field(description="Username of assigned user")
    ] = None,
    assignment_group: Annotated[
        Optional[str], Field(description="Assignment group name")
    ] = None,
    state: Annotated[
        Optional[List[int]], Field(description="List of state values")
    ] = None,
    priority: Annotated[
        Optional[List[int]], Field(description="List of priority values")
    ] = None,
    cmdb_ci: Annotated[Optional[str], Field(description="CI name")] = None,
    created_after: Annotated[
        Optional[str], Field(description="Created after date")
    ] = None,
    text_search: Annotated[
        Optional[str],
        Field(description="Text to search in short_description/description"),
    ] = None,
    limit: Annotated[int, Field(description="Max results")] = 50,
) -> Dict[str, Any]:
    """Search incidents with ergonomic filters."""
    config = get_config()
    query_parts = []
    if assigned_to:
        query_parts.append(f"assigned_to.user_name={assigned_to}")
    if assignment_group:
        query_parts.append(f"assignment_group.name={assignment_group}")
    if state:
        query_parts.append(f"stateIN{','.join(str(s) for s in state)}")
    if priority:
        query_parts.append(f"priorityIN{','.join(str(p) for p in priority)}")
    if cmdb_ci:
        query_parts.append(f"cmdb_ci.name={cmdb_ci}")
    if created_after:
        query_parts.append(f"sys_created_on>={created_after}")
    if text_search:
        query_parts.append(
            f"short_descriptionLIKE{text_search}^ORdescriptionLIKE{text_search}"
        )
    query_parts.append("ORDERBYDESCsys_created_on")
    encoded_query = "^".join(query_parts)

    params = {
        "sysparm_query": encoded_query,
        "sysparm_fields": "sys_id,number,short_description,state,priority,assigned_to,assignment_group,cmdb_ci,opened_at,resolved_at",
        "sysparm_display_value": "true",
        "sysparm_limit": limit,
    }
    url = f"{config.api_url}/table/incident"
    response = make_sn_request("GET", url, config.timeout, params=params)
    data = parse_json_response(response, url)
    result = data.get("result", [])
    return {"count": len(result), "incidents": result}


@mcp.tool(tags={"write", "itsm"})
def incident_create(
    short_description: Annotated[
        str, Field(description="Short description (required)")
    ],
    description: Annotated[Optional[str], Field(description="Full description")] = None,
    caller_id: Annotated[Optional[str], Field(description="Caller username")] = None,
    assignment_group: Annotated[
        Optional[str], Field(description="Assignment group")
    ] = None,
    category: Annotated[Optional[str], Field(description="Category")] = None,
    subcategory: Annotated[Optional[str], Field(description="Subcategory")] = None,
    impact: Annotated[Optional[int], Field(description="Impact level")] = None,
    urgency: Annotated[Optional[int], Field(description="Urgency level")] = None,
    cmdb_ci: Annotated[Optional[str], Field(description="Configuration item")] = None,
) -> Dict[str, Any]:
    """Create an incident."""
    config = get_config()
    payload: Dict[str, Any] = {"short_description": short_description}
    for key in (
        "description",
        "caller_id",
        "assignment_group",
        "category",
        "subcategory",
        "impact",
        "urgency",
        "cmdb_ci",
    ):
        val = locals()[key]
        if val is not None:
            payload[key] = val

    url = f"{config.api_url}/table/incident"
    response = make_sn_request("POST", url, config.timeout, json_data=payload)
    data = parse_json_response(response, url)
    result = data.get("result", {})
    return {
        "sys_id": result.get("sys_id"),
        "number": result.get("number"),
        "record": result,
    }


@mcp.tool(tags={"write", "itsm"})
def incident_update(
    sys_id: Annotated[str, Field(description="Incident sys_id")],
    state: Annotated[Optional[int], Field(description="New state")] = None,
    assigned_to: Annotated[Optional[str], Field(description="Assigned user")] = None,
    assignment_group: Annotated[
        Optional[str], Field(description="Assignment group")
    ] = None,
    work_notes: Annotated[Optional[str], Field(description="Work notes")] = None,
    comments: Annotated[Optional[str], Field(description="Comments")] = None,
    close_code: Annotated[Optional[str], Field(description="Close code")] = None,
    close_notes: Annotated[Optional[str], Field(description="Close notes")] = None,
) -> Dict[str, Any]:
    """Update an incident."""
    config = get_config()
    payload: Dict[str, Any] = {}
    for key in (
        "state",
        "assigned_to",
        "assignment_group",
        "work_notes",
        "comments",
        "close_code",
        "close_notes",
    ):
        val = locals()[key]
        if val is not None:
            payload[key] = val

    url = f"{config.api_url}/table/incident/{sys_id}"
    response = make_sn_request("PATCH", url, config.timeout, json_data=payload)
    data = parse_json_response(response, url)
    result = data.get("result", {})
    return {
        "sys_id": result.get("sys_id"),
        "number": result.get("number"),
        "state": result.get("state"),
    }


@mcp.tool(tags={"read", "itsm"})
def change_search(
    assignment_group: Annotated[
        Optional[str], Field(description="Assignment group name")
    ] = None,
    state: Annotated[
        Optional[List[int]], Field(description="List of state values")
    ] = None,
    type: Annotated[Optional[str], Field(description="Change type")] = None,
    cmdb_ci: Annotated[Optional[str], Field(description="CI name")] = None,
    planned_start_after: Annotated[
        Optional[str], Field(description="Planned start after date")
    ] = None,
    text_search: Annotated[Optional[str], Field(description="Text search")] = None,
    limit: Annotated[int, Field(description="Max results")] = 50,
) -> Dict[str, Any]:
    """Search change requests."""
    config = get_config()
    query_parts = []
    if assignment_group:
        query_parts.append(f"assignment_group.name={assignment_group}")
    if state:
        query_parts.append(f"stateIN{','.join(str(s) for s in state)}")
    if type:
        query_parts.append(f"type={type}")
    if cmdb_ci:
        query_parts.append(f"cmdb_ci.name={cmdb_ci}")
    if planned_start_after:
        query_parts.append(f"start_date>={planned_start_after}")
    if text_search:
        query_parts.append(f"short_descriptionLIKE{text_search}")
    query_parts.append("ORDERBYDESCsys_created_on")
    encoded_query = "^".join(query_parts)

    params = {
        "sysparm_query": encoded_query,
        "sysparm_fields": "sys_id,number,short_description,state,type,risk,priority,assignment_group,cmdb_ci,start_date,end_date",
        "sysparm_display_value": "true",
        "sysparm_limit": limit,
    }
    url = f"{config.api_url}/table/change_request"
    response = make_sn_request("GET", url, config.timeout, params=params)
    data = parse_json_response(response, url)
    result = data.get("result", [])
    return {"count": len(result), "changes": result}


@mcp.tool(tags={"write", "itsm"})
def change_create(
    short_description: Annotated[str, Field(description="Short description")],
    description: Annotated[Optional[str], Field(description="Description")] = None,
    type: Annotated[str, Field(description="Change type")] = "normal",
    risk: Annotated[Optional[int], Field(description="Risk level")] = None,
    impact: Annotated[Optional[int], Field(description="Impact level")] = None,
    assignment_group: Annotated[
        Optional[str], Field(description="Assignment group")
    ] = None,
    cmdb_ci: Annotated[Optional[str], Field(description="CI")] = None,
    planned_start_date: Annotated[
        Optional[str], Field(description="Planned start")
    ] = None,
    planned_end_date: Annotated[Optional[str], Field(description="Planned end")] = None,
    implementation_plan: Annotated[
        Optional[str], Field(description="Implementation plan")
    ] = None,
    backout_plan: Annotated[Optional[str], Field(description="Backout plan")] = None,
    test_plan: Annotated[Optional[str], Field(description="Test plan")] = None,
) -> Dict[str, Any]:
    """Create a change request."""
    config = get_config()
    payload: Dict[str, Any] = {"short_description": short_description, "type": type}
    for key in (
        "description",
        "risk",
        "impact",
        "assignment_group",
        "cmdb_ci",
        "planned_start_date",
        "planned_end_date",
        "implementation_plan",
        "backout_plan",
        "test_plan",
    ):
        val = locals()[key]
        if val is not None:
            payload[key] = val

    url = f"{config.api_url}/table/change_request"
    response = make_sn_request("POST", url, config.timeout, json_data=payload)
    data = parse_json_response(response, url)
    result = data.get("result", {})
    return {
        "sys_id": result.get("sys_id"),
        "number": result.get("number"),
        "record": result,
    }


@mcp.tool(tags={"write", "itsm"})
def change_update(
    sys_id: Annotated[str, Field(description="Change sys_id")],
    state: Annotated[Optional[int], Field(description="New state")] = None,
    work_notes: Annotated[Optional[str], Field(description="Work notes")] = None,
    review_status: Annotated[Optional[int], Field(description="Review status")] = None,
    assigned_to: Annotated[Optional[str], Field(description="Assigned user")] = None,
) -> Dict[str, Any]:
    """Update a change request."""
    config = get_config()
    payload: Dict[str, Any] = {}
    for key in ("state", "work_notes", "review_status", "assigned_to"):
        val = locals()[key]
        if val is not None:
            payload[key] = val

    url = f"{config.api_url}/table/change_request/{sys_id}"
    response = make_sn_request("PATCH", url, config.timeout, json_data=payload)
    data = parse_json_response(response, url)
    result = data.get("result", {})
    return {
        "sys_id": result.get("sys_id"),
        "number": result.get("number"),
        "state": result.get("state"),
    }


@mcp.tool(tags={"read", "itsm"})
def change_tasks(
    change_sys_id: Annotated[str, Field(description="Parent change request sys_id")],
) -> Dict[str, Any]:
    """Get tasks for a change request."""
    config = get_config()
    params = {
        "sysparm_query": f"change_request={change_sys_id}",
        "sysparm_fields": "sys_id,number,short_description,state,assigned_to,assignment_group,planned_start_date,planned_end_date",
    }
    url = f"{config.api_url}/table/change_task"
    response = make_sn_request("GET", url, config.timeout, params=params)
    data = parse_json_response(response, url)
    result = data.get("result", [])
    return {"count": len(result), "tasks": result}
