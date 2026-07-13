"""
Jira Cloud REST API v3 integration.

All HTTP calls to Jira live in this module — routers only call these functions.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

import requests

from app.config import settings

logger = logging.getLogger(__name__)

API_PREFIX = "/rest/api/3"


def _configured() -> bool:
    return bool(
        settings.JIRA_BASE_URL
        and settings.JIRA_EMAIL
        and settings.JIRA_API_TOKEN
        and _project_key()
    )


def _project_key() -> str:
    """Return the configured project key with surrounding whitespace stripped."""
    return (settings.JIRA_PROJECT_KEY or "").strip()


def _mask_email(email: str) -> str:
    if not email or "@" not in email:
        return "(not set)"
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        return f"{'*' * len(local)}@{domain}"
    return f"{local[0]}***{local[-1]}@{domain}"


def _log_config_context(operation: str) -> None:
    """Log non-secret Jira configuration used for a request."""
    logger.info(
        "jira_config operation=%s base_url=%s project_key=%r "
        "project_key_length=%s email=%s configured=%s",
        operation,
        settings.JIRA_BASE_URL,
        _project_key(),
        len(_project_key()),
        _mask_email(settings.JIRA_EMAIL),
        _configured(),
    )


def _config_error() -> dict[str, Any]:
    return {
        "success": False,
        "error": (
            "Jira integration is not configured. "
            "Set JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN, and JIRA_PROJECT_KEY."
        ),
    }


def _base_url() -> str:
    return settings.JIRA_BASE_URL.rstrip("/")


def _auth() -> tuple[str, str]:
    return settings.JIRA_EMAIL, settings.JIRA_API_TOKEN


def _plain_text_to_adf(text: str) -> dict[str, Any]:
    """Convert plain text to Atlassian Document Format for Jira v3."""
    return {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": text or ""}],
            }
        ],
    }


def _parse_issue(issue: dict[str, Any]) -> dict[str, Any]:
    fields = issue.get("fields") or {}
    status = fields.get("status") or {}
    assignee = fields.get("assignee") or {}
    issue_type = fields.get("issuetype") or {}

    return {
        "key": issue.get("key", ""),
        "id": issue.get("id"),
        "self_url": issue.get("self"),
        "fields": {
            "summary": fields.get("summary"),
            "status": status.get("name"),
            "assignee": assignee.get("displayName") or assignee.get("accountId"),
            "issue_type": issue_type.get("name"),
            "created": fields.get("created"),
            "updated": fields.get("updated"),
        },
    }


def _extract_error_detail(response: requests.Response) -> str:
    """Build a user-facing error string from the full Jira response body."""
    raw_text = (response.text or "").strip()
    logger.error(
        "jira_api_response_body status=%s body=%s",
        response.status_code,
        raw_text or "(empty)",
    )

    parts: list[str] = []

    try:
        payload = response.json()
    except ValueError:
        if raw_text:
            return raw_text[:2000]
        return f"Jira returned HTTP {response.status_code}."

    if isinstance(payload, dict):
        messages = payload.get("errorMessages") or []
        parts.extend(str(m) for m in messages if m)

        errors = payload.get("errors") or {}
        if isinstance(errors, dict):
            parts.extend(f"{k}: {v}" for k, v in errors.items() if v)

        message = payload.get("message")
        if message:
            parts.append(str(message))

        if not parts and raw_text:
            parts.append(raw_text[:2000])

    if parts:
        return "; ".join(parts)

    return f"Jira returned HTTP {response.status_code}."


def _request(
    method: str,
    path: str,
    *,
    json_body: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Execute a Jira REST API v3 request.

    Returns {"success": True, "data": ...} or {"success": False, "error": "..."}.
    """
    if not _configured():
        logger.warning("jira_request_skipped reason=missing_configuration path=%s", path)
        return _config_error()

    url = f"{_base_url()}{path}"
    started = time.perf_counter()

    if json_body is not None:
        logger.info(
            "jira_api_request method=%s path=%s payload=%s",
            method.upper(),
            path,
            json.dumps(json_body, ensure_ascii=False),
        )
    else:
        logger.info(
            "jira_api_request method=%s path=%s params=%s",
            method.upper(),
            path,
            json.dumps(params or {}, ensure_ascii=False),
        )

    try:
        response = requests.request(
            method=method.upper(),
            url=url,
            auth=_auth(),
            json=json_body,
            params=params,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            timeout=15,
        )
    except requests.Timeout:
        elapsed_ms = (time.perf_counter() - started) * 1000
        logger.error(
            "jira_api_failure method=%s path=%s reason=timeout elapsed_ms=%.1f",
            method.upper(),
            path,
            elapsed_ms,
        )
        return {
            "success": False,
            "error": "Jira request timed out. Please try again.",
        }
    except requests.RequestException as exc:
        elapsed_ms = (time.perf_counter() - started) * 1000
        logger.error(
            "jira_api_failure method=%s path=%s reason=%s elapsed_ms=%.1f",
            method.upper(),
            path,
            exc,
            elapsed_ms,
        )
        return {
            "success": False,
            "error": "Could not reach Jira. Please try again later.",
        }

    elapsed_ms = (time.perf_counter() - started) * 1000

    if response.status_code >= 400:
        detail = _extract_error_detail(response)
        logger.error(
            "jira_api_failure method=%s path=%s status=%s detail=%s elapsed_ms=%.1f",
            method.upper(),
            path,
            response.status_code,
            detail,
            elapsed_ms,
        )
        return {
            "success": False,
            "error": detail,
            "status_code": response.status_code,
            "jira_response": response.text,
        }

    if response.status_code == 204 or not response.content:
        logger.info(
            "jira_api_success method=%s path=%s status=%s elapsed_ms=%.1f",
            method.upper(),
            path,
            response.status_code,
            elapsed_ms,
        )
        return {"success": True, "data": {}}

    try:
        data = response.json()
    except ValueError:
        logger.error(
            "jira_api_failure method=%s path=%s reason=invalid_json body=%s elapsed_ms=%.1f",
            method.upper(),
            path,
            response.text,
            elapsed_ms,
        )
        return {
            "success": False,
            "error": "Received an invalid response from Jira.",
        }

    logger.info(
        "jira_api_success method=%s path=%s status=%s elapsed_ms=%.1f response=%s",
        method.upper(),
        path,
        response.status_code,
        elapsed_ms,
        json.dumps(data, ensure_ascii=False)[:500],
    )
    return {"success": True, "data": data}


