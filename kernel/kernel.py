from pathlib import Path
from typing import Any

from atrivon.domain.memory import GoalSnapshot
from atrivon.domain.models import Goal
from atrivon.domain.states import GoalState
from atrivon.memory.json_repository import (
    JsonMemoryRepository,
)
from atrivon.memory.service import MemoryService

from kernel.executor import Executor
from kernel.planner import Planner
from kernel.progress import ProgressTracker
from kernel.reasoner import Reasoner


class AtrivonKernel:
    """
    The central coordinator of Atrivon.

    Every user goal enters through the Kernel.

    The Kernel coordinates:
    - Goal creation
    - Planning
    - Reasoning
    - Execution
    - Progress tracking
    - Persistent memory
    - Goal resumption

    The Kernel orchestrates the system but does not own
    the specialized logic of these components.
    """

    def __init__(self):
        self.planner = Planner()
        self.reasoner = Reasoner()
        self.executor = Executor()
        self.progress_tracker = ProgressTracker()

        self.memory_repository = (
            self._create_memory_repository()
        )

        self.memory = MemoryService(
            self.memory_repository
        )

        self.current_goal: Goal | None = None
        self.current_plan = None
        self.current_execution_result: (
            dict[str, Any] | None
        ) = None
        self.current_progress: (
            dict[str, Any] | None
        ) = None

        print("Atrivon Kernel initialized.")

    def _create_memory_repository(
        self,
    ) -> JsonMemoryRepository:
        """
        Create the default persistent memory repository.

        Runtime memory is stored outside the source tree's
        tracked code and is excluded from Git through .gitignore.
        """

        project_root = (
            Path(__file__).resolve().parent.parent
        )

        memory_directory = (
            project_root
            / ".atrivon"
        )

        memory_file = (
            memory_directory
            / "memory.json"
        )

        return JsonMemoryRepository(
            memory_file
        )

    def _persist_current_goal(
        self,
    ) -> None:
        """
        Persist the current canonical Goal snapshot.

        The MemoryService updates the existing Goal snapshot
        instead of creating duplicate records.
        """

        if self.current_goal is None:
            return

        self.memory.save_goal_snapshot(
            goal=self.current_goal,
            plan=self.current_plan,
            execution_result=(
                self.current_execution_result
            ),
            progress=self.current_progress,
        )

    def process_goal(
        self,
        objective: str,
    ) -> dict[str, Any] | None:
        """
        Process a new user objective through Atrivon's core lifecycle.

        Lifecycle:

        PLANNED
            ↓
        APPROVED
            ↓
        IN_PROGRESS
            ↓
        EXECUTION
            ↓
        PROGRESS TRACKING
            ↓
        COMPLETED / BLOCKED

        The current Goal snapshot is persisted throughout
        the lifecycle.
        """

        objective = objective.strip()

        if not objective:
            print("\nA goal is required.")
            return None

        self.current_goal = Goal(
            objective=objective
        )

        self.current_plan = None
        self.current_execution_result = None
        self.current_progress = None

        self._persist_current_goal()

        print(
            f"\nGoal received: "
            f"{self.current_goal.objective}"
        )

        print(
            f"Goal ID: "
            f"{self.current_goal.id}"
        )

        print(
            f"Goal state: "
            f"{self.current_goal.state.value}"
        )

        print(
            "Understanding the goal..."
        )

        plan = self.planner.create_plan(
            self.current_goal
        )

        self.current_plan = plan

        self.current_goal.add_plan(
            plan
        )

        self._persist_current_goal()

        print(
            "\nPlan received by the Kernel."
        )

        plan_approved = (
            self.reasoner.evaluate_plan(
                plan
            )
        )

        if not plan_approved:
            self.current_goal.update_state(
                GoalState.NEEDS_REVISION
            )

            self._persist_current_goal()

            print(
                f"Goal state: "
                f"{self.current_goal.state.value}"
            )

            print(
                "Execution blocked: "
                "the plan needs revision."
            )

            return {
                "goal": (
                    self.current_goal.to_dict()
                ),
                "plan": (
                    self.current_plan.to_dict()
                ),
                "execution_result": None,
                "progress": None,
            }

        self.current_goal.update_state(
            GoalState.APPROVED
        )

        self._persist_current_goal()

        print(
            f"Goal state: "
            f"{self.current_goal.state.value}"
        )

        print(
            "Plan approved."
        )

        self.current_goal.update_state(
            GoalState.IN_PROGRESS
        )

        self._persist_current_goal()

        print(
            f"Goal state: "
            f"{self.current_goal.state.value}"
        )

        print(
            "Beginning execution..."
        )

        execution_result = (
            self.executor.execute_plan(
                plan
            )
        )

        self.current_execution_result = (
            execution_result
        )

        self.current_progress = (
            self.progress_tracker.calculate_progress(
                plan
            )
        )

        self._persist_current_goal()

        self.progress_tracker.display_progress(
            self.current_progress
        )

        execution_status = (
            execution_result.get(
                "status"
            )
        )

        if execution_status == "completed":
            self.current_goal.update_state(
                GoalState.COMPLETED
            )

            self._persist_current_goal()

            print(
                f"\nGoal state: "
                f"{self.current_goal.state.value}"
            )

            print(
                "Goal completed successfully."
            )

        else:
            self.current_goal.update_state(
                GoalState.BLOCKED
            )

            self._persist_current_goal()

            print(
                f"\nGoal state: "
                f"{self.current_goal.state.value}"
            )

            print(
                "Execution could not be completed."
            )

        return {
            "goal": (
                self.current_goal.to_dict()
            ),
            "plan": (
                self.current_plan.to_dict()
            ),
            "execution_result": (
                self.current_execution_result
            ),
            "progress": (
                self.current_progress
            ),
        }

    def resume_goal(
        self,
        goal_id: str,
    ) -> GoalSnapshot | None:
        """
        Restore a persisted Goal into the Kernel's active context.

        The restored context includes:
        - Canonical Goal
        - Canonical Plan
        - Execution result
        - Progress report

        Returns:
            A rehydrated GoalSnapshot if found.
            None if no matching goal exists.
        """

        goal_id = goal_id.strip()

        if not goal_id:
            raise ValueError(
                "Goal ID is required to resume a goal."
            )

        memory_record = (
            self.memory.get_goal_snapshot(
                goal_id
            )
        )

        if memory_record is None:
            print(
                f"\nNo persisted goal found "
                f"for Goal ID: {goal_id}"
            )
            return None

        snapshot = (
            GoalSnapshot.from_memory_record(
                memory_record
            )
        )

        self.current_goal = snapshot.goal
        self.current_plan = snapshot.plan
        self.current_execution_result = (
            snapshot.execution_result
        )
        self.current_progress = (
            snapshot.progress
        )

        print(
            "\nGoal resumed successfully."
        )

        print(
            f"Goal ID: "
            f"{self.current_goal.id}"
        )

        print(
            f"Goal: "
            f"{self.current_goal.objective}"
        )

        print(
            f"Goal state: "
            f"{self.current_goal.state.value}"
        )

        if self.current_plan is not None:
            print(
                f"Plan ID: "
                f"{self.current_plan.id}"
            )

            print(
                f"Plan version: "
                f"{self.current_plan.version}"
            )

            print(
                f"Plan state: "
                f"{self.current_plan.state.value}"
            )

        if self.current_progress is not None:
            print(
                f"Progress: "
                f"{self.current_progress.get('progress', 0.0)}%"
            )

        return snapshot

    def get_current_goal(
        self,
    ) -> Goal | None:
        """
        Return the current canonical Goal object.
        """

        return self.current_goal

    def get_current_plan(
        self,
    ):
        """
        Return the current canonical Plan object.
        """

        return self.current_plan

    def get_current_execution_result(
        self,
    ) -> dict[str, Any] | None:
        """
        Return the latest execution result.
        """

        return self.current_execution_result

    def get_current_progress(
        self,
    ) -> dict[str, Any] | None:
        """
        Return the latest progress report.
        """

        return self.current_progress

    def get_current_state(
        self,
    ) -> str | None:
        """
        Return the current Goal lifecycle state.
        """

        if self.current_goal is None:
            return None

        return self.current_goal.state.value

    def get_persisted_goal(
        self,
        goal_id: str,
    ) -> GoalSnapshot | None:
        """
        Retrieve and rehydrate a persisted Goal snapshot
        without making it the active Kernel context.
        """

        goal_id = goal_id.strip()

        if not goal_id:
            raise ValueError(
                "Goal ID is required."
            )

        memory_record = (
            self.memory.get_goal_snapshot(
                goal_id
            )
        )

        if memory_record is None:
            return None

        return GoalSnapshot.from_memory_record(
            memory_record
        )