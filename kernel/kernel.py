from pathlib import Path
from typing import Any

from atrivon.domain.memory import GoalSnapshot
from atrivon.domain.models import Goal
from atrivon.domain.states import (
    GoalState,
    PlanState,
    SubgoalState,
    TaskState,
)
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
    - Goal restoration
    - Goal pausing
    - Goal resumption
    - Continued execution

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

    def _restore_snapshot(
        self,
        snapshot: GoalSnapshot,
    ) -> None:
        """
        Restore a GoalSnapshot into the Kernel's active context.
        """

        self.current_goal = snapshot.goal

        self.current_plan = snapshot.plan

        self.current_execution_result = (
            snapshot.execution_result
        )

        self.current_progress = (
            snapshot.progress
        )

    def process_goal(
        self,
        objective: str,
    ) -> dict[str, Any] | None:
        """
        Process a new user objective through Atrivon's core lifecycle.
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

        return self._execute_current_goal()

    def _execute_current_goal(
        self,
    ) -> dict[str, Any]:
        """
        Execute or continue execution of the active Goal's Plan.

        The Executor is resume-aware and will skip completed
        tasks while continuing unfinished work.
        """

        if self.current_goal is None:
            raise ValueError(
                "No active Goal is available for execution."
            )

        if self.current_plan is None:
            raise ValueError(
                "No active Plan is available for execution."
            )

        if (
            self.current_goal.state
            not in {
                GoalState.IN_PROGRESS,
                GoalState.PAUSED,
            }
        ):
            raise ValueError(
                "Goal cannot be executed from its current state: "
                f"{self.current_goal.state.value}"
            )

        if (
            self.current_goal.state
            == GoalState.PAUSED
        ):
            self.current_goal.update_state(
                GoalState.IN_PROGRESS
            )

        if (
            self.current_plan.state
            == PlanState.PAUSED
        ):
            self.current_plan.update_state(
                PlanState.ACTIVE
            )

        self._persist_current_goal()

        print(
            "\nBeginning execution..."
        )

        execution_result = (
            self.executor.execute_plan(
                self.current_plan
            )
        )

        self.current_execution_result = (
            execution_result
        )

        self.current_progress = (
            self.progress_tracker.calculate_progress(
                self.current_plan
            )
        )

        execution_status = (
            execution_result.get(
                "status"
            )
        )

        if execution_status == (
            PlanState.COMPLETED.value
        ):
            self.current_goal.update_state(
                GoalState.COMPLETED
            )

        elif execution_status == "requires_input":
            self.current_goal.update_state(
                GoalState.REQUIRES_INPUT
            )

        elif execution_status == "needs_revision":
            self.current_goal.update_state(
                GoalState.NEEDS_REVISION
            )

        elif execution_status == "blocked":
            self.current_goal.update_state(
                GoalState.BLOCKED
            )

        else:
            self.current_goal.update_state(
                GoalState.IN_PROGRESS
            )

        self._persist_current_goal()

        self.progress_tracker.display_progress(
            self.current_progress
        )

        print(
            f"\nGoal state: "
            f"{self.current_goal.state.value}"
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

    def pause_goal(
        self,
    ) -> GoalSnapshot:
        """
        Pause the currently active Goal.

        Only an IN_PROGRESS Goal can be paused.

        Active Plan, Subgoals, and Tasks are moved to PAUSED.
        Pending and completed Tasks retain their existing states.
        """

        if self.current_goal is None:
            raise ValueError(
                "No active Goal is available to pause."
            )

        if (
            self.current_goal.state
            != GoalState.IN_PROGRESS
        ):
            raise ValueError(
                "Only an IN_PROGRESS Goal can be paused. "
                f"Current state: "
                f"{self.current_goal.state.value}"
            )

        self.current_goal.update_state(
            GoalState.PAUSED
        )

        if self.current_plan is not None:
            if (
                self.current_plan.state
                == PlanState.ACTIVE
            ):
                self.current_plan.update_state(
                    PlanState.PAUSED
                )

            for subgoal in (
                self.current_plan.subgoals
            ):
                if (
                    subgoal.state
                    == SubgoalState.IN_PROGRESS
                ):
                    subgoal.update_state(
                        SubgoalState.PAUSED
                    )

                for task in subgoal.tasks:
                    if (
                        task.state
                        == TaskState.IN_PROGRESS
                    ):
                        task.update_state(
                            TaskState.PAUSED
                        )

        self._persist_current_goal()

        snapshot_record = (
            self.memory.get_goal_snapshot(
                self.current_goal.id
            )
        )

        if snapshot_record is None:
            raise RuntimeError(
                "Paused Goal could not be reloaded "
                "from persistent memory."
            )

        print(
            "\nGoal paused successfully."
        )

        print(
            f"Goal state: "
            f"{self.current_goal.state.value}"
        )

        return GoalSnapshot.from_memory_record(
            snapshot_record
        )

    def resume_goal(
        self,
        goal_id: str,
    ) -> GoalSnapshot:
        """
        Restore and resume a persisted Goal.

        PAUSED Goals transition back to IN_PROGRESS.

        BLOCKED, REQUIRES_INPUT, and NEEDS_REVISION Goals
        are restored but are not automatically resumed.

        COMPLETED Goals cannot be resumed.
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
            raise ValueError(
                f"No persisted Goal found "
                f"for Goal ID: {goal_id}"
            )

        snapshot = (
            GoalSnapshot.from_memory_record(
                memory_record
            )
        )

        if (
            snapshot.goal.state
            == GoalState.COMPLETED
        ):
            raise ValueError(
                "Completed Goals cannot be resumed. "
                "A completed Goal is a finished outcome."
            )

        self._restore_snapshot(
            snapshot
        )

        if (
            self.current_goal.state
            == GoalState.PAUSED
        ):
            self.current_goal.update_state(
                GoalState.IN_PROGRESS
            )

            if (
                self.current_plan is not None
                and self.current_plan.state
                == PlanState.PAUSED
            ):
                self.current_plan.update_state(
                    PlanState.ACTIVE
                )

            if self.current_plan is not None:
                for subgoal in (
                    self.current_plan.subgoals
                ):
                    if (
                        subgoal.state
                        == SubgoalState.PAUSED
                    ):
                        subgoal.update_state(
                            SubgoalState.IN_PROGRESS
                        )

                    for task in subgoal.tasks:
                        if (
                            task.state
                            == TaskState.PAUSED
                        ):
                            task.update_state(
                                TaskState.IN_PROGRESS
                            )

            self._persist_current_goal()

            print(
                "\nGoal resumed successfully."
            )

        elif (
            self.current_goal.state
            == GoalState.IN_PROGRESS
        ):
            print(
                "\nGoal restored and already "
                "marked as in progress."
            )

        else:
            print(
                "\nGoal restored but not automatically resumed."
            )

            print(
                f"Current Goal state: "
                f"{self.current_goal.state.value}"
            )

        return GoalSnapshot(
            goal=self.current_goal,
            plan=self.current_plan,
            execution_result=(
                self.current_execution_result
            ),
            progress=self.current_progress,
        )

    def continue_goal(
        self,
    ) -> dict[str, Any]:
        """
        Continue execution of the currently active Goal.

        The Goal must be IN_PROGRESS.

        Completed tasks are skipped.
        Unfinished executable tasks continue.
        """

        if self.current_goal is None:
            raise ValueError(
                "No active Goal is available to continue."
            )

        if self.current_plan is None:
            raise ValueError(
                "No active Plan is available to continue."
            )

        if (
            self.current_goal.state
            != GoalState.IN_PROGRESS
        ):
            raise ValueError(
                "Only an IN_PROGRESS Goal can continue execution. "
                f"Current state: "
                f"{self.current_goal.state.value}"
            )

        return self._execute_current_goal()

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