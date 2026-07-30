from enum import Enum


class GoalState(Enum):
    """
    Defines the lifecycle states of an Atrivon goal.
    """

    PLANNED = "planned"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    REQUIRES_INPUT = "requires_input"
    NEEDS_REVISION = "needs_revision"