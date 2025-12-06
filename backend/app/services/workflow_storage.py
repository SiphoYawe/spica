"""
Workflow Storage Service - Persistent storage for workflow graphs.

This service implements Story 3.3 and provides:
1. Saving assembled workflows as JSON files
2. Loading workflows from JSON storage
3. Listing all stored workflows
4. Deleting workflows

Storage Format:
- Location: data/workflows/
- Filename: {workflow_id}.json
- Content: Complete StoredWorkflow with AssembledGraph

Security Features:
- File locking to prevent race conditions
- Path traversal protection via workflow_id validation
- Storage quotas to prevent resource exhaustion
- Sanitized error messages to prevent information disclosure
"""

import json
import logging
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict, Any

from pydantic import ValidationError
from filelock import FileLock, Timeout as FileLockTimeout

from app.models.graph_models import AssembledGraph, StoredWorkflow
from app.models.workflow_models import WorkflowSpec

logger = logging.getLogger(__name__)


# ============================================================================
# Storage Configuration
# ============================================================================

# Default storage directory relative to project root
DEFAULT_STORAGE_DIR = Path(__file__).parent.parent.parent / "data" / "workflows"

# Storage quotas to prevent resource exhaustion (Issue #6)
MAX_WORKFLOWS_PER_USER = 100  # Maximum workflows per user
MAX_TOTAL_WORKFLOWS = 10000   # Maximum total workflows in system

# Workflow ID validation pattern (Issue #2 - Path Traversal Protection)
# Format: wf_ followed by alphanumeric, underscore, or hyphen (1-64 chars)
# Example: wf_a1b2c3d4e5f6, wf_user-workflow_123
# Prevents: ../../../etc/passwd, ../../../../tmp/evil
WORKFLOW_ID_PATTERN = re.compile(r'^wf_[a-zA-Z0-9_-]{1,64}$')

# File lock timeout (in seconds)
FILE_LOCK_TIMEOUT = 10.0


# ============================================================================
# WorkflowStorage Service
# ============================================================================

