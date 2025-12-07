#!/usr/bin/env python3
"""
Seed Mock Execution History for Spica Demo

This script creates comprehensive mock execution records to showcase
the full range of Spica's DeFi workflow capabilities at the hackathon demo.

Usage:
    python seed_executions.py
"""

import asyncio
import json
import os
import sys
import random
from datetime import datetime, timedelta, UTC
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.execution_storage import ExecutionStorage, ExecutionRecord
from app.services.workflow_storage import get_workflow_storage


# ============================================================================
# Mock Data Configuration
# ============================================================================

# Sample Neo N3 transaction hashes (realistic format)
MOCK_TX_HASHES = [
    "0x7d5f3e2a1b9c4d6e8f0a2b4c6d8e0f1a3b5c7d9e1f3a5b7c9d1e3f5a7b9c1d3e5f",
    "0x8e6f4d2b1c0a9e8f7d6c5b4a3e2d1c0b9a8f7e6d5c4b3a2e1d0c9b8a7f6e5d4c3b",
    "0x9f7e5c3b2d1a0f8e7c6b5a4e3d2c1b0a9f8e7d6c5b4a3e2d1c0b9a8f7e6d5c4b3a",
    "0xa0f8e6d4c2b1a9f8e7d6c5b4a3e2d1c0b9a8f7e6d5c4b3a2e1d0c9b8a7f6e5d4c3",
    "0xb1a9f7e5d3c2b1a0f9e8d7c6b5a4e3d2c1b0a9f8e7d6c5b4a3e2d1c0b9a8f7e6d5",
    "0xc2b0f8e6d4c3b2a1f0e9d8c7b6a5e4d3c2b1a0f9e8d7c6b5a4e3d2c1b0a9f8e7d6",
    "0xd3c1a9f7e5d4c3b2a1f0e9d8c7b6a5e4d3c2b1a0f9e8d7c6b5a4e3d2c1b0a9f8e7",
    "0xe4d2b0f8e6d5c4b3a2f1e0d9c8b7a6e5d4c3b2a1f0e9d8c7b6a5e4d3c2b1a0f9e8",
    "0xf5e3c1a9f7e6d5c4b3a2f1e0d9c8b7a6e5d4c3b2a1f0e9d8c7b6a5e4d3c2b1a0f9",
    "0x06f4d2b0a8f7e6d5c4b3a2f1e0d9c8b7a6e5d4c3b2a1f0e9d8c7b6a5e4d3c2b1a0",
]

# User wallet address (from the demo wallet)
USER_ADDRESS = "NYxb4fSZVKAz8YsgaPK2WkT3KcAE9b3Vag"


async def get_workflow_ids() -> list:
    """Get all existing workflow IDs from storage."""
    storage = get_workflow_storage()
    workflows = await storage.list_workflows()
    return [(w.assembled_graph.workflow_id, w.assembled_graph.workflow_name) for w in workflows]


def generate_execution_id() -> str:
    """Generate a unique execution ID."""
    import uuid
    return f"exec_{uuid.uuid4().hex[:12]}"


def random_gas_used() -> str:
    """Generate realistic gas used amount."""
    return f"{random.randint(100000, 500000) / 1000:.3f}"


