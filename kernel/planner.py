class Planner:
    """
    The Planner is responsible for breaking a goal
    into clear, executable steps.
    """

    def __init__(self):
        print("Planner module loaded.")

    def create_plan(self, goal):
        print(f"\nCreating plan for goal: {goal}")

        plan = [
            "Understand the goal",
            "Break the work into tasks",
            "Prioritize the tasks",
            "Prepare for execution"
        ]

        print("\nPlan Created:")

        for step_number, step in enumerate(plan, start=1):
            print(f"{step_number}. {step}")

        return plan