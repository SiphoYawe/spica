"""
Services package - Business logic and external integrations.

This package contains service classes that handle:
- Neo N3 blockchain interactions (neo_service)
- SpoonOS agent management (spoon_service)
- Wallet management (wallet_service)
- Graph assembly and workflow execution (graph_assembler)
- Workflow storage and persistence (workflow_storage)
"""

from app.services.neo_service import NeoService, get_neo_service, close_neo_service
from app.services.graph_assembler import GraphAssembler, get_graph_assembler
from app.services.workflow_storage import WorkflowStorage, get_workflow_storage

__all__ = [
    # Neo blockchain service
    "NeoService",
    "get_neo_service",
    "close_neo_service",

    # Graph assembly service
    "GraphAssembler",
    "get_graph_assembler",

    # Workflow storage service
    "WorkflowStorage",
    "get_workflow_storage",
]
