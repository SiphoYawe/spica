"""
StakeDesignerAgent - Designs stake action nodes for Flamingo staking
"""

import logging
from typing import Optional

from app.models.workflow_models import StakeAction
from .base import BaseDesignerAgent, NodeSpecification, NodePosition

logger = logging.getLogger(__name__)


# ============================================================================
# StakeDesignerAgent
# ============================================================================

class StakeDesignerAgent(BaseDesignerAgent):
    """
    Designer agent for stake action nodes.

    Creates specifications for Flamingo staking operations in the workflow graph
    using deterministic formatting logic (no LLM required).
    """

    name: str = "stake_designer"
    description: str = "Designs stake action nodes for Flamingo staking"

    node_type: str = "stake"
    icon: str = "stake"

    async def design_node(
        self,
        component: StakeAction,
        node_id: str,
        position: Optional[NodePosition] = None
    ) -> NodeSpecification:
        """
        Design a stake node from a stake action.

        Args:
            component: StakeAction instance
            node_id: Unique identifier
            position: Optional position

        Returns:
            NodeSpecification: Complete stake node spec
        """
        logger.info(f"Designing stake node: {node_id}")

        # Create label
        label = self._create_stake_label(component)

        # Extract parameters
        parameters = component.model_dump()

        # Create and return node spec
        return self._create_node_spec(
            node_id=node_id,
            label=label,
            parameters=parameters,
            position=position
        )

    def _create_stake_label(self, action: StakeAction) -> str:
        """
        Create human-readable label for stake action.

        Args:
            action: StakeAction instance

        Returns:
            str: Formatted label like "Stake 100 NEO"
        """
        token = action.token.value

        # Format amount
        amount_str = self._format_amount(action.amount, action.percentage)

        # Build label
        return f"Stake {amount_str} {token}"


# ============================================================================
# Factory Function
# ============================================================================

def create_stake_designer(llm: Optional = None) -> StakeDesignerAgent:
    """
    Factory function to create a StakeDesignerAgent.

    Args:
        llm: Optional ChatBot instance (ignored - kept for API compatibility)

    Returns:
        StakeDesignerAgent: Configured designer agent
    """
    return StakeDesignerAgent()
