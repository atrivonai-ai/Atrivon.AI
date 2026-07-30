class Reasoner:
    """
    The Reasoner evaluates the structure and quality of plans
    before they move toward execution.

    Its current responsibility is to validate that a plan:
    - Exists
    - Contains a goal
    - Contains at least one subgoal
    - Gives each subgoal at least one task
    """

    def __init__(self):
        print("Reasoner module loaded.")

    def evaluate_plan(self, plan):
        """
        Evaluate whether a structured plan is valid and
        ready to move forward.
        """

        print("\nEvaluating plan...")

        if not isinstance(plan, dict):
            print("Plan evaluation failed: invalid plan format.")
            return False

        goal = plan.get("goal")
        subgoals = plan.get("subgoals")

        if not isinstance(goal, str) or not goal.strip():
            print("Plan evaluation failed: missing goal.")
            return False

        if not isinstance(subgoals, list) or not subgoals:
            print("Plan evaluation failed: no subgoals found.")
            return False

        for subgoal_number, subgoal in enumerate(
            subgoals,
            start=1,
        ):
            if not isinstance(subgoal, dict):
                print(
                    f"Plan evaluation failed: "
                    f"subgoal {subgoal_number} is invalid."
                )
                return False

            subgoal_name = subgoal.get("name")
            tasks = subgoal.get("tasks")

            if not isinstance(subgoal_name, str) or not subgoal_name.strip():
                print(
                    f"Plan evaluation failed: "
                    f"subgoal {subgoal_number} has no name."
                )
                return False

            if not isinstance(tasks, list) or not tasks:
                print(
                    f"Plan evaluation failed: "
                    f"subgoal '{subgoal_name}' has no tasks."
                )
                return False

            for task_number, task in enumerate(
                tasks,
                start=1,
            ):
                if not isinstance(task, str) or not task.strip():
                    print(
                        f"Plan evaluation failed: "
                        f"subgoal '{subgoal_name}' "
                        f"contains an invalid task at position "
                        f"{task_number}."
                    )
                    return False

        total_subgoals = len(subgoals)
        total_tasks = sum(
            len(subgoal["tasks"])
            for subgoal in subgoals
        )

        print("Plan evaluation complete.")
        print(f"Validated subgoals: {total_subgoals}")
        print(f"Validated tasks: {total_tasks}")
        print("Status: Plan approved for execution.")

        return True