def _list_issue_type_names(project_key: str) -> list[str]:
    """Return issue type names available for a project."""
    result = _request(
        "GET",
        f"{API_PREFIX}/issue/createmeta",
        params={"projectKeys": project_key},
    )
    if not result.get("success"):
        return []

    names: list[str] = []
    for project in result.get("data", {}).get("projects") or []:
        for issue_type in project.get("issuetypes") or []:
            name = issue_type.get("name")
            if name:
                names.append(name)
    return names


def verify_project_exists(project_key: str | None = None) -> dict[str, Any]:
    """Verify the Jira project exists and is accessible."""
    key = (project_key or _project_key()).strip()
    if not key:
        return {
            "success": False,
            "error": (
                "JIRA_PROJECT_KEY is empty. Set a valid project key in the environment."
            ),
        }

    result = _request("GET", f"{API_PREFIX}/project/{key}")
    if not result.get("success"):
        return {
            "success": False,
            "error": (
                f"Jira project '{key}' could not be accessed: {result.get('error')}"
            ),
            "status_code": result.get("status_code", 400),
        }

    project = result.get("data") or {}
    logger.info(
        "jira_project_verified key=%r id=%s name=%s",
        key,
        project.get("id"),
        project.get("name"),
    )
    return {
        "success": True,
        "project_key": key,
        "project_name": project.get("name"),
        "project_id": project.get("id"),
    }


def verify_issue_type_exists(
    issue_type: str,
    project_key: str | None = None,
) -> dict[str, Any]:
    """Verify the issue type is valid for the configured project."""
    key = (project_key or _project_key()).strip()
    cleaned_type = (issue_type or "").strip()
    if not cleaned_type:
        return {"success": False, "error": "Issue type is required."}

    result = _request(
        "GET",
        f"{API_PREFIX}/issue/createmeta",
        params={"projectKeys": key, "issuetypeNames": cleaned_type},
    )
    if not result.get("success"):
        return {
            "success": False,
            "error": (
                f"Could not verify issue type '{cleaned_type}' for project '{key}': "
                f"{result.get('error')}"
            ),
            "status_code": result.get("status_code", 400),
        }

    projects = result.get("data", {}).get("projects") or []
    if not projects:
        available = _list_issue_type_names(key)
        available_text = ", ".join(available) if available else "none found"
        return {
            "success": False,
            "error": (
                f"Issue type '{cleaned_type}' is not available in project '{key}'. "
                f"Available types: {available_text}"
            ),
            "status_code": 400,
        }

    issuetypes = projects[0].get("issuetypes") or []
    if not issuetypes:
        available = _list_issue_type_names(key)
        available_text = ", ".join(available) if available else "none found"
        return {
            "success": False,
            "error": (
                f"Issue type '{cleaned_type}' is not available in project '{key}'. "
                f"Available types: {available_text}"
            ),
            "status_code": 400,
        }

    logger.info(
        "jira_issue_type_verified project_key=%r issue_type=%r",
        key,
        cleaned_type,
    )
    return {"success": True, "issue_type": cleaned_type}


