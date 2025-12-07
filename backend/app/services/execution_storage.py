"""
Execution Storage Service for Spica

This module implements Task 3.3: Execution Storage

The ExecutionStorage service provides:
- Persistent storage of workflow execution records
- JSON file-based storage with indexing
- Fast lookups by workflow_id
- CRUD operations for execution records
- Execution history tracking

Acceptance Criteria:
- Store execution records to JSON files
- Maintain index file for fast lookups
- Support filtering by workflow_id
- Provide execution history retrieval
- Handle concurrent access safely
"""

import json
import logging
import asyncio
import os
from typing import Optional, Dict, Any, List
from datetime import datetime, UTC
from dataclasses import dataclass, field, asdict
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)


# ============================================================================
# Execution Record Model
# ============================================================================

@dataclass
class ExecutionRecord:
    """
    Record of a workflow execution.

    This represents a single execution instance of a workflow,
    including all steps, results, and metadata.
    """
    execution_id: str
    workflow_id: str
    workflow_name: str
    user_address: str
    trigger_type: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str = "running"  # running, completed, failed
    step_results: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        # Convert datetime objects to ISO format strings
        data["started_at"] = self.started_at.isoformat()
        if self.completed_at:
            data["completed_at"] = self.completed_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionRecord":
        """Create ExecutionRecord from dictionary."""
        # Parse datetime strings back to datetime objects
        data = data.copy()
        data["started_at"] = datetime.fromisoformat(data["started_at"])
        if data.get("completed_at"):
            data["completed_at"] = datetime.fromisoformat(data["completed_at"])
        return cls(**data)


# ============================================================================
# Execution Storage Service
# ============================================================================

