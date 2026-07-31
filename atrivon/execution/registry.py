from atrivon.execution.actions import (
    ActionRequest,
)
from atrivon.execution.capabilities import (
    Capability,
)


class CapabilityRegistry:
    """
    Registry of available Atrivon execution capabilities.

    The registry is responsible for:
    - Registering capabilities
    - Removing capabilities
    - Discovering capabilities
    - Resolving the best available capability for an action

    The registry does not execute actions itself.

    It only connects ActionRequests to capabilities
    that are able to handle them.
    """

    def __init__(self):
        self._capabilities: dict[
            str,
            Capability,
        ] = {}

    def register(
        self,
        capability: Capability,
    ) -> None:
        """
        Register a Capability.

        Capability names must be unique.
        """

        if not isinstance(
            capability,
            Capability,
        ):
            raise TypeError(
                "Only Capability objects can be registered."
            )

        capability_name = (
            capability.name.strip()
        )

        if not capability_name:
            raise ValueError(
                "Capability name cannot be empty."
            )

        if capability_name in (
            self._capabilities
        ):
            raise ValueError(
                f"Capability '{capability_name}' "
                "is already registered."
            )

        self._capabilities[
            capability_name
        ] = capability

    def unregister(
        self,
        capability_name: str,
    ) -> bool:
        """
        Remove a capability by name.

        Returns:
            True if the capability existed.
            False otherwise.
        """

        if (
            capability_name
            in self._capabilities
        ):
            del self._capabilities[
                capability_name
            ]

            return True

        return False

    def get(
        self,
        capability_name: str,
    ) -> Capability | None:
        """
        Retrieve a capability by name.
        """

        return self._capabilities.get(
            capability_name
        )

    def list_capabilities(
        self,
    ) -> list[Capability]:
        """
        Return all registered capabilities.
        """

        return list(
            self._capabilities.values()
        )

    def find_for_action(
        self,
        request: ActionRequest,
    ) -> list[Capability]:
        """
        Find all capabilities capable of handling
        an ActionRequest.
        """

        if not isinstance(
            request,
            ActionRequest,
        ):
            raise TypeError(
                "find_for_action() requires "
                "an ActionRequest."
            )

        return [
            capability
            for capability
            in self._capabilities.values()
            if capability.can_handle(
                request
            )
        ]

    def resolve(
        self,
        request: ActionRequest,
    ) -> Capability:
        """
        Resolve exactly one capability for an ActionRequest.

        Resolution behavior:

        1. If metadata specifies a capability name,
           use that capability.
        2. Otherwise find capabilities by action type.
        3. If none are found, fail.
        4. If multiple are found, fail rather than
           making an unsafe arbitrary choice.
        """

        if not isinstance(
            request,
            ActionRequest,
        ):
            raise TypeError(
                "resolve() requires an ActionRequest."
            )

        requested_capability = (
            request.metadata.get(
                "capability"
            )
        )

        if requested_capability:
            capability = self.get(
                requested_capability
            )

            if capability is None:
                raise ValueError(
                    f"Requested capability "
                    f"'{requested_capability}' "
                    "is not registered."
                )

            if not capability.can_handle(
                request
            ):
                raise ValueError(
                    f"Capability "
                    f"'{requested_capability}' "
                    "cannot handle action type "
                    f"'{request.action_type}'."
                )

            return capability

        matches = self.find_for_action(
            request
        )

        if not matches:
            raise ValueError(
                "No registered capability can handle "
                f"action type '{request.action_type}'."
            )

        if len(matches) > 1:
            names = [
                capability.name
                for capability in matches
            ]

            raise ValueError(
                "Multiple capabilities can handle "
                f"action type '{request.action_type}': "
                f"{names}. "
                "Specify the capability explicitly."
            )

        return matches[0]