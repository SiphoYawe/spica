"""Mem0-powered memory tools ."""

import logging
from typing import Any, Dict, List, Optional, Callable

from pydantic import Field

from spoon_ai.memory.mem0_client import SpoonMem0
from spoon_ai.tools.base import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class Mem0ToolBase(BaseTool):
    """Base class handling client injection, config, and standardized execution."""

    mem0_config: Dict[str, Any] = Field(default_factory=dict, description="Mem0 client configuration")
    mem0_client: Optional[SpoonMem0] = Field(default=None, description="Optional injected SpoonMem0 client")
    default_user_id: Optional[str] = Field(default=None, description="Default user/agent id")

    def model_post_init(self, __context: Any = None) -> None:
        super().model_post_init(__context)
        if self.mem0_client is None:
            self.mem0_client = SpoonMem0(self.mem0_config)
        
        self.default_user_id = (
            self.default_user_id
            or self.mem0_config.get("user_id")
            or self.mem0_config.get("agent_id")
            or getattr(self.mem0_client, "user_id", None)
        )

    def _get_client(self) -> Optional[Any]:
        """Return raw mem0 client if ready."""
        if self.mem0_client and self.mem0_client.is_ready():
            return self.mem0_client.client
        return None

    def _build_params(self, 
                      user_id: Optional[str] = None, 
                      metadata: Optional[Dict] = None, 
                      filters: Optional[Dict] = None, 
                      **kwargs) -> Dict[str, Any]:
        """
        Unified parameter builder. Merges defaults with runtime args and removes Nones.
        """
        runtime_args = {k: v for k, v in kwargs.items() if v is not None}

        final_user_id = user_id or self.default_user_id
        if final_user_id:
            runtime_args["user_id"] = final_user_id

        if hasattr(self.mem0_client, "collection") and self.mem0_client.collection:
            runtime_args.setdefault("collection", self.mem0_client.collection)

        client_meta = getattr(self.mem0_client, "metadata", {}) or {}
        if client_meta or metadata:
            runtime_args["metadata"] = {**client_meta, **(metadata or {})}

        client_filters = getattr(self.mem0_client, "filters", {}) or {}

        if final_user_id and "user_id" not in client_filters:
            client_filters["user_id"] = final_user_id
        
        if client_filters or filters:
            runtime_args["filters"] = {**client_filters, **(filters or {})}

        return runtime_args

    async def _safe_run(self, operation: Callable, **kwargs) -> ToolResult:
        """
        Centralized error handling and client validation.
        Removes the need for try-except in every tool.
        """
        client = self._get_client()
        if not client:
            return ToolResult(error="Mem0 client is not initialized; check config.")

        try:
            result = operation(**kwargs)
            return ToolResult(output=result)
        except Exception as exc:
            action_name = operation.__name__ if hasattr(operation, "__name__") else "operation"
            logger.warning(f"Mem0 {action_name} failed: {exc}")
            return ToolResult(error=f"Mem0 error: {str(exc)}")


class AddMemoryTool(Mem0ToolBase):
    name: str = "add_memory"
    description: str = "Store text or conversation snippets in Mem0."
    parameters: dict = {
        "type": "object",
        "properties": {
             "content": {"type": "string", "description": "Text to store"},
             "messages": {"type": "array", "items": {"type": "object"}},
             "role": {"type": "string", "default": "user"},
             "user_id": {"type": "string"},
             "metadata": {"type": "object"},
             "filters": {"type": "object"},
             "async_mode": {"type": "boolean"}
        }
    }

    async def execute(self, content: str = None, messages: list = None, role: str = "user", **kwargs) -> ToolResult:
        client = self._get_client()
        if not client: return ToolResult(error="Client not ready")

        messages = messages or []
        if content:
            messages.append({"role": role, "content": content})
        
        if not messages:
            return ToolResult(error="No content provided.")

        payload = [
            m if isinstance(m, dict) else {"role": "user", "content": str(m)}
            for m in messages
        ]

        params = self._build_params(**kwargs)
        if kwargs.get('async_mode') is not None:
            params['async_mode'] = kwargs['async_mode']

        return await self._safe_run(client.add, messages=payload, **params)