def create_issue(
    summary: str,
    description: str = "",
    issue_type: str = "Task",
) -> dict[str, Any]:
    """Create a Jira issue in the configured project."""
    _log_config_context("create_issue")

    project_key = _project_key()
    cleaned_type = (issue_type or "Task").strip()

    project_check = verify_project_exists(project_key)
    if not project_check.get("success"):
        return project_check

    type_check = verify_issue_type_exists(cleaned_type, project_key)
    if not type_check.get("success"):
        return type_check

    body = {
        "fields": {
            "project": {"key": project_key},
            "summary": summary,
            "description": _plain_text_to_adf(description),
            "issuetype": {"name": cleaned_type},
        }
    }

    logger.info(
        "jira_create_issue project_key=%r issue_type=%r summary=%r",
        project_key,
        cleaned_type,
        summary[:120],
    )

    result = _request("POST", f"{API_PREFIX}/issue", json_body=body)
    if not result.get("success"):
        return result

    data = result["data"]
    return {
        "success": True,
        "key": data.get("key"),
        "id": data.get("id"),
        "self_url": data.get("self"),
    }


def get_issue(issue_key: str) -> dict[str, Any]:
    """Fetch a single Jira issue by key."""
    key = (issue_key or "").strip()
    if not key:
        return {"success": False, "error": "Issue key is required."}

    result = _request("GET", f"{API_PREFIX}/issue/{key}")
    if not result.get("success"):
        return result

    return {
        "success": True,
        "issue": _parse_issue(result["data"]),
    }


def search_issues(jql: str, max_results: int = 50) -> dict[str, Any]:
    """Search Jira issues using JQL."""
    query = (jql or "").strip()
    if not query:
        return {"success": False, "error": "JQL query is required."}

    body = {
        "jql": query,
        "maxResults": max_results,
        "fields": [
            "summary",
            "status",
            "assignee",
            "issuetype",
            "created",
            "updated",
        ],
    }
    result = _request("POST", f"{API_PREFIX}/search", json_body=body)
    if not result.get("success"):
        return result

    data = result["data"]
    issues = [_parse_issue(issue) for issue in data.get("issues", [])]
    return {
        "success": True,
        "issues": issues,
        "total": data.get("total", len(issues)),
    }


def list_project_issues(max_results: int = 50) -> dict[str, Any]:
    """List issues for the configured Jira project."""
    jql = f'project = "{_project_key()}" ORDER BY created DESC'
    return search_issues(jql, max_results=max_results)


def assign_issue(issue_key: str, account_id: str) -> dict[str, Any]:
    """Assign a Jira issue to a user by account ID."""
    key = (issue_key or "").strip()
    assignee = (account_id or "").strip()
    if not key:
        return {"success": False, "error": "Issue key is required."}
    if not assignee:
        return {"success": False, "error": "Assignee account ID is required."}

    result = _request(
        "PUT",
        f"{API_PREFIX}/issue/{key}/assignee",
        json_body={"accountId": assignee},
    )
    if not result.get("success"):
        return result

    return {
        "success": True,
        "issue_key": key,
        "message": f"Issue {key} assigned successfully.",
    }


def update_issue_status(issue_key: str, transition_id: str) -> dict[str, Any]:
    """Transition a Jira issue to a new status."""
    key = (issue_key or "").strip()
    transition = (transition_id or "").strip()
    if not key:
        return {"success": False, "error": "Issue key is required."}
    if not transition:
        return {"success": False, "error": "Transition ID is required."}

    result = _request(
        "POST",
        f"{API_PREFIX}/issue/{key}/transitions",
        json_body={"transition": {"id": transition}},
    )
    if not result.get("success"):
        return result

    return {
        "success": True,
        "issue_key": key,
        "message": f"Issue {key} status updated successfully.",
    }
