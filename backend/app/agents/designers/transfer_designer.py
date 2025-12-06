"""
TransferDesignerAgent - Designs transfer action nodes for NEP-17 token transfers
"""

import logging
from typing import Optional

from app.models.workflow_models import TransferAction
from .base import BaseDesignerAgent, NodeSpecification, NodePosition

logger = logging.getLogger(__name__)


# ============================================================================
# TransferDesignerAgent
# ============================================================================

class TransferDesignerAgent(BaseDesignerAgent):
    """
    Designer agent for transfer action nodes.

    Creates specifications for NEP-17 token transfers in the workflow graph
    using deterministic formatting logic (no LLM required).
    """

    name: str = "transfer_designer"
    description: str = "Designs transfer action nodes for NEP-17 transfers"

    node_type: str = "transfer"
    icon: str = "transfer"

    async def design_node(
        self,
        component: TransferAction,
        node_id: str,
        position: Optional[NodePosition] = None
    ) -> NodeSpecification:
        """
        Design a transfer node from a transfer action.

        Args:
            component: TransferAction instance
            node_id: Unique identifier
            position: Optional position

        Returns:
            NodeSpecification: Complete transfer node spec
        """
        logger.info(f"Designing transfer node: {node_id}")

        # Create label
        label = self._create_transfer_label(component)

        # Extract parameters
        parameters = component.model_dump()

        # Create and return node spec
        return self._create_node_spec(
            node_id=node_id,
            label=label,
            parameters=parameters,
            position=position
        )

    def _create_transfer_label(self, action: TransferAction) -> str:
        """
        Create human-readable label for transfer action.

        Args:
            action: TransferAction instance

        Returns:
            str: Formatted label like "Transfer 10 GAS to Nabc...xyz"
        """
        token = action.token.value

        # Format amount
        amount_str = self._format_amount(action.amount, action.percentage)

        # Shorten address
        address = action.to_address
        short_address = self._shorten_address(address)

        # Build label
        return f"Transfer {amount_str} {token} to {short_address}"

    def _shorten_address(self, address: str) -> str:
        """
        Shorten Neo N3 address for display in UI labels.

        Neo N3 addresses are 34 characters long and start with 'N'.
        This function creates a compact representation showing just the
        beginning and end of the address for readability.

        Address shortening format: First 4 characters + "..." + Last 3 characters
        Example: "NabcdefghijklmnopqrstuvwxyzABCD" → "Nabc...BCD"

        Args:
            address: Full Neo N3 address (34 chars starting with 'N')

        Returns:
            str: Shortened address like "Nabc...xyz" for display purposes
        """
        if len(address) <= 10:
            return address

        # Show first 4 chars (including 'N' prefix) and last 3 chars
        return f"{address[:4]}...{address[-3:]}"


# ============================================================================
# Factory Function
# ============================================================================

def create_transfer_designer(llm: Optional = None) -> TransferDesignerAgent:
    """
    Factory function to create a TransferDesignerAgent.

    Args:
        llm: Optional ChatBot instance (ignored - kept for API compatibility)

    Returns:
        TransferDesignerAgent: Configured designer agent
    """
    return TransferDesignerAgent()
