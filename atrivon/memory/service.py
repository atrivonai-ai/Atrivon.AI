from typing import Any

from atrivon.domain.memory import MemoryRecord
from atrivon.domain.models import Goal, Plan
from atrivon.memory.repository import MemoryRepository


class MemoryService:
    """
    Intelligence-facing service for Atrivon's persistent memory.

    The MemoryService coordinates memory operations without
    exposing storage implementation details to the rest of Atrivon.

    The underlying repository may use JSON, SQLite, PostgreSQL,
    or another persistence technology.
    """

    GOAL_SNAPSHOT_TYPE = "goal_snapshot"

    def __init__(
        self,
        repository: MemoryRepository,
    ):
        if not isinstance(
            repository,
            MemoryRepository,
        ):
            raise TypeError(
                "MemoryService requires a "
                "MemoryRepository implementation."
            )

        self.repository = repository

    def remember(
        self,
        memory_type: str,
        content: dict[str, Any],
        owner_id: str | None = None,
        source_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> MemoryRecord:
        """
        Create and persist a new memory record.
        """

        record = MemoryRecord(
            memory_type=memory_type,
            content=content,
            owner_id=owner_id,
            source_id=source_id,
            metadata=metadata or {},
        )

        return self.repository.save(
            record
        )

    def save(
        self,
        record: MemoryRecord,
    ) -> MemoryRecord:
        """
        Save or update an existing MemoryRecord.
        """

        return self.repository.save(
            record
        )

    def save_goal_snapshot(
        self,
        goal: Goal,
        plan: Plan | None = None,
        execution_result: dict[str, Any] | None = None,
        progress: dict[str, Any] | None = None,
        owner_id: str | None = None,
    ) -> MemoryRecord:
        """
        Save or update the current persistent snapshot
        of an Atrivon Goal.

        The snapshot is identified by:
        - memory type: goal_snapshot
        - source ID: Goal ID

        If the snapshot already exists, its complete current
        representation is updated in one operation.
        """

        if not isinstance(
            goal,
            Goal,
        ):
            raise TypeError(
                "save_goal_snapshot() requires a Goal object."
            )

        if plan is not None and not isinstance(
            plan,
            Plan,
        ):
            raise TypeError(
                "save_goal_snapshot() requires a Plan object "
                "when a plan is provided."
            )

        existing_snapshot = (
            self.get_goal_snapshot(
                goal.id
            )
        )

        content = {
            "goal": goal.to_dict(),
            "plan": (
                plan.to_dict()
                if plan is not None
                else None
            ),
            "execution_result": execution_result,
            "progress": progress,
            "current_state": goal.state.value,
        }

        if existing_snapshot is not None:
            existing_snapshot.update_content(
                content
            )

            if owner_id is not None:
                existing_snapshot.owner_id = owner_id

            return self.repository.save(
                existing_snapshot
            )

        return self.remember(
            memory_type=self.GOAL_SNAPSHOT_TYPE,
            content=content,
            owner_id=owner_id,
            source_id=goal.id,
            metadata={
                "goal_object_type": "Goal",
                "snapshot_version": 1,
            },
        )

    def save_goal_state(
        self,
        goal: Goal,
        owner_id: str | None = None,
    ) -> MemoryRecord:
        """
        Update only the current Goal state in persistent memory.

        Existing plan, execution result, progress, and other
        snapshot information are preserved.

        If no snapshot exists yet, a new snapshot is created
        containing the Goal state.
        """

        if not isinstance(
            goal,
            Goal,
        ):
            raise TypeError(
                "save_goal_state() requires a Goal object."
            )

        existing_snapshot = (
            self.get_goal_snapshot(
                goal.id
            )
        )

        if existing_snapshot is None:
            return self.save_goal_snapshot(
                goal=goal,
                plan=None,
                execution_result=None,
                progress=None,
                owner_id=owner_id,
            )

        content = dict(
            existing_snapshot.content
        )

        content["goal"] = (
            goal.to_dict()
        )

        content["current_state"] = (
            goal.state.value
        )

        existing_snapshot.update_content(
            content
        )

        if owner_id is not None:
            existing_snapshot.owner_id = owner_id

        return self.repository.save(
            existing_snapshot
        )

    def get_goal_snapshot(
        self,
        goal_id: str,
    ) -> MemoryRecord | None:
        """
        Retrieve the latest persistent snapshot for a Goal.
        """

        records = self.repository.list_records(
            memory_type=self.GOAL_SNAPSHOT_TYPE,
            source_id=goal_id,
        )

        if not records:
            return None

        return max(
            records,
            key=lambda record: record.updated_at,
        )

    def get(
        self,
        record_id: str,
    ) -> MemoryRecord | None:
        """
        Retrieve a memory record by ID.
        """

        return self.repository.get(
            record_id
        )

    def list_records(
        self,
        memory_type: str | None = None,
        owner_id: str | None = None,
        source_id: str | None = None,
    ) -> list[MemoryRecord]:
        """
        Retrieve memory records using optional filters.
        """

        return self.repository.list_records(
            memory_type=memory_type,
            owner_id=owner_id,
            source_id=source_id,
        )

    def delete(
        self,
        record_id: str,
    ) -> bool:
        """
        Delete a memory record by ID.
        """

        return self.repository.delete(
            record_id
        )