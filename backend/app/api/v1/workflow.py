"""
Workflow parsing endpoints for API v1
"""

from fastapi import APIRouter, HTTPException, status, Request, Query
from fastapi.responses import JSONResponse
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field, field_validator
import logging
import time
import threading
import asyncio
import uuid
from datetime import datetime, UTC
from collections import defaultdict, deque

from app.agents import (
    create_workflow_parser,
    WorkflowParserAgent,
    SPOON_AI_AVAILABLE,
    design_workflow_nodes,
)
from app.services.graph_assembler import get_graph_assembler
from app.services.workflow_storage import get_workflow_storage
from app.services.execution_storage import get_execution_storage
from app.models.workflow_models import (
    WorkflowSpec,
    ParserSuccess,
    ParserError,
    ParserResponse,
)
from app.models.graph_models import AssembledGraph
from app.models.api_models import ErrorDetail, ErrorResponse

logger = logging.getLogger(__name__)

router = APIRouter()

# Singleton parser instance for efficiency with thread-safe initialization
_parser_instance: Optional[WorkflowParserAgent] = None
_parser_lock = threading.Lock()


# Simple in-memory rate limiter (10 requests per minute per IP)
# Note: For production, use Redis-backed rate limiting (e.g., slowapi)
_rate_limit_store: Dict[str, deque] = defaultdict(deque)
_rate_limit_lock = threading.Lock()
RATE_LIMIT_REQUESTS = 10
RATE_LIMIT_WINDOW = 60  # seconds


def check_rate_limit(client_ip: str) -> bool:
    """
    Check if client has exceeded rate limit.
    Returns True if request is allowed, False if rate limit exceeded.

    Simple sliding window implementation: 10 requests per 60 seconds.
    """
    current_time = time.time()

    with _rate_limit_lock:
        # Get request timestamps for this IP
        timestamps = _rate_limit_store[client_ip]

        # Remove timestamps older than the window
        while timestamps and current_time - timestamps[0] > RATE_LIMIT_WINDOW:
            timestamps.popleft()

        # Check if limit exceeded
        if len(timestamps) >= RATE_LIMIT_REQUESTS:
            return False

        # Add current request
        timestamps.append(current_time)
        return True


def get_parser() -> WorkflowParserAgent:
    """
    Get or create the workflow parser agent instance.

    Uses a thread-safe singleton pattern to avoid recreating the agent on each request.
    Raises HTTPException if spoon_ai is not available.
    """
    global _parser_instance

    # Check if spoon_ai is available
    if not SPOON_AI_AVAILABLE or create_workflow_parser is None:
        logger.error("Parser unavailable: spoon_ai package not installed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "success": False,
                "error": {
                    "code": "PARSER_UNAVAILABLE",
                    "message": "AI parser service is temporarily unavailable",
                    "details": "The spoon_ai package is not properly configured. Please check server logs.",
                    "retry": True
                },
                "timestamp": datetime.now(UTC).isoformat()
            }
        )

    if _parser_instance is None:
        with _parser_lock:
            if _parser_instance is None:
                logger.info("Creating WorkflowParserAgent instance")
                _parser_instance = create_workflow_parser()
    return _parser_instance


# ============================================================================
# Request/Response Models
# ============================================================================

class ParseRequest(BaseModel):
    """Request model for workflow parsing"""
    input: str = Field(
        ...,
        description="Natural language description of the workflow to parse",
        max_length=500
    )

    @field_validator('input', mode='after')
    @classmethod
    def validate_input(cls, v: str) -> str:
        """Validate and sanitize input"""
        if not v or not v.strip():
            raise ValueError("Input cannot be empty or whitespace only")

        # Check length
        if len(v) > 500:
            raise ValueError("Input exceeds maximum length of 500 characters")

        return v.strip()

    model_config = {
        "json_schema_extra": {
            "example": {
                "input": "When GAS drops below $5, swap 10 GAS for NEO"
            }
        }
    }


class ParseSuccessResponse(BaseModel):
    """Successful parse response"""
    success: bool = Field(True, description="Always true for successful parse")
    workflow_spec: WorkflowSpec = Field(..., description="Parsed workflow specification")
    confidence: float = Field(..., ge=0, le=1, description="Parser confidence score")
    parse_time_ms: float = Field(..., description="Time taken to parse in milliseconds")
    sla_exceeded: bool = Field(False, description="True if parse time exceeded 5000ms SLA")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "workflow_spec": {
                    "name": "Auto DCA into NEO",
                    "description": "When GAS price falls below $5, automatically swap 10 GAS for NEO",
                    "trigger": {
                        "type": "price",
                        "token": "GAS",
                        "operator": "below",
                        "value": 5.0
                    },
                    "steps": [
                        {
                            "action": {
                                "type": "swap",
                                "from_token": "GAS",
                                "to_token": "NEO",
                                "amount": 10.0
                            },
                            "description": "Swap 10 GAS to NEO"
                        }
                    ]
                },
                "confidence": 0.98,
                "parse_time_ms": 234.56,
                "sla_exceeded": False,
                "timestamp": "2025-12-06T00:00:00.000000"
            }
        }
    }


class ParseErrorResponse(BaseModel):
    """Error parse response"""
    success: bool = Field(False, description="Always false for parse errors")
    error: ErrorDetail = Field(..., description="Detailed error information")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": False,
                "error": {
                    "code": "PARSE_ERROR",
                    "message": "Unable to parse workflow description",
                    "details": "The workflow description is too vague. Please specify a trigger condition and action.",
                    "retry": True
                },
                "timestamp": "2025-12-06T00:00:00.000000"
            }
        }
    }


