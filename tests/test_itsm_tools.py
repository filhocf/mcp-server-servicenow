"""TDD RED tests for ITSM domain-specific tools.

These tests define the EXPECTED BEHAVIOR of each tool.
They MUST FAIL until the tools are implemented correctly.

Contract per tool:
- incident_search: builds encoded query from ergonomic params, returns {count, incidents}
- incident_create: posts payload with correct fields, returns {sys_id, number, record}
- incident_update: patches with only provided fields, returns {sys_id, number, state}
- change_search: builds encoded query, returns {count, changes}
- change_create: posts with type/risk/plans, returns {sys_id, number, record}
- change_update: patches with state/notes/review, returns {sys_id, number, state}
- change_tasks: queries change_task by parent, returns {count, tasks}
"""

from unittest.mock import MagicMock, patch

import pytest


# --- Fixtures ---


@pytest.fixture
def sn_config():
    config = MagicMock()
    config.api_url = "https://test.service-now.com/api/now"
    config.instance_url = "https://test.service-now.com"
    config.timeout = 30
    return config


def _make_response(data, status=200):
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = data
    return resp


# --- incident_search ---


class TestIncidentSearch:
    @patch("servicenow_mcp.tools.itsm_tools.make_sn_request")
    @patch("servicenow_mcp.tools.itsm_tools.get_config")
    def test_no_filters_returns_recent(self, mock_config, mock_request, sn_config):
        """With no filters, should query all incidents ordered by created desc."""
        mock_config.return_value = sn_config
        mock_request.return_value = _make_response({"result": [{"number": "INC001"}]})

        from servicenow_mcp.tools.itsm_tools import incident_search

        result = incident_search()

        assert result["count"] == 1
        assert "incidents" in result
        # Should have called with ORDER BY
        call_params = mock_request.call_args[1]["params"]
        assert "ORDERBYDESCsys_created_on" in call_params["sysparm_query"]
        # Should request display values
        assert call_params["sysparm_display_value"] == "true"

    @patch("servicenow_mcp.tools.itsm_tools.make_sn_request")
    @patch("servicenow_mcp.tools.itsm_tools.get_config")
    def test_filters_build_encoded_query(self, mock_config, mock_request, sn_config):
        """Ergonomic params must translate to correct encoded query parts."""
        mock_config.return_value = sn_config
        mock_request.return_value = _make_response({"result": []})

        from servicenow_mcp.tools.itsm_tools import incident_search

        incident_search(
            assigned_to="claudio.filho",
            assignment_group="MIR-INFRA",
            state=[1, 2],
            priority=[1],
            cmdb_ci="mir-api-prod",
            created_after="2026-01-01",
            text_search="VPN",
            limit=10,
        )

        query = mock_request.call_args[1]["params"]["sysparm_query"]
        assert "assigned_to.user_name=claudio.filho" in query
        assert "assignment_group.name=MIR-INFRA" in query
        assert "stateIN1,2" in query
        assert "priorityIN1" in query
        assert "cmdb_ci.name=mir-api-prod" in query
        assert "sys_created_on>=2026-01-01" in query
        assert "short_descriptionLIKEVPN" in query
        assert mock_request.call_args[1]["params"]["sysparm_limit"] == 10

    @patch("servicenow_mcp.tools.itsm_tools.make_sn_request")
    @patch("servicenow_mcp.tools.itsm_tools.get_config")
    def test_empty_result(self, mock_config, mock_request, sn_config):
        """Empty result returns count=0 and empty list."""
        mock_config.return_value = sn_config
        mock_request.return_value = _make_response({"result": []})

        from servicenow_mcp.tools.itsm_tools import incident_search

        result = incident_search(state=[7])

        assert result == {"count": 0, "incidents": []}


# --- incident_create ---


class TestIncidentCreate:
    @patch("servicenow_mcp.tools.itsm_tools.make_sn_request")
    @patch("servicenow_mcp.tools.itsm_tools.get_config")
    def test_creates_with_all_fields(self, mock_config, mock_request, sn_config):
        """All optional fields that are provided must appear in the POST payload."""
        mock_config.return_value = sn_config
        mock_request.return_value = _make_response(
            {"result": {"sys_id": "x1", "number": "INC002"}}
        )

        from servicenow_mcp.tools.itsm_tools import incident_create

        result = incident_create(
            short_description="Cannot login",
            description="User gets 403",
            caller_id="jose.silva",
            assignment_group="SUPORTE-N2",
            category="Access",
            subcategory="VPN",
            impact=2,
            urgency=1,
            cmdb_ci="vpn-gateway",
        )

        assert result["sys_id"] == "x1"
        assert result["number"] == "INC002"
        payload = mock_request.call_args[1]["json_data"]
        assert payload["short_description"] == "Cannot login"
        assert payload["description"] == "User gets 403"
        assert payload["impact"] == 2
        assert payload["urgency"] == 1
        assert payload["cmdb_ci"] == "vpn-gateway"

    @patch("servicenow_mcp.tools.itsm_tools.make_sn_request")
    @patch("servicenow_mcp.tools.itsm_tools.get_config")
    def test_only_required_field(self, mock_config, mock_request, sn_config):
        """Only short_description is required; optional fields must NOT be in payload if None."""
        mock_config.return_value = sn_config
        mock_request.return_value = _make_response(
            {"result": {"sys_id": "x2", "number": "INC003"}}
        )

        from servicenow_mcp.tools.itsm_tools import incident_create

        incident_create(short_description="Test")

        payload = mock_request.call_args[1]["json_data"]
        assert payload == {"short_description": "Test"}


