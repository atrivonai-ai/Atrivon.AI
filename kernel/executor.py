"""
Atrivon Executor

The Executor is responsible for executing Plans by:

- Validating dependencies
- Finding executable Tasks
- Executing Tasks
- Coordinating Capabilities
- Updating Task, Subgoal, and Plan states
"""

from typing import Any

from atrivon.domain.models import (
    Plan,
    Subgoal,
    Task,
)

from atrivon.domain.states import (
    PlanState,
    SubgoalState,
    TaskState,
)

from atrivon.execution.actions import (
    ActionStatus,
)

from atrivon.execution.dependencies import (
    DependencyResolver,
)

from atrivon.execution.service import (
    CapabilityExecutionService,
)

from atrivon.execution.task_actions import (
    TaskActionResolver,
)

class Executor:
    """
    Atrivon's execution engine.

    Responsible for:
    - Validating task dependencies
    - Executing dependency-ready tasks
    - Coordinating capabilities
    - Updating task, subgoal, and plan states
    """

    EXECUTABLE_TASK_STATES = {
        TaskState.PENDING,
        TaskState.IN_PROGRESS,
    }

    NON_EXECUTABLE_TASK_STATES = {
        TaskState.BLOCKED,
        TaskState.FAILED,
        TaskState.REQUIRES_INPUT,
        TaskState.NEEDS_REVISION,
    }

    def __init__(
        self,
        capability_execution_service: CapabilityExecutionService | None = None,
    ):
        self.dependency_resolver = DependencyResolver()
        self.task_action_resolver = TaskActionResolver()
        self.capability_execution_service = capability_execution_service

        print("Executor module loaded.")

    def execute_plan(
        self,
        plan: Plan,
    ) -> dict[str, Any]:
        """
        Execute an Atrivon Plan.

        Workflow:

        1. Validate the plan.
        2. Validate task dependencies.
        3. Find executable tasks.
        4. Execute ready tasks.
        5. Update task states.
        6. Update subgoal states.
        7. Update the plan state.
        8. Return a structured execution summary.
        """

        print("\nStarting plan execution...")

        if not isinstance(plan, Plan):
            return self._failed_result(
                "Execution failed: expected a Plan object."
            )

        if not plan.goal_id.strip():
            plan.update_state(
                PlanState.REJECTED
            )

            return self._failed_result(
                "Execution failed: plan has no Goal ID.",
                plan=plan,
            )

        if not plan.subgoals:
            plan.update_state(
                PlanState.REJECTED
            )

            return self._failed_result(
                "Execution failed: plan contains no Subgoals.",
                plan=plan,
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

            return {
                "plan_id": plan.id,
                "goal_id": plan.goal_id,
                "status": "failed",
                "dependency_errors": list(
                    dependency_validation.errors
                ),
            }

        print(
    f"Executing Plan {plan.id}"
)

plan.update_state(
    PlanState.ACTIVE
)

task_results = []

for subgoal in plan.subgoals:
    print(f"\nSubgoal: {subgoal.name}")

    for task in subgoal.tasks:
        result = self._execute_task(task)
        task_results.append(result)

for subgoal in plan.subgoals:
    completed = all(
        task.state == TaskState.COMPLETED
        for task in subgoal.tasks
    )

    if completed:
        subgoal.update_state(
            SubgoalState.COMPLETED
        )
    else:
        subgoal.update_state(
            SubgoalState.IN_PROGRESS
        )        
    def _execute_task(
        self,
        task: Task,
    ) -> dict[str, Any]:
        """
        Execute a single Task.
        """

        print(f"Executing Task: {task.title}")

        if task.state == TaskState.COMPLETED:
            return {
                "task_id": task.id,
                "executed": False,
                "skipped": True,
                "state": task.state.value,
                "result": task.result,
            }

        if task.state in self.NON_EXECUTABLE_TASK_STATES:
            return {
                "task_id": task.id,
                "executed": False,
                "failed": task.state == TaskState.FAILED,
                "state": task.state.value,
                "result": task.result,
            }

        task.update_state(
            TaskState.IN_PROGRESS
        )

        if self.task_action_resolver.has_action(task):
            return self._execute_action_task(task)

        return self._execute_simulated_task(task)
    def _execute_action_task(
        self,
        task: Task,
    ) -> dict[str, Any]:
        """
        Execute a Task using a real Capability.
        """

        if self.capability_execution_service is None:
            task.update_state(TaskState.FAILED)

            task.set_result(
                {
                    "error": (
                        "No CapabilityExecutionService "
                        "configured."
                    )
                }
            )

            return {
                "task_id": task.id,
                "task": task.title,
                "executed": True,
                "failed": True,
                "state": task.state.value,
                "result": task.result,
            }

        request = self.task_action_resolver.resolve(
            task
        )

        action_result = (
            self.capability_execution_service.execute(
                request
            )
        )

        task.set_result(
            action_result.to_dict()
        )

        if (
            action_result.status
            == ActionStatus.SUCCEEDED
        ):
            task.update_state(
                TaskState.COMPLETED
            )
        elif (
            action_result.status
            == ActionStatus.BLOCKED
        ):
            task.update_state(
                TaskState.BLOCKED
            )
        elif (
            action_result.status
            == ActionStatus.REQUIRES_INPUT
        ):
            task.update_state(
                TaskState.REQUIRES_INPUT
            )
        else:
            task.update_state(
                TaskState.FAILED
            )

        return {
            "task_id": task.id,
            "task": task.title,
            "executed": True,
            "failed": (
                task.state == TaskState.FAILED
            ),
            "state": task.state.value,
            "result": task.result,
        }
    def _execute_simulated_task(
        self,
        task: Task,
    ) -> dict[str, Any]:
        """
        Execute a Task using Atrivon's
        simulated execution framework.
        """

        task.update_state(
            TaskState.IN_PROGRESS
        )

        task.set_result(
            "Task processed by the Atrivon execution framework."
        )

        task.update_state(
            TaskState.COMPLETED
        )

        return {
            "task_id": task.id,
            "task": task.title,
            "executed": True,
            "failed": False,
            "state": task.state.value,
            "result": task.result,
        }
                        

