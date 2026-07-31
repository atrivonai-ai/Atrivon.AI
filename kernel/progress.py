from typing import Any

from atrivon.domain.models import Plan
from atrivon.domain.states import TaskState


class ProgressTracker:
    """
    Calculates progress for canonical Atrivon Plan objects.

    Progress is derived from the actual lifecycle states of
    canonical Task objects.

    The ProgressTracker does not own task state.
    The domain models remain the source of truth.
    """

    def __init__(self):
        print("Progress Tracker module loaded.")

    def calculate_progress(
        self,
        plan: Plan,
    ) -> dict[str, Any]:
        """
        Calculate progress directly from a canonical Plan.

        Returns:
            A structured progress report containing:

            - Plan identity
            - Goal identity
            - Plan version
            - Overall progress
            - Task counts
            - Subgoal progress
        """

        if not isinstance(
            plan,
            Plan,
        ):
            raise TypeError(
                "ProgressTracker.calculate_progress() "
                "requires a Plan object."
            )

        total_tasks = 0
        completed_tasks = 0
        in_progress_tasks = 0
        blocked_tasks = 0
        failed_tasks = 0

        subgoal_reports = []

        for subgoal in plan.subgoals:
            subgoal_total_tasks = len(
                subgoal.tasks
            )

            subgoal_completed_tasks = sum(
                1
                for task in subgoal.tasks
                if task.state
                == TaskState.COMPLETED
            )

            subgoal_in_progress_tasks = sum(
                1
                for task in subgoal.tasks
                if task.state
                == TaskState.IN_PROGRESS
            )

            subgoal_blocked_tasks = sum(
                1
                for task in subgoal.tasks
                if task.state
                == TaskState.BLOCKED
            )

            subgoal_failed_tasks = sum(
                1
                for task in subgoal.tasks
                if task.state
                == TaskState.FAILED
            )

            total_tasks += (
                subgoal_total_tasks
            )

            completed_tasks += (
                subgoal_completed_tasks
            )

            in_progress_tasks += (
                subgoal_in_progress_tasks
            )

            blocked_tasks += (
                subgoal_blocked_tasks
            )

            failed_tasks += (
                subgoal_failed_tasks
            )

            if subgoal_total_tasks == 0:
                subgoal_progress = 0.0
            else:
                subgoal_progress = (
                    subgoal_completed_tasks
                    / subgoal_total_tasks
                ) * 100

            subgoal_reports.append(
                {
                    "subgoal_id": subgoal.id,
                    "subgoal": subgoal.name,
                    "progress": round(
                        subgoal_progress,
                        2,
                    ),
                    "total_tasks": (
                        subgoal_total_tasks
                    ),
                    "completed_tasks": (
                        subgoal_completed_tasks
                    ),
                    "in_progress_tasks": (
                        subgoal_in_progress_tasks
                    ),
                    "blocked_tasks": (
                        subgoal_blocked_tasks
                    ),
                    "failed_tasks": (
                        subgoal_failed_tasks
                    ),
                    "state": (
                        subgoal.state.value
                    ),
                }
            )

        if total_tasks == 0:
            overall_progress = 0.0
        else:
            overall_progress = (
                completed_tasks
                / total_tasks
            ) * 100

        return {
            "plan_id": plan.id,
            "goal_id": plan.goal_id,
            "plan_version": plan.version,
            "progress": round(
                overall_progress,
                2,
            ),
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "in_progress_tasks": (
                in_progress_tasks
            ),
            "blocked_tasks": (
                blocked_tasks
            ),
            "failed_tasks": (
                failed_tasks
            ),
            "subgoals": subgoal_reports,
        }

    def display_progress(
        self,
        progress_report: dict[str, Any],
    ) -> None:
        """
        Display a progress report in a readable format.
        """

        print("\nProgress Report")

        print(
            f"Plan ID: "
            f"{progress_report.get('plan_id')}"
        )

        print(
            f"Goal ID: "
            f"{progress_report.get('goal_id')}"
        )

        print(
            f"Plan Version: "
            f"{progress_report.get('plan_version')}"
        )

        print(
            f"Overall Progress: "
            f"{progress_report.get('progress', 0.0)}%"
        )

        print(
            f"Tasks Completed: "
            f"{progress_report.get('completed_tasks', 0)}"
            f"/"
            f"{progress_report.get('total_tasks', 0)}"
        )

        print(
            f"Tasks In Progress: "
            f"{progress_report.get('in_progress_tasks', 0)}"
        )

        print(
            f"Tasks Blocked: "
            f"{progress_report.get('blocked_tasks', 0)}"
        )

        print(
            f"Tasks Failed: "
            f"{progress_report.get('failed_tasks', 0)}"
        )

        print("\nSubgoal Progress:")

        for subgoal in progress_report.get(
            "subgoals",
            [],
        ):
            print(
                f"- {subgoal['subgoal']}: "
                f"{subgoal['progress']}% "
                f"({subgoal['state']})"
            )