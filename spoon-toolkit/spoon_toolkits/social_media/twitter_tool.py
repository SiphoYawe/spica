"""Twitter tool for SpoonAI social media toolkit"""

import logging
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from spoon_ai.social_media.twitter import TwitterClient
from .base import NotificationToolBase, MessageRequest, MessageResponse

logger = logging.getLogger(__name__)


class TwitterMessageRequest(MessageRequest):
    """Twitter message request model"""
    tags: Optional[List[str]] = Field(None, description="Tags to include in the tweet")
    reply_to_tweet_id: Optional[str] = Field(None, description="Tweet ID to reply to")


class TwitterTweetRequest(BaseModel):
    """Twitter tweet request model"""
    message: str = Field(..., description="Tweet content")
    

class TwitterReplyRequest(BaseModel):
    """Twitter reply request model"""
    tweet_id: str = Field(..., description="Tweet ID to reply to")
    message: str = Field(..., description="Reply content")


class TwitterLikeRequest(BaseModel):
    """Twitter like request model"""
    tweet_id: str = Field(..., description="Tweet ID to like")


class TwitterTool(NotificationToolBase):
    """Twitter tool for posting tweets, replies, and notifications"""
    
    def __init__(self):
        super().__init__(
            name="twitter_tool",
            description="Tool for Twitter posting, replying, and social media interactions"
        )
        self.twitter_client = TwitterClient()
        
    def validate_config(self) -> bool:
        """Validate Twitter configuration"""
        try:
            self.twitter_client._get_credentials()
            return True
        except Exception as e:
            self.logger.error(f"Twitter configuration validation failed: {e}")
            return False
    
    async def send_message(self, message: str, tags: Optional[List[str]] = None, **kwargs) -> bool:
        """
        Send Twitter notification message
        
        Args:
            message: Notification message content
            tags: List of tags to append
            **kwargs: Other parameters
        
        Returns:
            bool: Whether the sending was successful
        """
        return self.twitter_client.send(message, tags, **kwargs)
    
    def post_tweet(self, message: str, **kwargs) -> dict:
        """Post a new tweet"""
        return self.twitter_client.post_tweet(message, **kwargs)
    
    def reply_to_tweet(self, tweet_id: str, message: str, **kwargs) -> dict:
        """Reply to an existing tweet"""
        return self.twitter_client.reply_to_tweet(tweet_id, message, **kwargs)

    def like_tweet(self, tweet_id: str, **kwargs) -> dict:
        """Like a tweet"""
        return self.twitter_client.like_tweet(tweet_id, **kwargs)
    
    def read_timeline(self, count: int = None, **kwargs) -> list:
        """Read tweets from the user's timeline"""
        return self.twitter_client.read_timeline(count, **kwargs)
    
    def get_tweet_replies(self, tweet_id: str, count: int = 10, **kwargs) -> List[dict]:
        """Fetch replies to a specific tweet"""
        return self.twitter_client.get_tweet_replies(tweet_id, count, **kwargs)
    
    # Tool interface methods
    async def execute_tweet(self, request: TwitterTweetRequest) -> MessageResponse:
        """Execute tweet posting"""
        try:
            result = self.post_tweet(request.message)
            return MessageResponse(
                success=True,
                message="Tweet posted successfully",
                data=result
            )
        except Exception as e:
            return MessageResponse(
                success=False,
                message=f"Error posting tweet: {str(e)}"
            )
    
    async def execute_reply(self, request: TwitterReplyRequest) -> MessageResponse:
        """Execute tweet reply"""
        try:
            result = self.reply_to_tweet(request.tweet_id, request.message)
            return MessageResponse(
                success=True,
                message="Reply posted successfully",
                data=result
            )
        except Exception as e:
            return MessageResponse(
                success=False,
                message=f"Error posting reply: {str(e)}"
            )
    
    async def execute_like(self, request: TwitterLikeRequest) -> MessageResponse:
        """Execute tweet like"""
        try:
            result = self.like_tweet(request.tweet_id)
            return MessageResponse(
                success=True,
                message="Tweet liked successfully",
                data=result
            )
        except Exception as e:
            return MessageResponse(
                success=False,
                message=f"Error liking tweet: {str(e)}"
            )


# Tool functions for direct usage
async def post_tweet(message: str) -> Dict[str, Any]:
    """
    Post a tweet
    
    Args:
        message: Tweet content
        
    Returns:
        Dict with success status and response data
    """
    tool = TwitterTool()
    
    if not tool.validate_config():
        return {
            "success": False,
            "message": "Twitter configuration is invalid"
        }
    
    try:
        result = tool.post_tweet(message)
        return {
            "success": True,
            "message": "Tweet posted successfully",
            "data": result
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error posting tweet: {str(e)}"
        }


async def reply_to_tweet(tweet_id: str, message: str) -> Dict[str, Any]:
    """
    Reply to a tweet
    
    Args:
        tweet_id: ID of the tweet to reply to
        message: Reply content
        
    Returns:
        Dict with success status and response data
    """
    tool = TwitterTool()
    
    if not tool.validate_config():
        return {
            "success": False,
            "message": "Twitter configuration is invalid"
        }
    
    try:
        result = tool.reply_to_tweet(tweet_id, message)
        return {
            "success": True,
            "message": "Reply posted successfully",
            "data": result
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error posting reply: {str(e)}"
        }


async def like_tweet(tweet_id: str) -> Dict[str, Any]:
    """
    Like a tweet
    
    Args:
        tweet_id: ID of the tweet to like
        
    Returns:
        Dict with success status and response data
    """
    tool = TwitterTool()
    
    if not tool.validate_config():
        return {
            "success": False,
            "message": "Twitter configuration is invalid"
        }
    
    try:
        result = tool.like_tweet(tweet_id)
        return {
            "success": True,
            "message": "Tweet liked successfully",
            "data": result
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error liking tweet: {str(e)}"
        } 