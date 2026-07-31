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

    The current implementation provides the execution framework
    and updates canonical domain objects as work progresses.

    The current task execution itself is still a controlled
    execution simulation. Real-world actions will be introduced
    through future execution and automation capabilities.
    """

    def __init__(self):
        print("Executor module loaded.")

    def execute_plan(
        self,
        plan: Plan,
    ) -> dict[str, Any]:
        """
        Execute a canonical Atrivon Plan.

        Returns a structured execution result containing:
        - Plan identity
        - Goal identity
        - Overall execution status
        - Subgoal results
        - Task results
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
            }

        plan.update_state(
            PlanState.ACTIVE
        )

        execution_results = []

        print(
            f"\nExecuting Plan: {plan.id}"
        )

        print(
            f"Plan version: {plan.version}"
        )

        print(
            f"Goal ID: {plan.goal_id}"
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

            subgoal.update_state(
                SubgoalState.IN_PROGRESS
            )

            task_results = []

            for task_number, task in enumerate(
                subgoal.tasks,
                start=1,
            ):
                task_result = self._execute_task(
                    task=task,
                    task_number=task_number,
                    subgoal_number=subgoal_number,
                )

                task_results.append(
                    task_result
                )

            all_tasks_completed = all(
                task_result["state"]
                == TaskState.COMPLETED.value
                for task_result in task_results
            )

            if all_tasks_completed:
                subgoal.update_state(
                    SubgoalState.COMPLETED
                )

                subgoal_status = (
                    SubgoalState.COMPLETED.value
                )

            else:
                subgoal.update_state(
                    SubgoalState.BLOCKED
                )

                subgoal_status = (
                    SubgoalState.BLOCKED.value
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
                    "tasks": task_results,
                }
            )

        all_subgoals_completed = all(
            result["status"]
            == SubgoalState.COMPLETED.value
            for result in execution_results
        )

        if all_subgoals_completed:
            plan.update_state(
                PlanState.COMPLETED
            )

            overall_status = (
                PlanState.COMPLETED.value
            )

            print(
                "\nPlan execution completed."
            )

        else:
            overall_status = (
                SubgoalState.BLOCKED.value
            )

            print(
                "\nPlan execution stopped: "
                "one or more subgoals are blocked."
            )

        return {
            "plan_id": plan.id,
            "goal_id": plan.goal_id,
            "plan_version": plan.version,
            "status": overall_status,
            "subgoals": execution_results,
        }

    def _execute_task(
        self,
        task,
        task_number: int,
        subgoal_number: int,
    ) -> dict[str, Any]:
        """
        Execute one canonical Task.

        The current implementation transitions the task through:

        PENDING
            ↓
        IN_PROGRESS
            ↓
        COMPLETED

        The architecture supports future states including:

        BLOCKED
        FAILED
        REQUIRES_INPUT
        NEEDS_REVISION
        """

        print(
            f"  Task "
            f"{subgoal_number}."
            f"{task_number}: "
            f"{task.title}"
        )

        task.update_state(
            TaskState.PENDING
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
        }