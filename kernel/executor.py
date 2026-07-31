from typing import Any

from atrivon.domain.models import Plan, Task
from atrivon.domain.states import (
    PlanState,
    SubgoalState,
    TaskState,
)
from atrivon.execution.dependencies import (
    DependencyResolver,
)


class Executor:
    """
    The Executor coordinates execution of an approved Atrivon Plan.

    The Executor is:

    - Resume-aware
    - Dependency-aware
    - State-aware

    Completed tasks are never executed again.

    Tasks are only executed when all dependencies are completed.

    The Executor does not decide strategy.
    It executes the Plan according to the dependency and
    lifecycle rules defined by Atrivon's execution architecture.

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
        self.dependency_resolver = (
            DependencyResolver()
        )

        print(
            "Executor module loaded."
        )

    def execute_plan(
        self,
        plan: Plan,
    ) -> dict[str, Any]:
        """
        Execute or continue execution of a canonical Atrivon Plan.

        The Executor:

        1. Validates task dependencies.
        2. Finds tasks that are ready.
        3. Executes ready tasks.
        4. Re-evaluates dependencies.
        5. Continues until no more executable work remains.

        Completed tasks are preserved and skipped.

        Returns:
            A structured execution result.
        """

        print(
            "\nStarting plan execution..."
        )

        if not isinstance(
            plan,
            Plan,
        ):
            return self._failed_result(
                "Execution failed: "
                "expected a Plan object."
            )

        if not plan.goal_id.strip():
            plan.update_state(
                PlanState.REJECTED
            )

            return self._failed_result(
                "Execution failed: "
                "plan has no goal ID.",
                plan=plan,
            )

        if not plan.subgoals:
            plan.update_state(
                PlanState.REJECTED
            )

            return self._failed_result(
                "Execution failed: "
                "plan contains no subgoals.",
                plan=plan,
            )

        if (
            plan.state
            == PlanState.COMPLETED
        ):
            raise ValueError(
                "Cannot execute a completed Plan."
            )

        dependency_validation = (
            self.dependency_resolver.validate_plan(
                plan
            )
        )

        if not dependency_validation.valid:
            plan.update_state(
                PlanState.REJECTED
            )

            print(
                "\nDependency validation failed."
            )

            for error in (
                dependency_validation.errors
            ):
                print(
                    f"- {error}"
                )

            return {
                "plan_id": plan.id,
                "goal_id": plan.goal_id,
                "plan_version": plan.version,
                "status": "failed",
                "subgoals": [],
                "execution_summary": {
                    "executed_tasks": 0,
                    "skipped_tasks": 0,
                    "dependency_blocked_tasks": 0,
                    "total_tasks": self._count_tasks(
                        plan
                    ),
                    "execution_passes": 0,
                },
                "dependency_errors": list(
                    dependency_validation.errors
                ),
            }

        plan.update_state(
            PlanState.ACTIVE
        )

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

        task_results: dict[
            str,
            dict[str, Any],
        ] = {}

        executed_tasks = 0
        skipped_tasks = 0
        execution_passes = 0

        all_tasks = self._collect_tasks(
            plan
        )

        total_tasks = len(
            all_tasks
        )

        for task in all_tasks:
            if (
                task.state
                == TaskState.COMPLETED
            ):
                task_results[
                    task.id
                ] = {
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

                skipped_tasks += 1

        while True:
            ready_tasks = (
                self.dependency_resolver.get_ready_tasks(
                    plan
                )
            )

            executable_tasks = [
                task
                for task in ready_tasks
                if task.state
                in self.EXECUTABLE_TASK_STATES
            ]

            if not executable_tasks:
                break

            execution_passes += 1

            print(
                f"\nExecution pass "
                f"{execution_passes}"
            )

            progress_made = False

            for task in executable_tasks:
                result = self._execute_task(
                    task
                )

                task_results[
                    task.id
                ] = result

                if result.get(
                    "executed"
                ):
                    executed_tasks += 1
                    progress_made = True

            if not progress_made:
                break

        dependency_blocked_tasks = (
            self.dependency_resolver.get_blocked_tasks(
                plan
            )
        )

        for task in dependency_blocked_tasks:
            unsatisfied_dependencies = (
                self.dependency_resolver
                .get_unsatisfied_dependencies(
                    task,
                    plan,
                )
            )

            task_results[
                task.id
            ] = {
                "task_id": task.id,
                "task": task.title,
                "state": task.state.value,
                "result": task.result,
                "executed": False,
                "skipped": True,
                "skip_reason": (
                    "Task is waiting for "
                    "incomplete dependencies."
                ),
                "unsatisfied_dependencies": (
                    unsatisfied_dependencies
                ),
            }

        dependency_blocked_ids = {
            task.id
            for task
            in dependency_blocked_tasks
        }

        subgoal_results = []

        for subgoal in plan.subgoals:
            task_results_for_subgoal = []

            for task in subgoal.tasks:
                result = task_results.get(
                    task.id
                )

                if result is None:
                    result = {
                        "task_id": task.id,
                        "task": task.title,
                        "state": task.state.value,
                        "result": task.result,
                        "executed": False,
                        "skipped": False,
                    }

                task_results_for_subgoal.append(
                    result
                )

            subgoal_status = (
                self._determine_subgoal_status(
                    subgoal,
                    dependency_blocked_ids,
                )
            )

            subgoal.update_state(
                SubgoalState(
                    subgoal_status
                )
            )

            print(
                f"\nSubgoal: "
                f"{subgoal.name}"
            )

            print(
                f"Subgoal status: "
                f"{subgoal_status}"
            )

            subgoal_results.append(
                {
                    "subgoal_id": subgoal.id,
                    "subgoal": subgoal.name,
                    "status": subgoal_status,
                    "tasks": (
                        task_results_for_subgoal
                    ),
                }
            )

        overall_status = (
            self._determine_plan_status(
                subgoal_results
            )
        )

        if (
            overall_status
            == PlanState.COMPLETED.value
        ):
            plan.update_state(
                PlanState.COMPLETED
            )

            print(
                "\nPlan execution completed."
            )

        elif (
            overall_status
            == PlanState.BLOCKED.value
        ):
            plan.update_state(
                PlanState.BLOCKED
            )

            print(
                "\nPlan execution blocked."
            )

        elif (
            overall_status
            == "requires_input"
        ):
            plan.update_state(
                PlanState.ACTIVE
            )

            print(
                "\nPlan execution requires user input."
            )

        elif (
            overall_status
            == "needs_revision"
        ):
            plan.update_state(
                PlanState.NEEDS_REVISION
            )

            print(
                "\nPlan requires revision."
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
            "subgoals": subgoal_results,
            "execution_summary": {
                "executed_tasks": executed_tasks,
                "skipped_tasks": skipped_tasks,
                "dependency_blocked_tasks": len(
                    dependency_blocked_tasks
                ),
                "total_tasks": total_tasks,
                "execution_passes": execution_passes,
            },
        }

    def _execute_task(
        self,
        task: Task,
    ) -> dict[str, Any]:
        """
        Execute one dependency-ready Task.

        Completed tasks are skipped.

        Pending, in-progress, and paused tasks continue execution.

        Tasks in blocked, failed, requires-input, or needs-revision
        states are not executed automatically.
        """

        print(
            f"  Task: "
            f"{task.title}"
        )

        if (
            task.state
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
            task.state
            in self.NON_EXECUTABLE_TASK_STATES
        ):
            print(
                "  Task cannot continue automatically."
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
            task.state
            not in self.EXECUTABLE_TASK_STATES
        ):
            raise ValueError(
                f"Unsupported task state: "
                f"{task.state.value}"
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
        subgoal,
        dependency_blocked_ids: set[str],
    ) -> str:
        """
        Determine the correct SubgoalState from task states
        and dependency readiness.
        """

        if not subgoal.tasks:
            return SubgoalState.BLOCKED.value

        task_states = {
            task.state
            for task in subgoal.tasks
        }

        if task_states == {
            TaskState.COMPLETED
        }:
            return (
                SubgoalState.COMPLETED.value
            )

        if any(
            task.state
            == TaskState.REQUIRES_INPUT
            for task in subgoal.tasks
        ):
            return (
                SubgoalState.REQUIRES_INPUT.value
            )

        if any(
            task.state
            == TaskState.NEEDS_REVISION
            for task in subgoal.tasks
        ):
            return (
                SubgoalState.NEEDS_REVISION.value
            )

        if any(
            task.state
            in {
                TaskState.BLOCKED,
                TaskState.FAILED,
            }
            for task in subgoal.tasks
        ):
            return (
                SubgoalState.BLOCKED.value
            )

        if any(
            task.id
            in dependency_blocked_ids
            for task in subgoal.tasks
        ):
            return (
                SubgoalState.BLOCKED.value
            )

        return (
            SubgoalState.IN_PROGRESS.value
        )

    def _determine_plan_status(
        self,
        subgoal_results: list[
            dict[str, Any]
        ],
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
            return (
                PlanState.COMPLETED.value
            )

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
            return (
                PlanState.BLOCKED.value
            )

        return "in_progress"

    def _collect_tasks(
        self,
        plan: Plan,
    ) -> list[Task]:
        """
        Collect all Tasks from a Plan.
        """

        return [
            task
            for subgoal in plan.subgoals
            for task in subgoal.tasks
        ]

    def _count_tasks(
        self,
        plan: Plan,
    ) -> int:
        """
        Count all Tasks in a Plan.
        """

        return sum(
            len(subgoal.tasks)
            for subgoal in plan.subgoals
        )

    def _failed_result(
        self,
        message: str,
        plan: Plan | None = None,
    ) -> dict[str, Any]:
        """
        Build a standardized failed execution result.
        """

        return {
            "plan_id": (
                plan.id
                if plan is not None
                else None
            ),
            "goal_id": (
                plan.goal_id
                if plan is not None
                else None
            ),
            "status": "failed",
            "subgoals": [],
            "message": message,
            "execution_summary": {
                "executed_tasks": 0,
                "skipped_tasks": 0,
                "dependency_blocked_tasks": 0,
                "total_tasks": (
                    self._count_tasks(plan)
                    if plan is not None
                    else 0
                ),
                "execution_passes": 0,
            },
        }