"""Tests for Jira Cloud REST API service (mocked — no real API calls)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import requests

from app.services import jira_service


MOCK_ISSUE = {
    "key": "PROJ-1",
    "id": "10001",
    "self": "https://example.atlassian.net/rest/api/3/issue/10001",
    "fields": {
        "summary": "Test issue",
        "status": {"name": "To Do"},
        "assignee": {"displayName": "Jane Doe", "accountId": "abc123"},
        "issuetype": {"name": "Task"},
        "created": "2026-01-01T10:00:00.000+0000",
        "updated": "2026-01-02T10:00:00.000+0000",
    },
}


@pytest.fixture
def jira_configured():
    with patch.multiple(
        "app.services.jira_service.settings",
        JIRA_BASE_URL="https://example.atlassian.net",
        JIRA_EMAIL="user@example.com",
        JIRA_API_TOKEN="token",
        JIRA_PROJECT_KEY="PROJ",
    ):
        yield


@pytest.fixture
def jira_not_configured():
    with patch.multiple(
        "app.services.jira_service.settings",
        JIRA_BASE_URL="",
        JIRA_EMAIL="",
        JIRA_API_TOKEN="",
        JIRA_PROJECT_KEY="",
    ):
        yield


def test_create_issue_success(jira_configured):
    with (
        patch("app.services.jira_service.verify_project_exists") as mock_project,
        patch("app.services.jira_service.verify_issue_type_exists") as mock_type,
        patch("app.services.jira_service._request") as mock_request,
    ):
        mock_project.return_value = {"success": True, "project_key": "PROJ"}
        mock_type.return_value = {"success": True, "issue_type": "Bug"}
        mock_request.return_value = {
            "success": True,
            "data": {"key": "PROJ-42", "id": "10042", "self": "https://x/issue/10042"},
        }

        result = jira_service.create_issue("Fix login", "Users cannot log in", "Bug")

        assert result["success"] is True
        assert result["key"] == "PROJ-42"
        mock_project.assert_called_once()
        mock_type.assert_called_once()
        mock_request.assert_called_once()
        call_kwargs = mock_request.call_args.kwargs
        assert call_kwargs["json_body"]["fields"]["summary"] == "Fix login"
        assert call_kwargs["json_body"]["fields"]["issuetype"]["name"] == "Bug"
        assert call_kwargs["json_body"]["fields"]["project"]["key"] == "PROJ"


def test_get_issue_success(jira_configured):
    with patch("app.services.jira_service._request") as mock_request:
        mock_request.return_value = {"success": True, "data": MOCK_ISSUE}

        result = jira_service.get_issue("PROJ-1")

        assert result["success"] is True
        assert result["issue"]["key"] == "PROJ-1"
        assert result["issue"]["fields"]["summary"] == "Test issue"
        assert result["issue"]["fields"]["status"] == "To Do"


def test_get_issue_missing_key(jira_configured):
    result = jira_service.get_issue("  ")
    assert result["success"] is False
    assert "required" in result["error"].lower()


def test_search_issues_success(jira_configured):
    with patch("app.services.jira_service._request") as mock_request:
        mock_request.return_value = {
            "success": True,
            "data": {"issues": [MOCK_ISSUE], "total": 1},
        }

        result = jira_service.search_issues('project = "PROJ"', max_results=10)

        assert result["success"] is True
        assert result["total"] == 1
        assert result["issues"][0]["key"] == "PROJ-1"
        body = mock_request.call_args.kwargs["json_body"]
        assert body["jql"] == 'project = "PROJ"'
        assert body["maxResults"] == 10


def test_search_issues_missing_jql(jira_configured):
    result = jira_service.search_issues("  ")
    assert result["success"] is False


def test_list_project_issues(jira_configured):
    with patch("app.services.jira_service.search_issues") as mock_search:
        mock_search.return_value = {"success": True, "issues": [], "total": 0}

        result = jira_service.list_project_issues()

        assert result["success"] is True
        mock_search.assert_called_once()
        jql = mock_search.call_args[0][0]
        assert "PROJ" in jql


def test_assign_issue_success(jira_configured):
    with patch("app.services.jira_service._request") as mock_request:
        mock_request.return_value = {"success": True, "data": {}}

        result = jira_service.assign_issue("PROJ-5", "account-999")

        assert result["success"] is True
        assert result["issue_key"] == "PROJ-5"
        body = mock_request.call_args.kwargs["json_body"]
        assert body["accountId"] == "account-999"


def test_update_issue_status_success(jira_configured):
    with patch("app.services.jira_service._request") as mock_request:
        mock_request.return_value = {"success": True, "data": {}}

        result = jira_service.update_issue_status("PROJ-5", "31")

        assert result["success"] is True
        body = mock_request.call_args.kwargs["json_body"]
        assert body["transition"]["id"] == "31"


def test_not_configured_returns_error(jira_not_configured):
    result = jira_service.create_issue("Summary", "Description")
    assert result["success"] is False
    error = result["error"].lower()
    assert "not configured" in error or "jira_project_key is empty" in error


@patch("app.services.jira_service.settings")
@patch("app.services.jira_service.requests.request")
def test_request_handles_404(mock_request_fn, mock_settings):
    mock_settings.JIRA_BASE_URL = "https://example.atlassian.net"
    mock_settings.JIRA_EMAIL = "user@example.com"
    mock_settings.JIRA_API_TOKEN = "token"
    mock_settings.JIRA_PROJECT_KEY = "PROJ"

    response = MagicMock()
    response.status_code = 404
    response.text = '{"errorMessages":["Issue does not exist."]}'
    response.json.return_value = {"errorMessages": ["Issue does not exist."]}
    mock_request_fn.return_value = response

    result = jira_service._request("GET", "/rest/api/3/issue/PROJ-999")

    assert result["success"] is False
    assert result["status_code"] == 404
    assert "does not exist" in result["error"]


@patch("app.services.jira_service.settings")
@patch("app.services.jira_service.requests.request")
def test_request_handles_timeout(mock_request_fn, mock_settings):
    mock_settings.JIRA_BASE_URL = "https://example.atlassian.net"
    mock_settings.JIRA_EMAIL = "user@example.com"
    mock_settings.JIRA_API_TOKEN = "token"
    mock_settings.JIRA_PROJECT_KEY = "PROJ"

    mock_request_fn.side_effect = requests.Timeout("timed out")

    result = jira_service._request("GET", "/rest/api/3/issue/PROJ-1")

    assert result["success"] is False
    assert "timed out" in result["error"].lower()


@patch("app.services.jira_service.settings")
@patch("app.services.jira_service.requests.request")
def test_request_uses_basic_auth(mock_request_fn, mock_settings):
    mock_settings.JIRA_BASE_URL = "https://example.atlassian.net"
    mock_settings.JIRA_EMAIL = "user@example.com"
    mock_settings.JIRA_API_TOKEN = "api-token"
    mock_settings.JIRA_PROJECT_KEY = "PROJ"

    response = MagicMock()
    response.status_code = 200
    response.content = b"{}"
    response.json.return_value = {}
    mock_request_fn.return_value = response

    jira_service._request("GET", "/rest/api/3/issue/PROJ-1")

    assert mock_request_fn.call_args.kwargs["auth"] == ("user@example.com", "api-token")


def test_plain_text_to_adf():
    adf = jira_service._plain_text_to_adf("Hello Jira")
    assert adf["type"] == "doc"
    assert adf["content"][0]["content"][0]["text"] == "Hello Jira"


def test_verify_project_exists_failure(jira_configured):
    with patch("app.services.jira_service._request") as mock_request:
        mock_request.return_value = {
            "success": False,
            "error": "No project could be found with key 'PROJ'.",
            "status_code": 404,
        }

        result = jira_service.verify_project_exists("PROJ")

        assert result["success"] is False
        assert "PROJ" in result["error"]
        mock_request.assert_called_once_with("GET", "/rest/api/3/project/PROJ")


def test_verify_issue_type_exists_failure(jira_configured):
    with (
        patch("app.services.jira_service._request") as mock_request,
        patch("app.services.jira_service._list_issue_type_names") as mock_types,
    ):
        mock_request.return_value = {"success": True, "data": {"projects": []}}
        mock_types.return_value = ["Task", "Bug"]

        result = jira_service.verify_issue_type_exists("Epic", "PROJ")

        assert result["success"] is False
        assert "Epic" in result["error"]
        assert "Task" in result["error"]


def test_create_issue_stops_when_project_invalid(jira_configured):
    with patch("app.services.jira_service.verify_project_exists") as mock_project:
        mock_project.return_value = {
            "success": False,
            "error": "Jira project 'AC' could not be accessed: No project could be found with key 'AC'.",
            "status_code": 404,
        }

        result = jira_service.create_issue("Summary", "Description")

        assert result["success"] is False
        assert "could not be accessed" in result["error"]

