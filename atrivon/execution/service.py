from atrivon.execution.actions import (
    ActionRequest,
    ActionResult,
    ActionStatus,
)
from atrivon.execution.registry import (
    CapabilityRegistry,
)


class CapabilityExecutionService:
    """
    Central execution gateway for Atrivon's capabilities.

    The service is responsible for:

    - Receiving ActionRequests
    - Resolving the correct Capability
    - Executing the ActionRequest
    - Returning a structured ActionResult
    - Converting execution exceptions into safe failures

    The service does not decide WHAT Atrivon should do.

    The intelligence layer creates the ActionRequest.

    The service is responsible only for safely routing
    the request to the appropriate execution capability.
    """

    def __init__(
        self,
        registry: CapabilityRegistry,
    ):
        if not isinstance(
            registry,
            CapabilityRegistry,
        ):
            raise TypeError(
                "CapabilityExecutionService requires "
                "a CapabilityRegistry."
            )

        self.registry = registry

    def can_execute(
        self,
        request: ActionRequest,
    ) -> bool:
        """
        Determine whether at least one registered capability
        can handle the ActionRequest.
        """

        if not isinstance(
            request,
            ActionRequest,
        ):
            raise TypeError(
                "can_execute() requires an ActionRequest."
            )

        return bool(
            self.registry.find_for_action(
                request
            )
        )

    def execute(
        self,
        request: ActionRequest,
    ) -> ActionResult:
        """
        Resolve and execute an ActionRequest.

        The service:

        1. Validates the request.
        2. Resolves the appropriate capability.
        3. Executes the action.
        4. Returns the capability's ActionResult.

        Resolution or execution errors are converted into
        structured failed ActionResults.
        """

        if not isinstance(
            request,
            ActionRequest,
        ):
            raise TypeError(
                "execute() requires an ActionRequest."
            )

        if not self.can_execute(
            request
        ):
            return ActionResult(
                action_id=request.id,
                status=ActionStatus.FAILED,
                error=(
                    "No registered capability can "
                    "handle this action."
                ),
            )

        try:
            capability = (
                self.registry.resolve(
                    request
                )
            )

        except Exception as error:
            return ActionResult(
                action_id=request.id,
                status=ActionStatus.FAILED,
                error=str(
                    error
                ),
            )

        try:
            result = capability.execute(
                request
            )

        except Exception as error:
            return ActionResult(
                action_id=request.id,
                status=ActionStatus.FAILED,
                error=(
                    f"Capability '{capability.name}' "
                    f"failed during execution: "
                    f"{error}"
                ),
                metadata={
                    "capability": (
                        capability.name
                    ),
                },
            )

        if not isinstance(
            result,
            ActionResult,
        ):
            return ActionResult(
                action_id=request.id,
                status=ActionStatus.FAILED,
                error=(
                    f"Capability '{capability.name}' "
                    "returned an invalid execution result."
                ),
                metadata={
                    "capability": (
                        capability.name
                    ),
                },
            )

        result.metadata.setdefault(
            "capability",
            capability.name,
        )

        return result