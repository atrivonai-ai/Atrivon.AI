from typing import Any

from atrivon.domain.models import Plan
from atrivon.domain.states import (
    PlanState,
    SubgoalState,
    TaskState,
)


class Executor:
    """
    The Executor coordinates execution of an approved Atrivon Plan.

    The Executor is resume-aware.

    Completed tasks are never executed again.

    Tasks in these states may continue execution:
    - pending
    - in_progress
    - paused

    Tasks in these states are preserved without automatic execution:
    - completed
    - blocked
    - failed
    - requires_input
    - needs_revision

    The current task execution itself remains a controlled
    execution framework. Real-world actions will be introduced
    through future execution and automation capabilities.
    """

    EXECUTABLE_TASK_STATES = {
        TaskState.PENDING,
        TaskState.IN_PROGRESS,
        TaskState.PAUSED,
    }

    NON_EXECUTABLE_TASK_STATES = {
        TaskState.BLOCKED,
        TaskState.FAILED,
        TaskState.REQUIRES_INPUT,
        TaskState.NEEDS_REVISION,
    }

    def __init__(self):
        print("Executor module loaded.")

    def execute_plan(
        self,
        plan: Plan,
    ) -> dict[str, Any]:
        """
        Execute or continue execution of a canonical Atrivon Plan.

        Completed work is preserved and skipped.

        Returns a structured execution result containing:
        - Plan identity
        - Goal identity
        - Plan version
        - Overall execution status
        - Subgoal results
        - Task results
        - Execution counts
        """

        print("\nStarting plan execution...")

        if not isinstance(
            plan,
            Plan,
        ):
            print(
                "Execution failed: "
                "expected a Plan object."
            )

            return {
                "plan_id": None,
                "goal_id": None,
                "status": "failed",
                "subgoals": [],
                "execution_summary": {
                    "executed_tasks": 0,
                    "skipped_tasks": 0,
                    "total_tasks": 0,
                },
            }

        if not plan.goal_id.strip():
            print(
                "Execution failed: "
                "plan has no goal ID."
            )

            plan.update_state(
                PlanState.REJECTED
            )

            return {
                "plan_id": plan.id,
                "goal_id": plan.goal_id,
                "status": "failed",
                "subgoals": [],
                "execution_summary": {
                    "executed_tasks": 0,
                    "skipped_tasks": 0,
                    "total_tasks": 0,
                },
            }

        if not plan.subgoals:
            print(
                "Execution failed: "
                "plan contains no subgoals."
            )

            plan.update_state(
                PlanState.REJECTED
            )

            return {
                "plan_id": plan.id,
                "goal_id": plan.goal_id,
                "status": "failed",
                "subgoals": [],
                "execution_summary": {
                    "executed_tasks": 0,
                    "skipped_tasks": 0,
                    "total_tasks": 0,
                },
            }

        if (
            plan.state
            == PlanState.COMPLETED
        ):
            raise ValueError(
                "Cannot execute a completed Plan."
            )

        plan.update_state(
            PlanState.ACTIVE
        )

        execution_results = []

        executed_tasks = 0
        skipped_tasks = 0
        total_tasks = 0

        print(
            f"\nExecuting Plan: "
            f"{plan.id}"
        )

        print(
            f"Plan version: "
            f"{plan.version}"
        )

        print(
            f"Goal ID: "
            f"{plan.goal_id}"
        )

        for subgoal_number, subgoal in enumerate(
            plan.subgoals,
            start=1,
        ):
            print(
                f"\nExecuting subgoal "
                f"{subgoal_number}: "
                f"{subgoal.name}"
            )

            subgoal_task_results = []

            for task_number, task in enumerate(
                subgoal.tasks,
                start=1,
            ):
                total_tasks += 1

                task_result = (
                    self._process_task(
                        task=task,
                        task_number=task_number,
                        subgoal_number=subgoal_number,
                    )
                )

                subgoal_task_results.append(
                    task_result
                )

                if task_result.get(
                    "executed"
                ):
                    executed_tasks += 1

                if task_result.get(
                    "skipped"
                ):
                    skipped_tasks += 1

            subgoal_status = (
                self._determine_subgoal_status(
                    subgoal_task_results
                )
            )

            subgoal.update_state(
                SubgoalState(
                    subgoal_status
                )
            )

            print(
                f"Subgoal status: "
                f"{subgoal_status}"
            )

            execution_results.append(
                {
                    "subgoal_id": subgoal.id,
                    "subgoal": subgoal.name,
                    "status": subgoal_status,
                    "tasks": subgoal_task_results,
                }
            )

        overall_status = (
            self._determine_plan_status(
                execution_results
            )
        )

        if overall_status == (
            PlanState.COMPLETED.value
        ):
            plan.update_state(
                PlanState.COMPLETED
            )

            print(
                "\nPlan execution completed."
            )

        else:
            plan.update_state(
                PlanState.ACTIVE
            )

            print(
                f"\nPlan execution status: "
                f"{overall_status}"
            )

        return {
            "plan_id": plan.id,
            "goal_id": plan.goal_id,
            "plan_version": plan.version,
            "status": overall_status,
            "subgoals": execution_results,
            "execution_summary": {
                "executed_tasks": executed_tasks,
                "skipped_tasks": skipped_tasks,
                "total_tasks": total_tasks,
            },
        }

    def _process_task(
        self,
        task,
        task_number: int,
        subgoal_number: int,
    ) -> dict[str, Any]:
        """
        Process one task according to its current lifecycle state.

        Completed tasks are skipped.

        Pending, in-progress, and paused tasks continue execution.

        Blocked, failed, requires-input, and needs-revision tasks
        are preserved without automatic execution.
        """

        print(
            f"  Task "
            f"{subgoal_number}."
            f"{task_number}: "
            f"{task.title}"
        )

        current_state = task.state

        if (
            current_state
            == TaskState.COMPLETED
        ):
            print(
                "  Task already completed."
            )

            print(
                "  Skipping previously completed work."
            )

            return {
                "task_id": task.id,
                "task": task.title,
                "state": task.state.value,
                "result": task.result,
                "executed": False,
                "skipped": True,
                "skip_reason": (
                    "Task was already completed."
                ),
            }

        if (
            current_state
            in self.NON_EXECUTABLE_TASK_STATES
        ):
            print(
                f"  Task cannot continue automatically."
            )

            print(
                f"  Task state: "
                f"{task.state.value}"
            )

            return {
                "task_id": task.id,
                "task": task.title,
                "state": task.state.value,
                "result": task.result,
                "executed": False,
                "skipped": True,
                "skip_reason": (
                    "Task requires resolution "
                    "before execution can continue."
                ),
            }

        if (
            current_state
            not in self.EXECUTABLE_TASK_STATES
        ):
            raise ValueError(
                f"Unsupported task state: "
                f"{current_state.value}"
            )

        print(
            f"  Task state: "
            f"{task.state.value}"
        )

        task.update_state(
            TaskState.IN_PROGRESS
        )

        print(
            f"  Task state: "
            f"{task.state.value}"
        )

        result = (
            "Task processed by the "
            "Atrivon execution framework."
        )

        task.set_result(
            result
        )

        task.update_state(
            TaskState.COMPLETED
        )

        print(
            f"  Task state: "
            f"{task.state.value}"
        )

        return {
            "task_id": task.id,
            "task": task.title,
            "state": task.state.value,
            "result": task.result,
            "executed": True,
            "skipped": False,
        }

    def _determine_subgoal_status(
        self,
        task_results: list[dict[str, Any]],
    ) -> str:
        """
        Determine the correct SubgoalState from task results.
        """

        if not task_results:
            return SubgoalState.BLOCKED.value

        task_states = {
            result["state"]
            for result in task_results
        }

        if task_states == {
            TaskState.COMPLETED.value
        }:
            return SubgoalState.COMPLETED.value

        if (
            TaskState.REQUIRES_INPUT.value
            in task_states
        ):
            return (
                SubgoalState.REQUIRES_INPUT.value
            )

        if (
            TaskState.NEEDS_REVISION.value
            in task_states
        ):
            return (
                SubgoalState.NEEDS_REVISION.value
            )

        if (
            TaskState.BLOCKED.value
            in task_states
            or TaskState.FAILED.value
            in task_states
        ):
            return SubgoalState.BLOCKED.value

        return SubgoalState.IN_PROGRESS.value

    def _determine_plan_status(
        self,
        subgoal_results: list[dict[str, Any]],
    ) -> str:
        """
        Determine the overall execution status of the Plan.
        """

        if not subgoal_results:
            return "failed"

        subgoal_states = {
            result["status"]
            for result in subgoal_results
        }

        if subgoal_states == {
            SubgoalState.COMPLETED.value
        }:
            return PlanState.COMPLETED.value

        if (
            SubgoalState.REQUIRES_INPUT.value
            in subgoal_states
        ):
            return "requires_input"

        if (
            SubgoalState.NEEDS_REVISION.value
            in subgoal_states
        ):
            return "needs_revision"

        if (
            SubgoalState.BLOCKED.value
            in subgoal_states
        ):
            return "blocked"

        return "in_progress"