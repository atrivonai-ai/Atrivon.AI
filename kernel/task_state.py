from enum import Enum


class TaskState(Enum):
    """
    Defines the lifecycle states of an Atrivon task.
    """

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"
    REQUIRES_INPUT = "requires_input"
    NEEDS_REVISION = "needs_revision"