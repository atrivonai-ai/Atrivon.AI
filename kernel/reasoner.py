from atrivon.domain.models import Plan


class Reasoner:
    """
    The Reasoner evaluates the structure and validity of
    canonical Atrivon Plan objects.

    The current implementation performs structural validation.

    Future versions will expand this responsibility to include:
    - Strategic evaluation
    - Risk analysis
    - Dependency analysis
    - Alternative strategies
    - Decision support
    - Replanning
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

        print("\nEvaluating plan...")

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
                    f"subgoal {subgoal_number} has no name."
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

        print("Plan evaluation complete.")
        print(
            f"Plan ID: {plan.id}"
        )
        print(
            f"Plan version: {plan.version}"
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