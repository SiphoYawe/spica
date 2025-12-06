"""
Workflow specification models for natural language workflow parsing.

These models define the structure of workflows that users can create
using natural language descriptions.
"""

from typing import Literal, Optional, Union, List
from pydantic import BaseModel, Field, field_validator
from enum import Enum


# ============================================================================
# Enums for supported types
# ============================================================================

class TokenType(str, Enum):
    """Supported token types in Spica workflows"""
    GAS = "GAS"
    NEO = "NEO"
    BNEO = "bNEO"


class ActionType(str, Enum):
    """Supported action types in Spica workflows"""
    SWAP = "swap"
    STAKE = "stake"
    TRANSFER = "transfer"


class TriggerType(str, Enum):
    """Supported trigger types in Spica workflows"""
    PRICE = "price"
    TIME = "time"


# ============================================================================
# Condition Models
# ============================================================================

class PriceCondition(BaseModel):
    """Price-based trigger condition"""
    type: Literal["price"] = "price"
    token: TokenType = Field(..., description="Token to monitor price for")
    operator: Literal["above", "below", "equals"] = Field(..., description="Comparison operator")
    value: float = Field(..., gt=0, description="Target price value in USD")



class TimeCondition(BaseModel):
    """Time-based trigger condition"""
    type: Literal["time"] = "time"
    schedule: str = Field(..., description="Cron expression or natural time description")
    # Examples: "daily at 9am", "every Monday", "*/15 * * * *" (every 15 minutes)

    @field_validator('schedule')
    @classmethod
    def validate_schedule(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Schedule cannot be empty")
        return v.strip()


TriggerCondition = Union[PriceCondition, TimeCondition]


# ============================================================================
# Action Models
# ============================================================================

class SwapAction(BaseModel):
    """Swap one token for another"""
    type: Literal["swap"] = "swap"
    from_token: TokenType = Field(..., description="Token to swap from")
    to_token: TokenType = Field(..., description="Token to swap to")
    amount: Optional[float] = Field(None, gt=0, description="Amount to swap (optional, can be percentage)")
    percentage: Optional[float] = Field(None, gt=0, le=100, description="Percentage of balance to swap")


    def model_post_init(self, __context) -> None:
        """Validate that from_token != to_token and amount/percentage are mutually exclusive"""
        if self.from_token == self.to_token:
            raise ValueError("Cannot swap a token to itself")
        if self.amount is not None and self.percentage is not None:
            raise ValueError("Cannot specify both amount and percentage")
        if self.amount is None and self.percentage is None:
            raise ValueError("Must specify either amount or percentage")


class StakeAction(BaseModel):
    """Stake tokens"""
    type: Literal["stake"] = "stake"
    token: TokenType = Field(..., description="Token to stake")
    amount: Optional[float] = Field(None, gt=0, description="Amount to stake")
    percentage: Optional[float] = Field(None, gt=0, le=100, description="Percentage of balance to stake")

    def model_post_init(self, __context) -> None:
        """Validate that amount and percentage are mutually exclusive"""
        if self.amount is not None and self.percentage is not None:
            raise ValueError("Cannot specify both amount and percentage")
        if self.amount is None and self.percentage is None:
            raise ValueError("Must specify either amount or percentage")


class TransferAction(BaseModel):
    """Transfer tokens to an address"""
    type: Literal["transfer"] = "transfer"
    token: TokenType = Field(..., description="Token to transfer")
    to_address: str = Field(..., description="Recipient Neo N3 address")
    amount: Optional[float] = Field(None, gt=0, description="Amount to transfer")
    percentage: Optional[float] = Field(None, gt=0, le=100, description="Percentage of balance to transfer")

    @field_validator('to_address')
    @classmethod
    def validate_address(cls, v: str) -> str:
        """Validate Neo N3 address with checksum verification"""
        if not v or not v.strip():
            raise ValueError("Address cannot be empty")
        v = v.strip()

        # Neo N3 addresses start with 'N' and are 34 characters
        if not v.startswith('N') or len(v) != 34:
            raise ValueError("Invalid Neo N3 address format (must start with 'N' and be 34 characters)")

        # Validate base58 encoding and checksum
        try:
            import base58
            import hashlib

            decoded = base58.b58decode(v)
            if len(decoded) != 25:
                raise ValueError("Invalid Neo N3 address length after decoding")

            # Verify checksum (last 4 bytes)
            data = decoded[:-4]
            checksum = decoded[-4:]
            hash_result = hashlib.sha256(hashlib.sha256(data).digest()).digest()[:4]

            if checksum != hash_result:
                raise ValueError("Invalid Neo N3 address checksum")

        except Exception as e:
            raise ValueError(f"Invalid Neo N3 address: {str(e)}")

        return v

    def model_post_init(self, __context) -> None:
        """Validate that amount and percentage are mutually exclusive"""
        if self.amount is not None and self.percentage is not None:
            raise ValueError("Cannot specify both amount and percentage")
        if self.amount is None and self.percentage is None:
            raise ValueError("Must specify either amount or percentage")


WorkflowAction = Union[SwapAction, StakeAction, TransferAction]


# ============================================================================
# Workflow Specification Models
# ============================================================================

class WorkflowStep(BaseModel):
    """A single step in a workflow"""
    action: WorkflowAction = Field(..., discriminator='type', description="Action to execute")
    description: Optional[str] = Field(None, description="Human-readable description of this step")


class WorkflowSpec(BaseModel):
    """
    Complete workflow specification parsed from natural language.

    This is the output format expected from the WorkflowParserAgent.
    """
    name: str = Field(..., description="User-friendly workflow name")
    description: str = Field(..., description="Description of what this workflow does")
    trigger: TriggerCondition = Field(..., discriminator='type', description="Condition that triggers this workflow")
    steps: List[WorkflowStep] = Field(..., min_length=1, description="Ordered list of actions to execute")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Workflow name cannot be empty")
        return v.strip()

    @field_validator('description')
    @classmethod
    def validate_description(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Workflow description cannot be empty")
        return v.strip()


# ============================================================================
# Parser Response Models
# ============================================================================

class ParserSuccess(BaseModel):
    """Successful workflow parsing result"""
    success: Literal[True] = True
    workflow: WorkflowSpec = Field(..., description="Parsed workflow specification")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score of the parsing")


class ParserError(BaseModel):
    """Error during workflow parsing"""
    success: Literal[False] = False
    error: str = Field(..., description="Error message explaining what went wrong")
    suggestions: List[str] = Field(default_factory=list, description="Suggestions to fix the input")


ParserResponse = Union[ParserSuccess, ParserError]


# ============================================================================
# Example Workflows for Documentation
# ============================================================================

EXAMPLE_WORKFLOWS = {
    "price_swap": WorkflowSpec(
        name="Auto DCA into NEO",
        description="When GAS price is below $5, swap 10 GAS for NEO",
        trigger=PriceCondition(
            type="price",
            token=TokenType.GAS,
            operator="below",
            value=5.0
        ),
        steps=[
            WorkflowStep(
                action=SwapAction(
                    type="swap",
                    from_token=TokenType.GAS,
                    to_token=TokenType.NEO,
                    amount=10.0
                ),
                description="Swap 10 GAS to NEO"
            )
        ]
    ),
    "time_stake": WorkflowSpec(
        name="Daily NEO Staking",
        description="Stake 50% of NEO balance daily at 9 AM",
        trigger=TimeCondition(
            type="time",
            schedule="daily at 9am"
        ),
        steps=[
            WorkflowStep(
                action=StakeAction(
                    type="stake",
                    token=TokenType.NEO,
                    percentage=50.0
                ),
                description="Stake 50% of NEO balance"
            )
        ]
    ),
    "multi_step": WorkflowSpec(
        name="Weekly Portfolio Rebalance",
        description="Every Monday, swap GAS to NEO and stake it",
        trigger=TimeCondition(
            type="time",
            schedule="every Monday at 10am"
        ),
        steps=[
            WorkflowStep(
                action=SwapAction(
                    type="swap",
                    from_token=TokenType.GAS,
                    to_token=TokenType.NEO,
                    percentage=30.0
                ),
                description="Swap 30% of GAS to NEO"
            ),
            WorkflowStep(
                action=StakeAction(
                    type="stake",
                    token=TokenType.NEO,
                    percentage=100.0
                ),
                description="Stake all NEO"
            )
        ]
    )
}
