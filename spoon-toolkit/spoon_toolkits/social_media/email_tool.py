"""Email tool for SpoonAI social media toolkit"""

import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from spoon_ai.social_media.email import EmailNotifier
from .base import NotificationToolBase, MessageRequest, MessageResponse

logger = logging.getLogger(__name__)


class EmailMessageRequest(MessageRequest):
    """Email message request model"""
    to_emails: Optional[List[str]] = Field(None, description="List of recipient email addresses")
    subject: Optional[str] = Field("Crypto Monitoring Alert", description="Email subject")
    html_format: Optional[bool] = Field(True, description="Whether to send in HTML format")


class EmailTool(NotificationToolBase):
    """Email tool for sending notification emails"""
    
    def __init__(self):
        super().__init__(
            name="email_tool",
            description="Tool for sending email notifications and alerts"
        )
        self.email_notifier = EmailNotifier()
    
    def validate_config(self) -> bool:
        """Validate email configuration"""
        missing = []
        for key in ["smtp_server", "smtp_user", "smtp_password"]:
            if not self.email_notifier.config.get(key):
                missing.append(key)
        
        if missing:
            self.logger.warning(f"Missing email configuration: {', '.join(missing)}")
            return False
        
        return True
    
    async def send_message(self, message: str, to_emails: Optional[List[str]] = None,
                          subject: str = "Crypto Monitoring Alert", 
                          html_format: bool = True, **kwargs) -> bool:
        """
        Send email notification
        
        Args:
            message: Email content
            to_emails: List of recipients, uses default recipients if None
            subject: Email subject
            html_format: Whether to send in HTML format
            **kwargs: Other SMTP parameters
        
        Returns:
            bool: Whether the send was successful
        """
        return self.email_notifier.send(message, to_emails, subject, html_format, **kwargs)
    
    # Tool interface methods
    async def execute(self, request: EmailMessageRequest) -> MessageResponse:
        """Execute email sending"""
        try:
            success = await self.send_message(
                message=request.message,
                to_emails=request.to_emails,
                subject=request.subject or "Crypto Monitoring Alert",
                html_format=request.html_format if request.html_format is not None else True
            )
            
            return MessageResponse(
                success=success,
                message="Email sent successfully" if success else "Failed to send email"
            )
        except Exception as e:
            return MessageResponse(
                success=False,
                message=f"Error: {str(e)}"
            )


# Tool function for direct usage
async def send_email(message: str, to_emails: Optional[List[str]] = None,
                    subject: str = "Crypto Monitoring Alert", 
                    html_format: bool = True) -> Dict[str, Any]:
    """
    Send an email
    
    Args:
        message: Email content
        to_emails: List of recipient email addresses
        subject: Email subject
        html_format: Whether to send in HTML format
        
    Returns:
        Dict with success status and message
    """
    tool = EmailTool()
    
    if not tool.validate_config():
        return {
            "success": False,
            "message": "Email configuration is invalid"
        }
    
    success = await tool.send_message(message, to_emails, subject, html_format)
    
    return {
        "success": success,
        "message": "Email sent successfully" if success else "Failed to send email"
    } 