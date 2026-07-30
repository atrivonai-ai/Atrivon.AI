from kernel.planner import Planner
from kernel.reasoner import Reasoner
from kernel.state import GoalState


class AtrivonKernel:
    """
    The central intelligence of Atrivon.

    Every goal enters the system through the Kernel.
    The Kernel coordinates Atrivon's intelligence modules
    and manages the lifecycle state of each goal.
    """

    def __init__(self):
        self.planner = Planner()
        self.reasoner = Reasoner()

        self.current_goal = None
        self.current_plan = None
        self.current_state = None

        print("Atrivon Kernel initialized.")

    def process_goal(self, goal):
        goal = goal.strip()

        if not goal:
            print("\nA goal is required.")
            return None

        self.current_goal = goal
        self.current_state = GoalState.PLANNED

        print(f"\nGoal received: {goal}")
        print(f"Goal state: {self.current_state.value}")
        print("Understanding the goal...")

        plan = self.planner.create_plan(goal)
        self.current_plan = plan

        print("\nPlan received by the Kernel.")

        plan_approved = self.reasoner.evaluate_plan(plan)

        if not plan_approved:
            self.current_state = GoalState.NEEDS_REVISION
            print(
                f"Goal state: {self.current_state.value}"
            )
            print("Execution blocked: the plan needs revision.")
            return None

        self.current_state = GoalState.APPROVED

        print(
            f"Goal state: {self.current_state.value}"
        )
        print("Plan approved.")
        print("Ready for execution.")

        return plan