"""
Base Designer Agent - Abstract base class for all node designer agents.

All designer agents extend this base class to provide consistent interface
for designing workflow nodes from WorkflowSpec components.

ARCHITECTURE NOTE:
Designer agents are simple data formatters that convert workflow specifications
into React Flow node specifications using deterministic Python logic. They do NOT
use LLM reasoning - just pure data transformation.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)


# ============================================================================
# Node Specification Models
# ============================================================================

class NodePosition(BaseModel):
    """Position for React Flow node layout"""
    x: int = 0
    y: int = 0


class NodeData(BaseModel):
    """React Flow node data"""
    label: str
    icon: str = ""
    status: str = "pending"


class NodeSpecification(BaseModel):
    """
    Complete node specification for React Flow.

    This is the standardized output format for all designer agents.
    """
    id: str
    type: str  # "trigger", "swap", "stake", "transfer"
    label: str
    parameters: Dict[str, Any]
    position: NodePosition
    data: NodeData


# ============================================================================
# Base Designer Agent
# ============================================================================

class BaseDesignerAgent(ABC):
    """
    Abstract base class for all node designer agents.

    Designer agents are data formatters responsible for:
    1. Converting WorkflowSpec components (triggers/actions) to node specs
    2. Generating human-readable labels from structured data
    3. Formatting parameters for React Flow visualization

    These agents use deterministic logic, not LLM reasoning.
    """

    # Subclasses must override these
    node_type: str = ""  # "trigger", "swap", "stake", "transfer"
    icon: str = ""  # Icon identifier for frontend
    name: str = ""  # Agent name
    description: str = ""  # Agent description

    def __init__(self):
        """Initialize the designer agent."""
        logger.info(f"Initialized {self.__class__.__name__}")

    @abstractmethod
    async def design_node(
        self,
        component: Any,
        node_id: str,
        position: Optional[NodePosition] = None
    ) -> NodeSpecification:
        """
        Design a node from a workflow component.

        Args:
            component: Trigger or Action model from WorkflowSpec
            node_id: Unique identifier for this node
            position: Optional position override

        Returns:
            NodeSpecification: Complete node spec for React Flow
        """
        pass

    def _create_node_spec(
        self,
        node_id: str,
        label: str,
        parameters: Dict[str, Any],
        position: Optional[NodePosition] = None
    ) -> NodeSpecification:
        """
        Helper to create standardized node specification.

        Args:
            node_id: Unique node identifier
            label: Human-readable label
            parameters: Node-specific parameters
            position: Optional position (defaults to 0,0)

        Returns:
            NodeSpecification: Complete node spec
        """
        if position is None:
            position = NodePosition(x=0, y=0)

        return NodeSpecification(
            id=node_id,
            type=self.node_type,
            label=label,
            parameters=parameters,
            position=position,
            data=NodeData(
                label=label,
                icon=self.icon,
                status="pending"
            )
        )

    def _format_amount(self, amount: Optional[float], percentage: Optional[float]) -> str:
        """
        Format amount or percentage for display.

        Args:
            amount: Fixed amount
            percentage: Percentage of balance

        Returns:
            str: Formatted string like "10" or "50%"

        Raises:
            ValueError: If both amount and percentage are None
        """
        if amount is not None:
            return f"{amount}"
        elif percentage is not None:
            return f"{percentage}%"
        else:
            raise ValueError("Either amount or percentage must be specified")