# ============================================================================
# Endpoints
# ============================================================================

@router.post(
    "/parse",
    response_model=ParseSuccessResponse,
    summary="Parse natural language workflow",
    description="Convert a natural language workflow description into a structured WorkflowSpec",
    responses={
        200: {
            "description": "Successfully parsed workflow",
            "model": ParseSuccessResponse
        },
        400: {
            "description": "Invalid input or unable to parse",
            "model": ParseErrorResponse
        },
        422: {
            "description": "Validation error",
            "model": ParseErrorResponse
        },
        500: {
            "description": "Internal server error",
            "model": ParseErrorResponse
        },
        503: {
            "description": "Parser service unavailable",
            "model": ParseErrorResponse
        }
    },
    tags=["workflow"]
)
async def parse_workflow(request: ParseRequest, http_request: Request) -> ParseSuccessResponse:
    """
    Parse a natural language workflow description into a structured WorkflowSpec.

    This endpoint accepts a natural language description of a DeFi workflow
    and uses an AI agent to parse it into a structured specification that
    can be executed on the Neo N3 blockchain.

    **Rate Limit:** 10 requests per minute per IP address

    **Example inputs:**
    - "When GAS drops below $5, swap 10 GAS for NEO"
    - "Stake 50% of my NEO every day at 9 AM"
    - "Every Monday, swap 30% of my GAS to NEO and stake all of it"

    **Response time:** < 5 seconds

    Args:
        request: ParseRequest containing the natural language input
        http_request: FastAPI Request object for client IP extraction

    Returns:
        ParseSuccessResponse with the parsed workflow specification

    Raises:
        HTTPException: If parsing fails or validation errors occur
    """
    start_time = time.time()

    # Rate limiting
    client_ip = http_request.client.host if http_request.client else "unknown"
    if not check_rate_limit(client_ip):
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "success": False,
                "error": {
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": "Too many requests",
                    "details": f"Rate limit: {RATE_LIMIT_REQUESTS} requests per {RATE_LIMIT_WINDOW} seconds",
                    "retry": True
                },
                "timestamp": datetime.now(UTC).isoformat()
            }
        )

    logger.info(f"Received parse request from {client_ip}: {request.input[:100]}...")

    try:
        # Get parser instance
        parser = get_parser()

        # Parse the workflow with timeout (5 second SLA)
        try:
            result: ParserResponse = await asyncio.wait_for(
                parser.parse_workflow(request.input),
                timeout=5.0
            )
        except asyncio.TimeoutError:
            error_id = str(uuid.uuid4())[:8]
            logger.error(f"Parse timeout after 5s [error_id={error_id}]")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "success": False,
                    "error": {
                        "code": "TIMEOUT_ERROR",
                        "message": "Parser request timed out",
                        "details": f"The parsing operation exceeded the 5 second timeout. Error ID: {error_id}",
                        "retry": True
                    },
                    "timestamp": datetime.now(UTC).isoformat()
                }
            )

        # Calculate parse time
        parse_time_ms = (time.time() - start_time) * 1000

        # Check if we exceeded the 5-second SLA
        sla_exceeded = parse_time_ms > 5000
        if sla_exceeded:
            logger.warning(f"Parse time {parse_time_ms}ms exceeded 5s SLA")

        # Handle success
        if isinstance(result, ParserSuccess):
            logger.info(f"Successfully parsed workflow in {parse_time_ms:.2f}ms")
            return ParseSuccessResponse(
                success=True,
                workflow_spec=result.workflow,
                confidence=result.confidence,
                parse_time_ms=round(parse_time_ms, 2),
                sla_exceeded=sla_exceeded
            )

        # Handle parser errors (semantic/logical errors in the description)
        elif isinstance(result, ParserError):
            logger.warning(f"Parse error: {result.error}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "error": {
                        "code": "PARSE_ERROR",
                        "message": result.error,
                        "details": "; ".join(result.suggestions) if result.suggestions else None,
                        "retry": True
                    },
                    "timestamp": datetime.now(UTC).isoformat()
                }
            )

        else:
            # Should never happen, but handle gracefully
            logger.error(f"Unexpected result type: {type(result)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "success": False,
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": "Unexpected error during parsing",
                        "details": "The parser returned an unexpected result type",
                        "retry": True
                    },
                    "timestamp": datetime.now(UTC).isoformat()
                }
            )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except ValueError as e:
        # Input validation errors - these are safe to expose as they come from validation
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid input",
                    "details": str(e),
                    "retry": False
                },
                "timestamp": datetime.now(UTC).isoformat()
            }
        )

    except Exception as e:
        # Unexpected errors - generate error ID for tracking, don't expose internal details
        error_id = str(uuid.uuid4())[:8]
        logger.error(f"Unexpected error during parsing [error_id={error_id}]: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred during parsing",
                    "details": f"Please contact support with error ID: {error_id}",
                    "retry": True
                },
                "timestamp": datetime.now(UTC).isoformat()
            }
        )


# ============================================================================
# Workflow List Endpoint - Story 6.8
# ============================================================================

class WorkflowSummary(BaseModel):
    """Summary view of a workflow for listing"""
    workflow_id: str = Field(..., description="Unique workflow identifier")
    workflow_name: str = Field(..., description="User-friendly workflow name")
    workflow_description: str = Field(..., description="Workflow description")
    status: str = Field(..., description="Current status (active/paused/completed/failed)")
    enabled: bool = Field(..., description="Whether workflow is enabled")
    trigger_type: str = Field(..., description="Trigger type (price/time)")
    trigger_summary: str = Field(..., description="Human-readable trigger summary")
    execution_count: int = Field(..., description="Number of successful executions")
    created_at: datetime = Field(..., description="Creation timestamp")
    last_executed_at: Optional[datetime] = Field(None, description="Last execution timestamp")