# --- incident_update ---


class TestIncidentUpdate:
    @patch("servicenow_mcp.tools.itsm_tools.make_sn_request")
    @patch("servicenow_mcp.tools.itsm_tools.get_config")
    def test_resolve_incident(self, mock_config, mock_request, sn_config):
        """Resolving must send state=6, close_code, close_notes via PATCH."""
        mock_config.return_value = sn_config
        mock_request.return_value = _make_response(
            {"result": {"sys_id": "x1", "number": "INC001", "state": "6"}}
        )

        from servicenow_mcp.tools.itsm_tools import incident_update

        result = incident_update(
            sys_id="x1", state=6, close_code="Solved", close_notes="Restarted service"
        )

        assert result["state"] == "6"
        assert "x1" in mock_request.call_args[0][1]  # sys_id in URL
        payload = mock_request.call_args[1]["json_data"]
        assert payload["state"] == 6
        assert payload["close_code"] == "Solved"
        assert payload["close_notes"] == "Restarted service"
        # Method must be PATCH
        assert mock_request.call_args[0][0] == "PATCH"

    @patch("servicenow_mcp.tools.itsm_tools.make_sn_request")
    @patch("servicenow_mcp.tools.itsm_tools.get_config")
    def test_only_sends_provided_fields(self, mock_config, mock_request, sn_config):
        """Fields not provided must NOT appear in PATCH payload."""
        mock_config.return_value = sn_config
        mock_request.return_value = _make_response(
            {"result": {"sys_id": "x1", "number": "INC001", "state": "2"}}
        )

        from servicenow_mcp.tools.itsm_tools import incident_update

        incident_update(sys_id="x1", work_notes="Investigating")

        payload = mock_request.call_args[1]["json_data"]
        assert payload == {"work_notes": "Investigating"}
        assert "state" not in payload


# --- change_search ---


class TestChangeSearch:
    @patch("servicenow_mcp.tools.itsm_tools.make_sn_request")
    @patch("servicenow_mcp.tools.itsm_tools.get_config")
    def test_filters_build_query(self, mock_config, mock_request, sn_config):
        mock_config.return_value = sn_config
        mock_request.return_value = _make_response({"result": [{"number": "CHG001"}]})

        from servicenow_mcp.tools.itsm_tools import change_search

        result = change_search(
            assignment_group="MIR-INFRA",
            type="normal",
            state=[-2, -1],
            planned_start_after="2026-06-01",
        )

        assert result["count"] == 1
        query = mock_request.call_args[1]["params"]["sysparm_query"]
        assert "assignment_group.name=MIR-INFRA" in query
        assert "type=normal" in query
        assert "stateIN-2,-1" in query
        assert "start_date>=2026-06-01" in query


# --- change_create ---


class TestChangeCreate:
    @patch("servicenow_mcp.tools.itsm_tools.make_sn_request")
    @patch("servicenow_mcp.tools.itsm_tools.get_config")
    def test_creates_with_plans(self, mock_config, mock_request, sn_config):
        """Change with implementation/backout/test plans must send all in payload."""
        mock_config.return_value = sn_config
        mock_request.return_value = _make_response(
            {"result": {"sys_id": "c1", "number": "CHG001"}}
        )

        from servicenow_mcp.tools.itsm_tools import change_create

        result = change_create(
            short_description="Deploy API v2",
            type="normal",
            risk=3,
            implementation_plan="1. Deploy image\n2. Verify health",
            backout_plan="Rollback to v1",
            test_plan="curl /health returns 200",
        )

        assert result["number"] == "CHG001"
        payload = mock_request.call_args[1]["json_data"]
        assert payload["type"] == "normal"
        assert payload["risk"] == 3
        assert "Deploy image" in payload["implementation_plan"]
        assert payload["backout_plan"] == "Rollback to v1"
        assert payload["test_plan"] == "curl /health returns 200"


# --- change_update ---


class TestChangeUpdate:
    @patch("servicenow_mcp.tools.itsm_tools.make_sn_request")
    @patch("servicenow_mcp.tools.itsm_tools.get_config")
    def test_advance_state(self, mock_config, mock_request, sn_config):
        mock_config.return_value = sn_config
        mock_request.return_value = _make_response(
            {"result": {"sys_id": "c1", "number": "CHG001", "state": "-1"}}
        )

        from servicenow_mcp.tools.itsm_tools import change_update

        result = change_update(sys_id="c1", state=-1)

        assert result["state"] == "-1"
        payload = mock_request.call_args[1]["json_data"]
        assert payload == {"state": -1}


# --- change_tasks ---


class TestChangeTasks:
    @patch("servicenow_mcp.tools.itsm_tools.make_sn_request")
    @patch("servicenow_mcp.tools.itsm_tools.get_config")
    def test_returns_tasks_for_change(self, mock_config, mock_request, sn_config):
        mock_config.return_value = sn_config
        mock_request.return_value = _make_response(
            {
                "result": [
                    {"number": "CTASK001", "short_description": "Deploy"},
                    {"number": "CTASK002", "short_description": "Verify"},
                ]
            }
        )

        from servicenow_mcp.tools.itsm_tools import change_tasks

        result = change_tasks(change_sys_id="c1")

        assert result["count"] == 2
        assert result["tasks"][0]["number"] == "CTASK001"
        query = mock_request.call_args[1]["params"]["sysparm_query"]
        assert "change_request=c1" in query
