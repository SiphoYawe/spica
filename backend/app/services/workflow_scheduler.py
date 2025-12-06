"""
Workflow Scheduler Service for Spica

This module implements Story 5.6: Workflow Scheduler

The WorkflowScheduler provides:
- Time-based workflow trigger scheduling
- Price-based workflow trigger monitoring
- Integration with workflow execution engine
- Persistent schedule management

Acceptance Criteria:
- Schedule workflows for time triggers
- Register workflows for price triggers
- Execute workflows when conditions met
- Support one-time and recurring schedules
- Handle scheduler failures gracefully
- Track execution history
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List, Callable, Awaitable
from decimal import Decimal
from datetime import datetime, UTC, timedelta
from dataclasses import dataclass, field
from enum import Enum
import uuid

from app.config import settings
from app.models.workflow_models import (
    WorkflowSpec,
    TriggerType,
    TokenType,
    TimeCondition,
    PriceCondition,
    SwapAction,
    WorkflowStep
)
from app.services.price_monitor import (
    PriceMonitorService,
    get_price_monitor,
    PriceConditionResult,
    TriggerCondition
)

logger = logging.getLogger(__name__)


# ============================================================================
# Scheduler Models
# ============================================================================

class ScheduleStatus(Enum):
    """Status of a scheduled workflow."""
    PENDING = "pending"
    ACTIVE = "active"
    TRIGGERED = "triggered"
    EXECUTED = "executed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ScheduledWorkflow:
    """A workflow scheduled for future execution."""
    schedule_id: str
    workflow_id: str
    workflow_spec: WorkflowSpec
    trigger_type: TriggerType
    status: ScheduleStatus
    created_at: datetime
    scheduled_for: Optional[datetime] = None  # For time triggers
    price_condition: Optional[Dict[str, Any]] = None  # For price triggers
    executed_at: Optional[datetime] = None
    execution_result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "schedule_id": self.schedule_id,
            "workflow_id": self.workflow_id,
            "trigger_type": self.trigger_type.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "scheduled_for": self.scheduled_for.isoformat() if self.scheduled_for else None,
            "price_condition": self.price_condition,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "execution_result": self.execution_result,
            "error_message": self.error_message
        }


@dataclass
class ExecutionHistoryEntry:
    """Record of a workflow execution."""
    execution_id: str
    schedule_id: str
    workflow_id: str
    trigger_type: TriggerType
    started_at: datetime
    completed_at: Optional[datetime] = None
    success: bool = False
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "execution_id": self.execution_id,
            "schedule_id": self.schedule_id,
            "workflow_id": self.workflow_id,
            "trigger_type": self.trigger_type.value,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "success": self.success,
            "result": self.result,
            "error": self.error
        }


# ============================================================================
# Workflow Scheduler Service
# ============================================================================

class WorkflowScheduler:
    """
    Service for scheduling and executing workflows based on triggers.

    Implements Story 5.6: Workflow Scheduler

    Features:
    - Time-based scheduling with cron-like precision
    - Price-based triggers with continuous monitoring
    - In-memory schedule management
    - Execution history tracking
    - Graceful error handling

    Usage:
        ```python
        scheduler = WorkflowScheduler()

        # Schedule a time-based workflow
        schedule_id = await scheduler.schedule_time_trigger(
            workflow_spec=workflow,
            scheduled_time=datetime.now() + timedelta(hours=1)
        )

        # Register a price-based workflow
        schedule_id = await scheduler.schedule_price_trigger(
            workflow_spec=workflow,
            token=TokenType.GAS,
            condition=TriggerCondition.ABOVE,
            target_price=6.0
        )

        # Start the scheduler
        await scheduler.start()
        ```
    """

    # Default check interval for time triggers
    TIME_CHECK_INTERVAL = 1  # seconds

    def __init__(
        self,
        price_monitor: Optional[PriceMonitorService] = None,
        workflow_executor: Optional[Callable[[WorkflowSpec], Awaitable[Dict[str, Any]]]] = None,
        demo_mode: bool = None
    ):
        """
        Initialize the workflow scheduler.

        Args:
            price_monitor: Optional price monitor service
            workflow_executor: Async function to execute workflows
            demo_mode: Enable demo mode
        """
        self._price_monitor = price_monitor
        self._workflow_executor = workflow_executor or self._default_executor
        self.demo_mode = demo_mode if demo_mode is not None else settings.spica_demo_mode

        # Schedule storage
        self._schedules: Dict[str, ScheduledWorkflow] = {}

        # Execution history
        self._history: List[ExecutionHistoryEntry] = []

        # Background tasks
        self._time_checker_task: Optional[asyncio.Task] = None
        self._running = False

        logger.info(f"WorkflowScheduler initialized (demo_mode={self.demo_mode})")

    async def _get_price_monitor(self) -> PriceMonitorService:
        """Get or create price monitor service."""
        if self._price_monitor is None:
            self._price_monitor = await get_price_monitor()
        return self._price_monitor

    async def _default_executor(self, workflow_spec: WorkflowSpec) -> Dict[str, Any]:
        """
        Default workflow executor (demo mode).

        In production, this would invoke the actual workflow execution engine.
        """
        logger.info(f"DEMO: Executing workflow {workflow_spec.name}")

        # Simulate execution time
        await asyncio.sleep(0.5)

        return {
            "status": "success",
            "message": f"Workflow '{workflow_spec.name}' executed successfully (demo)",
            "steps_executed": len(workflow_spec.steps),
            "timestamp": datetime.now(UTC).isoformat()
        }

    # ========================================================================
    # Time-Based Scheduling
    # ========================================================================

    async def schedule_time_trigger(
        self,
        workflow_spec: WorkflowSpec,
        scheduled_time: datetime,
        workflow_id: Optional[str] = None
    ) -> str:
        """
        Schedule a workflow for execution at a specific time.

        Args:
            workflow_spec: Workflow to execute
            scheduled_time: When to execute
            workflow_id: Optional workflow ID (generated if not provided)

        Returns:
            Schedule ID for tracking
        """
        schedule_id = str(uuid.uuid4())
        workflow_id = workflow_id or str(uuid.uuid4())

        # Ensure time is in UTC
        if scheduled_time.tzinfo is None:
            scheduled_time = scheduled_time.replace(tzinfo=UTC)

        scheduled = ScheduledWorkflow(
            schedule_id=schedule_id,
            workflow_id=workflow_id,
            workflow_spec=workflow_spec,
            trigger_type=TriggerType.TIME,
            status=ScheduleStatus.PENDING,
            created_at=datetime.now(UTC),
            scheduled_for=scheduled_time
        )

        self._schedules[schedule_id] = scheduled

        logger.info(
            f"Scheduled time trigger: {schedule_id} for "
            f"{scheduled_time.isoformat()} ({workflow_spec.name})"
        )

        return schedule_id

    async def _check_time_triggers(self):
        """Check and execute any due time-based triggers."""
        now = datetime.now(UTC)

        for schedule_id, scheduled in list(self._schedules.items()):
            if scheduled.trigger_type != TriggerType.TIME:
                continue
            if scheduled.status != ScheduleStatus.PENDING:
                continue
            if scheduled.scheduled_for is None:
                continue

            # Check if it's time to execute
            if now >= scheduled.scheduled_for:
                logger.info(f"Time trigger activated: {schedule_id}")
                scheduled.status = ScheduleStatus.TRIGGERED
                await self._execute_workflow(scheduled)

    # ========================================================================
    # Price-Based Scheduling
    # ========================================================================

    async def schedule_price_trigger(
        self,
        workflow_spec: WorkflowSpec,
        token: TokenType,
        condition: TriggerCondition,
        target_price: float,
        workflow_id: Optional[str] = None
    ) -> str:
        """
        Register a workflow for execution when price condition is met.

        Args:
            workflow_spec: Workflow to execute
            token: Token to monitor
            condition: Price condition (ABOVE, BELOW, EQUALS)
            target_price: Target price threshold
            workflow_id: Optional workflow ID

        Returns:
            Schedule ID for tracking
        """
        schedule_id = str(uuid.uuid4())
        workflow_id = workflow_id or str(uuid.uuid4())

        scheduled = ScheduledWorkflow(
            schedule_id=schedule_id,
            workflow_id=workflow_id,
            workflow_spec=workflow_spec,
            trigger_type=TriggerType.PRICE,
            status=ScheduleStatus.ACTIVE,
            created_at=datetime.now(UTC),
            price_condition={
                "token": token.value,
                "condition": condition.value,
                "target_price": target_price
            }
        )

        self._schedules[schedule_id] = scheduled

        # Start price monitoring
        price_monitor = await self._get_price_monitor()
        await price_monitor.start_price_monitoring(
            token=token,
            condition=condition,
            target_price=target_price,
            callback=lambda result: self._on_price_condition_met(schedule_id, result),
            monitoring_id=schedule_id
        )

        logger.info(
            f"Scheduled price trigger: {schedule_id} - "
            f"{token.value} {condition.value} ${target_price} ({workflow_spec.name})"
        )

        return schedule_id

    async def _on_price_condition_met(
        self,
        schedule_id: str,
        result: PriceConditionResult
    ):
        """Handle price condition being met."""
        if schedule_id not in self._schedules:
            logger.warning(f"Schedule {schedule_id} not found for price trigger")
            return

        scheduled = self._schedules[schedule_id]
        if scheduled.status != ScheduleStatus.ACTIVE:
            logger.warning(f"Schedule {schedule_id} not active, skipping execution")
            return

        logger.info(f"Price trigger activated: {schedule_id} - {result.message}")
        scheduled.status = ScheduleStatus.TRIGGERED
        await self._execute_workflow(scheduled)

    # ========================================================================
    # Workflow Execution
    # ========================================================================

    async def _execute_workflow(self, scheduled: ScheduledWorkflow):
        """Execute a scheduled workflow."""
        execution_id = str(uuid.uuid4())
        history_entry = ExecutionHistoryEntry(
            execution_id=execution_id,
            schedule_id=scheduled.schedule_id,
            workflow_id=scheduled.workflow_id,
            trigger_type=scheduled.trigger_type,
            started_at=datetime.now(UTC)
        )

        try:
            logger.info(
                f"Executing workflow: {scheduled.workflow_spec.name} "
                f"(schedule: {scheduled.schedule_id})"
            )

            result = await self._workflow_executor(scheduled.workflow_spec)

            # Update schedule
            scheduled.status = ScheduleStatus.EXECUTED
            scheduled.executed_at = datetime.now(UTC)
            scheduled.execution_result = result

            # Update history
            history_entry.completed_at = datetime.now(UTC)
            history_entry.success = True
            history_entry.result = result

            logger.info(
                f"Workflow executed successfully: {scheduled.workflow_spec.name}"
            )

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")

            # Update schedule
            scheduled.status = ScheduleStatus.FAILED
            scheduled.executed_at = datetime.now(UTC)
            scheduled.error_message = str(e)

            # Update history
            history_entry.completed_at = datetime.now(UTC)
            history_entry.success = False
            history_entry.error = str(e)

        finally:
            self._history.append(history_entry)

    # ========================================================================
    # Scheduler Control
    # ========================================================================

    async def start(self):
        """Start the scheduler background tasks."""
        if self._running:
            logger.warning("Scheduler already running")
            return

        self._running = True

        # Start time trigger checker
        self._time_checker_task = asyncio.create_task(self._time_checker_loop())

        logger.info("WorkflowScheduler started")

    async def stop(self):
        """Stop the scheduler and cleanup."""
        self._running = False

        # Cancel time checker
        if self._time_checker_task:
            self._time_checker_task.cancel()
            try:
                await self._time_checker_task
            except asyncio.CancelledError:
                pass
            self._time_checker_task = None

        # Stop price monitors
        price_monitor = await self._get_price_monitor()
        for schedule_id in list(self._schedules.keys()):
            scheduled = self._schedules[schedule_id]
            if scheduled.trigger_type == TriggerType.PRICE:
                price_monitor.stop_price_monitoring(schedule_id)

        logger.info("WorkflowScheduler stopped")

    async def _time_checker_loop(self):
        """Background loop to check time triggers."""
        logger.info("Time trigger checker started")

        while self._running:
            try:
                await self._check_time_triggers()
                await asyncio.sleep(self.TIME_CHECK_INTERVAL)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in time checker: {e}")
                await asyncio.sleep(self.TIME_CHECK_INTERVAL)

        logger.info("Time trigger checker stopped")

    # ========================================================================
    # Schedule Management
    # ========================================================================

    def get_schedule(self, schedule_id: str) -> Optional[ScheduledWorkflow]:
        """Get a scheduled workflow by ID."""
        return self._schedules.get(schedule_id)

    def get_all_schedules(
        self,
        status: Optional[ScheduleStatus] = None,
        trigger_type: Optional[TriggerType] = None
    ) -> List[ScheduledWorkflow]:
        """
        Get all schedules, optionally filtered.

        Args:
            status: Filter by status
            trigger_type: Filter by trigger type

        Returns:
            List of scheduled workflows
        """
        schedules = list(self._schedules.values())

        if status:
            schedules = [s for s in schedules if s.status == status]
        if trigger_type:
            schedules = [s for s in schedules if s.trigger_type == trigger_type]

        return schedules

    async def cancel_schedule(self, schedule_id: str) -> bool:
        """
        Cancel a scheduled workflow.

        Args:
            schedule_id: Schedule to cancel

        Returns:
            True if cancelled successfully
        """
        if schedule_id not in self._schedules:
            return False

        scheduled = self._schedules[schedule_id]

        # Can only cancel pending or active schedules
        if scheduled.status not in [ScheduleStatus.PENDING, ScheduleStatus.ACTIVE]:
            logger.warning(
                f"Cannot cancel schedule {schedule_id} with status {scheduled.status}"
            )
            return False

        # Stop price monitoring if applicable
        if scheduled.trigger_type == TriggerType.PRICE:
            price_monitor = await self._get_price_monitor()
            price_monitor.stop_price_monitoring(schedule_id)

        scheduled.status = ScheduleStatus.CANCELLED
        logger.info(f"Cancelled schedule: {schedule_id}")

        return True

    def get_execution_history(
        self,
        schedule_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        limit: int = 100
    ) -> List[ExecutionHistoryEntry]:
        """
        Get execution history.

        Args:
            schedule_id: Filter by schedule ID
            workflow_id: Filter by workflow ID
            limit: Maximum entries to return

        Returns:
            List of execution history entries
        """
        history = self._history.copy()

        if schedule_id:
            history = [h for h in history if h.schedule_id == schedule_id]
        if workflow_id:
            history = [h for h in history if h.workflow_id == workflow_id]

        # Return most recent first, limited
        return sorted(history, key=lambda h: h.started_at, reverse=True)[:limit]

    def get_statistics(self) -> Dict[str, Any]:
        """Get scheduler statistics."""
        total = len(self._schedules)
        by_status = {}
        for status in ScheduleStatus:
            count = len([s for s in self._schedules.values() if s.status == status])
            by_status[status.value] = count

        by_type = {}
        for trigger_type in TriggerType:
            count = len([s for s in self._schedules.values() if s.trigger_type == trigger_type])
            by_type[trigger_type.value] = count

        executions = len(self._history)
        successful = len([h for h in self._history if h.success])
        failed = executions - successful

        return {
            "total_schedules": total,
            "by_status": by_status,
            "by_type": by_type,
            "total_executions": executions,
            "successful_executions": successful,
            "failed_executions": failed,
            "running": self._running
        }


# ============================================================================
# Singleton Instance
# ============================================================================

_scheduler: Optional[WorkflowScheduler] = None
_scheduler_lock = asyncio.Lock()


async def get_workflow_scheduler() -> WorkflowScheduler:
    """
    Get the global WorkflowScheduler instance (thread-safe).

    Returns:
        WorkflowScheduler singleton
    """
    global _scheduler

    if _scheduler is not None:
        return _scheduler

    async with _scheduler_lock:
        if _scheduler is None:
            _scheduler = WorkflowScheduler()
        return _scheduler


async def close_workflow_scheduler():
    """Close the global WorkflowScheduler instance."""
    global _scheduler

    async with _scheduler_lock:
        if _scheduler is not None:
            await _scheduler.stop()
            _scheduler = None
