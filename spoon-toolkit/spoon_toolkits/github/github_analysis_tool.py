"""GitHub analysis tools"""

from typing import Optional
from spoon_ai.tools.base import BaseTool, ToolResult
from .github_provider import GitHubProvider

class GetGitHubIssuesTool(BaseTool):
    name: str = "get_github_issues"
    description: str = "Get GitHub repository issues data. Useful when you need to analyze project issues, track bug reports, or monitor project development activity. Returns GitHub issues data with keys: total_count, issues_list, date_range."
    parameters: dict = {
        "type": "object",
        "properties": {
            "owner": {
                "type": "string",
                "description": "Repository owner (e.g., 'neo-project')"
            },
            "repo": {
                "type": "string",
                "description": "Repository name (e.g., 'neo')"
            },
            "start_date": {
                "type": "string",
                "description": "Start date in YYYY-MM-DD format (e.g., '2023-01-01')"
            },
            "end_date": {
                "type": "string",
                "description": "End date in YYYY-MM-DD format (e.g., '2023-12-31')"
            },
            "token": {
                "type": "string",
                "description": "GitHub personal access token for authenticated requests",
                "default": None
            }
        },
        "required": ["owner", "repo", "start_date", "end_date"]
    }

    async def execute(self, owner: str, repo: str, start_date: str, end_date: str, token: Optional[str] = None) -> ToolResult:
        try:
            provider = GitHubProvider(token=token)
            issues = await provider.fetch_issues(owner, repo, start_date, end_date)
            return ToolResult(output=f"GitHub issues: {issues}")
        except Exception as e:
            return ToolResult(error=str(e))

class GetGitHubPullRequestsTool(BaseTool):
    name: str = "get_github_pull_requests"
    description: str = "Get GitHub repository pull requests data. Useful when you need to analyze code contributions, track feature development, or monitor project collaboration. Returns GitHub pull requests data with keys: total_count, pull_requests_list, date_range."
    parameters: dict = {
        "type": "object",
        "properties": {
            "owner": {
                "type": "string",
                "description": "Repository owner (e.g., 'neo-project')"
            },
            "repo": {
                "type": "string",
                "description": "Repository name (e.g., 'neo')"
            },
            "start_date": {
                "type": "string",
                "description": "Start date in YYYY-MM-DD format (e.g., '2023-01-01')"
            },
            "end_date": {
                "type": "string",
                "description": "End date in YYYY-MM-DD format (e.g., '2023-12-31')"
            },
            "token": {
                "type": "string",
                "description": "GitHub personal access token for authenticated requests",
                "default": None
            }
        },
        "required": ["owner", "repo", "start_date", "end_date"]
    }

    async def execute(self, owner: str, repo: str, start_date: str, end_date: str, token: Optional[str] = None) -> ToolResult:
        try:
            provider = GitHubProvider(token=token)
            pull_requests = await provider.fetch_pull_requests(owner, repo, start_date, end_date)
            return ToolResult(output=f"GitHub pull requests: {pull_requests}")
        except Exception as e:
            return ToolResult(error=str(e))

class GetGitHubCommitsTool(BaseTool):
    name: str = "get_github_commits"
    description: str = "Get GitHub repository commits data. Useful when you need to analyze code changes, track development progress, or monitor repository activity. Returns GitHub commits data with keys: total_count, commits_list, date_range."
    parameters: dict = {
        "type": "object",
        "properties": {
            "owner": {
                "type": "string",
                "description": "Repository owner (e.g., 'neo-project')"
            },
            "repo": {
                "type": "string",
                "description": "Repository name (e.g., 'neo')"
            },
            "start_date": {
                "type": "string",
                "description": "Start date in YYYY-MM-DD format (e.g., '2023-01-01')"
            },
            "end_date": {
                "type": "string",
                "description": "End date in YYYY-MM-DD format (e.g., '2023-12-31')"
            },
            "token": {
                "type": "string",
                "description": "GitHub personal access token for authenticated requests",
                "default": None
            }
        },
        "required": ["owner", "repo", "start_date", "end_date"]
    }

    async def execute(self, owner: str, repo: str, start_date: str, end_date: str, token: Optional[str] = None) -> ToolResult:
        try:
            provider = GitHubProvider(token=token)
            commits = await provider.fetch_commits(owner, repo, start_date, end_date)
            return ToolResult(output=f"GitHub commits: {commits}")
        except Exception as e:
            return ToolResult(error=str(e)) 