class WorkflowListResponse(BaseModel):
    """Response for workflow listing"""
    success: bool = Field(True, description="Always true for successful requests")
    workflows: List[WorkflowSummary] = Field(..., description="List of workflow summaries")
    total: int = Field(..., description="Total number of workflows")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


@router.get(
    "/workflows",
    response_model=WorkflowListResponse,
    summary="List all workflows",
    description="Get a list of all workflows, optionally filtered by status",
    tags=["workflow"]
)
async def list_workflows(
    workflow_status: Optional[str] = None,
    user_id: Optional[str] = None,
) -> WorkflowListResponse:
    """
    List all workflows with optional filtering.

    Args:
        workflow_status: Optional status filter (active, paused, completed, failed)
        user_id: Optional user ID filter

    Returns:
        WorkflowListResponse with list of workflow summaries
    """
    logger.info(f"Listing workflows (status={workflow_status}, user_id={user_id})")

    try:
        storage = get_workflow_storage()
        workflows = await storage.list_workflows(user_id=user_id, status=workflow_status)

        # Convert to summaries
        summaries = []
        for w in workflows:
            # Build trigger summary - handle legacy workflows without workflow_spec
            workflow_spec = w.assembled_graph.workflow_spec
            trigger = workflow_spec.trigger if workflow_spec else None
            trigger_type = "manual"
            trigger_summary = "Manual execution"

            if trigger:
                trigger_type = trigger.type
                if trigger.type == "price":
                    trigger_summary = f"When {trigger.token.value} {trigger.operator} ${trigger.value}"
                elif trigger.type == "time":
                    trigger_summary = f"Schedule: {trigger.schedule}"
                else:
                    trigger_summary = f"{trigger.type} trigger"
            elif w.assembled_graph.state_graph_config:
                # Fallback: extract trigger info from state_graph_config for legacy workflows
                state_config = w.assembled_graph.state_graph_config
                trigger_data = state_config.get("trigger", {})
                trigger_type = trigger_data.get("type", "manual")
                trigger_params = trigger_data.get("params", {})

                if trigger_type == "price":
                    token = trigger_params.get("token", "?")
                    # Handle both new format (operator/value) and legacy format (condition/threshold)
                    operator = trigger_params.get("operator") or trigger_params.get("condition", "?")
                    value = trigger_params.get("value") or trigger_params.get("threshold", "?")
                    # Normalize condition names for display
                    if operator == "less_than":
                        operator = "below"
                    elif operator == "greater_than":
                        operator = "above"
                    trigger_summary = f"When {token} {operator} ${value}"
                elif trigger_type == "time":
                    schedule = trigger_params.get("schedule", "unknown schedule")
                    trigger_summary = f"Schedule: {schedule}"
                else:
                    trigger_summary = f"{trigger_type} trigger"

            summaries.append(WorkflowSummary(
                workflow_id=w.workflow_id,
                workflow_name=w.assembled_graph.workflow_name,
                workflow_description=w.assembled_graph.workflow_description,
                status=w.status,
                enabled=w.enabled,
                trigger_type=trigger_type,
                trigger_summary=trigger_summary,
                execution_count=w.execution_count,
                created_at=w.created_at,
                last_executed_at=w.last_executed_at,
            ))

        return WorkflowListResponse(
            success=True,
            workflows=summaries,
            total=len(summaries),
        )

    except Exception as e:
        error_id = str(uuid.uuid4())[:8]
        logger.error(f"Failed to list workflows [error_id={error_id}]: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Failed to list workflows",
                    "details": f"Error ID: {error_id}",
                    "retry": True
                },
                "timestamp": datetime.now(UTC).isoformat()
            }
        )


# ============================================================================
# Workflow Detail Endpoint - Story 6.9
# ============================================================================

class WorkflowDetailResponse(BaseModel):
    """Detailed workflow response"""
    success: bool = Field(True)
    workflow_id: str
    workflow_name: str
    workflow_description: str
    status: str
    enabled: bool
    trigger_type: str
    trigger_summary: str
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    execution_count: int
    trigger_count: int
    created_at: datetime
    updated_at: datetime
    last_executed_at: Optional[datetime]
    last_error: Optional[str]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


