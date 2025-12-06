"""Base classes for social media tools"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SocialMediaToolBase(ABC):
    """Base class for all social media tools"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @abstractmethod
    async def send_message(self, message: str, **kwargs) -> bool:
        """Send a message through the social media platform"""
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """Validate the configuration for the social media platform"""
        pass


class MessageRequest(BaseModel):
    """Base request model for sending messages"""
    message: str = Field(..., description="The message content to send")
    
    
class MessageResponse(BaseModel):
    """Base response model for message operations"""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Response message or error description")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional response data")


class NotificationToolBase(SocialMediaToolBase):
    """Base class for notification tools"""
    
    async def send_notification(self, message: str, tags: Optional[List[str]] = None, **kwargs) -> bool:
        """
        Send a notification message
        
        Args:
            message: Notification content
            tags: Optional tags to include
            **kwargs: Additional parameters
            
        Returns:
            bool: Whether the notification was sent successfully
        """
        try:
            return await self.send_message(message, tags=tags, **kwargs)
        except Exception as e:
            self.logger.error(f"Failed to send notification: {str(e)}")
            return False


class InteractiveToolBase(SocialMediaToolBase):
    """Base class for interactive social media tools (bots)"""
    
    @abstractmethod
    async def start_bot(self):
        """Start the interactive bot"""
        pass
    
    @abstractmethod
    async def stop_bot(self):
        """Stop the interactive bot"""
        pass 