"""Discord tool for SpoonAI social media toolkit"""

import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from spoon_ai.social_media.discord import DiscordClient
from .base import InteractiveToolBase, MessageRequest, MessageResponse

logger = logging.getLogger(__name__)


class DiscordMessageRequest(MessageRequest):
    """Discord message request model"""
    channel_id: Optional[str] = Field(None, description="Discord channel ID to send message to")


class DiscordTool(InteractiveToolBase):
    """Discord tool for sending messages and running interactive bot"""
    
    def __init__(self, agent=None):
        super().__init__(
            name="discord_tool",
            description="Tool for Discord messaging and bot interactions"
        )
        self.discord_client = DiscordClient(agent=agent)
        
    def validate_config(self) -> bool:
        """Validate Discord configuration"""
        if not self.discord_client.config.get("token"):
            self.logger.warning("Missing Discord bot token")
            return False
        return True
    
    async def send_message(self, message: str, channel_id: Optional[str] = None, **kwargs) -> bool:
        """
        Send Discord message
        
        Args:
            message: Message content
            channel_id: Channel ID, uses default channel if None
            **kwargs: Additional parameters
        
        Returns:
            bool: Whether the send was successful
        """
        return await self.discord_client.send(message, channel_id, **kwargs)
    
    async def start_bot(self):
        """Start Discord bot"""
        if not self.validate_config():
            raise ValueError("Discord configuration is invalid")
            
        await self.discord_client.run()
    
    async def stop_bot(self):
        """Stop Discord bot"""
        await self.discord_client.stop()
    
    # Tool interface methods
    async def execute(self, request: DiscordMessageRequest) -> MessageResponse:
        """Execute Discord message sending"""
        try:
            success = await self.send_message(
                message=request.message,
                channel_id=request.channel_id
            )
            
            return MessageResponse(
                success=success,
                message="Message sent successfully" if success else "Failed to send message"
            )
        except Exception as e:
            return MessageResponse(
                success=False,
                message=f"Error: {str(e)}"
            )


# Tool function for direct usage
async def send_discord_message(message: str, channel_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Send a Discord message
    
    Args:
        message: Message content to send
        channel_id: Optional Discord channel ID
        
    Returns:
        Dict with success status and message
    """
    tool = DiscordTool()
    
    if not tool.validate_config():
        return {
            "success": False,
            "message": "Discord configuration is invalid"
        }
    
    success = await tool.send_message(message, channel_id)
    
    return {
        "success": success,
        "message": "Message sent successfully" if success else "Failed to send message"
    } 