class SearchMemoryTool(Mem0ToolBase):
    name: str = "search_memory"
    description: str = "Search Mem0 using natural language."
    parameters: dict = {
        "type": "object", 
        "properties": {
            "query": {"type": "string"},
            "user_id": {"type": "string"},
            "limit": {"type": "integer"}, 
            "top_k": {"type": "integer"},
            "filters": {"type": "object"}
        },
        "required": ["query"]
    }

    async def execute(self, query: str, limit: int = None, top_k: int = None, **kwargs) -> ToolResult:
        client = self._get_client()
        if not client: return ToolResult(error="Client not ready")
        
        params = self._build_params(top_k=(top_k if top_k is not None else limit), **kwargs)
        
        return await self._safe_run(client.search, query=query, **params)


class GetAllMemoryTool(Mem0ToolBase):
    name: str = "get_all_memory"
    description: str = "Fetch all stored memories."
    parameters: dict = {
        "type": "object",
        "properties": {
            "user_id": {"type": "string"},
            "page": {"type": "integer"},
            "page_size": {"type": "integer"},
            "limit": {"type": "integer"},
            "top_k": {"type": "integer"},
            "filters": {"type": "object"}
        }
    }

    async def execute(
        self,
        page: int = None,
        page_size: int = None,
        limit: int = None,
        top_k: int = None,
        **kwargs,
    ) -> ToolResult:
        client = self._get_client()
        if not client: return ToolResult(error="Client not ready")

        default_limit = getattr(self.mem0_client, "limit", None)
        final_size = page_size or limit or default_limit

        params = self._build_params(page=page, page_size=final_size, top_k=top_k or limit, **kwargs)
        return await self._safe_run(client.get_all, **params)


class UpdateMemoryTool(Mem0ToolBase):
    name: str = "update_memory"
    description: str = "Update a stored memory by ID."
    parameters: dict = {
        "type": "object",
        "properties": {
            "memory_id": {"type": "string"},
            "text": {"type": "string"},
            "metadata": {"type": "object"},
            "user_id": {"type": "string"}
        },
        "required": ["memory_id"]
    }

    async def execute(self, memory_id: str, text: str = None, metadata: dict = None, **kwargs) -> ToolResult:
        if not text and not metadata:
            return ToolResult(error="Provide text or metadata to update.")
            
        client = self._get_client()
        if not client: return ToolResult(error="Client not ready")

        # Build params but exclude metadata to avoid conflict with explicit parameter
        params = self._build_params(metadata=None, **kwargs)
        # Merge explicit metadata with params metadata if both exist
        if metadata:
            if "metadata" in params:
                params["metadata"] = {**params["metadata"], **metadata}
            else:
                params["metadata"] = metadata
        
        # MemoryClient.update() only accepts memory_id, text, metadata
        # Remove unsupported parameters like user_id, collection, filters
        update_params = {k: v for k, v in params.items() if k in ("metadata",)}
        
        return await self._safe_run(client.update, memory_id=memory_id, text=text, **update_params)


class DeleteMemoryTool(Mem0ToolBase):
    name: str = "delete_memory"
    description: str = "Delete a stored memory by ID."
    parameters: dict = {
        "type": "object", 
        "properties": {
            "memory_id": {"type": "string"},
            "user_id": {"type": "string"}
        }, 
        "required": ["memory_id"]
    }

    async def execute(self, memory_id: str, **kwargs) -> ToolResult:
        client = self._get_client()
        if not client: return ToolResult(error="Client not ready")
        
        # MemoryClient.delete() only accepts memory_id, not user_id or other params
        # So we don't pass any additional params to delete()
        return await self._safe_run(client.delete, memory_id=memory_id)

__all__ = [
    "AddMemoryTool",
    "SearchMemoryTool",
    "GetAllMemoryTool",
    "UpdateMemoryTool",
    "DeleteMemoryTool",
]
