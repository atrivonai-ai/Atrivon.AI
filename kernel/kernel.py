from typing import Any

from atrivon.domain.models import Goal
from atrivon.domain.states import GoalState

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

    The Kernel orchestrates the system but does not own
    the specialized logic of these components.
    """

    def __init__(self):
        self.planner = Planner()
        self.reasoner = Reasoner()
        self.executor = Executor()
        self.progress_tracker = ProgressTracker()

        self.current_goal: Goal | None = None
        self.current_plan = None
        self.current_execution_result: dict[str, Any] | None = None
        self.current_progress: dict[str, Any] | None = None

        print("Atrivon Kernel initialized.")

    def process_goal(
        self,
        objective: str,
    ) -> dict[str, Any] | None:
        """
        Process a user objective through Atrivon's core lifecycle.

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

        # Create the canonical Plan.
        plan = self.planner.create_plan(
            self.current_goal
        )

        self.current_plan = plan

        # Link the Plan to the Goal.
        self.current_goal.add_plan(
            plan
        )

        print(
            "\nPlan received by the Kernel."
        )

        # Evaluate the Plan.
        plan_approved = (
            self.reasoner.evaluate_plan(
                plan
            )
        )

        if not plan_approved:
            self.current_goal.update_state(
                GoalState.NEEDS_REVISION
            )

            print(
                f"Goal state: "
                f"{self.current_goal.state.value}"
            )

            print(
                "Execution blocked: "
                "the plan needs revision."
            )

            return {
                "goal_id": self.current_goal.id,
                "plan_id": plan.id,
                "status": "needs_revision",
            }

        # Plan approved.
        self.current_goal.update_state(
            GoalState.APPROVED
        )

        print(
            f"Goal state: "
            f"{self.current_goal.state.value}"
        )

        print(
            "Plan approved."
        )

        # Begin execution.
        self.current_goal.update_state(
            GoalState.IN_PROGRESS
        )

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

        # Calculate progress directly from
        # the canonical Plan and its Task states.
        self.current_progress = (
            self.progress_tracker.calculate_progress(
                plan
            )
        )

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

            print(
                f"\nGoal state: "
                f"{self.current_goal.state.value}"
            )

            print(
                "Execution could not be completed."
            )

        return {
            "goal": self.current_goal.to_dict(),
            "plan": self.current_plan.to_dict(),
            "execution_result": (
                self.current_execution_result
            ),
            "progress": (
                self.current_progress
            ),
        }

    def get_current_goal(
        self,
    ) -> Goal | None:
        """
        Return the current canonical Goal object.
        """

        return self.current_goal

    def get_current_plan(self):
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