from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from atrivon.domain.states import (
    GoalState,
    PlanState,
    SubgoalState,
    TaskState,
)


def utc_now() -> datetime:
    """
    Return the current UTC timestamp.
    """

    return datetime.now(timezone.utc)


def generate_id() -> str:
    """
    Generate a unique domain object identifier.
    """

    return str(uuid4())


@dataclass
class Task:
    """
    Canonical Atrivon task domain model.

    A Task represents one unit of work required to advance
    a Subgoal.
    """

    title: str
    description: str = ""
    id: str = field(default_factory=generate_id)
    state: TaskState = TaskState.PENDING
    dependencies: list[str] = field(default_factory=list)
    result: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def __post_init__(self):
        if not self.title.strip():
            raise ValueError(
                "Task title cannot be empty."
            )

        if not isinstance(
            self.state,
            TaskState,
        ):
            self.state = TaskState(
                self.state
            )

    def update_state(
        self,
        state: TaskState,
    ) -> None:
        """
        Update the task lifecycle state.
        """

        if not isinstance(
            state,
            TaskState,
        ):
            state = TaskState(state)

        self.state = state
        self.updated_at = utc_now()

    def set_result(
        self,
        result: Any,
    ) -> None:
        """
        Store the result of task execution.
        """

        self.result = result
        self.updated_at = utc_now()

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the task into a serialization-friendly dictionary.
        """

        data = asdict(self)

        data["state"] = self.state.value
        data["created_at"] = (
            self.created_at.isoformat()
        )
        data["updated_at"] = (
            self.updated_at.isoformat()
        )

        return data


@dataclass
class Subgoal:
    """
    Canonical Atrivon subgoal domain model.

    A Subgoal represents a meaningful objective that contributes
    to the completion of a larger Plan.
    """

    name: str
    description: str = ""
    id: str = field(default_factory=generate_id)
    state: SubgoalState = SubgoalState.PENDING
    tasks: list[Task] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def __post_init__(self):
        if not self.name.strip():
            raise ValueError(
                "Subgoal name cannot be empty."
            )

        if not isinstance(
            self.state,
            SubgoalState,
        ):
            self.state = SubgoalState(
                self.state
            )

    def add_task(
        self,
        task: Task,
    ) -> None:
        """
        Add a Task to the Subgoal.
        """

        if not isinstance(
            task,
            Task,
        ):
            raise TypeError(
                "Subgoal tasks must be Task objects."
            )

        self.tasks.append(task)
        self.updated_at = utc_now()

    def update_state(
        self,
        state: SubgoalState,
    ) -> None:
        """
        Update the subgoal lifecycle state.
        """

        if not isinstance(
            state,
            SubgoalState,
        ):
            state = SubgoalState(state)

        self.state = state
        self.updated_at = utc_now()

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the subgoal and its tasks into a
        serialization-friendly dictionary.
        """

        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "state": self.state.value,
            "dependencies": self.dependencies,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "tasks": [
                task.to_dict()
                for task in self.tasks
            ],
        }


@dataclass
class Plan:
    """
    Canonical Atrivon plan domain model.

    A Plan represents a strategy for achieving a Goal.

    Plans are versioned so Atrivon can revise a strategy
    without destroying the history of previous plans.
    """

    goal_id: str
    version: int = 1
    id: str = field(default_factory=generate_id)
    state: PlanState = PlanState.DRAFT
    subgoals: list[Subgoal] = field(default_factory=list)
    rationale: str = ""
    dependencies: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def __post_init__(self):
        if not self.goal_id.strip():
            raise ValueError(
                "Plan goal_id cannot be empty."
            )

        if self.version < 1:
            raise ValueError(
                "Plan version must be at least 1."
            )

        if not isinstance(
            self.state,
            PlanState,
        ):
            self.state = PlanState(
                self.state
            )

    def add_subgoal(
        self,
        subgoal: Subgoal,
    ) -> None:
        """
        Add a Subgoal to the Plan.
        """

        if not isinstance(
            subgoal,
            Subgoal,
        ):
            raise TypeError(
                "Plan subgoals must be Subgoal objects."
            )

        self.subgoals.append(subgoal)
        self.updated_at = utc_now()

    def update_state(
        self,
        state: PlanState,
    ) -> None:
        """
        Update the plan lifecycle state.
        """

        if not isinstance(
            state,
            PlanState,
        ):
            state = PlanState(state)

        self.state = state
        self.updated_at = utc_now()

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the plan and its subgoals into a
        serialization-friendly dictionary.
        """

        return {
            "id": self.id,
            "goal_id": self.goal_id,
            "version": self.version,
            "state": self.state.value,
            "rationale": self.rationale,
            "dependencies": self.dependencies,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "subgoals": [
                subgoal.to_dict()
                for subgoal in self.subgoals
            ],
        }


@dataclass
class Goal:
    """
    Canonical Atrivon goal domain model.

    A Goal is the primary unit of work in Atrivon.

    A goal may have multiple plans over its lifetime.
    The active_plan_id identifies the plan currently guiding
    execution.
    """

    objective: str
    context: str = ""
    id: str = field(default_factory=generate_id)
    state: GoalState = GoalState.PLANNED
    plan_ids: list[str] = field(default_factory=list)
    active_plan_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def __post_init__(self):
        if not self.objective.strip():
            raise ValueError(
                "Goal objective cannot be empty."
            )

        if not isinstance(
            self.state,
            GoalState,
        ):
            self.state = GoalState(
                self.state
            )

    def add_plan(
        self,
        plan: Plan,
    ) -> None:
        """
        Associate a Plan with this Goal.
        """

        if not isinstance(
            plan,
            Plan,
        ):
            raise TypeError(
                "Goal plans must be Plan objects."
            )

        if plan.goal_id != self.id:
            raise ValueError(
                "Plan goal_id must match the Goal id."
            )

        if plan.id not in self.plan_ids:
            self.plan_ids.append(
                plan.id
            )

        self.active_plan_id = plan.id
        self.updated_at = utc_now()

    def update_state(
        self,
        state: GoalState,
    ) -> None:
        """
        Update the goal lifecycle state.
        """

        if not isinstance(
            state,
            GoalState,
        ):
            state = GoalState(state)

        self.state = state
        self.updated_at = utc_now()

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the Goal into a serialization-friendly dictionary.
        """

        return {
            "id": self.id,
            "objective": self.objective,
            "context": self.context,
            "state": self.state.value,
            "plan_ids": self.plan_ids,
            "active_plan_id": self.active_plan_id,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }