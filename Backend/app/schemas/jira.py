from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class CreateIssueRequest(BaseModel):
    summary: str = Field(..., min_length=1, max_length=255)
    description: str = Field(default="", max_length=5000)
    issue_type: str = Field(default="Task", min_length=1, max_length=50)


class AssignIssueRequest(BaseModel):
    issue_key: str = Field(..., min_length=1, max_length=50)
    account_id: str = Field(..., min_length=1, max_length=100)


class UpdateIssueStatusRequest(BaseModel):
    issue_key: str = Field(..., min_length=1, max_length=50)
    transition_id: str = Field(..., min_length=1, max_length=20)


class SearchIssuesRequest(BaseModel):
    jql: str = Field(..., min_length=1, max_length=2000)
    max_results: int = Field(default=50, ge=1, le=100)


class IssueFields(BaseModel):
    summary: Optional[str] = None
    status: Optional[str] = None
    assignee: Optional[str] = None
    issue_type: Optional[str] = None
    created: Optional[datetime] = None
    updated: Optional[datetime] = None


class IssueResponse(BaseModel):
    key: str
    id: Optional[str] = None
    self_url: Optional[str] = None
    fields: IssueFields = Field(default_factory=IssueFields)


class CreateIssueResponse(BaseModel):
    success: bool
    key: Optional[str] = None
    id: Optional[str] = None
    self_url: Optional[str] = None
    message: Optional[str] = None


class IssueListResponse(BaseModel):
    success: bool
    issues: list[IssueResponse] = Field(default_factory=list)
    total: int = 0
    message: Optional[str] = None


class IssueDetailResponse(BaseModel):
    success: bool
    issue: Optional[IssueResponse] = None
    message: Optional[str] = None


class SearchIssuesResponse(BaseModel):
    success: bool
    issues: list[IssueResponse] = Field(default_factory=list)
    total: int = 0
    message: Optional[str] = None


class JiraActionResponse(BaseModel):
    success: bool
    issue_key: Optional[str] = None
    message: Optional[str] = None
    data: Optional[dict[str, Any]] = None
