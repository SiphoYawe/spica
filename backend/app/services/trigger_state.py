"""
Trigger State Persistence for Spica Workflows

Implements Task 2.5: Trigger State Persistence

This module provides persistent storage for workflow trigger state,
allowing triggers to maintain state across backend restarts.

Features:
- JSON-based file storage for simplicity and debuggability
- State tracking: last_checked, last_triggered, check_count, errors
- Active/inactive trigger management
- Thread-safe singleton pattern

Storage Structure:
data/triggers/
  ├── wf_abc123.json
  ├── wf_def456.json
  └── ...

Each file contains trigger state in JSON format:
{
  "workflow_id": "wf_abc123",
  "trigger_type": "price",
  "last_checked": "2025-12-06T10:30:00Z",
  "last_triggered": "2025-12-06T10:28:00Z",
  "check_count": 145,
  "is_active": true,
  "error_count": 0,
  "last_error": null
}
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, List
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class TriggerState:
    """
    State of a workflow trigger.

    Attributes:
        workflow_id: Unique workflow identifier
        trigger_type: Type of trigger ("price" or "time")
        last_checked: When trigger condition was last evaluated
        last_triggered: When trigger condition was last met
        check_count: Number of times trigger has been checked
        is_active: Whether trigger is currently active
        error_count: Number of consecutive errors
        last_error: Last error message (if any)
    """
    workflow_id: str
    trigger_type: str  # "price" or "time"
    last_checked: Optional[datetime] = None
    last_triggered: Optional[datetime] = None
    check_count: int = 0
    is_active: bool = True
    error_count: int = 0
    last_error: Optional[str] = None

    def to_dict(self) -> dict:
        """
        Convert to dictionary for JSON serialization.

        Converts datetime objects to ISO 8601 strings.
        """
        data = asdict(self)
        # Convert datetime to ISO string
        for key in ["last_checked", "last_triggered"]:
            if data[key]:
                data[key] = data[key].isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "TriggerState":
        """
        Create TriggerState from dictionary.

        Converts ISO 8601 strings back to datetime objects.
        """
        # Convert ISO strings back to datetime
        for key in ["last_checked", "last_triggered"]:
            if data.get(key):
                data[key] = datetime.fromisoformat(data[key])
        return cls(**data)


class TriggerStateStorage:
    """
    Persists trigger state to JSON files.

    Provides CRUD operations for trigger state with file-based persistence.
    Each workflow gets its own JSON file for atomic updates.

    Thread-safe for single-process usage. For multi-process deployments,
    consider using a database backend.
    """

    def __init__(self, storage_dir: str = "data/triggers"):
        """
        Initialize storage with directory path.

        Args:
            storage_dir: Directory path for storing trigger state files
                        (relative to backend root)
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"TriggerStateStorage initialized: {self.storage_dir.absolute()}")

    def _get_path(self, workflow_id: str) -> Path:
        """
        Get file path for workflow trigger state.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Path to JSON file for this workflow
        """
        # Sanitize workflow_id to prevent directory traversal
        safe_id = workflow_id.replace("/", "_").replace("\\", "_")
        return self.storage_dir / f"{safe_id}.json"

    def save(self, state: TriggerState) -> None:
        """
        Save trigger state to disk.

        Args:
            state: TriggerState to persist

        Raises:
            IOError: If file write fails
        """
        try:
            path = self._get_path(state.workflow_id)
            data = state.to_dict()

            # Write atomically using temp file + rename
            temp_path = path.with_suffix(".tmp")
            with open(temp_path, "w") as f:
                json.dump(data, f, indent=2)

            # Atomic rename
            temp_path.replace(path)

            logger.debug(f"Saved trigger state: {state.workflow_id}")

        except Exception as e:
            logger.error(f"Failed to save trigger state for {state.workflow_id}: {e}")
            raise

    def load(self, workflow_id: str) -> Optional[TriggerState]:
        """
        Load trigger state from disk.

        Args:
            workflow_id: Workflow identifier

        Returns:
            TriggerState if found, None otherwise

        Raises:
            ValueError: If JSON is malformed
        """
        path = self._get_path(workflow_id)
        if not path.exists():
            logger.debug(f"No trigger state found for: {workflow_id}")
            return None

        try:
            with open(path) as f:
                data = json.load(f)

            state = TriggerState.from_dict(data)
            logger.debug(f"Loaded trigger state: {workflow_id}")
            return state

        except Exception as e:
            logger.error(f"Failed to load trigger state for {workflow_id}: {e}")
            raise ValueError(f"Invalid trigger state file: {path}") from e

    def delete(self, workflow_id: str) -> bool:
        """
        Delete trigger state from disk.

        Args:
            workflow_id: Workflow identifier

        Returns:
            True if state was deleted, False if not found
        """
        path = self._get_path(workflow_id)
        if path.exists():
            try:
                path.unlink()
                logger.info(f"Deleted trigger state: {workflow_id}")
                return True
            except Exception as e:
                logger.error(f"Failed to delete trigger state for {workflow_id}: {e}")
                raise
        return False

    def list_active(self) -> List[TriggerState]:
        """
        List all active trigger states.

        Returns:
            List of TriggerState objects where is_active=True

        Note:
            This reads all files in storage directory. For large numbers
            of workflows, consider indexing or database backend.
        """
        states = []
        for path in self.storage_dir.glob("*.json"):
            try:
                state = self.load(path.stem)
                if state and state.is_active:
                    states.append(state)
            except Exception as e:
                logger.warning(f"Skipping invalid state file {path}: {e}")
                continue

        logger.info(f"Found {len(states)} active triggers")
        return states

    def list_all(self) -> List[TriggerState]:
        """
        List all trigger states (active and inactive).

        Returns:
            List of all TriggerState objects
        """
        states = []
        for path in self.storage_dir.glob("*.json"):
            try:
                state = self.load(path.stem)
                if state:
                    states.append(state)
            except Exception as e:
                logger.warning(f"Skipping invalid state file {path}: {e}")
                continue

        logger.info(f"Found {len(states)} total triggers")
        return states

    def update_check(self, workflow_id: str, error: Optional[str] = None) -> None:
        """
        Update trigger check timestamp and count.

        Convenience method to record a trigger check.

        Args:
            workflow_id: Workflow identifier
            error: Optional error message if check failed
        """
        state = self.load(workflow_id)
        if state is None:
            # Create new state if doesn't exist
            state = TriggerState(
                workflow_id=workflow_id,
                trigger_type="unknown"
            )

        state.last_checked = datetime.now()
        state.check_count += 1

        if error:
            state.error_count += 1
            state.last_error = error
        else:
            state.error_count = 0
            state.last_error = None

        self.save(state)

    def update_trigger(self, workflow_id: str) -> None:
        """
        Update trigger activation timestamp.

        Convenience method to record when trigger condition was met.

        Args:
            workflow_id: Workflow identifier
        """
        state = self.load(workflow_id)
        if state is None:
            logger.warning(f"Cannot update trigger for unknown workflow: {workflow_id}")
            return

        state.last_triggered = datetime.now()
        self.save(state)


# ============================================================================
# Singleton Instance
# ============================================================================

_storage: Optional[TriggerStateStorage] = None


def get_trigger_storage() -> TriggerStateStorage:
    """
    Get global TriggerStateStorage singleton.

    Returns:
        TriggerStateStorage instance

    Usage:
        storage = get_trigger_storage()
        state = storage.load("wf_abc123")
    """
    global _storage
    if _storage is None:
        _storage = TriggerStateStorage()
    return _storage


def reset_trigger_storage(storage_dir: Optional[str] = None) -> None:
    """
    Reset global storage instance (mainly for testing).

    Args:
        storage_dir: Optional custom storage directory
    """
    global _storage
    if storage_dir:
        _storage = TriggerStateStorage(storage_dir)
    else:
        _storage = None
