from dataclasses import dataclass
from typing import Any

from atrivon.domain.models import (
    Goal,
    Plan,
)
from atrivon.domain.states import (
    GoalState,
    PlanState,
)


@dataclass(frozen=True)
class PlanRevisionResult:
    """
    Result of creating a revised Plan.
    """

    previous_plan_id: str
    new_plan_id: str
    previous_version: int
    new_version: int
    reason: str


@dataclass(frozen=True)
class AdaptiveReplanningResult:
    """
    Result of an adaptive replanning operation.
    """

    analysis: dict[str, Any]
    revision: PlanRevisionResult
    revised_plan: Plan


class PlanRevisionService:
    """
    Manages safe Plan revision and succession.

    The service does not decide how a new strategy should be created.

    Instead, the Planner or Reasoner provides a new Plan,
    and this service manages:

    - Plan versioning
    - Plan succession
    - Plan lifecycle transitions
    - Goal active-plan updates
    - Revision metadata
    """

    def revise_plan(
        self,
        goal: Goal,
        current_plan: Plan,
        revised_plan: Plan,
        reason: str,
    ) -> PlanRevisionResult:
        """
        Replace the current Plan with a revised Plan.

        The previous Plan becomes SUPERSEDED.

        The revised Plan:
        - Gets the next version number.
        - References the previous Plan.
        - Records the revision reason.
        - Becomes ACTIVE.
        - Becomes the Goal's active Plan.
        """

        if not isinstance(
            goal,
            Goal,
        ):
            raise TypeError(
                "goal must be a Goal object."
            )

        if not isinstance(
            current_plan,
            Plan,
        ):
            raise TypeError(
                "current_plan must be a Plan object."
            )

        if not isinstance(
            revised_plan,
            Plan,
        ):
            raise TypeError(
                "revised_plan must be a Plan object."
            )

        reason = reason.strip()

        if not reason:
            raise ValueError(
                "A revision reason is required."
            )

        if current_plan.goal_id != goal.id:
            raise ValueError(
                "Current Plan does not belong "
                "to the provided Goal."
            )

        if revised_plan.goal_id != goal.id:
            raise ValueError(
                "Revised Plan does not belong "
                "to the provided Goal."
            )

        if current_plan.id == revised_plan.id:
            raise ValueError(
                "A Plan revision must create "
                "a new Plan object."
            )

        if current_plan.state == (
            PlanState.SUPERSEDED
        ):
            raise ValueError(
                "The current Plan is already superseded."
            )

        next_version = (
            current_plan.version + 1
        )

        revised_plan.version = (
            next_version
        )

        revised_plan.supersedes_plan_id = (
            current_plan.id
        )

        revised_plan.revision_reason = (
            reason
        )

        current_plan.update_state(
            PlanState.SUPERSEDED
        )

        revised_plan.update_state(
            PlanState.ACTIVE
        )

        goal.add_plan(
            revised_plan
        )

        if goal.state in {
            GoalState.BLOCKED,
            GoalState.NEEDS_REVISION,
        }:
            goal.update_state(
                GoalState.IN_PROGRESS
            )

        return PlanRevisionResult(
            previous_plan_id=current_plan.id,
            new_plan_id=revised_plan.id,
            previous_version=current_plan.version,
            new_version=revised_plan.version,
            reason=reason,
        )

    def can_revise(
        self,
        goal: Goal,
        current_plan: Plan,
    ) -> bool:
        """
        Determine whether a Goal and Plan are eligible
        for revision.
        """

        if not isinstance(
            goal,
            Goal,
        ):
            return False

        if not isinstance(
            current_plan,
            Plan,
        ):
            return False

        if current_plan.goal_id != goal.id:
            return False

        if current_plan.state in {
            PlanState.COMPLETED,
            PlanState.SUPERSEDED,
        }:
            return False

        return goal.state in {
            GoalState.BLOCKED,
            GoalState.NEEDS_REVISION,
            GoalState.IN_PROGRESS,
        }

    def get_revision_metadata(
        self,
        plan: Plan,
    ) -> dict[str, Any]:
        """
        Return structured revision metadata for a Plan.
        """

        return {
            "plan_id": plan.id,
            "version": plan.version,
            "supersedes_plan_id": (
                plan.supersedes_plan_id
            ),
            "revision_reason": (
                plan.revision_reason
            ),
            "state": plan.state.value,
        }


class AdaptiveReplanner:
    """
    Coordinates the first adaptive replanning loop.

    The workflow is:

    Execution Result
        ↓
    Reasoner analyzes the problem
        ↓
    Planner creates a revised strategy
        ↓
    Reasoner validates the revised strategy
        ↓
    PlanRevisionService activates the new Plan
    """

    def __init__(
        self,
        planner,
        reasoner,
        revision_service: PlanRevisionService | None = None,
    ):
        if not hasattr(
            planner,
            "create_revised_plan",
        ):
            raise TypeError(
                "planner must provide "
                "create_revised_plan()."
            )

        if not hasattr(
            reasoner,
            "analyze_execution_result",
        ):
            raise TypeError(
                "reasoner must provide "
                "analyze_execution_result()."
            )

        if not hasattr(
            reasoner,
            "evaluate_plan",
        ):
            raise TypeError(
                "reasoner must provide "
                "evaluate_plan()."
            )

        self.planner = planner

        self.reasoner = reasoner

        self.revision_service = (
            revision_service
            or PlanRevisionService()
        )

    def can_replan(
        self,
        goal: Goal,
        current_plan: Plan,
        execution_result: dict[str, Any],
    ) -> bool:
        """
        Determine whether the current execution result
        requires adaptive replanning.
        """

        if not self.revision_service.can_revise(
            goal,
            current_plan,
        ):
            return False

        analysis = (
            self.reasoner.analyze_execution_result(
                current_plan,
                execution_result,
            )
        )

        return bool(
            analysis.get(
                "needs_revision"
            )
        )

    def replan(
        self,
        goal: Goal,
        current_plan: Plan,
        execution_result: dict[str, Any],
    ) -> AdaptiveReplanningResult:
        """
        Analyze an execution problem, create a revised Plan,
        validate it, and activate it.
        """

        if not self.revision_service.can_revise(
            goal,
            current_plan,
        ):
            raise ValueError(
                "The current Goal and Plan are not eligible "
                "for adaptive replanning."
            )

        analysis = (
            self.reasoner.analyze_execution_result(
                current_plan,
                execution_result,
            )
        )

        if not analysis.get(
            "needs_revision"
        ):
            raise ValueError(
                "The execution result does not require "
                "adaptive replanning."
            )

        revised_plan = (
            self.planner.create_revised_plan(
                goal,
                current_plan,
                analysis,
            )
        )

        revised_plan_is_valid = (
            self.reasoner.evaluate_plan(
                revised_plan
            )
        )

        if not revised_plan_is_valid:
            raise ValueError(
                "The revised Plan failed Reasoner validation."
            )

        revision = (
            self.revision_service.revise_plan(
                goal=goal,
                current_plan=current_plan,
                revised_plan=revised_plan,
                reason=analysis["reason"],
            )
        )

        return AdaptiveReplanningResult(
            analysis=analysis,
            revision=revision,
            revised_plan=revised_plan,
        )