@router.get(
    "/workflows/{workflow_id}",
    response_model=WorkflowDetailResponse,
    summary="Get workflow details",
    description="Get detailed information about a specific workflow",
    tags=["workflow"]
)
async def get_workflow(workflow_id: str) -> WorkflowDetailResponse:
    """
    Get detailed workflow information.

    Args:
        workflow_id: Workflow identifier

    Returns:
        WorkflowDetailResponse with full workflow details
    """
    logger.info(f"Getting workflow details: {workflow_id}")

    try:
        storage = get_workflow_storage()
        w = await storage.load_workflow(workflow_id)

        # Build trigger summary - handle legacy workflows without workflow_spec
        workflow_spec = w.assembled_graph.workflow_spec
        trigger = workflow_spec.trigger if workflow_spec else None
        trigger_type = "manual"
        trigger_summary = "Manual execution"

        if trigger:
            trigger_type = trigger.type
            if trigger.type == "price":
                trigger_summary = f"When {trigger.token.value} {trigger.operator} ${trigger.value}"
            elif trigger.type == "time":
                trigger_summary = f"Schedule: {trigger.schedule}"
            else:
                trigger_summary = f"{trigger.type} trigger"
        elif w.assembled_graph.state_graph_config:
            # Fallback: extract trigger info from state_graph_config for legacy workflows
            state_config = w.assembled_graph.state_graph_config
            trigger_data = state_config.get("trigger", {})
            trigger_type = trigger_data.get("type", "manual")
            trigger_params = trigger_data.get("params", {})

            if trigger_type == "price":
                token = trigger_params.get("token", "?")
                # Handle both new format (operator/value) and legacy format (condition/threshold)
                operator = trigger_params.get("operator") or trigger_params.get("condition", "?")
                value = trigger_params.get("value") or trigger_params.get("threshold", "?")
                # Normalize condition names for display
                if operator == "less_than":
                    operator = "below"
                elif operator == "greater_than":
                    operator = "above"
                trigger_summary = f"When {token} {operator} ${value}"
            elif trigger_type == "time":
                schedule = trigger_params.get("schedule", "unknown schedule")
                trigger_summary = f"Schedule: {schedule}"
            else:
                trigger_summary = f"{trigger_type} trigger"

        # Convert nodes and edges
        nodes = [n.model_dump() for n in w.assembled_graph.react_flow.nodes]
        edges = [e.model_dump() for e in w.assembled_graph.react_flow.edges]

        return WorkflowDetailResponse(
            success=True,
            workflow_id=w.workflow_id,
            workflow_name=w.assembled_graph.workflow_name,
            workflow_description=w.assembled_graph.workflow_description,
            status=w.status,
            enabled=w.enabled,
            trigger_type=trigger_type,
            trigger_summary=trigger_summary,
            nodes=nodes,
            edges=edges,
            execution_count=w.execution_count,
            trigger_count=w.trigger_count,
            created_at=w.created_at,
            updated_at=w.updated_at,
            last_executed_at=w.last_executed_at,
            last_error=w.last_error,
        )

    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Workflow {workflow_id} not found",
                    "retry": False
                },
                "timestamp": datetime.now(UTC).isoformat()
            }
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "INVALID_ID",
                    "message": str(e),
                    "retry": False
                },
                "timestamp": datetime.now(UTC).isoformat()
            }
        )

    except Exception as e:
        error_id = str(uuid.uuid4())[:8]
        logger.error(f"Failed to get workflow [error_id={error_id}]: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Failed to get workflow",
                    "details": f"Error ID: {error_id}",
                    "retry": True
                },
                "timestamp": datetime.now(UTC).isoformat()
            }
        )


# ============================================================================
# Workflow Pause/Resume Endpoint - Story 6.8
# ============================================================================

class UpdateWorkflowRequest(BaseModel):
    """Request to update workflow status"""
    enabled: Optional[bool] = Field(None, description="Enable/disable workflow")
    status: Optional[str] = Field(None, description="New status (active/paused)")


class UpdateWorkflowResponse(BaseModel):
    """Response after updating workflow"""
    success: bool = Field(True)
    workflow_id: str
    status: str
    enabled: bool
    message: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


@router.patch(
    "/workflows/{workflow_id}",
    response_model=UpdateWorkflowResponse,
    summary="Update workflow",
    description="Update workflow status (pause/resume)",
    tags=["workflow"]
)
async def update_workflow(
    workflow_id: str,
    request: UpdateWorkflowRequest
) -> UpdateWorkflowResponse:
    """
    Update workflow status (pause/resume).

    Args:
        workflow_id: Workflow identifier
        request: Update request with new status

    Returns:
        UpdateWorkflowResponse with updated status
    """
    logger.info(f"Updating workflow: {workflow_id}")

    try:
        storage = get_workflow_storage()

        # Build updates dict
        updates = {}
        if request.enabled is not None:
            updates["enabled"] = request.enabled
        if request.status is not None:
            if request.status not in ("active", "paused"):
                raise ValueError("Status must be 'active' or 'paused'")
            updates["status"] = request.status

        if not updates:
            raise ValueError("No updates provided")

        # Update workflow
        updated = await storage.update_workflow(workflow_id, updates)

        action = "resumed" if updated.enabled else "paused"
        return UpdateWorkflowResponse(
            success=True,
            workflow_id=workflow_id,
            status=updated.status,
            enabled=updated.enabled,
            message=f"Workflow {action} successfully",
        )

    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Workflow {workflow_id} not found",
                    "retry": False
                },
                "timestamp": datetime.now(UTC).isoformat()
            }
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": str(e),
                    "retry": False
                },
                "timestamp": datetime.now(UTC).isoformat()
            }
        )

    except Exception as e:
        error_id = str(uuid.uuid4())[:8]
        logger.error(f"Failed to update workflow [error_id={error_id}]: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Failed to update workflow",
                    "details": f"Error ID: {error_id}",
                    "retry": True
                },
                "timestamp": datetime.now(UTC).isoformat()
            }
        )


# ============================================================================
# Workflow Delete Endpoint - Story 6.8
# ============================================================================

class DeleteWorkflowResponse(BaseModel):
    """Response after deleting workflow"""
    success: bool = Field(True)
    workflow_id: str
    message: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


