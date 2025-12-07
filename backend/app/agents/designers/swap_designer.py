"""
SwapDesignerAgent - Designs swap action nodes for Flamingo token swaps
"""

import logging
from typing import Optional

from app.models.workflow_models import SwapAction
from .base import BaseDesignerAgent, NodeSpecification, NodePosition

logger = logging.getLogger(__name__)


# ============================================================================
# SwapDesignerAgent
# ============================================================================

class SwapDesignerAgent(BaseDesignerAgent):
    """
    Designer agent for swap action nodes.

    Creates specifications for Flamingo swap operations in the workflow graph
    using deterministic formatting logic (no LLM required).
    """

    name: str = "swap_designer"
    description: str = "Designs swap action nodes for Flamingo token exchanges"

    node_type: str = "swap"
    icon: str = "swap"

    async def design_node(
        self,
        component: SwapAction,
        node_id: str,
        position: Optional[NodePosition] = None
    ) -> NodeSpecification:
        """
        Design a swap node from a swap action.

        Args:
            component: SwapAction instance
            node_id: Unique identifier
            position: Optional position

        Returns:
            NodeSpecification: Complete swap node spec
        """
        logger.info(f"Designing swap node: {node_id}")

        # Create label
        label = self._create_swap_label(component)

        # Extract parameters and add frontend-compatible fields
        parameters = component.model_dump()

        # Add amountType for frontend compatibility
        # Frontend expects "fixed" or "percentage", not separate fields
        parameters["amountType"] = "percentage" if component.percentage is not None else "fixed"

        # Normalize amount field - frontend expects single "amount" field
        if component.percentage is not None:
            parameters["amount"] = component.percentage

        # Create and return node spec
        return self._create_node_spec(
            node_id=node_id,
            label=label,
            parameters=parameters,
            position=position
        )

    def _create_swap_label(self, action: SwapAction) -> str:
        """
        Create human-readable label for swap action.

        Args:
            action: SwapAction instance

        Returns:
            str: Formatted label like "Swap 10 GAS → NEO"
        """
        from_token = action.from_token.value
        to_token = action.to_token.value

        # Format amount
        amount_str = self._format_amount(action.amount, action.percentage)

        # Build label with arrow
        return f"Swap {amount_str} {from_token} → {to_token}"


# ============================================================================
# Factory Function
# ============================================================================

def create_swap_designer(llm: Optional = None) -> SwapDesignerAgent:
    """
    Factory function to create a SwapDesignerAgent.

    Args:
        llm: Optional ChatBot instance (ignored - kept for API compatibility)

    Returns:
        SwapDesignerAgent: Configured designer agent
    """
    return SwapDesignerAgent()
