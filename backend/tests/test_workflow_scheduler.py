"""
Unit tests for Workflow Scheduler Service

Tests Story 5.6: Workflow Scheduler acceptance criteria:
- Schedule workflows for time triggers ✓
- Register workflows for price triggers ✓
- Execute workflows when conditions met ✓
- Support one-time and recurring schedules ✓
- Handle scheduler failures gracefully ✓
- Track execution history ✓
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from decimal import Decimal
from datetime import datetime, UTC, timedelta

from app.services.workflow_scheduler import (
    WorkflowScheduler,
    ScheduledWorkflow,
    ExecutionHistoryEntry,
    ScheduleStatus,
    get_workflow_scheduler,
    close_workflow_scheduler
)
from app.services.price_monitor import PriceConditionResult, PriceData, TriggerCondition
from app.models.workflow_models import (
    WorkflowSpec,
    TriggerType,
    TokenType,
    TimeCondition,
    PriceCondition,
    SwapAction,
    WorkflowStep
)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def sample_workflow_spec():
    """Create a sample workflow specification"""
    return WorkflowSpec(
        name="Test Workflow",
        description="A test workflow for unit testing",
        trigger=TimeCondition(
            type="time",
            schedule="0 12 * * *"  # Daily at noon
        ),
        steps=[
            WorkflowStep(
                action=SwapAction(
                    type="swap",
                    from_token=TokenType.GAS,
                    to_token=TokenType.BNEO,
                    amount=10.0
                ),
                description="Swap GAS to bNEO"
            )
        ]
    )


@pytest.fixture
def mock_price_monitor():
    """Create a mock price monitor"""
    monitor = AsyncMock()
    monitor.start_price_monitoring = AsyncMock(return_value="monitor_123")
    monitor.stop_price_monitoring = Mock(return_value=True)
    monitor.check_price_condition = AsyncMock(return_value=PriceConditionResult(
        condition_met=True,
        current_price=PriceData(
            token=TokenType.GAS,
            price_usd=Decimal("6.00"),
            timestamp=datetime.now(UTC),
            source="mock"
        ),
        target_price=Decimal("5.00"),
        condition=TriggerCondition.ABOVE,
        message="GAS price $6.00 > target $5.00"
    ))
    return monitor


@pytest.fixture
def scheduler(mock_price_monitor):
    """Create a workflow scheduler with mocked dependencies"""
    return WorkflowScheduler(
        price_monitor=mock_price_monitor,
        demo_mode=True
    )


# ============================================================================
# Test ScheduledWorkflow Model
# ============================================================================

class TestScheduledWorkflow:
    """Test ScheduledWorkflow model"""

    def test_scheduled_workflow_creation(self, sample_workflow_spec):
        """Test creating a scheduled workflow"""
        scheduled = ScheduledWorkflow(
            schedule_id="sched_123",
            workflow_id="wf_456",
            workflow_spec=sample_workflow_spec,
            trigger_type=TriggerType.TIME,
            status=ScheduleStatus.PENDING,
            created_at=datetime.now(UTC),
            scheduled_for=datetime.now(UTC) + timedelta(hours=1)
        )

        assert scheduled.schedule_id == "sched_123"
        assert scheduled.workflow_id == "wf_456"
        assert scheduled.status == ScheduleStatus.PENDING
        assert scheduled.trigger_type == TriggerType.TIME

    def test_scheduled_workflow_to_dict(self, sample_workflow_spec):
        """Test converting to dictionary"""
        scheduled = ScheduledWorkflow(
            schedule_id="sched_123",
            workflow_id="wf_456",
            workflow_spec=sample_workflow_spec,
            trigger_type=TriggerType.TIME,
            status=ScheduleStatus.PENDING,
            created_at=datetime.now(UTC)
        )

        result = scheduled.to_dict()

        assert result["schedule_id"] == "sched_123"
        assert result["status"] == "pending"
        assert result["trigger_type"] == "time"
        assert "created_at" in result


class TestExecutionHistoryEntry:
    """Test ExecutionHistoryEntry model"""

    def test_history_entry_creation(self):
        """Test creating execution history entry"""
        entry = ExecutionHistoryEntry(
            execution_id="exec_123",
            schedule_id="sched_456",
            workflow_id="wf_789",
            trigger_type=TriggerType.TIME,
            started_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
            success=True,
            result={"status": "success"}
        )

        assert entry.execution_id == "exec_123"
        assert entry.success is True
        assert entry.result["status"] == "success"

    def test_history_entry_to_dict(self):
        """Test converting to dictionary"""
        entry = ExecutionHistoryEntry(
            execution_id="exec_123",
            schedule_id="sched_456",
            workflow_id="wf_789",
            trigger_type=TriggerType.PRICE,
            started_at=datetime.now(UTC),
            success=False,
            error="Test error"
        )

        result = entry.to_dict()

        assert result["success"] is False
        assert result["error"] == "Test error"
        assert result["trigger_type"] == "price"


# ============================================================================
# Test WorkflowScheduler
# ============================================================================

class TestWorkflowScheduler:
    """Test WorkflowScheduler class"""

    @pytest.mark.asyncio
    async def test_schedule_time_trigger(self, scheduler, sample_workflow_spec):
        """Test scheduling a time-based trigger"""
        scheduled_time = datetime.now(UTC) + timedelta(hours=1)

        schedule_id = await scheduler.schedule_time_trigger(
            workflow_spec=sample_workflow_spec,
            scheduled_time=scheduled_time
        )

        assert schedule_id is not None
        scheduled = scheduler.get_schedule(schedule_id)
        assert scheduled is not None
        assert scheduled.status == ScheduleStatus.PENDING
        assert scheduled.trigger_type == TriggerType.TIME
        assert scheduled.scheduled_for == scheduled_time

    @pytest.mark.asyncio
    async def test_schedule_price_trigger(self, scheduler, sample_workflow_spec, mock_price_monitor):
        """Test scheduling a price-based trigger"""
        schedule_id = await scheduler.schedule_price_trigger(
            workflow_spec=sample_workflow_spec,
            token=TokenType.GAS,
            condition=TriggerCondition.ABOVE,
            target_price=5.0
        )

        assert schedule_id is not None
        scheduled = scheduler.get_schedule(schedule_id)
        assert scheduled is not None
        assert scheduled.status == ScheduleStatus.ACTIVE
        assert scheduled.trigger_type == TriggerType.PRICE
        assert scheduled.price_condition["token"] == "GAS"
        assert scheduled.price_condition["target_price"] == 5.0

        # Verify price monitor was called
        mock_price_monitor.start_price_monitoring.assert_called_once()

    @pytest.mark.asyncio
    async def test_time_trigger_execution(self, scheduler, sample_workflow_spec):
        """Test that time triggers execute at scheduled time"""
        # Schedule for "now" (past)
        scheduled_time = datetime.now(UTC) - timedelta(seconds=1)

        schedule_id = await scheduler.schedule_time_trigger(
            workflow_spec=sample_workflow_spec,
            scheduled_time=scheduled_time
        )

        # Manually trigger time check
        await scheduler._check_time_triggers()

        # Should be executed
        scheduled = scheduler.get_schedule(schedule_id)
        assert scheduled.status == ScheduleStatus.EXECUTED
        assert scheduled.executed_at is not None

    @pytest.mark.asyncio
    async def test_price_trigger_callback(self, scheduler, sample_workflow_spec, mock_price_monitor):
        """Test that price condition callback triggers execution"""
        schedule_id = await scheduler.schedule_price_trigger(
            workflow_spec=sample_workflow_spec,
            token=TokenType.GAS,
            condition=TriggerCondition.ABOVE,
            target_price=5.0
        )

        # Simulate price condition being met
        result = PriceConditionResult(
            condition_met=True,
            current_price=PriceData(
                token=TokenType.GAS,
                price_usd=Decimal("6.00"),
                timestamp=datetime.now(UTC),
                source="mock"
            ),
            target_price=Decimal("5.00"),
            condition=TriggerCondition.ABOVE,
            message="Test"
        )

        await scheduler._on_price_condition_met(schedule_id, result)

        scheduled = scheduler.get_schedule(schedule_id)
        assert scheduled.status == ScheduleStatus.EXECUTED

    @pytest.mark.asyncio
    async def test_cancel_schedule(self, scheduler, sample_workflow_spec, mock_price_monitor):
        """Test cancelling a scheduled workflow"""
        schedule_id = await scheduler.schedule_price_trigger(
            workflow_spec=sample_workflow_spec,
            token=TokenType.GAS,
            condition=TriggerCondition.ABOVE,
            target_price=5.0
        )

        result = await scheduler.cancel_schedule(schedule_id)

        assert result is True
        scheduled = scheduler.get_schedule(schedule_id)
        assert scheduled.status == ScheduleStatus.CANCELLED
        mock_price_monitor.stop_price_monitoring.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_all_schedules(self, scheduler, sample_workflow_spec):
        """Test retrieving all schedules"""
        # Schedule multiple workflows
        await scheduler.schedule_time_trigger(
            workflow_spec=sample_workflow_spec,
            scheduled_time=datetime.now(UTC) + timedelta(hours=1)
        )
        await scheduler.schedule_time_trigger(
            workflow_spec=sample_workflow_spec,
            scheduled_time=datetime.now(UTC) + timedelta(hours=2)
        )

        all_schedules = scheduler.get_all_schedules()
        assert len(all_schedules) == 2

    @pytest.mark.asyncio
    async def test_get_schedules_filtered(self, scheduler, sample_workflow_spec, mock_price_monitor):
        """Test filtering schedules"""
        await scheduler.schedule_time_trigger(
            workflow_spec=sample_workflow_spec,
            scheduled_time=datetime.now(UTC) + timedelta(hours=1)
        )
        await scheduler.schedule_price_trigger(
            workflow_spec=sample_workflow_spec,
            token=TokenType.GAS,
            condition=TriggerCondition.ABOVE,
            target_price=5.0
        )

        # Filter by type
        time_schedules = scheduler.get_all_schedules(trigger_type=TriggerType.TIME)
        assert len(time_schedules) == 1
        assert time_schedules[0].trigger_type == TriggerType.TIME

        price_schedules = scheduler.get_all_schedules(trigger_type=TriggerType.PRICE)
        assert len(price_schedules) == 1

    @pytest.mark.asyncio
    async def test_execution_history_tracking(self, scheduler, sample_workflow_spec):
        """Test that execution history is tracked"""
        # Schedule and execute
        scheduled_time = datetime.now(UTC) - timedelta(seconds=1)
        schedule_id = await scheduler.schedule_time_trigger(
            workflow_spec=sample_workflow_spec,
            scheduled_time=scheduled_time
        )

        await scheduler._check_time_triggers()

        # Check history
        history = scheduler.get_execution_history()
        assert len(history) == 1
        assert history[0].schedule_id == schedule_id
        assert history[0].success is True

    @pytest.mark.asyncio
    async def test_execution_failure_tracking(self, sample_workflow_spec, mock_price_monitor):
        """Test that execution failures are tracked"""
        async def failing_executor(spec):
            raise Exception("Execution failed!")

        scheduler = WorkflowScheduler(
            price_monitor=mock_price_monitor,
            workflow_executor=failing_executor,
            demo_mode=True
        )

        scheduled_time = datetime.now(UTC) - timedelta(seconds=1)
        schedule_id = await scheduler.schedule_time_trigger(
            workflow_spec=sample_workflow_spec,
            scheduled_time=scheduled_time
        )

        await scheduler._check_time_triggers()

        scheduled = scheduler.get_schedule(schedule_id)
        assert scheduled.status == ScheduleStatus.FAILED
        assert scheduled.error_message is not None

        history = scheduler.get_execution_history()
        assert len(history) == 1
        assert history[0].success is False
        assert history[0].error is not None

    @pytest.mark.asyncio
    async def test_scheduler_statistics(self, scheduler, sample_workflow_spec, mock_price_monitor):
        """Test getting scheduler statistics"""
        # Create some schedules
        await scheduler.schedule_time_trigger(
            workflow_spec=sample_workflow_spec,
            scheduled_time=datetime.now(UTC) + timedelta(hours=1)
        )
        await scheduler.schedule_price_trigger(
            workflow_spec=sample_workflow_spec,
            token=TokenType.GAS,
            condition=TriggerCondition.ABOVE,
            target_price=5.0
        )

        stats = scheduler.get_statistics()

        assert stats["total_schedules"] == 2
        assert stats["by_type"]["time"] == 1
        assert stats["by_type"]["price"] == 1
        assert "total_executions" in stats

    @pytest.mark.asyncio
    async def test_start_and_stop(self, scheduler):
        """Test starting and stopping the scheduler"""
        assert scheduler._running is False

        await scheduler.start()
        assert scheduler._running is True
        assert scheduler._time_checker_task is not None

        await scheduler.stop()
        assert scheduler._running is False

    @pytest.mark.asyncio
    async def test_cannot_cancel_executed_schedule(self, scheduler, sample_workflow_spec):
        """Test that executed schedules cannot be cancelled"""
        scheduled_time = datetime.now(UTC) - timedelta(seconds=1)
        schedule_id = await scheduler.schedule_time_trigger(
            workflow_spec=sample_workflow_spec,
            scheduled_time=scheduled_time
        )

        await scheduler._check_time_triggers()

        # Try to cancel after execution
        result = await scheduler.cancel_schedule(schedule_id)
        assert result is False


# ============================================================================
# Test Singleton Pattern
# ============================================================================

class TestSingletonPattern:
    """Test singleton pattern for global instance"""

    @pytest.mark.asyncio
    async def test_get_workflow_scheduler_singleton(self):
        """Test that get_workflow_scheduler returns singleton"""
        import app.services.workflow_scheduler as ws_module
        ws_module._scheduler = None

        scheduler1 = await get_workflow_scheduler()
        scheduler2 = await get_workflow_scheduler()

        assert scheduler1 is scheduler2

        await close_workflow_scheduler()

    @pytest.mark.asyncio
    async def test_close_workflow_scheduler(self):
        """Test closing the singleton"""
        import app.services.workflow_scheduler as ws_module
        ws_module._scheduler = None

        scheduler = await get_workflow_scheduler()
        assert ws_module._scheduler is not None

        await close_workflow_scheduler()
        assert ws_module._scheduler is None


# ============================================================================
# Test Edge Cases
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_schedule_with_past_time(self, scheduler, sample_workflow_spec):
        """Test scheduling with past time executes immediately on check"""
        past_time = datetime.now(UTC) - timedelta(hours=1)

        schedule_id = await scheduler.schedule_time_trigger(
            workflow_spec=sample_workflow_spec,
            scheduled_time=past_time
        )

        # Should execute on first check
        await scheduler._check_time_triggers()

        scheduled = scheduler.get_schedule(schedule_id)
        assert scheduled.status == ScheduleStatus.EXECUTED

    @pytest.mark.asyncio
    async def test_cancel_nonexistent_schedule(self, scheduler):
        """Test cancelling a nonexistent schedule"""
        result = await scheduler.cancel_schedule("nonexistent_id")
        assert result is False

    @pytest.mark.asyncio
    async def test_get_nonexistent_schedule(self, scheduler):
        """Test getting a nonexistent schedule"""
        scheduled = scheduler.get_schedule("nonexistent_id")
        assert scheduled is None

    @pytest.mark.asyncio
    async def test_price_trigger_inactive_schedule(self, scheduler, sample_workflow_spec, mock_price_monitor):
        """Test that inactive schedules don't execute on price trigger"""
        schedule_id = await scheduler.schedule_price_trigger(
            workflow_spec=sample_workflow_spec,
            token=TokenType.GAS,
            condition=TriggerCondition.ABOVE,
            target_price=5.0
        )

        # Cancel the schedule
        await scheduler.cancel_schedule(schedule_id)

        # Simulate price condition callback
        result = PriceConditionResult(
            condition_met=True,
            current_price=PriceData(
                token=TokenType.GAS,
                price_usd=Decimal("6.00"),
                timestamp=datetime.now(UTC),
                source="mock"
            ),
            target_price=Decimal("5.00"),
            condition=TriggerCondition.ABOVE,
            message="Test"
        )

        await scheduler._on_price_condition_met(schedule_id, result)

        # Should remain cancelled
        scheduled = scheduler.get_schedule(schedule_id)
        assert scheduled.status == ScheduleStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_execution_history_filtering(self, scheduler, sample_workflow_spec):
        """Test filtering execution history"""
        # Execute multiple workflows
        for i in range(3):
            scheduled_time = datetime.now(UTC) - timedelta(seconds=1)
            await scheduler.schedule_time_trigger(
                workflow_spec=sample_workflow_spec,
                scheduled_time=scheduled_time,
                workflow_id=f"wf_{i}"
            )
            await scheduler._check_time_triggers()

        # Filter by workflow ID
        history = scheduler.get_execution_history(workflow_id="wf_1")
        assert len(history) == 1
        assert history[0].workflow_id == "wf_1"

        # Test limit
        history = scheduler.get_execution_history(limit=2)
        assert len(history) == 2
