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
from atrivon.execution.replanning import (
    AdaptiveReplanner,
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
    - Dependency-aware execution readiness
    - Adaptive replanning

    The Kernel orchestrates the system but does not own
    the specialized logic of these components.
    """

    def __init__(self):
        self.planner = Planner()

        self.reasoner = Reasoner()

        self.executor = Executor()

        self.progress_tracker = (
            ProgressTracker()
        )

        self.adaptive_replanner = (
            AdaptiveReplanner(
                planner=self.planner,
                reasoner=self.reasoner,
            )
        )

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

        print(
            "Atrivon Kernel initialized."
        )

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

    def _get_dependency_readiness(
        self,
    ) -> dict[str, Any]:
        """
        Inspect the current Plan's dependency readiness.

        Returns information about:
        - Dependency validity
        - Ready tasks
        - Dependency-blocked tasks
        - Tasks that can execute
        - Whether execution can continue
        """

        if self.current_plan is None:
            return {
                "valid": False,
                "errors": [
                    "No active Plan is available."
                ],
                "ready_tasks": [],
                "blocked_tasks": [],
                "can_continue": False,
            }

        resolver = (
            self.executor.dependency_resolver
        )

        validation = (
            resolver.validate_plan(
                self.current_plan
            )
        )

        if not validation.valid:
            return {
                "valid": False,
                "errors": list(
                    validation.errors
                ),
                "ready_tasks": [],
                "blocked_tasks": [],
                "can_continue": False,
            }

        ready_tasks = (
            resolver.get_ready_tasks(
                self.current_plan
            )
        )

        blocked_tasks = (
            resolver.get_blocked_tasks(
                self.current_plan
            )
        )

        executable_ready_tasks = [
            task
            for task in ready_tasks
            if task.state
            in {
                TaskState.PENDING,
                TaskState.IN_PROGRESS,
                TaskState.PAUSED,
            }
        ]

        return {
            "valid": True,
            "errors": [],
            "ready_tasks": [
                task.title
                for task
                in executable_ready_tasks
            ],
            "blocked_tasks": [
                {
                    "task": task.title,
                    "unsatisfied_dependencies": (
                        resolver.get_unsatisfied_dependencies(
                            task,
                            self.current_plan,
                        )
                    ),
                }
                for task
                in blocked_tasks
            ],
            "can_continue": bool(
                executable_ready_tasks
            ),
        }

    def _attempt_adaptive_replan(
        self,
        execution_result: dict[str, Any],
    ) -> dict[str, Any] | None:
        """
        Analyze an execution problem and, when appropriate,
        replace the active Plan with a revised strategy.

        Returns:
            Structured replanning information if a new Plan
            was created, otherwise None.
        """

        if self.current_goal is None:
            return None

        if self.current_plan is None:
            return None

        can_replan = (
            self.adaptive_replanner.can_replan(
                goal=self.current_goal,
                current_plan=self.current_plan,
                execution_result=execution_result,
            )
        )

        if not can_replan:
            return None

        print(
            "\nAdaptive replanning triggered."
        )

        adaptive_result = (
            self.adaptive_replanner.replan(
                goal=self.current_goal,
                current_plan=self.current_plan,
                execution_result=execution_result,
            )
        )

        previous_plan_id = (
            self.current_plan.id
        )

        self.current_plan = (
            adaptive_result.revised_plan
        )

        self.current_goal.update_state(
            GoalState.IN_PROGRESS
        )

        self.current_progress = (
            self.progress_tracker.calculate_progress(
                self.current_plan
            )
        )

        self.current_execution_result = {
            "status": "replanned",
            "previous_execution": (
                execution_result
            ),
            "replanning": {
                "previous_plan_id": (
                    previous_plan_id
                ),
                "new_plan_id": (
                    adaptive_result.revision
                    .new_plan_id
                ),
                "previous_version": (
                    adaptive_result.revision
                    .previous_version
                ),
                "new_version": (
                    adaptive_result.revision
                    .new_version
                ),
                "reason": (
                    adaptive_result.revision
                    .reason
                ),
                "analysis": (
                    adaptive_result.analysis
                ),
            },
        }

        self._persist_current_goal()

        print(
            "\nAdaptive replanning completed."
        )

        print(
            f"Previous Plan: "
            f"{previous_plan_id}"
        )

        print(
            f"New Plan: "
            f"{self.current_plan.id}"
        )

        print(
            f"New Plan Version: "
            f"{self.current_plan.version}"
        )

        print(
            "New Plan State: "
            f"{self.current_plan.state.value}"
        )

        print(
            f"Goal State: "
            f"{self.current_goal.state.value}"
        )

        return {
            "analysis": (
                adaptive_result.analysis
            ),
            "revision": {
                "previous_plan_id": (
                    adaptive_result.revision
                    .previous_plan_id
                ),
                "new_plan_id": (
                    adaptive_result.revision
                    .new_plan_id
                ),
                "previous_version": (
                    adaptive_result.revision
                    .previous_version
                ),
                "new_version": (
                    adaptive_result.revision
                    .new_version
                ),
                "reason": (
                    adaptive_result.revision
                    .reason
                ),
            },
        }

    def process_goal(
        self,
        objective: str,
    ) -> dict[str, Any] | None:
        """
        Process a new user objective through Atrivon's core lifecycle.
        """

        objective = objective.strip()

        if not objective:
            print(
                "\nA goal is required."
            )

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

        return self._execute_current_goal()

    def _execute_current_goal(
        self,
    ) -> dict[str, Any]:
        """
        Execute or continue execution of the active Goal's Plan.

        When execution fails or becomes blocked:

        1. The result is analyzed.
        2. Adaptive replanning may be triggered.
        3. The previous Plan is superseded.
        4. The revised Plan becomes active.
        5. The Goal remains IN_PROGRESS.
        6. The revised Plan is persisted.
        7. Execution can continue through continue_goal().
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
                GoalState.BLOCKED,
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

        readiness = (
            self._get_dependency_readiness()
        )

        if not readiness["valid"]:
            raise ValueError(
                "Dependency validation failed: "
                + " | ".join(
                    readiness["errors"]
                )
            )

        if (
            not readiness["can_continue"]
            and readiness["blocked_tasks"]
        ):
            print(
                "\nNo executable tasks are currently ready."
            )

            print(
                "The Goal may require adaptive replanning."
            )

        print(
            "\nBeginning execution..."
        )

        execution_result = (
            self.executor.execute_plan(
                self.current_plan
            )
        )

        adaptive_replanning = (
            self._attempt_adaptive_replan(
                execution_result
            )
        )

        if adaptive_replanning is not None:
            print(
                "\nRevised strategy is now active."
            )

            print(
                "Use continue_goal() to execute "
                "the revised Plan."
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
                "adaptive_replanning": (
                    adaptive_replanning
                ),
                "dependency_readiness": (
                    self._get_dependency_readiness()
                ),
            }

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

        elif execution_status == (
            PlanState.BLOCKED.value
        ):
            self.current_goal.update_state(
                GoalState.BLOCKED
            )

        elif execution_status == "failed":
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
            "dependency_readiness": (
                self._get_dependency_readiness()
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

        IN_PROGRESS Goals are restored as active.

        BLOCKED Goals are restored as BLOCKED and are not
        falsely marked active. Dependency readiness is inspected.

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

        elif (
            self.current_goal.state
            == GoalState.BLOCKED
        ):
            print(
                "\nGoal restored in BLOCKED state."
            )

        else:
            print(
                "\nGoal restored but not automatically resumed."
            )

            print(
                f"Current Goal state: "
                f"{self.current_goal.state.value}"
            )

        readiness = (
            self._get_dependency_readiness()
        )

        print(
            "\nDependency readiness:"
        )

        print(
            f"Ready tasks: "
            f"{readiness['ready_tasks']}"
        )

        print(
            f"Blocked tasks: "
            f"{readiness['blocked_tasks']}"
        )

        print(
            f"Can continue: "
            f"{readiness['can_continue']}"
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

        IN_PROGRESS Goals continue normally.

        BLOCKED Goals are re-evaluated through the dependency
        system and may trigger adaptive replanning.

        Completed tasks are skipped.
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
            not in {
                GoalState.IN_PROGRESS,
                GoalState.BLOCKED,
            }
        ):
            raise ValueError(
                "Goal cannot continue execution from its current state: "
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

    def get_current_dependency_readiness(
        self,
    ) -> dict[str, Any]:
        """
        Return the dependency readiness of the active Plan.
        """

        return self._get_dependency_readiness()

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