@router.delete(
    "/workflows/{workflow_id}",
    response_model=DeleteWorkflowResponse,
    summary="Delete workflow",
    description="Delete a workflow from the system",
    tags=["workflow"]
)
async def delete_workflow(workflow_id: str) -> DeleteWorkflowResponse:
    """
    Delete a workflow.

    Args:
        workflow_id: Workflow identifier

    Returns:
        DeleteWorkflowResponse confirming deletion
    """
    logger.info(f"Deleting workflow: {workflow_id}")

    try:
        storage = get_workflow_storage()
        await storage.delete_workflow(workflow_id)

        return DeleteWorkflowResponse(
            success=True,
            workflow_id=workflow_id,
            message="Workflow deleted successfully",
        )

    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Workflow {workflow_id} not found",
                    "retry": False
                },
                "timestamp": datetime.now(UTC).isoformat()
            }
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "INVALID_ID",
                    "message": str(e),
                    "retry": False
                },
                "timestamp": datetime.now(UTC).isoformat()
            }
        )

    except Exception as e:
        error_id = str(uuid.uuid4())[:8]
        logger.error(f"Failed to delete workflow [error_id={error_id}]: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Failed to delete workflow",
                    "details": f"Error ID: {error_id}",
                    "retry": True
                },
                "timestamp": datetime.now(UTC).isoformat()
            }
        )


@router.get(
    "/parse/examples",
    summary="Get example workflows",
    description="Returns example natural language prompts for reference",
    tags=["workflow"]
)
async def get_example_workflows():
    """
    Get example workflow prompts.

    Returns pre-defined example natural language inputs to help users
    understand how to describe workflows.

    Returns:
        dict: Example workflow prompts with descriptions
    """
    # Complex real-world workflow examples showcasing full Spica capabilities
    # Features: Multi-step workflows, price triggers, time triggers, all action types, percentage & fixed amounts
    examples = [
        {
            "input": "Every Monday at 9am, swap 25% of my GAS to NEO and stake all of it",
            "description": "Weekly DCA strategy: Convert GAS to NEO and compound via staking",
            "category": "multi-step"
        },
        {
            "input": "When NEO rises above $25, swap 50% of my NEO to GAS and transfer 100 GAS to NikhQp1aAD1YFCiwknhM5LQQebj4464bCJ",
            "description": "Profit-taking automation: Sell NEO at target price and send profits to savings wallet",
            "category": "multi-step"
        },
        {
            "input": "Every day at midnight, swap 10% of my bNEO to GAS, then stake 75% of my remaining bNEO",
            "description": "Daily portfolio rebalancing: Harvest bNEO rewards and re-stake for compounding",
            "category": "multi-step"
        },
        {
            "input": "If GAS drops below $3, swap 500 GAS to bNEO and stake 100% of my bNEO",
            "description": "Buy-the-dip automation: Accumulate bNEO when GAS is cheap and stake immediately",
            "category": "multi-step"
        },
        {
            "input": "Every Friday at 6pm, transfer 50 GAS to NikhQp1aAD1YFCiwknhM5LQQebj4464bCJ and stake 100% of my NEO",
            "description": "Weekly savings routine: Send GAS to cold wallet and stake remaining NEO",
            "category": "multi-step"
        },
        {
            "input": "When bNEO rises above $18, swap 30% of my bNEO to NEO, swap 20% to GAS, and transfer 25 NEO to NikhQp1aAD1YFCiwknhM5LQQebj4464bCJ",
            "description": "Advanced profit distribution: Diversify gains across tokens and secure profits",
            "category": "multi-step"
        }
    ]

    return {
        "success": True,
        "examples": examples,
        "timestamp": datetime.now(UTC).isoformat()
    }


@router.get(
    "/parse/capabilities",
    summary="Get parser capabilities",
    description="Returns supported tokens, actions, and triggers",
    tags=["workflow"]
)
async def get_parser_capabilities():
    """
    Get parser capabilities.

    Returns information about what the parser supports:
    - Supported tokens (GAS, NEO, bNEO)
    - Supported actions (swap, stake, transfer)
    - Supported triggers (price, time)

    Returns:
        dict: Parser capabilities
    """
    parser = get_parser()

    return {
        "success": True,
        "capabilities": {
            "tokens": parser.get_supported_tokens(),
            "actions": parser.get_supported_actions(),
            "triggers": parser.get_supported_triggers(),
        },
        "constraints": {
            "max_input_length": 500,
            "max_parse_time_ms": 5000,
        },
        "timestamp": datetime.now(UTC).isoformat()
    }


# ============================================================================
# Generate Endpoint - Story 3.3
# ============================================================================

