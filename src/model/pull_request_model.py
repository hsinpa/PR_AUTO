from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


class PullRequestInputModel(BaseModel):
    sha: str
    token: str

    patch_content: str
    comment_url: str
    fetch_file_url: str

class FileModel(BaseModel):
    filename: str
    raw_content: Optional[str] = Field(default='')
    dependency_paths: Optional[list[str]] = Field(default=[])


class PullRequestIssueModel(BaseModel):
    pr_patch: str = Field(default='', description='The section on [PR PATCH], that has issue')
    title: str = Field(default='', description='The unique title for this issue')
    issue: str = Field(default='', description='a explanation on what the issue is and what Code review rule it break')
    priority: str = Field(default='', description="how serious is the issue, categorize into 'high', 'medium' and 'low' only")
    file_path: str = Field(default='', description='the path of main file')
    dependency_paths: list[str] = Field(default='', description='a list of dependency file paths, worth a look')
    line_number: int = Field(default='', description='The start line where the issue begin')
    content: Optional[str] = Field(default='', description='Follow the [Instruction]')
