from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_current_user
from app.schemas.jira import (
    AssignIssueRequest,
    CreateIssueRequest,
    CreateIssueResponse,
    IssueDetailResponse,
    IssueListResponse,
    IssueResponse,
    JiraActionResponse,
    SearchIssuesRequest,
    SearchIssuesResponse,
    UpdateIssueStatusRequest,
)
from app.services import jira_service

router = APIRouter(prefix="/jira", tags=["jira"])


def _raise_if_failed(result: dict, status_code: int = 400) -> None:
    if result.get("success"):
        return
    code = result.get("status_code", status_code)
    detail = result.get("error") or "Jira request failed"
    if code == 404:
        raise HTTPException(status_code=404, detail=detail)
    if code == 401:
        raise HTTPException(status_code=502, detail=detail)
    if code == 403:
        raise HTTPException(status_code=403, detail=detail)
    # Pass through Jira 400 errors with the exact message for the frontend
    raise HTTPException(
        status_code=code if 400 <= code < 600 else 400,
        detail=detail,
    )


@router.post("/create", response_model=CreateIssueResponse)
async def create_jira_issue(
    body: CreateIssueRequest,
    current_user=Depends(get_current_user),
):
    result = jira_service.create_issue(
        summary=body.summary,
        description=body.description,
        issue_type=body.issue_type,
    )
    if not result.get("success"):
        _raise_if_failed(result)
    return CreateIssueResponse(
        success=True,
        key=result.get("key"),
        id=result.get("id"),
        self_url=result.get("self_url"),
        message=f"Issue {result.get('key')} created successfully.",
    )


@router.get("/issues", response_model=IssueListResponse)
async def list_jira_issues(
    current_user=Depends(get_current_user),
):
    result = jira_service.list_project_issues()
    if not result.get("success"):
        _raise_if_failed(result)
    return IssueListResponse(
        success=True,
        issues=[IssueResponse(**issue) for issue in result.get("issues", [])],
        total=result.get("total", 0),
    )


@router.get("/{issue_key}", response_model=IssueDetailResponse)
async def get_jira_issue(
    issue_key: str,
    current_user=Depends(get_current_user),
):
    result = jira_service.get_issue(issue_key)
    if not result.get("success"):
        _raise_if_failed(result, status_code=404)
    issue = result.get("issue")
    return IssueDetailResponse(
        success=True,
        issue=IssueResponse(**issue) if issue else None,
    )


@router.post("/search", response_model=SearchIssuesResponse)
async def search_jira_issues(
    body: SearchIssuesRequest,
    current_user=Depends(get_current_user),
):
    result = jira_service.search_issues(body.jql, max_results=body.max_results)
    if not result.get("success"):
        _raise_if_failed(result)
    return SearchIssuesResponse(
        success=True,
        issues=[IssueResponse(**issue) for issue in result.get("issues", [])],
        total=result.get("total", 0),
    )


@router.post("/assign", response_model=JiraActionResponse)
async def assign_jira_issue(
    body: AssignIssueRequest,
    current_user=Depends(get_current_user),
):
    result = jira_service.assign_issue(body.issue_key, body.account_id)
    if not result.get("success"):
        _raise_if_failed(result)
    return JiraActionResponse(
        success=True,
        issue_key=result.get("issue_key"),
        message=result.get("message"),
    )


@router.post("/status", response_model=JiraActionResponse)
async def update_jira_issue_status(
    body: UpdateIssueStatusRequest,
    current_user=Depends(get_current_user),
):
    result = jira_service.update_issue_status(body.issue_key, body.transition_id)
    if not result.get("success"):
        _raise_if_failed(result)
    return JiraActionResponse(
        success=True,
        issue_key=result.get("issue_key"),
        message=result.get("message"),
    )
