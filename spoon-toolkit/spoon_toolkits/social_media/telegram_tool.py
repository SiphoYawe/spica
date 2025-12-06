"""Telegram tool for SpoonAI social media toolkit"""

import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from spoon_ai.social_media.telegram import TelegramClient
from .base import InteractiveToolBase, MessageRequest, MessageResponse

logger = logging.getLogger(__name__)


class TelegramMessageRequest(MessageRequest):
    """Telegram message request model"""
    chat_id: Optional[str] = Field(None, description="Telegram chat ID to send message to")


class TelegramTool(InteractiveToolBase):
    """Telegram tool for sending messages and running interactive bot"""
    
    def __init__(self, agent=None):
        super().__init__(
            name="telegram_tool",
            description="Tool for Telegram messaging and bot interactions"
        )
        self.telegram_client = TelegramClient(agent) if agent else None
        self.default_chat_id = "0000000000"
        
    def validate_config(self) -> bool:
        """Validate Telegram configuration"""
        import os
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not bot_token:
            self.logger.warning("Missing Telegram bot token")
            return False
        return True
    
    async def send_proactive_message(self, text: str, chat_id: Optional[str] = None):
        """Send a proactive message (keep original method name for compatibility)"""
        if self.telegram_client:
            await self.telegram_client.send_proactive_message(text, chat_id or self.default_chat_id)
        else:
            # If no agent provided, create temporary client to send message
            from spoon_ai.agents.toolcall import ToolCallAgent
            temp_agent = ToolCallAgent()
            temp_client = TelegramClient(temp_agent)
            await temp_client.send_proactive_message(text, chat_id or self.default_chat_id)
    
    async def send_message(self, message: str, chat_id: Optional[str] = None, **kwargs) -> bool:
        """
        Send Telegram message
        
        Args:
            message: Message content
            chat_id: Chat ID, uses default chat ID if None
            **kwargs: Additional parameters
        
        Returns:
            bool: Whether the send was successful
        """
        try:
            await self.send_proactive_message(message, chat_id)
            self.logger.info(f"Telegram message sent to chat {chat_id or self.default_chat_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to send Telegram message: {str(e)}")
            return False
    
    async def start_bot(self):
        """Start Telegram bot"""
        if not self.validate_config():
            raise ValueError("Telegram configuration is invalid")
            
        if not self.telegram_client:
            raise ValueError("Telegram client not initialized - agent required for bot mode")
            
        await self.telegram_client.run()
    
    async def stop_bot(self):
        """Stop Telegram bot"""
        if self.telegram_client:
            await self.telegram_client.stop()
    
    # Tool interface methods
    async def execute(self, request: TelegramMessageRequest) -> MessageResponse:
        """Execute Telegram message sending"""
        try:
            success = await self.send_message(
                message=request.message,
                chat_id=request.chat_id
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
async def send_telegram_message(message: str, chat_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Send a Telegram message
    
    Args:
        message: Message content to send
        chat_id: Optional Telegram chat ID
        
    Returns:
        Dict with success status and message
    """
    tool = TelegramTool()
    
    if not tool.validate_config():
        return {
            "success": False,
            "message": "Telegram configuration is invalid"
        }
    
    success = await tool.send_message(message, chat_id)
    
    return {
        "success": success,
        "message": "Message sent successfully" if success else "Failed to send message"
    } 