async def seed_executions():
    """Seed comprehensive mock execution history."""

    print("\n" + "=" * 60)
    print("Spica Demo - Seeding Mock Execution History")
    print("=" * 60 + "\n")

    # Initialize storage
    storage = ExecutionStorage()

    # Get existing workflows
    workflow_data = await get_workflow_ids()

    if not workflow_data:
        print("⚠ No workflows found. Please run the backend first to seed workflows.")
        print("  Then re-run this script to add execution history.\n")
        return

    print(f"✓ Found {len(workflow_data)} workflows to seed executions for\n")

    # Track all executions
    all_executions = []

    # Current time for reference
    now = datetime.now(UTC)

    # ========================================================================
    # Create diverse execution history for each workflow
    # ========================================================================

    for workflow_id, workflow_name in workflow_data:
        print(f"  Seeding executions for: {workflow_name}")

        # Determine execution patterns based on workflow type
        # Limited to ~14 total executions for demo clarity
        if "DCA" in workflow_name or "price" in workflow_name.lower():
            # Price-triggered workflows - 2-3 executions each
            execution_count = random.randint(2, 3)
            trigger_type = "price"
        elif "Weekly" in workflow_name:
            # Weekly scheduled - 2 weeks of history
            execution_count = 2
            trigger_type = "schedule"
        elif "Daily" in workflow_name:
            # Daily scheduled - 3 days of history
            execution_count = 3
            trigger_type = "schedule"
        else:
            # Generic workflows
            execution_count = 2
            trigger_type = "manual"

        # Create executions going back in time
        for i in range(execution_count):
            # Calculate execution time
            if trigger_type == "schedule" and "Weekly" in workflow_name:
                # Weekly executions on Mondays at 10am
                days_ago = i * 7 + random.randint(0, 2)  # Slight variance
            elif trigger_type == "schedule" and "Daily" in workflow_name:
                # Daily executions at 9am
                days_ago = i + random.randint(0, 1)
            else:
                # Random distribution over past 30 days
                days_ago = random.randint(0, 30)

            hours_ago = random.randint(0, 23)
            minutes_ago = random.randint(0, 59)

            started_at = now - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)

            # Determine execution outcome
            # 85% success rate for demo purposes
            if random.random() < 0.85:
                status = "completed"
                completed_at = started_at + timedelta(seconds=random.randint(3, 45))
                error = None
                tx_hash = random.choice(MOCK_TX_HASHES)
                gas_used = random_gas_used()
            elif random.random() < 0.5:
                # Some failed executions
                status = "failed"
                completed_at = started_at + timedelta(seconds=random.randint(5, 30))
                error = random.choice([
                    "Insufficient GAS balance for transaction",
                    "Price slippage exceeded threshold (2%)",
                    "Transaction timeout after 30s",
                    "Network congestion - retry recommended",
                ])
                tx_hash = None
                gas_used = None
            else:
                # Some running (recent ones)
                status = "running"
                completed_at = None
                error = None
                tx_hash = None
                gas_used = None

            # Build step results based on workflow type
            step_results = []

            if "Swap" in workflow_name or "swap" in workflow_name.lower() or "DCA" in workflow_name:
                # Swap workflow steps
                step_results = [
                    {
                        "action_type": "check_price",
                        "status": "completed",
                        "result": {
                            "token": "GAS",
                            "price_usd": round(random.uniform(3.5, 6.5), 2),
                            "source": "flamingo"
                        }
                    },
                    {
                        "action_type": "swap",
                        "status": status,
                        "tx_hash": tx_hash if status == "completed" else None,
                        "gas_used": gas_used if status == "completed" else None,
                        "result": {
                            "from_token": "GAS",
                            "to_token": "NEO",
                            "amount": round(random.uniform(5, 50), 2),
                            "received": round(random.uniform(0.5, 5), 4) if status == "completed" else None,
                            "rate": round(random.uniform(0.08, 0.12), 4)
                        }
                    }
                ]
            elif "Stake" in workflow_name or "stake" in workflow_name.lower():
                # Staking workflow steps
                step_results = [
                    {
                        "action_type": "check_balance",
                        "status": "completed",
                        "result": {
                            "token": "GAS",
                            "balance": round(random.uniform(100, 1000), 2)
                        }
                    },
                    {
                        "action_type": "stake",
                        "status": status,
                        "tx_hash": tx_hash if status == "completed" else None,
                        "gas_used": gas_used if status == "completed" else None,
                        "result": {
                            "token": "GAS",
                            "amount": 100,
                            "pool": "flamingo",
                            "expected_apy": "12.5%"
                        }
                    }
                ]
            elif "Rebalance" in workflow_name:
                # Portfolio rebalance steps
                step_results = [
                    {
                        "action_type": "check_portfolio",
                        "status": "completed",
                        "result": {
                            "gas_balance": round(random.uniform(100, 500), 2),
                            "neo_balance": round(random.uniform(10, 50), 2),
                            "gas_percentage": round(random.uniform(40, 80), 1)
                        }
                    },
                    {
                        "action_type": "swap",
                        "status": "completed" if status == "completed" else status,
                        "result": {
                            "from_token": "GAS",
                            "to_token": "NEO",
                            "percentage": "30%",
                            "amount_swapped": round(random.uniform(20, 100), 2)
                        }
                    },
                    {
                        "action_type": "stake",
                        "status": status,
                        "tx_hash": tx_hash if status == "completed" else None,
                        "gas_used": gas_used if status == "completed" else None,
                        "result": {
                            "token": "NEO",
                            "amount": round(random.uniform(5, 20), 2),
                            "pool": "neoburger"
                        }
                    }
                ]
            else:
                # Generic workflow steps
                step_results = [
                    {
                        "action_type": "initialize",
                        "status": "completed",
                        "result": {"message": "Workflow initialized"}
                    },
                    {
                        "action_type": "execute",
                        "status": status,
                        "tx_hash": tx_hash if status == "completed" else None,
                        "gas_used": gas_used if status == "completed" else None,
                        "result": {"message": "Execution complete" if status == "completed" else "Execution in progress"}
                    }
                ]

            # Create execution record
            execution = ExecutionRecord(
                execution_id=generate_execution_id(),
                workflow_id=workflow_id,
                workflow_name=workflow_name,
                user_address=USER_ADDRESS,
                trigger_type=trigger_type,
                started_at=started_at,
                completed_at=completed_at,
                status=status,
                step_results=step_results,
                error=error,
                metadata={
                    "tx_hash": tx_hash,
                    "gas_used": gas_used,
                    "network": "neo-testnet",
                    "trigger_price": round(random.uniform(4.0, 5.5), 2) if trigger_type == "price" else None
                }
            )

            # Save execution
            await storage.save_execution(execution)
            all_executions.append(execution)

    # ========================================================================
    # Summary
    # ========================================================================

    print("\n" + "-" * 60)
    print("Execution Seeding Complete!")
    print("-" * 60)

    # Count by status
    completed = sum(1 for e in all_executions if e.status == "completed")
    failed = sum(1 for e in all_executions if e.status == "failed")
    running = sum(1 for e in all_executions if e.status == "running")

    print(f"\n✓ Total Executions Created: {len(all_executions)}")
    print(f"  • Completed: {completed}")
    print(f"  • Failed: {failed}")
    print(f"  • Running: {running}")

    # Count by workflow
    print(f"\n✓ Executions per Workflow:")
    for wf_id, wf_name in workflow_data:
        count = sum(1 for e in all_executions if e.workflow_id == wf_id)
        print(f"  • {wf_name}: {count} executions")

    print("\n" + "=" * 60)
    print("Demo ready! Visit the History page to see execution history.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(seed_executions())
