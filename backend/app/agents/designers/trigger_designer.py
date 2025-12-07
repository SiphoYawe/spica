"""
TriggerDesignerAgent - Designs trigger nodes (price/time conditions)
"""

import logging
import re
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

        # Extract parameters and add frontend-compatible fields
        parameters = component.model_dump()

        # For time triggers, parse schedule into structured fields for frontend
        if isinstance(component, TimeCondition):
            parsed_time = self._parse_time_schedule(component.schedule)
            parameters.update(parsed_time)

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

    def _parse_time_schedule(self, schedule: str) -> dict:
        """
        Parse a time schedule string into structured fields for frontend.

        The frontend expects:
        - interval: "daily", "weekly", "monthly"
        - dayOfWeek: "monday", "tuesday", etc. (for weekly)
        - dayOfMonth: 1-28 (for monthly)
        - time: "HH:MM" format

        Args:
            schedule: Natural language schedule like "every Monday at 9am"

        Returns:
            dict with structured time fields
        """
        schedule_lower = schedule.lower().strip()
        result = {
            "interval": "daily",
            "time": "09:00",
        }

        # Parse interval
        if "weekly" in schedule_lower or "every monday" in schedule_lower or "every tuesday" in schedule_lower or \
           "every wednesday" in schedule_lower or "every thursday" in schedule_lower or "every friday" in schedule_lower or \
           "every saturday" in schedule_lower or "every sunday" in schedule_lower:
            result["interval"] = "weekly"

            # Determine day of week
            days = {
                "monday": "monday", "tuesday": "tuesday", "wednesday": "wednesday",
                "thursday": "thursday", "friday": "friday", "saturday": "saturday", "sunday": "sunday"
            }
            for day_name, day_value in days.items():
                if day_name in schedule_lower:
                    result["dayOfWeek"] = day_value
                    break
            else:
                result["dayOfWeek"] = "monday"  # Default

        elif "monthly" in schedule_lower:
            result["interval"] = "monthly"
            result["dayOfMonth"] = 1  # Default

            # Try to extract day number
            day_match = re.search(r'(\d+)(st|nd|rd|th)?', schedule_lower)
            if day_match:
                day = int(day_match.group(1))
                if 1 <= day <= 28:
                    result["dayOfMonth"] = day

        else:
            result["interval"] = "daily"

        # Parse time
        # Match patterns like "9am", "10:30am", "14:00", "at 9am"
        time_patterns = [
            r'(\d{1,2}):(\d{2})\s*(am|pm)',  # 9:00am, 10:30pm
            r'(\d{1,2})(am|pm)',              # 9am, 10pm
            r'(\d{1,2}):(\d{2})',              # 14:00, 09:30 (24h format)
        ]

        for pattern in time_patterns:
            match = re.search(pattern, schedule_lower)
            if match:
                groups = match.groups()
                if len(groups) == 3:  # 9:00am format
                    hour, minute, period = int(groups[0]), groups[1], groups[2]
                    if period == "pm" and hour != 12:
                        hour += 12
                    elif period == "am" and hour == 12:
                        hour = 0
                    result["time"] = f"{hour:02d}:{minute}"
                elif len(groups) == 2:
                    if groups[1] in ("am", "pm"):  # 9am format
                        hour, period = int(groups[0]), groups[1]
                        if period == "pm" and hour != 12:
                            hour += 12
                        elif period == "am" and hour == 12:
                            hour = 0
                        result["time"] = f"{hour:02d}:00"
                    else:  # 14:00 format
                        result["time"] = f"{int(groups[0]):02d}:{groups[1]}"
                break

        return result

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