class GenerateRequest(BaseModel):
    """Request model for workflow graph generation"""
    workflow_spec: WorkflowSpec = Field(
        ...,
        description="Parsed workflow specification to convert to graph"
    )
    user_id: Optional[str] = Field(
        default="anonymous",
        description="User ID for workflow ownership",
        max_length=100
    )
    user_address: Optional[str] = Field(
        default="N/A",
        description="User's Neo N3 address",
        max_length=100
    )

    @field_validator('user_id', mode='after')
    @classmethod
    def validate_user_id(cls, v: Optional[str]) -> str:
        """
        Validate and sanitize user_id (Issue #4 - Input Sanitization).

        Args:
            v: User ID to validate

        Returns:
            Validated user ID

        Raises:
            ValueError: If user_id contains invalid characters
        """
        if v is None:
            return "anonymous"

        # Strip whitespace
        v = v.strip()

        # Check for empty string
        if not v:
            return "anonymous"

        # Allow alphanumeric, underscore, hyphen, and dot
        # Reject potential injection characters
        if not all(c.isalnum() or c in ('_', '-', '.') for c in v):
            raise ValueError(
                "user_id can only contain alphanumeric characters, underscore, hyphen, and dot"
            )

        # Check length
        if len(v) > 100:
            raise ValueError("user_id exceeds maximum length of 100 characters")

        return v

    @field_validator('user_address', mode='after')
    @classmethod
    def validate_user_address(cls, v: Optional[str]) -> str:
        """
        Validate and sanitize user_address (Issue #4 - Input Sanitization).

        Args:
            v: User address to validate

        Returns:
            Validated user address

        Raises:
            ValueError: If user_address contains invalid characters or format
        """
        if v is None:
            return "N/A"

        # Strip whitespace
        v = v.strip()

        # Check for empty string
        if not v:
            return "N/A"

        # If not N/A, validate Neo N3 address format
        if v != "N/A":
            # Neo N3 addresses start with 'N' and are Base58 encoded
            # Length is typically 34 characters
            if not v.startswith('N'):
                raise ValueError("Neo N3 addresses must start with 'N'")

            # Check length (Neo addresses are typically 34 characters)
            if len(v) < 25 or len(v) > 35:
                raise ValueError(
                    "Invalid Neo N3 address length (expected 25-35 characters)"
                )

            # Check for valid Base58 characters (no 0, O, I, l)
            valid_base58_chars = set('123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz')
            if not all(c in valid_base58_chars for c in v):
                raise ValueError(
                    "Invalid characters in Neo N3 address (must be Base58)"
                )

        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "workflow_spec": {
                    "name": "Auto DCA into NEO",
                    "description": "When GAS price falls below $5, automatically swap 10 GAS for NEO",
                    "trigger": {
                        "type": "price",
                        "token": "GAS",
                        "operator": "below",
                        "value": 5.0
                    },
                    "steps": [
                        {
                            "action": {
                                "type": "swap",
                                "from_token": "GAS",
                                "to_token": "NEO",
                                "amount": 10.0
                            },
                            "description": "Swap 10 GAS to NEO"
                        }
                    ]
                },
                "user_id": "user_123",
                "user_address": "NXXXyyy..."
            }
        }
    }


class GenerateSuccessResponse(BaseModel):
    """Successful graph generation response"""
    success: bool = Field(True, description="Always true for successful generation")
    workflow_id: str = Field(..., description="Unique identifier for the generated workflow")
    nodes: List[Dict[str, Any]] = Field(..., description="React Flow nodes for visualization")
    edges: List[Dict[str, Any]] = Field(..., description="React Flow edges connecting nodes")
    workflow_name: str = Field(..., description="Name of the workflow")
    workflow_description: str = Field(..., description="Description of the workflow")
    generation_time_ms: float = Field(..., description="Time taken to generate graph in milliseconds")
    sla_exceeded: bool = Field(False, description="True if generation time exceeded 10000ms SLA")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "workflow_id": "wf_a1b2c3d4e5f6",
                "nodes": [
                    {
                        "id": "trigger_1",
                        "type": "trigger",
                        "label": "GAS Below $5.00",
                        "position": {"x": 250, "y": 0},
                        "data": {"label": "Price Trigger", "icon": "dollar-sign"}
                    },
                    {
                        "id": "action_1",
                        "type": "swap",
                        "label": "Swap 10.0 GAS → NEO",
                        "position": {"x": 250, "y": 150},
                        "data": {"label": "Swap Action", "icon": "repeat"}
                    }
                ],
                "edges": [
                    {
                        "id": "e1",
                        "source": "trigger_1",
                        "target": "action_1",
                        "type": "default",
                        "animated": False
                    }
                ],
                "workflow_name": "Auto DCA into NEO",
                "workflow_description": "When GAS price falls below $5, automatically swap 10 GAS for NEO",
                "generation_time_ms": 345.67,
                "sla_exceeded": False,
                "timestamp": "2025-12-06T00:00:00.000000"
            }
        }
    }


class GenerateErrorResponse(BaseModel):
    """Error graph generation response"""
    success: bool = Field(False, description="Always false for generation errors")
    error: ErrorDetail = Field(..., description="Detailed error information")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


