# SpoonOS agents package
"""
Agent module exports - handles missing spoon_ai gracefully for testing.
"""

import logging

logger = logging.getLogger(__name__)

# Designer agents (do NOT require spoon_ai)
from .designers import (
    BaseDesignerAgent,
    TriggerDesignerAgent,
    SwapDesignerAgent,
    StakeDesignerAgent,
    TransferDesignerAgent,
    create_trigger_designer,
    create_swap_designer,
    create_stake_designer,
    create_transfer_designer,
    design_workflow_nodes,
    NodeSpecification,
    NodePosition,
)

# WorkflowParser requires spoon_ai - handle gracefully
try:
    from .workflow_parser import WorkflowParserAgent, create_workflow_parser
    SPOON_AI_AVAILABLE = True
except ImportError:
    WorkflowParserAgent = None
    create_workflow_parser = None
    SPOON_AI_AVAILABLE = False
    logger.warning("spoon_ai package not available - WorkflowParserAgent disabled")

__all__ = [
    # Workflow parser (may be None if spoon_ai unavailable)
    "WorkflowParserAgent",
    "create_workflow_parser",
    "SPOON_AI_AVAILABLE",

    # Designer agents
    "BaseDesignerAgent",
    "TriggerDesignerAgent",
    "SwapDesignerAgent",
    "StakeDesignerAgent",
    "TransferDesignerAgent",

    # Designer factories
    "create_trigger_designer",
    "create_swap_designer",
    "create_stake_designer",
    "create_transfer_designer",

    # Parallel execution
    "design_workflow_nodes",

    # Models
    "NodeSpecification",
    "NodePosition",
]
