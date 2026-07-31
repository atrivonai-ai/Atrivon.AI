from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from atrivon.domain.models import generate_id


def utc_now() -> datetime:
    """
    Return the current UTC timestamp.
    """

    return datetime.now(
        timezone.utc
    )


class ActionStatus(str, Enum):
    """
    Canonical lifecycle states for an Atrivon action.
    """

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    BLOCKED = "blocked"
    REQUIRES_INPUT = "requires_input"


@dataclass
class ActionRequest:
    """
    Canonical request for a real-world action.

    An ActionRequest describes WHAT Atrivon wants performed.

    It does not define HOW the action is performed.

    That responsibility belongs to a Capability.
    """

    action_type: str

    target: str

    parameters: dict[str, Any] = field(
        default_factory=dict
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    id: str = field(
        default_factory=generate_id
    )

    created_at: datetime = field(
        default_factory=utc_now
    )

    def __post_init__(self):
        if not self.action_type.strip():
            raise ValueError(
                "Action type cannot be empty."
            )

        if not self.target.strip():
            raise ValueError(
                "Action target cannot be empty."
            )

        if not isinstance(
            self.parameters,
            dict,
        ):
            raise TypeError(
                "Action parameters must be a dictionary."
            )

        if not isinstance(
            self.metadata,
            dict,
        ):
            raise TypeError(
                "Action metadata must be a dictionary."
            )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        """
        Convert the ActionRequest into a
        serialization-friendly dictionary.
        """

        return {
            "id": self.id,
            "action_type": self.action_type,
            "target": self.target,
            "parameters": self.parameters,
            "metadata": self.metadata,
            "created_at": (
                self.created_at.isoformat()
            ),
        }


@dataclass
class ActionResult:
    """
    Canonical result produced after attempting an action.

    An ActionResult describes WHAT happened.

    It allows Atrivon to:
    - Observe success
    - Observe failure
    - Detect blocking conditions
    - Request additional input
    - Record execution output
    """

    action_id: str

    status: ActionStatus

    output: Any = None

    error: str | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    started_at: datetime = field(
        default_factory=utc_now
    )

    completed_at: datetime | None = None

    def __post_init__(self):
        if not isinstance(
            self.status,
            ActionStatus,
        ):
            self.status = ActionStatus(
                self.status
            )

        if not self.action_id.strip():
            raise ValueError(
                "Action ID cannot be empty."
            )

        if not isinstance(
            self.metadata,
            dict,
        ):
            raise TypeError(
                "Action result metadata must be a dictionary."
            )

    def mark_completed(
        self,
        status: ActionStatus,
        output: Any = None,
        error: str | None = None,
    ) -> None:
        """
        Mark the action as completed with its final result.
        """

        if not isinstance(
            status,
            ActionStatus,
        ):
            status = ActionStatus(
                status
            )

        self.status = status

        self.output = output

        self.error = error

        self.completed_at = utc_now()

    def to_dict(
        self,
    ) -> dict[str, Any]:
        """
        Convert the ActionResult into a
        serialization-friendly dictionary.
        """

        return {
            "action_id": self.action_id,
            "status": self.status.value,
            "output": self.output,
            "error": self.error,
            "metadata": self.metadata,
            "started_at": (
                self.started_at.isoformat()
            ),
            "completed_at": (
                self.completed_at.isoformat()
                if self.completed_at is not None
                else None
            ),
        }