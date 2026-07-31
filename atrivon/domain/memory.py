from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from atrivon.domain.models import (
    Goal,
    Plan,
    generate_id,
)


def utc_now() -> datetime:
    """
    Return the current UTC timestamp.
    """

    return datetime.now(timezone.utc)


@dataclass
class MemoryRecord:
    """
    Canonical Atrivon memory record.
    """

    memory_type: str
    content: dict[str, Any]

    id: str = field(
        default_factory=generate_id
    )

    owner_id: str | None = None

    source_id: str | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    created_at: datetime = field(
        default_factory=utc_now
    )

    updated_at: datetime = field(
        default_factory=utc_now
    )

    def __post_init__(self):
        if not self.memory_type.strip():
            raise ValueError(
                "Memory type cannot be empty."
            )

        if not isinstance(
            self.content,
            dict,
        ):
            raise TypeError(
                "Memory content must be a dictionary."
            )

    def update_content(
        self,
        content: dict[str, Any],
    ) -> None:
        """
        Replace the memory content and update the timestamp.
        """

        if not isinstance(
            content,
            dict,
        ):
            raise TypeError(
                "Memory content must be a dictionary."
            )

        self.content = content
        self.updated_at = utc_now()

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the memory record into a
        serialization-friendly dictionary.
        """

        return {
            "id": self.id,
            "memory_type": self.memory_type,
            "content": self.content,
            "owner_id": self.owner_id,
            "source_id": self.source_id,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class GoalSnapshot:
    """
    Rehydrated persistent context for an Atrivon Goal.

    A GoalSnapshot reconstructs the canonical Goal and Plan
    objects required to restore active working context.
    """

    goal: Goal

    plan: Plan | None = None

    execution_result: dict[str, Any] | None = None

    progress: dict[str, Any] | None = None

    @classmethod
    def from_memory_record(
        cls,
        record: MemoryRecord,
    ) -> "GoalSnapshot":
        """
        Reconstruct a GoalSnapshot from a persistent
        goal_snapshot MemoryRecord.
        """

        if record.memory_type != "goal_snapshot":
            raise ValueError(
                "MemoryRecord is not a goal_snapshot."
            )

        content = record.content

        goal_data = content.get(
            "goal"
        )

        if not isinstance(
            goal_data,
            dict,
        ):
            raise ValueError(
                "Goal snapshot is missing valid Goal data."
            )

        goal = Goal.from_dict(
            goal_data
        )

        plan_data = content.get(
            "plan"
        )

        plan = None

        if plan_data is not None:
            if not isinstance(
                plan_data,
                dict,
            ):
                raise ValueError(
                    "Goal snapshot contains invalid Plan data."
                )

            plan = Plan.from_dict(
                plan_data
            )

            if plan.goal_id != goal.id:
                raise ValueError(
                    "Persisted Plan does not belong "
                    "to the persisted Goal."
                )

        return cls(
            goal=goal,
            plan=plan,
            execution_result=content.get(
                "execution_result"
            ),
            progress=content.get(
                "progress"
            ),
        )