@router.post(
    "/generate",
    response_model=GenerateSuccessResponse,
    summary="Generate workflow graph",
    description="Convert a WorkflowSpec into a visual graph with nodes and edges",
    responses={
        200: {
            "description": "Successfully generated workflow graph",
            "model": GenerateSuccessResponse
        },
        400: {
            "description": "Invalid workflow specification",
            "model": GenerateErrorResponse
        },
        422: {
            "description": "Validation error",
            "model": GenerateErrorResponse
        },
        429: {
            "description": "Rate limit exceeded",
            "model": GenerateErrorResponse
        },
        500: {
            "description": "Internal server error",
            "model": GenerateErrorResponse
        },
        503: {
            "description": "Service timeout",
            "model": GenerateErrorResponse
        }
    },
    tags=["workflow"]
)
async def generate_workflow_graph(
    request: GenerateRequest,
    http_request: Request
) -> GenerateSuccessResponse:
    """
    Generate a visual workflow graph from a WorkflowSpec.

    This endpoint accepts a parsed WorkflowSpec and:
    1. Designs individual nodes using parallel designer agents
    2. Assembles the nodes into a React Flow graph
    3. Stores the complete workflow with a unique ID
    4. Returns the graph data for frontend visualization

    **Rate Limit:** 10 requests per minute per IP address
    **Response time SLA:** < 10 seconds

    Args:
        request: GenerateRequest containing the workflow specification
        http_request: FastAPI Request object for client IP extraction

    Returns:
        GenerateSuccessResponse with nodes, edges, and workflow_id

    Raises:
        HTTPException: If generation fails or validation errors occur
    """
    start_time = time.time()

    # Rate limiting (Issue #3)
    client_ip = http_request.client.host if http_request.client else "unknown"
    if not check_rate_limit(client_ip):
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "success": False,
                "error": {
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": "Too many requests",
                    "details": f"Rate limit: {RATE_LIMIT_REQUESTS} requests per {RATE_LIMIT_WINDOW} seconds",
                    "retry": True
                },
                "timestamp": datetime.now(UTC).isoformat()
            }
        )

    logger.info(f"Received generate request from {client_ip} for workflow: {request.workflow_spec.name}")

    try:
        # ====================================================================
        # Step 1: Design workflow nodes in parallel
        # ====================================================================

        logger.info(f"Designing nodes for workflow: {request.workflow_spec.name}")

        try:
            nodes = await asyncio.wait_for(
                design_workflow_nodes(request.workflow_spec),
                timeout=8.0  # Leave 2 seconds for assembly and storage
            )
            logger.info(f"Designed {len(nodes)} nodes in parallel")

        except asyncio.TimeoutError:
            error_id = str(uuid.uuid4())[:8]
            logger.error(f"Node design timeout after 8s [error_id={error_id}]")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "success": False,
                    "error": {
                        "code": "TIMEOUT_ERROR",
                        "message": "Node design timed out",
                        "details": f"The node design operation exceeded the timeout. Error ID: {error_id}",
                        "retry": True
                    },
                    "timestamp": datetime.now(UTC).isoformat()
                }
            )

        # ====================================================================
        # Step 2: Assemble graph
        # ====================================================================

        logger.info("Assembling workflow graph")

        assembler = await get_graph_assembler()
        assembled = await assembler.assemble(
            workflow_spec=request.workflow_spec,
            nodes=nodes
        )

        logger.info(f"Assembled graph with ID: {assembled.workflow_id}")

        # ====================================================================
        # Step 3: Store workflow
        # ====================================================================

        logger.info(f"Storing workflow: {assembled.workflow_id}")

        storage = get_workflow_storage()
        workflow_id = await storage.save_workflow(
            assembled_graph=assembled,
            workflow_spec=request.workflow_spec,
            user_id=request.user_id,
            user_address=request.user_address
        )

        logger.info(f"Workflow stored successfully: {workflow_id}")

        # ====================================================================
        # Step 4: Prepare response
        # ====================================================================

        # Calculate generation time
        generation_time_ms = (time.time() - start_time) * 1000
        sla_exceeded = generation_time_ms > 10000

        if sla_exceeded:
            logger.warning(f"Generation time {generation_time_ms}ms exceeded 10s SLA")

        # Convert nodes to dicts for response
        nodes_dict = [node.model_dump() for node in assembled.react_flow.nodes]
        edges_dict = [edge.model_dump() for edge in assembled.react_flow.edges]

        logger.info(f"Successfully generated workflow graph in {generation_time_ms:.2f}ms")

        return GenerateSuccessResponse(
            success=True,
            workflow_id=workflow_id,
            nodes=nodes_dict,
            edges=edges_dict,
            workflow_name=assembled.workflow_name,
            workflow_description=assembled.workflow_description,
            generation_time_ms=round(generation_time_ms, 2),
            sla_exceeded=sla_exceeded
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except ValueError as e:
        # Validation errors
        logger.error(f"Validation error during generation: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid workflow specification",
                    "details": str(e),
                    "retry": False
                },
                "timestamp": datetime.now(UTC).isoformat()
            }
        )

    except Exception as e:
        # Unexpected errors
        error_id = str(uuid.uuid4())[:8]
        logger.error(f"Unexpected error during generation [error_id={error_id}]: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred during graph generation",
                    "details": f"Please contact support with error ID: {error_id}",
                    "retry": True
                },
                "timestamp": datetime.now(UTC).isoformat()
            }
        )


# ============================================================================
# Workflow Executions Endpoint - Task 4.2
# ============================================================================

@router.get(
    "/workflows/{workflow_id}/executions",
    summary="Get workflow executions",
    description="Get recent executions for a specific workflow",
    tags=["workflow"]
)
async def get_workflow_executions(
    workflow_id: str,
    limit: int = Query(10, ge=1, le=50, description="Number of executions to return")
):
    """
    Get recent executions for a specific workflow.

    This endpoint returns the execution history for a workflow,
    showing the most recent executions first.

    Args:
        workflow_id: Workflow identifier
        limit: Maximum number of executions to return (default: 10, max: 50)

    Returns:
        List of execution records for the workflow
    """
    logger.info(f"Getting executions for workflow: {workflow_id}")

    try:
        storage = await get_execution_storage()
        executions = await storage.get_workflow_executions(workflow_id, limit=limit)

        return [
            {
                "execution_id": e.execution_id,
                "workflow_id": e.workflow_id,
                "workflow_name": e.workflow_name,
                "status": e.status,
                "trigger_type": e.trigger_type,
                "started_at": e.started_at.isoformat(),
                "completed_at": e.completed_at.isoformat() if e.completed_at else None,
                "error": e.error
            }
            for e in executions
        ]

    except Exception as e:
        error_id = str(uuid.uuid4())[:8]
        logger.error(f"Failed to get workflow executions [error_id={error_id}]: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Failed to get workflow executions",
                    "details": f"Error ID: {error_id}",
                    "retry": True
                },
                "timestamp": datetime.now(UTC).isoformat()
            }
        )


# ============================================================================
# Activate Workflow from Canvas - Hackathon Demo
# ============================================================================

class ActivateCanvasNode(BaseModel):
    """Canvas node data"""
    id: str
    type: str
    position: Dict[str, float]
    data: Dict[str, Any]


class ActivateCanvasEdge(BaseModel):
    """Canvas edge data"""
    id: str
    source: str
    target: str
    animated: Optional[bool] = True


