"""
Workflow parsing endpoints for API v1
"""

from fastapi import APIRouter, HTTPException, status, Request
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
    """
    global _parser_instance
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


@router.get(
    "/parse/examples",
    summary="Get example workflows",
    description="Returns example workflow specifications for reference",
    tags=["workflow"]
)
async def get_example_workflows():
    """
    Get example workflow specifications.

    Returns pre-defined example workflows to help users understand
    the format and capabilities of the workflow system.

    Returns:
        dict: Example workflows with their specifications
    """
    parser = get_parser()
    examples = parser.get_example_workflows()

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
