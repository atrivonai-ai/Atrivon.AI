from kernel.executor import Executor
from kernel.planner import Planner
from kernel.progress import ProgressTracker
from kernel.reasoner import Reasoner
from kernel.state import GoalState


class AtrivonKernel:
    """
    The central intelligence of Atrivon.

    Every goal enters the system through the Kernel.
    The Kernel coordinates Atrivon's intelligence modules
    and manages the lifecycle of the goal from planning
    through execution and progress tracking.

    The Kernel currently coordinates:
    - Planner
    - Reasoner
    - Executor
    - Progress Tracker
    """

    def __init__(self):
        self.planner = Planner()
        self.reasoner = Reasoner()
        self.executor = Executor()
        self.progress_tracker = ProgressTracker()

        self.current_goal = None
        self.current_plan = None
        self.current_execution_result = None
        self.current_progress = None
        self.current_state = None

        print("Atrivon Kernel initialized.")

    def process_goal(self, goal):
        """
        Process a user goal through Atrivon's core pipeline.

        Lifecycle:

        PLANNED
            ↓
        APPROVED
            ↓
        IN_PROGRESS
            ↓
        EXECUTION
            ↓
        PROGRESS TRACKING
            ↓
        COMPLETED

        If planning or execution fails, the goal moves
        to an appropriate failure state.
        """

        goal = goal.strip()

        if not goal:
            print("\nA goal is required.")
            return None

        self.current_goal = goal
        self.current_plan = None
        self.current_execution_result = None
        self.current_progress = None
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
            print(
                "Execution blocked: "
                "the plan needs revision."
            )

            return None

        self.current_state = GoalState.APPROVED

        print(
            f"Goal state: {self.current_state.value}"
        )
        print("Plan approved.")

        self.current_state = GoalState.IN_PROGRESS

        print(
            f"Goal state: {self.current_state.value}"
        )
        print("Beginning execution...")

        execution_result = self.executor.execute_plan(plan)

        self.current_execution_result = execution_result

        execution_status = execution_result.get(
            "status"
        )

        self.current_progress = (
            self.progress_tracker.calculate_progress(
                execution_result
            )
        )

        self.progress_tracker.display_progress(
            self.current_progress
        )

        if execution_status == "completed":
            self.current_state = GoalState.COMPLETED

            print(
                f"\nGoal state: {self.current_state.value}"
            )
            print("Goal completed successfully.")

        else:
            self.current_state = GoalState.BLOCKED

            print(
                f"\nGoal state: {self.current_state.value}"
            )
            print(
                "Execution could not be completed."
            )

        return execution_result

    def get_current_state(self):
        """
        Return the current state of the active goal.
        """

        if self.current_state is None:
            return None

        return self.current_state.value

    def get_current_goal(self):
        """
        Return the current goal.
        """

        return self.current_goal

    def get_current_plan(self):
        """
        Return the current structured plan.
        """

        return self.current_plan

    def get_current_execution_result(self):
        """
        Return the latest execution result, including
        subgoal and task-level execution states.
        """

        return self.current_execution_result

    def get_current_progress(self):
        """
        Return the latest progress report for the active goal.
        """

        return self.current_progress