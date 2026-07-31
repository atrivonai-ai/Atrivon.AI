from enum import Enum


class GoalState(str, Enum):
    """
    Canonical lifecycle states for an Atrivon goal.
    """

    PLANNED = "planned"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    REQUIRES_INPUT = "requires_input"
    NEEDS_REVISION = "needs_revision"


class PlanState(str, Enum):
    """
    Canonical lifecycle states for an Atrivon plan.
    """

    DRAFT = "draft"
    PROPOSED = "proposed"
    APPROVED = "approved"
    ACTIVE = "active"
    COMPLETED = "completed"
    SUPERSEDED = "superseded"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"


class SubgoalState(str, Enum):
    """
    Canonical lifecycle states for an Atrivon subgoal.
    """

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    REQUIRES_INPUT = "requires_input"
    NEEDS_REVISION = "needs_revision"


class TaskState(str, Enum):
    """
    Canonical lifecycle states for an Atrivon task.
    """

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"
    REQUIRES_INPUT = "requires_input"
    NEEDS_REVISION = "needs_revision"