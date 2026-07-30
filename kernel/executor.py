from kernel.task_state import TaskState


class Executor:
    """
    The Executor is responsible for coordinating the execution
    of an approved Atrivon plan.

    The Executor processes a hierarchical plan containing:
    - A goal
    - Subgoals
    - Tasks

    Each task has its own lifecycle state.

    The current implementation establishes the execution
    lifecycle framework. It does not yet perform arbitrary
    real-world actions.
    """

    def __init__(self):
        print("Executor module loaded.")

    def execute_plan(self, plan):
        """
        Execute an approved hierarchical plan.

        Returns a structured execution result containing:
        - The original goal
        - The overall execution status
        - Subgoal execution results
        - Task execution states
        """

        print("\nStarting plan execution...")

        if not isinstance(plan, dict):
            print("Execution failed: invalid plan format.")

            return {
                "goal": None,
                "status": "failed",
                "subgoals": [],
            }

        goal = plan.get("goal")
        subgoals = plan.get("subgoals")

        if not isinstance(goal, str) or not goal.strip():
            print("Execution failed: missing goal.")

            return {
                "goal": goal,
                "status": "failed",
                "subgoals": [],
            }

        if not isinstance(subgoals, list) or not subgoals:
            print("Execution failed: no subgoals available.")

            return {
                "goal": goal,
                "status": "failed",
                "subgoals": [],
            }

        execution_results = []

        print(f"\nExecuting goal: {goal}")

        for subgoal_number, subgoal in enumerate(
            subgoals,
            start=1,
        ):
            subgoal_name = subgoal.get("name")
            tasks = subgoal.get("tasks")

            print(
                f"\nExecuting subgoal "
                f"{subgoal_number}: {subgoal_name}"
            )

            task_results = []

            for task_number, task in enumerate(
                tasks,
                start=1,
            ):
                task_result = self._execute_task(
                    task=task,
                    task_number=task_number,
                    subgoal_number=subgoal_number,
                )

                task_results.append(task_result)

            subgoal_completed = all(
                task_result["state"] == TaskState.COMPLETED.value
                for task_result in task_results
            )

            if subgoal_completed:
                subgoal_status = "completed"
            else:
                subgoal_status = "blocked"

            execution_results.append(
                {
                    "subgoal": subgoal_name,
                    "status": subgoal_status,
                    "tasks": task_results,
                }
            )

            print(
                f"Subgoal status: {subgoal_status}"
            )

        overall_completed = all(
            subgoal_result["status"] == "completed"
            for subgoal_result in execution_results
        )

        if overall_completed:
            overall_status = "completed"
            print("\nPlan execution completed.")
        else:
            overall_status = "blocked"
            print(
                "\nPlan execution stopped: "
                "one or more subgoals are blocked."
            )

        return {
            "goal": goal,
            "status": overall_status,
            "subgoals": execution_results,
        }

    def _execute_task(
        self,
        task,
        task_number,
        subgoal_number,
    ):
        """
        Process one task through the task lifecycle.

        The current implementation transitions the task from
        pending to in_progress to completed.

        Future versions will perform real actions and will be
        able to transition tasks into blocked, failed,
        requires_input, or needs_revision states.
        """

        print(
            f"  Task "
            f"{subgoal_number}.{task_number}: {task}"
        )

        task_state = TaskState.PENDING

        print(
            f"  Task state: {task_state.value}"
        )

        task_state = TaskState.IN_PROGRESS

        print(
            f"  Task state: {task_state.value}"
        )

        task_state = TaskState.COMPLETED

        print(
            f"  Task state: {task_state.value}"
        )

        return {
            "task": task,
            "state": task_state.value,
            "message": (
                "Task processed by the Atrivon "
                "execution framework."
            ),
        }