class Planner:
    """
    The Planner is responsible for transforming a user goal
    into a structured hierarchy of subgoals and tasks.

    The current planning layer uses deterministic planning rules
    as a foundation for more advanced goal decomposition.
    """

    def __init__(self):
        print("Planner module loaded.")

    def create_plan(self, goal):
        """
        Create a structured plan for the user's goal.
        """

        original_goal = goal.strip()
        normalized_goal = original_goal.lower()

        print(f"\nCreating plan for goal: {original_goal}")

        plan = self._build_plan(
            original_goal=original_goal,
            normalized_goal=normalized_goal,
        )

        self._display_plan(plan)

        return plan

    def _build_plan(self, original_goal, normalized_goal):
        """
        Build a structured plan containing subgoals and tasks.
        """

        if any(
            keyword in normalized_goal
            for keyword in ["website", "web app", "web application"]
        ):
            return {
                "goal": original_goal,
                "subgoals": [
                    {
                        "name": "Define the website objective",
                        "tasks": [
                            "Understand the website requirements",
                            "Define the target users",
                            "Define the desired outcomes",
                        ],
                    },
                    {
                        "name": "Design the website",
                        "tasks": [
                            "Design the website structure",
                            "Design the user experience",
                            "Define the required functionality",
                        ],
                    },
                    {
                        "name": "Build the website",
                        "tasks": [
                            "Implement the required functionality",
                            "Integrate required systems",
                            "Prepare the website for testing",
                        ],
                    },
                    {
                        "name": "Launch and improve the website",
                        "tasks": [
                            "Test the website",
                            "Deploy the website",
                            "Monitor performance and improve the experience",
                        ],
                    },
                ],
            }

        if any(
            keyword in normalized_goal
            for keyword in [
                "online business",
                "business",
                "startup",
                "company",
            ]
        ):
            return {
                "goal": original_goal,
                "subgoals": [
                    {
                        "name": "Validate the business opportunity",
                        "tasks": [
                            "Understand the business objective",
                            "Identify the target market",
                            "Identify customer needs",
                            "Analyze the competitive landscape",
                        ],
                    },
                    {
                        "name": "Design the business model",
                        "tasks": [
                            "Define the value proposition",
                            "Define the products or services",
                            "Define the pricing model",
                            "Define the operating model",
                        ],
                    },
                    {
                        "name": "Build the business foundation",
                        "tasks": [
                            "Define the required systems",
                            "Prepare the operational structure",
                            "Build the required technology",
                            "Prepare the launch strategy",
                        ],
                    },
                    {
                        "name": "Launch and improve the business",
                        "tasks": [
                            "Launch the business",
                            "Measure the results",
                            "Identify problems and opportunities",
                            "Improve based on real-world feedback",
                        ],
                    },
                ],
            }

        if any(
            keyword in normalized_goal
            for keyword in [
                "analyze",
                "analysis",
                "research",
            ]
        ):
            return {
                "goal": original_goal,
                "subgoals": [
                    {
                        "name": "Define the research objective",
                        "tasks": [
                            "Understand the analysis objective",
                            "Identify the required information",
                            "Define the desired outcome",
                        ],
                    },
                    {
                        "name": "Collect and organize information",
                        "tasks": [
                            "Collect relevant information",
                            "Validate the information",
                            "Organize the information",
                        ],
                    },
                    {
                        "name": "Analyze the information",
                        "tasks": [
                            "Identify important patterns",
                            "Identify risks and opportunities",
                            "Form conclusions",
                        ],
                    },
                    {
                        "name": "Produce recommendations",
                        "tasks": [
                            "Summarize the findings",
                            "Develop recommendations",
                            "Present the final analysis",
                        ],
                    },
                ],
            }

        if any(
            keyword in normalized_goal
            for keyword in [
                "learn",
                "study",
                "understand",
                "teach",
            ]
        ):
            return {
                "goal": original_goal,
                "subgoals": [
                    {
                        "name": "Define the learning objective",
                        "tasks": [
                            "Understand the subject",
                            "Define the learning outcome",
                            "Assess the current level of knowledge",
                        ],
                    },
                    {
                        "name": "Build the learning path",
                        "tasks": [
                            "Identify the key concepts",
                            "Organize the concepts in a logical sequence",
                            "Create a structured learning plan",
                        ],
                    },
                    {
                        "name": "Practice and apply knowledge",
                        "tasks": [
                            "Study the key concepts",
                            "Practice the concepts",
                            "Apply the knowledge to real problems",
                        ],
                    },
                    {
                        "name": "Evaluate and improve",
                        "tasks": [
                            "Evaluate understanding",
                            "Identify knowledge gaps",
                            "Improve weak areas",
                        ],
                    },
                ],
            }

        return {
            "goal": original_goal,
            "subgoals": [
                {
                    "name": "Understand the goal",
                    "tasks": [
                        "Clarify the desired outcome",
                        "Identify the requirements",
                        "Identify constraints and assumptions",
                    ],
                },
                {
                    "name": "Design the approach",
                    "tasks": [
                        "Break the goal into smaller objectives",
                        "Identify dependencies",
                        "Determine the order of work",
                    ],
                },
                {
                    "name": "Prepare for execution",
                    "tasks": [
                        "Identify required resources",
                        "Identify potential risks",
                        "Prepare the plan for reasoning and execution",
                    ],
                },
            ],
        }

    def _display_plan(self, plan):
        """
        Display the structured plan in a readable format.
        """

        print("\nPlan Created:")
        print(f"Goal: {plan['goal']}")

        for subgoal_number, subgoal in enumerate(
            plan["subgoals"],
            start=1,
        ):
            print(f"\n{subgoal_number}. {subgoal['name']}")

            for task_number, task in enumerate(
                subgoal["tasks"],
                start=1,
            ):
                print(
                    f"   {subgoal_number}.{task_number}. {task}"
                )