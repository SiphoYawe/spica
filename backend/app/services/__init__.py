"""
Services package - Business logic and external integrations.

This package contains service classes that handle:
- Neo N3 blockchain interactions (neo_service)
- SpoonOS agent management (spoon_service)
- Wallet management (wallet_service)
- Graph assembly and workflow execution (graph_assembler)
- Workflow storage and persistence (workflow_storage)
- x402 payment processing (payment_service)
- Transaction execution engine (execution_engine)
- Transaction builders (transaction_builders)
- Price monitoring (price_monitor)
- Workflow scheduling (workflow_scheduler)
"""

from app.services.neo_service import NeoService, get_neo_service, close_neo_service
from app.services.graph_assembler import GraphAssembler, get_graph_assembler
from app.services.workflow_storage import WorkflowStorage, get_workflow_storage
from app.services.payment_service import PaymentService, get_payment_service
from app.services.execution_engine import (
    NeoExecutionEngine,
    get_execution_engine,
    close_execution_engine,
    TransactionResult,
    TransactionError,
    TransactionBroadcastError,
    TransactionConfirmationError,
)
from app.services.transaction_builders import (
    SwapTransactionBuilder,
    StakeTransactionBuilder,
    TransferTransactionBuilder,
    get_swap_builder,
    get_stake_builder,
    get_transfer_builder,
)
from app.services.price_monitor import (
    PriceMonitorService,
    get_price_monitor,
    close_price_monitor,
    PriceData,
    PriceConditionResult,
    TriggerCondition,
)
from app.services.workflow_scheduler import (
    WorkflowScheduler,
    get_workflow_scheduler,
    close_workflow_scheduler,
    ScheduledWorkflow,
    ScheduleStatus,
)

__all__ = [
    # Neo blockchain service
    "NeoService",
    "get_neo_service",
    "close_neo_service",

    # Graph assembly service
    "GraphAssembler",
    "get_graph_assembler",

    # Workflow storage service
    "WorkflowStorage",
    "get_workflow_storage",

    # Payment service
    "PaymentService",
    "get_payment_service",

    # Execution engine (Story 5.1)
    "NeoExecutionEngine",
    "get_execution_engine",
    "close_execution_engine",
    "TransactionResult",
    "TransactionError",
    "TransactionBroadcastError",
    "TransactionConfirmationError",

    # Transaction builders (Stories 5.2-5.4)
    "SwapTransactionBuilder",
    "StakeTransactionBuilder",
    "TransferTransactionBuilder",
    "get_swap_builder",
    "get_stake_builder",
    "get_transfer_builder",

    # Price monitor (Story 5.5)
    "PriceMonitorService",
    "get_price_monitor",
    "close_price_monitor",
    "PriceData",
    "PriceConditionResult",
    "TriggerCondition",

    # Workflow scheduler (Story 5.6)
    "WorkflowScheduler",
    "get_workflow_scheduler",
    "close_workflow_scheduler",
    "ScheduledWorkflow",
    "ScheduleStatus",
]
