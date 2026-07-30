from kernel.planner import Planner
from kernel.reasoner import Reasoner


class AtrivonKernel:
    """
    The central intelligence of Atrivon.

    Every goal enters the system through the Kernel.
    The Kernel coordinates Atrivon's intelligence modules.
    """

    def __init__(self):
        self.planner = Planner()
        self.reasoner = Reasoner()

        print("Atrivon Kernel initialized.")

    def process_goal(self, goal):
        goal = goal.strip()

        if not goal:
            print("\nA goal is required.")
            return None

        print(f"\nGoal received: {goal}")
        print("Understanding the goal...")

        plan = self.planner.create_plan(goal)

        print("\nPlan received by the Kernel.")

        plan_approved = self.reasoner.evaluate_plan(plan)

        if not plan_approved:
            print("Execution blocked: the plan was not approved.")
            return None

        print("Ready to execute.")

        return plan
