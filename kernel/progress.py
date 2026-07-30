from kernel.task_state import TaskState


class ProgressTracker:
    """
    The ProgressTracker calculates progress for Atrivon's
    goals, subgoals, and tasks.

    Progress is calculated from actual task states.
    It does not use manually assigned percentages.
    """

    def __init__(self):
        print("Progress Tracker module loaded.")

    def calculate_progress(self, execution_result):
        """
        Calculate overall goal progress from task states.

        Returns:
            A structured progress report containing:
            - Goal
            - Overall progress percentage
            - Total tasks
            - Completed tasks
            - Subgoal progress
        """

        if not isinstance(execution_result, dict):
            return {
                "goal": None,
                "progress": 0.0,
                "total_tasks": 0,
                "completed_tasks": 0,
                "subgoals": [],
            }

        goal = execution_result.get("goal")
        subgoals = execution_result.get("subgoals", [])

        if not isinstance(subgoals, list):
            subgoals = []

        subgoal_results = []

        total_tasks = 0
        completed_tasks = 0

        for subgoal in subgoals:
            subgoal_progress = self._calculate_subgoal_progress(
                subgoal
            )

            subgoal_results.append(subgoal_progress)

            total_tasks += subgoal_progress["total_tasks"]
            completed_tasks += subgoal_progress["completed_tasks"]

        if total_tasks == 0:
            overall_progress = 0.0
        else:
            overall_progress = (
                completed_tasks / total_tasks
            ) * 100

        return {
            "goal": goal,
            "progress": round(overall_progress, 2),
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "subgoals": subgoal_results,
        }

    def _calculate_subgoal_progress(self, subgoal):
        """
        Calculate progress for a single subgoal.
        """

        if not isinstance(subgoal, dict):
            return {
                "subgoal": None,
                "progress": 0.0,
                "total_tasks": 0,
                "completed_tasks": 0,
                "status": "invalid",
            }

        subgoal_name = subgoal.get("subgoal")
        tasks = subgoal.get("tasks", [])

        if not isinstance(tasks, list):
            tasks = []

        total_tasks = len(tasks)

        completed_tasks = sum(
            1
            for task in tasks
            if isinstance(task, dict)
            and task.get("state")
            == TaskState.COMPLETED.value
        )

        if total_tasks == 0:
            progress = 0.0
            status = "pending"
        else:
            progress = (
                completed_tasks / total_tasks
            ) * 100

            if completed_tasks == total_tasks:
                status = "completed"
            elif completed_tasks == 0:
                status = "pending"
            else:
                status = "in_progress"

        return {
            "subgoal": subgoal_name,
            "progress": round(progress, 2),
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "status": status,
        }

    def display_progress(self, progress_report):
        """
        Display the progress report in a readable format.
        """

        print("\nProgress Report")

        goal = progress_report.get("goal")

        if goal:
            print(f"Goal: {goal}")

        overall_progress = progress_report.get(
            "progress",
            0.0,
        )

        completed_tasks = progress_report.get(
            "completed_tasks",
            0,
        )

        total_tasks = progress_report.get(
            "total_tasks",
            0,
        )

        print(
            f"Overall Progress: "
            f"{overall_progress}%"
        )

        print(
            f"Tasks Completed: "
            f"{completed_tasks}/{total_tasks}"
        )

        print("\nSubgoal Progress:")

        for subgoal in progress_report.get(
            "subgoals",
            [],
        ):
            print(
                f"- {subgoal['subgoal']}: "
                f"{subgoal['progress']}% "
                f"({subgoal['status']})"
            )