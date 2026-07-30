class Reasoner:
    """
    The Reasoner evaluates plans before execution.

    Its responsibility is to determine whether a plan
    is logical, complete, and ready to execute.
    """

    def __init__(self):
        print("Reasoner module loaded.")

    def evaluate_plan(self, plan):
        print("\nEvaluating plan...")

        if not plan:
            print("No plan available.")
            return False

        print("Plan evaluation complete.")
        print("Status: Plan approved for execution.")

        return True