class WorkflowStorage:
    """
    Service for persisting workflow graphs to disk.

    This service handles saving and loading workflow graphs as JSON files,
    providing a simple file-based storage solution for the MVP.

    Security Features:
        - File-based locking to prevent race conditions
        - Workflow ID validation to prevent path traversal attacks
        - Storage quotas to prevent resource exhaustion
        - Sanitized error messages to prevent information disclosure

    Usage:
        ```python
        storage = WorkflowStorage()

        # Save a workflow
        workflow_id = await storage.save_workflow(
            assembled_graph=assembled,
            workflow_spec=workflow_spec,
            user_id="user_123",
            user_address="NXXXyyy..."
        )

        # Load a workflow
        stored = await storage.load_workflow(workflow_id)

        # List all workflows
        workflows = await storage.list_workflows()
        ```

    Notes:
        - For production, replace with database storage (PostgreSQL, MongoDB)
        - File-based storage is simple and sufficient for MVP
        - Thread-safe for concurrent read/write operations via file locking
    """

    def __init__(self, storage_dir: Optional[Path] = None):
        """
        Initialize workflow storage service.

        Args:
            storage_dir: Optional custom storage directory.
                        Defaults to data/workflows/ in project root.
        """
        self.storage_dir = storage_dir or DEFAULT_STORAGE_DIR
        self._ensure_storage_dir()
        logger.info(f"WorkflowStorage initialized with storage_dir={self.storage_dir}")

    def _ensure_storage_dir(self) -> None:
        """Create storage directory if it doesn't exist."""
        try:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Storage directory ready: {self.storage_dir}")
        except OSError as e:
            # Sanitized error message - don't expose internal paths (Issue #7)
            logger.error(f"Failed to create storage directory {self.storage_dir}: {e}")
            raise RuntimeError("Cannot create storage directory") from e

    def _validate_workflow_id(self, workflow_id: str) -> None:
        """
        Validate workflow ID to prevent path traversal attacks (Issue #2).

        Args:
            workflow_id: Workflow identifier to validate

        Raises:
            ValueError: If workflow_id doesn't match expected pattern

        Example:
            Valid: "wf_a1b2c3d4e5f6", "wf_user-workflow_123"
            Invalid: "../../../etc/passwd", "wf_", "workflow_123" (missing prefix)
        """
        if not WORKFLOW_ID_PATTERN.match(workflow_id):
            logger.warning(f"Invalid workflow_id format rejected: {workflow_id}")
            raise ValueError(
                f"Invalid workflow_id format. Expected format: wf_[a-zA-Z0-9_-]{{1,64}}, got: {workflow_id}"
            )

    def _get_workflow_path(self, workflow_id: str) -> Path:
        """
        Get file path for a workflow.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Path to workflow JSON file

        Raises:
            ValueError: If workflow_id is invalid (path traversal protection)
        """
        # Validate workflow_id to prevent path traversal (Issue #2)
        self._validate_workflow_id(workflow_id)
        return self.storage_dir / f"{workflow_id}.json"

    def _get_lock_path(self, workflow_id: str) -> Path:
        """
        Get file lock path for a workflow.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Path to lock file
        """
        return self.storage_dir / f"{workflow_id}.lock"

    async def _check_storage_quotas(self, user_id: str) -> None:
        """
        Check storage quotas to prevent resource exhaustion (Issue #6).

        Args:
            user_id: User ID to check quotas for

        Raises:
            RuntimeError: If storage quotas are exceeded
        """
        # Count total workflows
        total_count = len(list(self.storage_dir.glob("*.json")))
        if total_count >= MAX_TOTAL_WORKFLOWS:
            logger.error(f"Total workflow limit reached: {total_count}/{MAX_TOTAL_WORKFLOWS}")
            raise RuntimeError(
                f"System storage quota exceeded. Maximum {MAX_TOTAL_WORKFLOWS} workflows allowed."
            )

        # Count user workflows
        user_count = 0
        for file_path in self.storage_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("user_id") == user_id:
                        user_count += 1
            except (json.JSONDecodeError, OSError):
                continue

        if user_count >= MAX_WORKFLOWS_PER_USER:
            logger.warning(f"User {user_id} exceeded workflow quota: {user_count}/{MAX_WORKFLOWS_PER_USER}")
            raise RuntimeError(
                f"User storage quota exceeded. Maximum {MAX_WORKFLOWS_PER_USER} workflows allowed per user."
            )

    # ========================================================================
    # Save Operations
    # ========================================================================

    async def save_workflow(
        self,
        assembled_graph: AssembledGraph,
        workflow_spec: WorkflowSpec,
        user_id: str = "anonymous",
        user_address: str = "N/A"
    ) -> str:
        """
        Save an assembled workflow to disk with file locking and quota checks.

        Security Features:
            - File locking to prevent race conditions (Issue #1)
            - Workflow ID validation to prevent path traversal (Issue #2)
            - Storage quota enforcement (Issue #6)
            - Sanitized error messages (Issue #7)

        Args:
            assembled_graph: Complete assembled graph from GraphAssembler
            workflow_spec: Original workflow specification
            user_id: User identifier (default: "anonymous")
            user_address: User's Neo N3 address (default: "N/A")

        Returns:
            workflow_id: Unique identifier for the saved workflow

        Raises:
            ValueError: If assembled_graph is invalid or workflow_id format is invalid
            RuntimeError: If file write fails or storage quotas exceeded

        Example:
            ```python
            # After assembling a graph
            workflow_id = await storage.save_workflow(
                assembled_graph=assembled,
                workflow_spec=workflow_spec,
                user_id="user_123",
                user_address="NXXXyyy..."
            )
            print(f"Workflow saved: {workflow_id}")
            ```
        """
        workflow_id = assembled_graph.workflow_id

        logger.info(f"Saving workflow {workflow_id} for user {user_id}")

        # Validate workflow_id format (Issue #2 - Path Traversal Protection)
        self._validate_workflow_id(workflow_id)

        # Check storage quotas (Issue #6 - Resource Exhaustion Protection)
        await self._check_storage_quotas(user_id)

        try:
            # Create StoredWorkflow with execution state
            stored = StoredWorkflow(
                workflow_id=workflow_id,
                user_id=user_id,
                user_address=user_address,
                assembled_graph=assembled_graph,
                status="active",
                enabled=True,
                trigger_count=0,
                execution_count=0,
            )

            # Serialize to JSON
            json_data = stored.model_dump_json(indent=2)

            # Get file paths
            file_path = self._get_workflow_path(workflow_id)
            temp_path = file_path.with_suffix(".tmp")
            lock_path = self._get_lock_path(workflow_id)

            # Use file lock to prevent race conditions (Issue #1)
            lock = FileLock(lock_path, timeout=FILE_LOCK_TIMEOUT)

            try:
                with lock:
                    logger.debug(f"Acquired lock for workflow {workflow_id}")

                    # Write to temp file
                    try:
                        with open(temp_path, "w", encoding="utf-8") as f:
                            f.write(json_data)

                        # Atomic rename (overwrites existing file)
                        temp_path.replace(file_path)

                        logger.info(f"Successfully saved workflow {workflow_id}")
                        return workflow_id

                    except OSError as e:
                        # Clean up temp file if it exists
                        if temp_path.exists():
                            temp_path.unlink()
                        # Sanitized error message (Issue #7)
                        logger.error(f"Failed to write workflow file {workflow_id}: {e}")
                        raise RuntimeError("Failed to write workflow file") from e

            except FileLockTimeout:
                # Sanitized error message (Issue #7)
                logger.error(f"Lock timeout for workflow {workflow_id}")
                raise RuntimeError(
                    f"Could not acquire file lock for workflow. Please try again."
                ) from None

        except ValidationError as e:
            logger.error(f"Validation error creating StoredWorkflow: {e}")
            raise ValueError(f"Invalid workflow data: {e}") from e

    async def update_workflow(
        self,
        workflow_id: str,
        updates: Dict[str, Any]
    ) -> StoredWorkflow:
        """
        Update an existing workflow's metadata with file locking.

        Security Features:
            - File locking to prevent race conditions (Issue #1)
            - Workflow ID validation (Issue #2)
            - Sanitized error messages (Issue #7)

        Args:
            workflow_id: Workflow to update
            updates: Dictionary of fields to update

        Returns:
            Updated StoredWorkflow

        Raises:
            FileNotFoundError: If workflow doesn't exist
            ValueError: If updates are invalid or workflow_id format is invalid
            RuntimeError: If file lock cannot be acquired

        Example:
            ```python
            # Disable a workflow
            await storage.update_workflow(
                workflow_id="wf_123abc456def",
                updates={"enabled": False, "status": "paused"}
            )
            ```
        """
        logger.info(f"Updating workflow {workflow_id}")

        # Validate workflow_id format (Issue #2)
        self._validate_workflow_id(workflow_id)

        # Get file paths
        file_path = self._get_workflow_path(workflow_id)
        lock_path = self._get_lock_path(workflow_id)

        # Use file lock to prevent race conditions (Issue #1)
        lock = FileLock(lock_path, timeout=FILE_LOCK_TIMEOUT)

        try:
            with lock:
                logger.debug(f"Acquired lock for workflow {workflow_id}")

                # Load existing workflow
                stored = await self.load_workflow(workflow_id)

                # Apply updates
                for key, value in updates.items():
                    if hasattr(stored, key):
                        setattr(stored, key, value)
                    else:
                        logger.warning(f"Ignoring unknown field in update: {key}")

                # Update timestamp
                stored.updated_at = datetime.now(timezone.utc)

                # Save back
                json_data = stored.model_dump_json(indent=2)

                try:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(json_data)
                except OSError as e:
                    # Sanitized error message (Issue #7)
                    logger.error(f"Failed to update workflow file {workflow_id}: {e}")
                    raise RuntimeError("Failed to update workflow file") from e

                logger.info(f"Successfully updated workflow {workflow_id}")
                return stored

        except FileLockTimeout:
            # Sanitized error message (Issue #7)
            logger.error(f"Lock timeout for workflow {workflow_id}")
            raise RuntimeError(
                f"Could not acquire file lock for workflow. Please try again."
            ) from None

    # ========================================================================
    # Load Operations
    # ========================================================================

    async def load_workflow(self, workflow_id: str) -> StoredWorkflow:
        """
        Load a workflow from disk with validation.

        Security Features:
            - Workflow ID validation (Issue #2)
            - Sanitized error messages (Issue #7)

        Args:
            workflow_id: Workflow identifier

        Returns:
            StoredWorkflow with complete graph data

        Raises:
            FileNotFoundError: If workflow doesn't exist
            ValueError: If JSON is invalid, corrupted, or workflow_id format is invalid

        Example:
            ```python
            stored = await storage.load_workflow("wf_123abc456def")
            print(f"Workflow: {stored.assembled_graph.workflow_name}")
            print(f"Status: {stored.status}")
            ```
        """
        # Validate workflow_id format (Issue #2)
        self._validate_workflow_id(workflow_id)

        file_path = self._get_workflow_path(workflow_id)

        if not file_path.exists():
            logger.warning(f"Workflow not found: {workflow_id}")
            raise FileNotFoundError(f"Workflow {workflow_id} does not exist")

        logger.debug(f"Loading workflow {workflow_id}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                json_data = f.read()

            # Parse and validate
            stored = StoredWorkflow.model_validate_json(json_data)

            logger.debug(f"Successfully loaded workflow {workflow_id}")
            return stored

        except json.JSONDecodeError as e:
            # Sanitized error message (Issue #7)
            logger.error(f"Invalid JSON in workflow file {workflow_id}: {e}")
            raise ValueError(f"Corrupted workflow file") from e

        except ValidationError as e:
            logger.error(f"Validation error loading workflow {workflow_id}: {e}")
            raise ValueError(f"Invalid workflow data: {e}") from e

        except OSError as e:
            # Sanitized error message (Issue #7)
            logger.error(f"Failed to read workflow file {workflow_id}: {e}")
            raise RuntimeError("Failed to read workflow file") from e

    async def workflow_exists(self, workflow_id: str) -> bool:
        """
        Check if a workflow exists in storage.

        Security Features:
            - Workflow ID validation (Issue #2)

        Args:
            workflow_id: Workflow identifier

        Returns:
            True if workflow exists, False otherwise

        Raises:
            ValueError: If workflow_id format is invalid

        Example:
            ```python
            if await storage.workflow_exists("wf_123abc456def"):
                print("Workflow exists!")
            ```
        """
        # Validate workflow_id format (Issue #2)
        self._validate_workflow_id(workflow_id)
        return self._get_workflow_path(workflow_id).exists()

    # ========================================================================
    # List Operations
    # ========================================================================

    async def list_workflows(
        self,
        user_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[StoredWorkflow]:
        """
        List all workflows, optionally filtered by user or status.

        Args:
            user_id: Optional user ID filter
            status: Optional status filter ("active", "paused", etc.)

        Returns:
            List of StoredWorkflow instances

        Example:
            ```python
            # List all workflows
            all_workflows = await storage.list_workflows()

            # List user's active workflows
            user_workflows = await storage.list_workflows(
                user_id="user_123",
                status="active"
            )
            ```
        """
        logger.debug(f"Listing workflows (user_id={user_id}, status={status})")

        workflows = []

        # Iterate through all JSON files in storage directory
        for file_path in self.storage_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    json_data = f.read()

                stored = StoredWorkflow.model_validate_json(json_data)

                # Apply filters
                if user_id and stored.user_id != user_id:
                    continue
                if status and stored.status != status:
                    continue

                workflows.append(stored)

            except (json.JSONDecodeError, ValidationError) as e:
                # Sanitized logging - don't expose file paths (Issue #7)
                logger.warning(f"Skipping invalid workflow file {file_path.stem}: {e}")
                continue
            except OSError as e:
                # Sanitized logging - don't expose file paths (Issue #7)
                logger.warning(f"Failed to read workflow file {file_path.stem}: {e}")
                continue

        logger.info(f"Found {len(workflows)} workflows")
        return workflows

    async def list_workflow_ids(self) -> List[str]:
        """
        List all workflow IDs (lightweight operation).

        Returns:
            List of workflow IDs

        Example:
            ```python
            ids = await storage.list_workflow_ids()
            print(f"Total workflows: {len(ids)}")
            ```
        """
        workflow_ids = [
            f.stem  # filename without .json extension
            for f in self.storage_dir.glob("*.json")
        ]
        return workflow_ids

    # ========================================================================
    # Delete Operations
    # ========================================================================

    async def delete_workflow(self, workflow_id: str) -> None:
        """
        Delete a workflow from storage with file locking.

        Security Features:
            - File locking to prevent race conditions (Issue #1)
            - Workflow ID validation (Issue #2)
            - Sanitized error messages (Issue #7)

        Args:
            workflow_id: Workflow identifier

        Raises:
            FileNotFoundError: If workflow doesn't exist
            ValueError: If workflow_id format is invalid
            RuntimeError: If file lock cannot be acquired or deletion fails

        Example:
            ```python
            await storage.delete_workflow("wf_123abc456def")
            print("Workflow deleted")
            ```
        """
        # Validate workflow_id format (Issue #2)
        self._validate_workflow_id(workflow_id)

        file_path = self._get_workflow_path(workflow_id)
        lock_path = self._get_lock_path(workflow_id)

        if not file_path.exists():
            logger.warning(f"Cannot delete non-existent workflow: {workflow_id}")
            raise FileNotFoundError(f"Workflow {workflow_id} does not exist")

        logger.info(f"Deleting workflow {workflow_id}")

        # Use file lock to prevent race conditions (Issue #1)
        lock = FileLock(lock_path, timeout=FILE_LOCK_TIMEOUT)

        try:
            with lock:
                logger.debug(f"Acquired lock for workflow {workflow_id}")

                try:
                    file_path.unlink()
                    logger.info(f"Successfully deleted workflow {workflow_id}")

                    # Clean up lock file
                    if lock_path.exists():
                        lock_path.unlink()

                except OSError as e:
                    # Sanitized error message (Issue #7)
                    logger.error(f"Failed to delete workflow file {workflow_id}: {e}")
                    raise RuntimeError("Failed to delete workflow") from e

        except FileLockTimeout:
            # Sanitized error message (Issue #7)
            logger.error(f"Lock timeout for workflow {workflow_id}")
            raise RuntimeError(
                f"Could not acquire file lock for workflow. Please try again."
            ) from None

    # ========================================================================
    # Utility Operations
    # ========================================================================

    async def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics.

        Returns:
            Dictionary with storage stats

        Example:
            ```python
            stats = await storage.get_storage_stats()
            print(f"Total workflows: {stats['total_workflows']}")
            print(f"Storage size: {stats['total_size_mb']} MB")
            ```
        """
        workflow_files = list(self.storage_dir.glob("*.json"))

        total_size = sum(f.stat().st_size for f in workflow_files)

        return {
            "total_workflows": len(workflow_files),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "storage_dir": str(self.storage_dir),
        }


# ============================================================================
# Singleton Instance
# ============================================================================

_workflow_storage: Optional[WorkflowStorage] = None


def get_workflow_storage(storage_dir: Optional[Path] = None) -> WorkflowStorage:
    """
    Get the global WorkflowStorage instance (singleton pattern).

    Args:
        storage_dir: Optional custom storage directory (only used on first call)

    Returns:
        WorkflowStorage instance

    Example:
        ```python
        storage = get_workflow_storage()
        await storage.save_workflow(...)
        ```
    """
    global _workflow_storage

    if _workflow_storage is None:
        _workflow_storage = WorkflowStorage(storage_dir=storage_dir)

    return _workflow_storage
