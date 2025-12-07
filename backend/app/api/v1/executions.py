"""
Executions API Endpoints

Implements Task 4.1: Executions API

This module provides REST endpoints for:
- Listing execution records with filtering and pagination
- Getting detailed execution information
- Filtering by workflow_id and status
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

from app.services.execution_storage import get_execution_storage, ExecutionRecord

router = APIRouter()


# ============================================================================
# Response Models
# ============================================================================

class ExecutionResponse(BaseModel):
    """Execution record response."""
    execution_id: str
    workflow_id: str
    workflow_name: str
    status: str
    trigger_type: str
    action_summary: str
    started_at: datetime
    completed_at: Optional[datetime]
    tx_hash: Optional[str]
    error: Optional[str]
    gas_used: Optional[str]

    class Config:
        from_attributes = True


class ExecutionListResponse(BaseModel):
    """Paginated list of executions."""
    executions: List[ExecutionResponse]
    total: int
    page: int
    limit: int
    has_next: bool


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/", response_model=ExecutionListResponse)
async def list_executions(
    workflow_id: Optional[str] = Query(None, description="Filter by workflow ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page")
):
    """
    List execution records with optional filters.

    This endpoint provides paginated access to workflow execution history.
    Results can be filtered by workflow_id and/or status.

    Args:
        workflow_id: Optional workflow ID to filter by
        status: Optional status filter (running, completed, failed)
        page: Page number (1-indexed)
        limit: Number of items per page (max 100)

    Returns:
        ExecutionListResponse with paginated execution records
    """
    storage = await get_execution_storage()

    offset = (page - 1) * limit

    # Get executions based on filters
    if workflow_id:
        executions = await storage.get_workflow_executions(
            workflow_id=workflow_id,
            status=status,
            limit=limit + 1  # Get one extra to check if there's a next page
        )
    else:
        executions = await storage.get_all_executions(
            status=status,
            limit=limit + 1
        )

    # Skip offset items (for pagination beyond first page)
    executions = executions[offset:] if offset < len(executions) else []

    # Check if there's a next page
    has_next = len(executions) > limit
    if has_next:
        executions = executions[:limit]

    # Calculate total count (simplified - in production would use separate count query)
    if workflow_id:
        all_executions = await storage.get_workflow_executions(workflow_id=workflow_id, limit=10000)
    else:
        all_executions = await storage.get_all_executions(limit=10000)
    total = len(all_executions)

    # Convert to response format
    def to_response(e: ExecutionRecord) -> ExecutionResponse:
        """Convert ExecutionRecord to ExecutionResponse."""
        # Generate action summary from step_results if available
        action_summary = "N/A"
        tx_hash = None
        gas_used = None

        if e.step_results:
            actions = [r.get("action_type", "unknown") for r in e.step_results]
            action_summary = ", ".join(actions)
            # Get last tx_hash from step results
            for result in reversed(e.step_results):
                if result.get("tx_hash"):
                    tx_hash = result["tx_hash"]
                    break
            # Get gas_used if available
            for result in reversed(e.step_results):
                if result.get("gas_used"):
                    gas_used = result["gas_used"]
                    break

        return ExecutionResponse(
            execution_id=e.execution_id,
            workflow_id=e.workflow_id,
            workflow_name=e.workflow_name,
            status=e.status,
            trigger_type=e.trigger_type,
            action_summary=action_summary,
            started_at=e.started_at,
            completed_at=e.completed_at,
            tx_hash=tx_hash,
            error=e.error,
            gas_used=gas_used
        )

    return ExecutionListResponse(
        executions=[to_response(e) for e in executions],
        total=total,
        page=page,
        limit=limit,
        has_next=has_next
    )


@router.get("/{execution_id}", response_model=ExecutionResponse)
async def get_execution(execution_id: str):
    """
    Get a specific execution by ID.

    Args:
        execution_id: Unique execution identifier

    Returns:
        ExecutionResponse with detailed execution information

    Raises:
        HTTPException: 404 if execution not found
    """
    storage = await get_execution_storage()
    record = await storage.get_execution(execution_id)

    if not record:
        raise HTTPException(404, f"Execution not found: {execution_id}")

    # Generate action summary and extract transaction data
    action_summary = "N/A"
    tx_hash = None
    gas_used = None

    if record.step_results:
        actions = [r.get("action_type", "unknown") for r in record.step_results]
        action_summary = ", ".join(actions)
        # Get last tx_hash
        for result in reversed(record.step_results):
            if result.get("tx_hash"):
                tx_hash = result["tx_hash"]
                break
        # Get gas_used if available
        for result in reversed(record.step_results):
            if result.get("gas_used"):
                gas_used = result["gas_used"]
                break

    return ExecutionResponse(
        execution_id=record.execution_id,
        workflow_id=record.workflow_id,
        workflow_name=record.workflow_name,
        status=record.status,
        trigger_type=record.trigger_type,
        action_summary=action_summary,
        started_at=record.started_at,
        completed_at=record.completed_at,
        tx_hash=tx_hash,
        error=record.error,
        gas_used=gas_used
    )
