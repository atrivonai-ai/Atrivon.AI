from atrivon.domain.models import Plan


class Reasoner:
    """
    The Reasoner evaluates and analyzes canonical Atrivon Plan objects.

    Responsibilities include:
    - Structural Plan validation
    - Execution-result analysis
    - Identifying when a Plan may require revision
    - Describing why a Plan requires revision

    The Reasoner does not create revised Plans.
    The Planner owns strategy creation.
    """

    def __init__(self):
        print("Reasoner module loaded.")

    def evaluate_plan(
        self,
        plan: Plan,
    ) -> bool:
        """
        Evaluate whether a canonical Plan is valid and
        ready to move forward.
        """

        print(
            "\nEvaluating plan..."
        )

        if not isinstance(
            plan,
            Plan,
        ):
            print(
                "Plan evaluation failed: "
                "expected a Plan object."
            )

            return False

        if not plan.goal_id.strip():
            print(
                "Plan evaluation failed: "
                "missing goal ID."
            )

            return False

        if not plan.subgoals:
            print(
                "Plan evaluation failed: "
                "no subgoals found."
            )

            return False

        total_tasks = 0

        for subgoal_number, subgoal in enumerate(
            plan.subgoals,
            start=1,
        ):
            if not subgoal.name.strip():
                print(
                    f"Plan evaluation failed: "
                    f"subgoal {subgoal_number} "
                    f"has no name."
                )

                return False

            if not subgoal.tasks:
                print(
                    f"Plan evaluation failed: "
                    f"subgoal '{subgoal.name}' "
                    f"has no tasks."
                )

                return False

            for task_number, task in enumerate(
                subgoal.tasks,
                start=1,
            ):
                if not task.title.strip():
                    print(
                        f"Plan evaluation failed: "
                        f"subgoal '{subgoal.name}' "
                        f"contains an invalid task "
                        f"at position {task_number}."
                    )

                    return False

                total_tasks += 1

        print(
            "Plan evaluation complete."
        )

        print(
            f"Plan ID: "
            f"{plan.id}"
        )

        print(
            f"Plan version: "
            f"{plan.version}"
        )

        print(
            f"Validated subgoals: "
            f"{len(plan.subgoals)}"
        )

        print(
            f"Validated tasks: "
            f"{total_tasks}"
        )

        print(
            "Status: Plan approved for execution."
        )

        return True

    def analyze_execution_result(
        self,
        plan: Plan,
        execution_result: dict,
    ) -> dict:
        """
        Analyze the result of Plan execution.

        Determines whether the current Plan should be revised
        and provides structured information that can guide
        the Planner when creating a revised strategy.
        """

        if not isinstance(
            plan,
            Plan,
        ):
            raise TypeError(
                "analyze_execution_result() "
                "requires a Plan object."
            )

        if not isinstance(
            execution_result,
            dict,
        ):
            raise TypeError(
                "execution_result must be a dictionary."
            )

        status = execution_result.get(
            "status"
        )

        execution_summary = (
            execution_result.get(
                "execution_summary",
                {},
            )
        )

        dependency_blocked_tasks = (
            execution_summary.get(
                "dependency_blocked_tasks",
                0,
            )
        )

        failed_tasks = (
            execution_summary.get(
                "failed_tasks",
                0,
            )
        )

        if status == "blocked":
            if (
                dependency_blocked_tasks
                > 0
            ):
                return {
                    "needs_revision": True,
                    "trigger": (
                        "dependency_blocked"
                    ),
                    "reason": (
                        "The current Plan is blocked "
                        "by unresolved task dependencies."
                    ),
                    "strategy": (
                        "Introduce explicit blocker-resolution "
                        "steps before resuming the main work."
                    ),
                    "recommended_actions": [
                        (
                            "Analyze the unresolved execution blockers"
                        ),
                        (
                            "Resolve or redesign the blocked dependencies"
                        ),
                        (
                            "Validate the revised execution path"
                        ),
                    ],
                }

            return {
                "needs_revision": True,
                "trigger": "execution_blocked",
                "reason": (
                    "The current Plan is blocked "
                    "and cannot continue safely."
                ),
                "strategy": (
                    "Introduce a blocker-resolution phase "
                    "before continuing the original objective."
                ),
                "recommended_actions": [
                    (
                        "Analyze the cause of the execution blocker"
                    ),
                    (
                        "Define a safe path around the blocker"
                    ),
                    (
                        "Validate the revised execution path"
                    ),
                ],
            }

        if status == "failed":
            return {
                "needs_revision": True,
                "trigger": "execution_failed",
                "reason": (
                    "The current Plan failed during execution "
                    "and requires a revised strategy."
                ),
                "strategy": (
                    "Analyze the failure and introduce "
                    "a safer execution approach."
                ),
                "recommended_actions": [
                    (
                        "Analyze the execution failure"
                    ),
                    (
                        "Identify a safer alternative approach"
                    ),
                    (
                        "Validate the revised execution path"
                    ),
                ],
            }

        if status == "needs_revision":
            return {
                "needs_revision": True,
                "trigger": "plan_revision_required",
                "reason": (
                    "The current Plan has been identified "
                    "as requiring revision."
                ),
                "strategy": (
                    "Revise the current strategy "
                    "while preserving useful completed work."
                ),
                "recommended_actions": [
                    (
                        "Analyze why the current strategy is insufficient"
                    ),
                    (
                        "Develop an improved strategy"
                    ),
                    (
                        "Validate the revised execution path"
                    ),
                ],
            }

        if failed_tasks > 0:
            return {
                "needs_revision": True,
                "trigger": "task_failure",
                "reason": (
                    "One or more tasks failed during execution."
                ),
                "strategy": (
                    "Revise the strategy around failed work "
                    "before continuing."
                ),
                "recommended_actions": [
                    (
                        "Analyze the failed tasks"
                    ),
                    (
                        "Identify alternative execution approaches"
                    ),
                    (
                        "Validate the revised execution path"
                    ),
                ],
            }

        return {
            "needs_revision": False,
            "trigger": None,
            "reason": "",
            "strategy": "",
            "recommended_actions": [],
        }