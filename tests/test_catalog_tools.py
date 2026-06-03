"""TDD RED tests for Service Catalog domain-specific tools.

Contract:
- catalog_items: query sc_cat_item with active=true, filter by category/text, return {count, items}
- ritm_search: build encoded query on sc_req_item, return {count, ritms}
- ritm_create: POST to /api/sn_sc/servicecatalog/items/{id}/order_now, return {request_number, request_id}
"""

from unittest.mock import MagicMock, patch

import pytest


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


class TestCatalogItems:
    @patch("servicenow_mcp.tools.catalog_tools.make_sn_request")
    @patch("servicenow_mcp.tools.catalog_tools.get_config")
    def test_lists_active_items(self, mock_config, mock_request, sn_config):
        """Default query must filter active=true."""
        mock_config.return_value = sn_config
        mock_request.return_value = _make_response({"result": [{"name": "VPN Access"}]})

        from servicenow_mcp.tools.catalog_tools import catalog_items

        result = catalog_items()

        assert result["count"] == 1
        query = mock_request.call_args[1]["params"]["sysparm_query"]
        assert "active=true" in query

    @patch("servicenow_mcp.tools.catalog_tools.make_sn_request")
    @patch("servicenow_mcp.tools.catalog_tools.get_config")
    def test_filters_by_category_and_text(self, mock_config, mock_request, sn_config):
        mock_config.return_value = sn_config
        mock_request.return_value = _make_response({"result": []})

        from servicenow_mcp.tools.catalog_tools import catalog_items

        catalog_items(category="Network", query="VPN")

        query = mock_request.call_args[1]["params"]["sysparm_query"]
        assert "category.title=Network" in query
        assert "nameLIKEVPN" in query


class TestRitmSearch:
    @patch("servicenow_mcp.tools.catalog_tools.make_sn_request")
    @patch("servicenow_mcp.tools.catalog_tools.get_config")
    def test_search_by_user(self, mock_config, mock_request, sn_config):
        mock_config.return_value = sn_config
        mock_request.return_value = _make_response({"result": [{"number": "RITM001"}]})

        from servicenow_mcp.tools.catalog_tools import ritm_search

        result = ritm_search(requested_for="claudio.filho")

        assert result["count"] == 1
        assert result["ritms"][0]["number"] == "RITM001"
        query = mock_request.call_args[1]["params"]["sysparm_query"]
        assert "requested_for.user_name=claudio.filho" in query

    @patch("servicenow_mcp.tools.catalog_tools.make_sn_request")
    @patch("servicenow_mcp.tools.catalog_tools.get_config")
    def test_search_with_state_and_item(self, mock_config, mock_request, sn_config):
        mock_config.return_value = sn_config
        mock_request.return_value = _make_response({"result": []})

        from servicenow_mcp.tools.catalog_tools import ritm_search

        ritm_search(state=[1, 2], cat_item="Firewall Rule")

        query = mock_request.call_args[1]["params"]["sysparm_query"]
        assert "stateIN1,2" in query
        assert "cat_item.name=Firewall Rule" in query


class TestRitmCreate:
    @patch("servicenow_mcp.tools.catalog_tools.make_sn_request")
    @patch("servicenow_mcp.tools.catalog_tools.get_config")
    def test_orders_catalog_item(self, mock_config, mock_request, sn_config):
        """Must POST to sn_sc/servicecatalog/items/{id}/order_now."""
        mock_config.return_value = sn_config
        mock_request.return_value = _make_response(
            {"result": {"request_number": "REQ001", "request_id": "r1"}}
        )

        from servicenow_mcp.tools.catalog_tools import ritm_create

        result = ritm_create(
            cat_item_sys_id="item123",
            requested_for="claudio.filho",
            variables={"justification": "Need VPN access"},
        )

        assert result["request_number"] == "REQ001"
        # URL must contain the catalog item sys_id
        url_called = mock_request.call_args[0][1]
        assert "item123" in url_called
        assert "servicecatalog" in url_called
        # Payload must have variables
        payload = mock_request.call_args[1]["json_data"]
        assert payload["variables"]["justification"] == "Need VPN access"
        assert payload["variables"]["requested_for"] == "claudio.filho"
