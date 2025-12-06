"""
Designer Agents Module - Node designers for workflow graph construction

This module provides specialized agents that design individual workflow nodes
from parsed WorkflowSpec components. Each designer handles a specific node type
and creates React Flow-compatible node specifications.

Agents:
- TriggerDesignerAgent: Price and time trigger nodes
- SwapDesignerAgent: Flamingo token swap nodes
- StakeDesignerAgent: Flamingo staking nodes
- TransferDesignerAgent: NEP-17 transfer nodes

Parallel Execution:
The design_workflow_nodes function runs all designers in parallel using
asyncio.gather for optimal performance.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from pydantic import ValidationError

from app.models.workflow_models import (
    WorkflowSpec,
    SwapAction,
    StakeAction,
    TransferAction,
)

from .base import BaseDesignerAgent, NodeSpecification, NodePosition
from .trigger_designer import TriggerDesignerAgent, create_trigger_designer
from .swap_designer import SwapDesignerAgent, create_swap_designer
from .stake_designer import StakeDesignerAgent, create_stake_designer
from .transfer_designer import TransferDesignerAgent, create_transfer_designer

logger = logging.getLogger(__name__)


# ============================================================================
# Layout Constants
# ============================================================================

# Horizontal position for centered vertical layout
NODE_X_POSITION = 250

# Vertical spacing between nodes in pixels
NODE_Y_SPACING = 150


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    # Base classes
    "BaseDesignerAgent",
    "NodeSpecification",
    "NodePosition",

    # Designer agents
    "TriggerDesignerAgent",
    "SwapDesignerAgent",
    "StakeDesignerAgent",
    "TransferDesignerAgent",

    # Factory functions
    "create_trigger_designer",
    "create_swap_designer",
    "create_stake_designer",
    "create_transfer_designer",

    # Parallel execution
    "design_workflow_nodes",
]


# ============================================================================
# Parallel Workflow Design
# ============================================================================

async def design_workflow_nodes(
    workflow_spec: WorkflowSpec,
    llm: Optional = None
) -> List[NodeSpecification]:
    """
    Design all nodes for a workflow in parallel.

    This function creates designer agents for each node type and runs them
    in parallel using asyncio.gather for maximum performance.

    Args:
        workflow_spec: Parsed workflow specification
        llm: Optional ChatBot instance (ignored - kept for API compatibility)

    Returns:
        List[NodeSpecification]: Complete list of node specs for React Flow

    Example:
        ```python
        workflow = await parser.parse_workflow("Swap GAS to NEO when price drops")
        nodes = await design_workflow_nodes(workflow.workflow)

        # nodes[0] = Trigger node
        # nodes[1] = Swap node
        # nodes[2] = ... more action nodes
        ```
    """
    logger.info(f"Designing nodes for workflow: {workflow_spec.name}")

    design_tasks: List[asyncio.Task] = []

    # ========================================================================
    # Pre-instantiate designers ONCE for reuse (optimization)
    # ========================================================================

    trigger_designer = create_trigger_designer()
    swap_designer = create_swap_designer()
    stake_designer = create_stake_designer()
    transfer_designer = create_transfer_designer()

    # Calculate positions for vertical layout
    # Trigger at top, actions below
    current_y = 0

    # ========================================================================
    # Design trigger node
    # ========================================================================

    trigger_position = NodePosition(x=NODE_X_POSITION, y=current_y)

    trigger_task = asyncio.create_task(
        trigger_designer.design_node(
            component=workflow_spec.trigger,
            node_id="trigger_1",
            position=trigger_position
        )
    )
    design_tasks.append(trigger_task)
    current_y += NODE_Y_SPACING

    # ========================================================================
    # Design action nodes
    # ========================================================================

    for i, step in enumerate(workflow_spec.steps):
        action = step.action
        node_id = f"action_{i+1}"
        position = NodePosition(x=NODE_X_POSITION, y=current_y)

        # Select appropriate pre-instantiated designer based on action type
        if isinstance(action, SwapAction):
            designer = swap_designer
        elif isinstance(action, StakeAction):
            designer = stake_designer
        elif isinstance(action, TransferAction):
            designer = transfer_designer
        else:
            logger.warning(f"Unknown action type: {type(action)}")
            continue

        # Create design task
        task = asyncio.create_task(
            designer.design_node(
                component=action,
                node_id=node_id,
                position=position
            )
        )
        design_tasks.append(task)
        current_y += NODE_Y_SPACING

    # ========================================================================
    # Run all designers in parallel
    # ========================================================================

    logger.info(f"Running {len(design_tasks)} designer agents in parallel")

    try:
        # Wait for all design tasks to complete
        node_specs = await asyncio.gather(*design_tasks)

        logger.info(f"Successfully designed {len(node_specs)} nodes")

        return list(node_specs)

    except (ValidationError, ValueError, AttributeError) as e:
        logger.error(f"Error during parallel node design: {e}", exc_info=True)
        raise


# ============================================================================
# Utility Functions
# ============================================================================

def create_edges(nodes: List[NodeSpecification]) -> List[Dict[str, str]]:
    """
    Create React Flow edges connecting nodes sequentially.

    Args:
        nodes: List of node specifications

    Returns:
        List of edge objects for React Flow

    Example:
        ```python
        edges = create_edges(nodes)
        # [
        #   {"id": "e1", "source": "trigger_1", "target": "action_1"},
        #   {"id": "e2", "source": "action_1", "target": "action_2"},
        # ]
        ```
    """
    edges = []

    for i in range(len(nodes) - 1):
        edge = {
            "id": f"e{i+1}",
            "source": nodes[i].id,
            "target": nodes[i+1].id,
            "type": "default",
            "animated": False,
        }
        edges.append(edge)

    return edges


def workflow_to_react_flow(
    nodes: List[NodeSpecification]
) -> Dict[str, Any]:
    """
    Convert node specifications to complete React Flow data structure.

    Args:
        nodes: List of node specifications from design_workflow_nodes

    Returns:
        Dict containing nodes and edges for React Flow

    Example:
        ```python
        nodes = await design_workflow_nodes(workflow)
        react_flow_data = workflow_to_react_flow(nodes)

        # Returns:
        # {
        #   "nodes": [...node specs...],
        #   "edges": [...edge specs...]
        # }
        ```
    """
    # Convert nodes to dicts
    node_dicts = [node.model_dump() for node in nodes]

    # Create edges
    edges = create_edges(nodes)

    return {
        "nodes": node_dicts,
        "edges": edges
    }
