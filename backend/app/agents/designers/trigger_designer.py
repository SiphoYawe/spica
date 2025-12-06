"""
TriggerDesignerAgent - Designs trigger nodes (price/time conditions)
"""

import logging
from typing import Optional, Union

from app.models.workflow_models import PriceCondition, TimeCondition, TriggerCondition
from .base import BaseDesignerAgent, NodeSpecification, NodePosition

logger = logging.getLogger(__name__)


# ============================================================================
# TriggerDesignerAgent
# ============================================================================

class TriggerDesignerAgent(BaseDesignerAgent):
    """
    Designer agent for trigger nodes.

    Handles both price and time triggers, creating user-friendly
    labels and specifications for the workflow graph using deterministic
    formatting logic (no LLM required).
    """

    name: str = "trigger_designer"
    description: str = "Designs trigger nodes for price and time conditions"

    node_type: str = "trigger"
    icon: str = "trigger"

    async def design_node(
        self,
        component: TriggerCondition,
        node_id: str,
        position: Optional[NodePosition] = None
    ) -> NodeSpecification:
        """
        Design a trigger node from a trigger condition.

        Args:
            component: PriceCondition or TimeCondition
            node_id: Unique identifier
            position: Optional position

        Returns:
            NodeSpecification: Complete trigger node spec
        """
        logger.info(f"Designing trigger node: {node_id}")

        # Create label based on trigger type
        if isinstance(component, PriceCondition):
            label = self._create_price_label(component)
        elif isinstance(component, TimeCondition):
            label = self._create_time_label(component)
        else:
            label = f"Trigger: {component.type}"

        # Extract parameters
        parameters = component.model_dump()

        # Create and return node spec
        return self._create_node_spec(
            node_id=node_id,
            label=label,
            parameters=parameters,
            position=position
        )

    def _create_price_label(self, condition: PriceCondition) -> str:
        """
        Create human-readable label for price trigger.

        Args:
            condition: PriceCondition instance

        Returns:
            str: Formatted label like "GAS price below $5.00"
        """
        token = condition.token.value
        operator = condition.operator
        value = condition.value

        # Format operator
        operator_text = {
            "above": "above",
            "below": "below",
            "equals": "equals"
        }.get(operator, operator)

        # Format price with 2 decimal places
        price_str = f"${value:.2f}"

        return f"{token} price {operator_text} {price_str}"

    def _create_time_label(self, condition: TimeCondition) -> str:
        """
        Create human-readable label for time trigger.

        Args:
            condition: TimeCondition instance

        Returns:
            str: Formatted label like "Daily at 9:00 AM"
        """
        schedule = condition.schedule

        # Normalize common patterns
        schedule_lower = schedule.lower().strip()

        # Handle common patterns
        if "daily" in schedule_lower or "every day" in schedule_lower:
            if "at" in schedule_lower:
                # Extract time
                parts = schedule_lower.split("at")
                if len(parts) > 1:
                    time_part = parts[1].strip()
                    return f"Daily at {self._format_time(time_part)}"
            return "Daily"

        if "every monday" in schedule_lower or "mondays" in schedule_lower:
            if "at" in schedule_lower:
                parts = schedule_lower.split("at")
                if len(parts) > 1:
                    time_part = parts[1].strip()
                    return f"Every Monday at {self._format_time(time_part)}"
            return "Every Monday"

        if "every" in schedule_lower and "minute" in schedule_lower:
            # Extract number
            words = schedule_lower.split()
            for i, word in enumerate(words):
                if word == "every" and i + 1 < len(words):
                    next_word = words[i + 1]
                    if next_word.isdigit():
                        return f"Every {next_word} minutes"
            return "Every 15 minutes"  # Default

        # If we can't parse it nicely, capitalize it properly
        return schedule.title()

    def _format_time(self, time_str: str) -> str:
        """
        Format time string consistently.

        Args:
            time_str: Time string like "9am", "10:30am", "14:00"

        Returns:
            str: Formatted time like "9:00 AM"
        """
        time_str = time_str.strip().lower()

        # Handle "9am" -> "9:00 AM"
        if "am" in time_str or "pm" in time_str:
            if ":" not in time_str:
                # Add :00
                time_str = time_str.replace("am", ":00 AM").replace("pm", ":00 PM")
            else:
                time_str = time_str.replace("am", " AM").replace("pm", " PM")
            return time_str.upper()

        # Handle 24-hour format
        if ":" in time_str:
            parts = time_str.split(":")
            if len(parts) == 2:
                try:
                    hour = int(parts[0])
                    minute = parts[1]

                    if hour >= 12:
                        period = "PM"
                        if hour > 12:
                            hour -= 12
                    else:
                        period = "AM"
                        if hour == 0:
                            hour = 12

                    return f"{hour}:{minute} {period}"
                except ValueError:
                    pass

        # Fallback
        return time_str.upper()


# ============================================================================
# Factory Function
# ============================================================================

def create_trigger_designer(llm: Optional = None) -> TriggerDesignerAgent:
    """
    Factory function to create a TriggerDesignerAgent.

    Args:
        llm: Optional ChatBot instance (ignored - kept for API compatibility)

    Returns:
        TriggerDesignerAgent: Configured designer agent
    """
    return TriggerDesignerAgent()
