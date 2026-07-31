from abc import ABC, abstractmethod

from atrivon.execution.actions import (
    ActionRequest,
    ActionResult,
)


class Capability(ABC):
    """
    Abstract contract for an Atrivon execution capability.

    A Capability defines HOW Atrivon can perform an action.

    Capabilities are intentionally separate from:
    - Goals
    - Plans
    - Tasks
    - Reasoning
    - The Kernel

    Atrivon intelligence decides WHAT should happen.

    Capabilities provide the mechanisms for HOW it can happen.
    """

    @property
    @abstractmethod
    def name(
        self,
    ) -> str:
        """
        Return the unique capability name.
        """

        raise NotImplementedError

    @property
    @abstractmethod
    def supported_action_types(
        self,
    ) -> tuple[str, ...]:
        """
        Return the action types supported by this capability.
        """

        raise NotImplementedError

    def can_handle(
        self,
        request: ActionRequest,
    ) -> bool:
        """
        Determine whether this capability can handle
        a given ActionRequest.
        """

        if not isinstance(
            request,
            ActionRequest,
        ):
            return False

        return (
            request.action_type
            in self.supported_action_types
        )

    @abstractmethod
    def execute(
        self,
        request: ActionRequest,
    ) -> ActionResult:
        """
        Execute an ActionRequest and return an ActionResult.
        """

        raise NotImplementedError