class ExecutionStorage:
    """
    Service for persistent storage of workflow execution records.

    Implements Task 3.3: Execution Storage

    Storage Structure:
    - Individual execution files: data/executions/{execution_id}.json
    - Index file: data/executions/index.json
    - By-workflow index: data/executions/by_workflow/{workflow_id}.json

    Features:
    - JSON file-based storage (simple, debuggable)
    - Fast lookups via index files
    - Filtering by workflow_id
    - Thread-safe operations with asyncio locks

    Usage:
        ```python
        storage = ExecutionStorage()

        # Create execution record
        record = ExecutionRecord(
            execution_id="exec_123",
            workflow_id="wf_456",
            workflow_name="Auto Swap",
            user_address="NXXXyyy...",
            trigger_type="price",
            started_at=datetime.now(UTC)
        )

        # Save record
        await storage.save_execution(record)

        # Retrieve record
        retrieved = await storage.get_execution("exec_123")

        # Get history for workflow
        history = await storage.get_workflow_executions("wf_456")
        ```
    """

    def __init__(self, storage_dir: Optional[Path] = None):
        """
        Initialize execution storage.

        Args:
            storage_dir: Directory for execution data (default: data/executions)
        """
        # Use configured storage directory or default
        if storage_dir is None:
            base_dir = Path(settings.spica_data_dir if hasattr(settings, 'spica_data_dir') else "data")
            storage_dir = base_dir / "executions"

        self.storage_dir = Path(storage_dir)
        self.index_file = self.storage_dir / "index.json"
        self.by_workflow_dir = self.storage_dir / "by_workflow"

        # Thread safety
        self._lock = asyncio.Lock()

        # In-memory cache for fast access
        self._cache: Dict[str, ExecutionRecord] = {}
        self._index: Dict[str, str] = {}  # execution_id -> file_path

        # Initialize storage
        self._initialize_storage()

        logger.info(f"ExecutionStorage initialized at {self.storage_dir}")

    def _initialize_storage(self):
        """Create storage directories if they don't exist."""
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.by_workflow_dir.mkdir(parents=True, exist_ok=True)

        # Create index file if it doesn't exist
        if not self.index_file.exists():
            self._save_index({})

    def _save_index(self, index: Dict[str, str]):
        """Save index file."""
        with open(self.index_file, 'w') as f:
            json.dump(index, f, indent=2)

    def _load_index(self) -> Dict[str, str]:
        """Load index file."""
        if not self.index_file.exists():
            return {}

        try:
            with open(self.index_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading index: {e}")
            return {}

    def _get_execution_file_path(self, execution_id: str) -> Path:
        """Get file path for execution record."""
        return self.storage_dir / f"{execution_id}.json"

    def _get_workflow_index_path(self, workflow_id: str) -> Path:
        """Get file path for workflow execution index."""
        return self.by_workflow_dir / f"{workflow_id}.json"

    # ========================================================================
    # CRUD Operations
    # ========================================================================

    async def save_execution(self, record: ExecutionRecord) -> bool:
        """
        Save execution record to storage.

        Args:
            record: ExecutionRecord to save

        Returns:
            True if saved successfully
        """
        async with self._lock:
            try:
                execution_id = record.execution_id
                workflow_id = record.workflow_id

                # Save execution file
                file_path = self._get_execution_file_path(execution_id)
                with open(file_path, 'w') as f:
                    json.dump(record.to_dict(), f, indent=2)

                # Update main index
                index = self._load_index()
                index[execution_id] = str(file_path)
                self._save_index(index)

                # Update workflow index
                workflow_index_path = self._get_workflow_index_path(workflow_id)
                if workflow_index_path.exists():
                    with open(workflow_index_path, 'r') as f:
                        workflow_executions = json.load(f)
                else:
                    workflow_executions = []

                # Add to workflow index if not already present
                if execution_id not in workflow_executions:
                    workflow_executions.append(execution_id)
                    with open(workflow_index_path, 'w') as f:
                        json.dump(workflow_executions, f, indent=2)

                # Update cache
                self._cache[execution_id] = record

                logger.info(f"Saved execution record: {execution_id}")
                return True

            except Exception as e:
                logger.error(f"Error saving execution {record.execution_id}: {e}")
                return False

    def _get_execution_unlocked(self, execution_id: str) -> Optional[ExecutionRecord]:
        """
        Get execution record by ID without acquiring lock.
        Internal method for use when lock is already held.
        """
        # Check cache first
        if execution_id in self._cache:
            return self._cache[execution_id]

        # Load from file
        try:
            file_path = self._get_execution_file_path(execution_id)
            if not file_path.exists():
                return None

            with open(file_path, 'r') as f:
                data = json.load(f)

            record = ExecutionRecord.from_dict(data)

            # Update cache
            self._cache[execution_id] = record

            return record

        except Exception as e:
            logger.error(f"Error loading execution {execution_id}: {e}")
            return None

    async def get_execution(self, execution_id: str) -> Optional[ExecutionRecord]:
        """
        Get execution record by ID.

        Args:
            execution_id: Execution ID to retrieve

        Returns:
            ExecutionRecord if found, None otherwise
        """
        async with self._lock:
            result = self._get_execution_unlocked(execution_id)
            if result is None and execution_id not in self._cache:
                logger.warning(f"Execution record not found: {execution_id}")
            return result

    async def update_execution(self, record: ExecutionRecord) -> bool:
        """
        Update existing execution record.

        Args:
            record: Updated ExecutionRecord

        Returns:
            True if updated successfully
        """
        # Same as save - overwrites existing file
        return await self.save_execution(record)

    async def delete_execution(self, execution_id: str) -> bool:
        """
        Delete execution record.

        Args:
            execution_id: Execution ID to delete

        Returns:
            True if deleted successfully
        """
        async with self._lock:
            try:
                # Remove execution file
                file_path = self._get_execution_file_path(execution_id)
                if file_path.exists():
                    file_path.unlink()

                # Update main index
                index = self._load_index()
                if execution_id in index:
                    del index[execution_id]
                    self._save_index(index)

                # Remove from cache
                if execution_id in self._cache:
                    del self._cache[execution_id]

                logger.info(f"Deleted execution record: {execution_id}")
                return True

            except Exception as e:
                logger.error(f"Error deleting execution {execution_id}: {e}")
                return False

    # ========================================================================
    # Query Operations
    # ========================================================================

    async def get_workflow_executions(
        self,
        workflow_id: str,
        limit: int = 100,
        status: Optional[str] = None
    ) -> List[ExecutionRecord]:
        """
        Get all executions for a specific workflow.

        Args:
            workflow_id: Workflow ID to filter by
            limit: Maximum number of records to return
            status: Optional status filter (running, completed, failed)

        Returns:
            List of ExecutionRecords, sorted by started_at (newest first)
        """
        async with self._lock:
            try:
                workflow_index_path = self._get_workflow_index_path(workflow_id)
                if not workflow_index_path.exists():
                    return []

                with open(workflow_index_path, 'r') as f:
                    execution_ids = json.load(f)

                # Load execution records (using unlocked version to avoid deadlock)
                records = []
                for execution_id in execution_ids:
                    record = self._get_execution_unlocked(execution_id)
                    if record:
                        # Apply status filter if provided
                        if status is None or record.status == status:
                            records.append(record)

                # Sort by started_at (newest first)
                records.sort(key=lambda r: r.started_at, reverse=True)

                # Apply limit
                return records[:limit]

            except Exception as e:
                logger.error(f"Error getting workflow executions for {workflow_id}: {e}")
                return []

    async def get_all_executions(
        self,
        limit: int = 100,
        status: Optional[str] = None
    ) -> List[ExecutionRecord]:
        """
        Get all execution records.

        Args:
            limit: Maximum number of records to return
            status: Optional status filter

        Returns:
            List of ExecutionRecords, sorted by started_at (newest first)
        """
        async with self._lock:
            try:
                index = self._load_index()

                records = []
                for execution_id in index.keys():
                    # Use unlocked version to avoid deadlock
                    record = self._get_execution_unlocked(execution_id)
                    if record:
                        # Apply status filter if provided
                        if status is None or record.status == status:
                            records.append(record)

                # Sort by started_at (newest first)
                records.sort(key=lambda r: r.started_at, reverse=True)

                # Apply limit
                return records[:limit]

            except Exception as e:
                logger.error(f"Error getting all executions: {e}")
                return []

    async def get_execution_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about executions.

        Returns:
            Dictionary with execution statistics
        """
        async with self._lock:
            try:
                index = self._load_index()
                total = len(index)

                # Count by status
                status_counts = {
                    "running": 0,
                    "completed": 0,
                    "failed": 0
                }

                for execution_id in index.keys():
                    # Use unlocked version to avoid deadlock
                    record = self._get_execution_unlocked(execution_id)
                    if record:
                        status_counts[record.status] = status_counts.get(record.status, 0) + 1

                return {
                    "total_executions": total,
                    "by_status": status_counts,
                    "cache_size": len(self._cache)
                }

            except Exception as e:
                logger.error(f"Error getting statistics: {e}")
                return {
                    "total_executions": 0,
                    "by_status": {},
                    "cache_size": 0
                }

    # ========================================================================
    # Cleanup Operations
    # ========================================================================

    async def cleanup_old_executions(self, days: int = 30) -> int:
        """
        Remove execution records older than specified days.

        Args:
            days: Delete records older than this many days

        Returns:
            Number of records deleted
        """
        from datetime import timedelta

        cutoff_date = datetime.now(UTC) - timedelta(days=days)
        deleted_count = 0

        # Get list of old execution IDs first (with lock)
        async with self._lock:
            try:
                index = self._load_index()
                old_execution_ids = []

                for execution_id in list(index.keys()):
                    record = self._get_execution_unlocked(execution_id)
                    if record and record.started_at < cutoff_date:
                        old_execution_ids.append(execution_id)

            except Exception as e:
                logger.error(f"Error during cleanup scan: {e}")
                return 0

        # Delete old executions (each call will acquire its own lock)
        for execution_id in old_execution_ids:
            if await self.delete_execution(execution_id):
                deleted_count += 1

        logger.info(f"Cleaned up {deleted_count} old execution records")
        return deleted_count


# ============================================================================
# Singleton Instance
# ============================================================================

_execution_storage: Optional[ExecutionStorage] = None
_storage_lock = asyncio.Lock()


async def get_execution_storage() -> ExecutionStorage:
    """
    Get the global ExecutionStorage instance (thread-safe).

    Returns:
        ExecutionStorage singleton
    """
    global _execution_storage

    if _execution_storage is not None:
        return _execution_storage

    async with _storage_lock:
        if _execution_storage is None:
            _execution_storage = ExecutionStorage()
        return _execution_storage


async def close_execution_storage():
    """Close the global ExecutionStorage instance."""
    global _execution_storage

    async with _storage_lock:
        if _execution_storage is not None:
            logger.info("ExecutionStorage closed")
            _execution_storage = None
