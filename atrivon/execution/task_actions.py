from typing import Any

from atrivon.domain.models import Task
from atrivon.execution.actions import (
    ActionRequest,
)


class TaskActionResolver:
    """
    Converts a canonical Atrivon Task into an ActionRequest
    when the Task explicitly declares a real-world action.

    A Task remains a planning/execution domain object.

    The ActionRequest represents the concrete action Atrivon
    wants a Capability to perform.

    This resolver does not execute anything.
    """

    ACTION_METADATA_KEY = "action"

    def has_action(
        self,
        task: Task,
    ) -> bool:
        """
        Determine whether a Task explicitly defines
        a real-world action.
        """

        if not isinstance(
            task,
            Task,
        ):
            raise TypeError(
                "has_action() requires a Task object."
            )

        action_data = (
            task.metadata.get(
                self.ACTION_METADATA_KEY
            )
        )

        return isinstance(
            action_data,
            dict,
        )

    def resolve(
        self,
        task: Task,
    ) -> ActionRequest | None:
        """
        Convert a Task's action metadata into an ActionRequest.

        Returns:
            ActionRequest when the Task defines a valid action.
            None when the Task has no action metadata.
        """

        if not isinstance(
            task,
            Task,
        ):
            raise TypeError(
                "resolve() requires a Task object."
            )

        action_data = (
            task.metadata.get(
                self.ACTION_METADATA_KEY
            )
        )

        if action_data is None:
            return None

        if not isinstance(
            action_data,
            dict,
        ):
            raise ValueError(
                "Task action metadata must be a dictionary."
            )

        action_type = action_data.get(
            "action_type"
        )

        target = action_data.get(
            "target"
        )

        parameters = action_data.get(
            "parameters",
            {},
        )

        metadata = action_data.get(
            "metadata",
            {},
        )

        if not isinstance(
            action_type,
            str,
        ) or not action_type.strip():
            raise ValueError(
                "Task action metadata requires "
                "a non-empty 'action_type'."
            )

        if not isinstance(
            target,
            str,
        ) or not target.strip():
            raise ValueError(
                "Task action metadata requires "
                "a non-empty 'target'."
            )

        if not isinstance(
            parameters,
            dict,
        ):
            raise TypeError(
                "Task action 'parameters' must be a dictionary."
            )

        if not isinstance(
            metadata,
            dict,
        ):
            raise TypeError(
                "Task action 'metadata' must be a dictionary."
            )

        action_metadata = dict(
            metadata
        )

        action_metadata.setdefault(
            "task_id",
            task.id,
        )

        action_metadata.setdefault(
            "task_title",
            task.title,
        )

        return ActionRequest(
            action_type=action_type,
            target=target,
            parameters=parameters,
            metadata=action_metadata,
        )

    def build_action_metadata(
        self,
        action_type: str,
        target: str,
        parameters: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Build a normalized Task action metadata structure.

        This helper is useful when the Planner or another
        intelligence component needs to create a Task that
        explicitly represents a real-world action.
        """

        if not action_type.strip():
            raise ValueError(
                "Action type cannot be empty."
            )

        if not target.strip():
            raise ValueError(
                "Action target cannot be empty."
            )

        return {
            self.ACTION_METADATA_KEY: {
                "action_type": action_type,
                "target": target,
                "parameters": (
                    parameters
                    if parameters is not None
                    else {}
                ),
                "metadata": (
                    metadata
                    if metadata is not None
                    else {}
                ),
            }
        }