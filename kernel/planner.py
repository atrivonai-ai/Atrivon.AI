class Planner:
    """
    The Planner is responsible for transforming a user goal
    into a structured sequence of steps.

    The Planner currently uses a deterministic planning layer.
    This provides a stable foundation for more advanced
    planning intelligence as Atrivon evolves.
    """

    def __init__(self):
        print("Planner module loaded.")

    def create_plan(self, goal):
        """
        Create a plan based on the user's goal.
        """

        normalized_goal = goal.strip().lower()

        print(f"\nCreating plan for goal: {goal}")

        plan = self._build_plan(normalized_goal)

        print("\nPlan Created:")

        for step_number, step in enumerate(plan, start=1):
            print(f"{step_number}. {step}")

        return plan

    def _build_plan(self, goal):
        """
        Build a goal-aware plan using the current planning rules.
        """

        if any(
            keyword in goal
            for keyword in ["website", "web app", "web application"]
        ):
            return [
                "Understand the website requirements",
                "Define the target users and desired outcomes",
                "Design the website structure and user experience",
                "Implement the required functionality",
                "Test the website",
                "Deploy and monitor the website",
            ]

        if any(
            keyword in goal
            for keyword in [
                "online business",
                "business",
                "startup",
                "company",
            ]
        ):
            return [
                "Understand the business objective",
                "Identify the target market and customer needs",
                "Define the business model and value proposition",
                "Design the required products, services, and operations",
                "Build the systems needed to launch",
                "Test the business model",
                "Launch and measure results",
                "Improve based on real-world feedback",
            ]

        if any(
            keyword in goal
            for keyword in [
                "analyze",
                "analysis",
                "analyze this",
                "research",
            ]
        ):
            return [
                "Understand the analysis objective",
                "Identify the required information and data",
                "Collect and organize relevant information",
                "Analyze the available information",
                "Identify patterns, risks, and opportunities",
                "Form conclusions",
                "Present the findings and recommendations",
            ]

        if any(
            keyword in goal
            for keyword in [
                "learn",
                "study",
                "understand",
                "teach",
            ]
        ):
            return [
                "Understand the learning objective",
                "Assess the current level of knowledge",
                "Break the subject into key concepts",
                "Create a structured learning sequence",
                "Practice and apply the knowledge",
                "Evaluate understanding",
                "Identify areas for improvement",
            ]

        return [
            "Understand the goal and desired outcome",
            "Identify the requirements and constraints",
            "Break the goal into smaller tasks",
            "Determine the correct order of execution",
            "Identify risks and dependencies",
            "Prepare the plan for reasoning and execution",
        ]