class ActivateWorkflowRequest(BaseModel):
    """Request to activate a workflow from canvas data"""
    workflow_name: str = Field(..., description="Workflow name")
    workflow_description: str = Field("", description="Workflow description")
    nodes: List[ActivateCanvasNode] = Field(..., description="Canvas nodes")
    edges: List[ActivateCanvasEdge] = Field(..., description="Canvas edges")
    user_id: str = Field("demo_user", description="User ID")
    user_address: str = Field("NRNdUkU78B9NShjNbEyBLS8cgZUeS2vKgM", description="User wallet address")


class ActivateWorkflowResponse(BaseModel):
    """Response after activating workflow"""
    success: bool = Field(True)
    workflow_id: str
    workflow_name: str
    message: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


@router.post(
    "/workflows/activate",
    response_model=ActivateWorkflowResponse,
    summary="Activate workflow from canvas",
    description="Create an active workflow from canvas nodes and edges (demo endpoint)",
    tags=["workflow"]
)
async def activate_workflow_from_canvas(
    request: ActivateWorkflowRequest
) -> ActivateWorkflowResponse:
    """
    Create an active workflow from canvas data.

    This is a hackathon demo endpoint that takes the canvas state
    and creates an active workflow entry that appears on the
    active workflows page.

    Args:
        request: Canvas data with nodes, edges, and metadata

    Returns:
        ActivateWorkflowResponse with workflow ID
    """
    logger.info(f"Activating workflow from canvas: {request.workflow_name}")

    try:
        from app.models.graph_models import (
            AssembledGraph,
            ReactFlowGraph,
            GraphNode,
            GraphEdge,
            NodePosition,
            StoredWorkflow,
        )

        # Generate workflow ID
        workflow_id = f"wf_{uuid.uuid4().hex[:12]}"

        # Convert canvas nodes to GraphNodes
        graph_nodes = []
        trigger_node = None
        action_nodes = []
        for node in request.nodes:
            pos = NodePosition(
                x=int(node.position.get("x", 0)),
                y=int(node.position.get("y", 0))
            )
            graph_node = GraphNode(
                id=node.id,
                type=node.type,
                label=node.data.get("label", node.type.capitalize()),
                parameters=node.data,
                position=pos,
                data=node.data
            )
            graph_nodes.append(graph_node)
            if node.type == "trigger":
                trigger_node = node
            else:
                action_nodes.append(node)

        # Convert canvas edges to GraphEdges
        graph_edges = [
            GraphEdge(
                id=edge.id,
                source=edge.source,
                target=edge.target,
                type="default",
                animated=edge.animated if edge.animated is not None else True
            )
            for edge in request.edges
        ]

        # Create ReactFlowGraph
        react_flow = ReactFlowGraph(nodes=graph_nodes, edges=graph_edges)

        # Determine trigger type from nodes
        trigger_type = "time"
        trigger_params = {"schedule": "daily at 9am"}
        if trigger_node:
            trigger_type = trigger_node.data.get("type", "time")
            trigger_params = {k: v for k, v in trigger_node.data.items() if k not in ["label", "icon", "status"]}
            # Ensure schedule exists for time triggers
            if trigger_type == "time" and "schedule" not in trigger_params:
                trigger_params["schedule"] = "daily at 9am"

        # Build steps from action nodes
        steps = []
        for action_node in action_nodes:
            step = {
                "action_type": action_node.type,
                "params": {k: v for k, v in action_node.data.items() if k not in ["label", "icon", "status"]},
                "description": action_node.data.get("label", f"{action_node.type} action")
            }
            steps.append(step)

        # Create state graph config (this is what list_workflows uses for trigger info)
        state_graph_config = {
            "trigger": {
                "type": trigger_type,
                "params": trigger_params
            },
            "steps": steps,
            "node_count": len(graph_nodes),
            "initial_state": {
                "workflow_id": workflow_id,
                "trigger_type": trigger_type,
                "trigger_params": trigger_params,
                "current_step": 0,
                "total_steps": len(action_nodes),
                "completed_steps": [],
                "step_results": [],
                "workflow_status": "pending",
                "error": None,
                "metadata": {
                    "workflow_name": request.workflow_name,
                    "created_at": datetime.now(UTC).isoformat()
                }
            }
        }

        # Create AssembledGraph (workflow_spec=None, use state_graph_config for trigger info)
        assembled = AssembledGraph(
            workflow_id=workflow_id,
            workflow_name=request.workflow_name,
            workflow_description=request.workflow_description or f"Workflow created from canvas",
            workflow_spec=None,  # Skip WorkflowSpec validation, use state_graph_config instead
            react_flow=react_flow,
            state_graph_config=state_graph_config
        )

        # Create StoredWorkflow
        stored = StoredWorkflow(
            workflow_id=workflow_id,
            user_id=request.user_id,
            user_address=request.user_address,
            assembled_graph=assembled,
            status="active",
            enabled=True,
            trigger_count=0,
            execution_count=0
        )

        # Save to storage
        storage = get_workflow_storage()
        file_path = storage.storage_dir / f"{workflow_id}.json"

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(stored.model_dump_json(indent=2))

        logger.info(f"Successfully activated workflow: {workflow_id}")

        return ActivateWorkflowResponse(
            success=True,
            workflow_id=workflow_id,
            workflow_name=request.workflow_name,
            message="Workflow activated successfully"
        )

    except Exception as e:
        error_id = str(uuid.uuid4())[:8]
        logger.error(f"Failed to activate workflow [error_id={error_id}]: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Failed to activate workflow",
                    "details": f"Error ID: {error_id}",
                    "retry": True
                },
                "timestamp": datetime.now(UTC).isoformat()
            }
        )
