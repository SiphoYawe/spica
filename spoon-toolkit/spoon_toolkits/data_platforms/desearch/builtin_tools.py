"""
Desearch Builtin Tools for Spoon-Core Integration

This module provides Desearch tools as builtin tools that can be directly
integrated into spoon-core without requiring MCP servers.
"""

import os
import json
import logging
from typing import Any, Dict, List, Optional, Union
from pydantic import Field

# Import spoon-core base tool
try:
    from spoon_ai.tools.base import BaseTool
except ImportError:
    # Fallback for development/testing
    from abc import ABC, abstractmethod
    from pydantic import BaseModel

    class BaseTool(ABC, BaseModel):
        name: str = Field(description="The name of the tool")
        description: str = Field(description="A description of the tool")
        parameters: dict = Field(description="The parameters of the tool")

        class Config:
            arbitrary_types_allowed = True

        async def __call__(self, *args, **kwargs) -> Any:
            return await self.execute(*args, **kwargs)

        @abstractmethod
        async def execute(self, *args, **kwargs) -> Any:
            raise NotImplementedError("Subclasses must implement this method")

# Import Desearch functions
try:
    from .ai_search_official import search_ai_data, search_academic
    from .web_search_official import search_web, search_twitter_links, search_twitter_posts
except ImportError:
    # Fallback for direct import
    from ai_search_official import search_ai_data, search_academic
    from web_search_official import search_web, search_twitter_links, search_twitter_posts

logger = logging.getLogger(__name__)


class DesearchAISearchTool(BaseTool):
    """Desearch AI Search Tool for comprehensive data search across multiple platforms"""

    name: str = "desearch_ai_search"
    description: str = "Search for AI-related data across web, Reddit, Wikipedia, YouTube, and arXiv platforms"
    parameters: dict = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query"
            },
            "platforms": {
                "type": "string",
                "description": "Comma-separated platforms to search (web,reddit,wikipedia,youtube,arxiv)",
                "default": "web,reddit"
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of results to return",
                "default": 10,
                "minimum": 1,
                "maximum": 50
            }
        },
        "required": ["query"]
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._validate_api_key()

    def _validate_api_key(self):
        """Validate that the Desearch API key is available"""
        api_key = os.getenv('DESEARCH_API_KEY')
        if not api_key:
            raise ValueError("DESEARCH_API_KEY environment variable is required")

    async def execute(self, query: str, platforms: str = "web,reddit", limit: int = 10) -> Dict[str, Any]:
        """Execute AI search across specified platforms"""
        try:
            # Convert platforms string to list
            platform_list = [p.strip() for p in platforms.split(',')]

            # Call the search function
            result = await search_ai_data(
                query=query,
                platforms=platform_list,
                limit=limit
            )

            return {
                "success": True,
                "data": result,
                "tool": "desearch_ai_search"
            }

        except Exception as e:
            logger.error(f"Desearch AI search failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "tool": "desearch_ai_search"
            }


class DesearchWebSearchTool(BaseTool):
    """Desearch Web Search Tool for general web search"""

    name: str = "desearch_web_search"
    description: str = "Search the web for general information"
    parameters: dict = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query"
            },
            "num_results": {
                "type": "integer",
                "description": "Number of results to return",
                "default": 10,
                "minimum": 1,
                "maximum": 50
            }
        },
        "required": ["query"]
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._validate_api_key()

    def _validate_api_key(self):
        """Validate that the Desearch API key is available"""
        api_key = os.getenv('DESEARCH_API_KEY')
        if not api_key:
            raise ValueError("DESEARCH_API_KEY environment variable is required")

    async def execute(self, query: str, num_results: int = 10) -> Dict[str, Any]:
        """Execute web search"""
        try:
            result = await search_web(query=query, num_results=num_results)

            return {
                "success": True,
                "data": result,
                "tool": "desearch_web_search"
            }

        except Exception as e:
            logger.error(f"Desearch web search failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "tool": "desearch_web_search"
            }


class DesearchAcademicSearchTool(BaseTool):
    """Desearch Academic Search Tool for arXiv papers"""

    name: str = "desearch_academic_search"
    description: str = "Search for academic papers on arXiv"
    parameters: dict = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query"
            },
            "platform": {
                "type": "string",
                "description": "Academic platform to search",
                "default": "arxiv",
                "enum": ["arxiv"]
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of results to return",
                "default": 10,
                "minimum": 1,
                "maximum": 50
            }
        },
        "required": ["query"]
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._validate_api_key()

    def _validate_api_key(self):
        """Validate that the Desearch API key is available"""
        api_key = os.getenv('DESEARCH_API_KEY')
        if not api_key:
            raise ValueError("DESEARCH_API_KEY environment variable is required")

    async def execute(self, query: str, platform: str = "arxiv", limit: int = 10) -> Dict[str, Any]:
        """Execute academic search"""
        try:
            result = await search_academic(query=query, platform=platform, limit=limit)

            return {
                "success": True,
                "data": result,
                "tool": "desearch_academic_search"
            }

        except Exception as e:
            logger.error(f"Desearch academic search failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "tool": "desearch_academic_search"
            }


class DesearchTwitterSearchTool(BaseTool):
    """Desearch Twitter Search Tool for social media search"""

    name: str = "desearch_twitter_search"
    description: str = "Search Twitter/X for posts and links"
    parameters: dict = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query"
            },
            "search_type": {
                "type": "string",
                "description": "Type of Twitter search",
                "default": "posts",
                "enum": ["posts", "links"]
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of results to return",
                "default": 10,
                "minimum": 1,
                "maximum": 50
            }
        },
        "required": ["query"]
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._validate_api_key()

    def _validate_api_key(self):
        """Validate that the Desearch API key is available"""
        api_key = os.getenv('DESEARCH_API_KEY')
        if not api_key:
            raise ValueError("DESEARCH_API_KEY environment variable is required")

    async def execute(self, query: str, search_type: str = "posts", limit: int = 10) -> Dict[str, Any]:
        """Execute Twitter search"""
        try:
            if search_type == "links":
                result = await search_twitter_links(query=query, limit=limit)
            else:
                result = await search_twitter_posts(query=query, limit=limit)

            return {
                "success": True,
                "data": result,
                "tool": "desearch_twitter_search"
            }

        except Exception as e:
            logger.error(f"Desearch Twitter search failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "tool": "desearch_twitter_search"
            }


# Export all tools
__all__ = [
    "DesearchAISearchTool",
    "DesearchWebSearchTool",
    "DesearchAcademicSearchTool",
    "DesearchTwitterSearchTool"
]
