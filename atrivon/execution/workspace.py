from pathlib import Path

from atrivon.execution.actions import (
    ActionRequest,
    ActionResult,
    ActionStatus,
)
from atrivon.execution.capabilities import (
    Capability,
)


class WorkspaceCapability(Capability):
    """
    Controlled local workspace capability.

    This capability allows Atrivon to perform safe file and
    directory operations inside one configured workspace root.

    Supported actions:

    - workspace.create_file
    - workspace.read_file
    - workspace.update_file
    - workspace.create_directory
    - workspace.list_directory

    Paths outside the configured workspace root are rejected.
    """

    @property
    def name(
        self,
    ) -> str:
        return "workspace.local"

    @property
    def supported_action_types(
        self,
    ) -> tuple[str, ...]:
        return (
            "workspace.create_file",
            "workspace.read_file",
            "workspace.update_file",
            "workspace.create_directory",
            "workspace.list_directory",
        )

    def __init__(
        self,
        workspace_root: str | Path,
    ):
        self.workspace_root = (
            Path(workspace_root)
            .resolve()
        )

        self.workspace_root.mkdir(
            parents=True,
            exist_ok=True,
        )

    def execute(
        self,
        request: ActionRequest,
    ) -> ActionResult:
        """
        Execute a supported workspace action.
        """

        if not self.can_handle(
            request
        ):
            return ActionResult(
                action_id=request.id,
                status=ActionStatus.FAILED,
                error=(
                    f"Unsupported workspace action: "
                    f"{request.action_type}"
                ),
            )

        try:
            target_path = (
                self._resolve_safe_path(
                    request.target
                )
            )

            if (
                request.action_type
                == "workspace.create_file"
            ):
                return self._create_file(
                    request,
                    target_path,
                )

            if (
                request.action_type
                == "workspace.read_file"
            ):
                return self._read_file(
                    request,
                    target_path,
                )

            if (
                request.action_type
                == "workspace.update_file"
            ):
                return self._update_file(
                    request,
                    target_path,
                )

            if (
                request.action_type
                == "workspace.create_directory"
            ):
                return self._create_directory(
                    request,
                    target_path,
                )

            if (
                request.action_type
                == "workspace.list_directory"
            ):
                return self._list_directory(
                    request,
                    target_path,
                )

            return ActionResult(
                action_id=request.id,
                status=ActionStatus.FAILED,
                error=(
                    "Workspace action was not recognized."
                ),
            )

        except Exception as error:
            return ActionResult(
                action_id=request.id,
                status=ActionStatus.FAILED,
                error=str(error),
            )

    def _resolve_safe_path(
        self,
        target: str,
    ) -> Path:
        """
        Resolve a path and ensure it remains inside
        the configured workspace root.
        """

        if not target.strip():
            raise ValueError(
                "Workspace target cannot be empty."
            )

        candidate = (
            self.workspace_root
            / target
        ).resolve()

        try:
            candidate.relative_to(
                self.workspace_root
            )

        except ValueError as error:
            raise ValueError(
                "Workspace action attempted to access "
                "a path outside the workspace root."
            ) from error

        return candidate

    def _create_file(
        self,
        request: ActionRequest,
        target_path: Path,
    ) -> ActionResult:
        """
        Create a new file.
        """

        if target_path.exists():
            return ActionResult(
                action_id=request.id,
                status=ActionStatus.FAILED,
                error=(
                    "File already exists."
                ),
            )

        content = request.parameters.get(
            "content",
            "",
        )

        if not isinstance(
            content,
            str,
        ):
            return ActionResult(
                action_id=request.id,
                status=ActionStatus.FAILED,
                error=(
                    "File content must be a string."
                ),
            )

        target_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        target_path.write_text(
            content,
            encoding="utf-8",
        )

        return ActionResult(
            action_id=request.id,
            status=ActionStatus.SUCCEEDED,
            output={
                "path": str(
                    target_path
                ),
                "created": True,
            },
        )

    def _read_file(
        self,
        request: ActionRequest,
        target_path: Path,
    ) -> ActionResult:
        """
        Read an existing file.
        """

        if not target_path.exists():
            return ActionResult(
                action_id=request.id,
                status=ActionStatus.FAILED,
                error=(
                    "File does not exist."
                ),
            )

        if not target_path.is_file():
            return ActionResult(
                action_id=request.id,
                status=ActionStatus.FAILED,
                error=(
                    "Target is not a file."
                ),
            )

        content = target_path.read_text(
            encoding="utf-8"
        )

        return ActionResult(
            action_id=request.id,
            status=ActionStatus.SUCCEEDED,
            output={
                "path": str(
                    target_path
                ),
                "content": content,
            },
        )

    def _update_file(
        self,
        request: ActionRequest,
        target_path: Path,
    ) -> ActionResult:
        """
        Update or replace an existing file.
        """

        if not target_path.exists():
            return ActionResult(
                action_id=request.id,
                status=ActionStatus.FAILED,
                error=(
                    "File does not exist."
                ),
            )

        if not target_path.is_file():
            return ActionResult(
                action_id=request.id,
                status=ActionStatus.FAILED,
                error=(
                    "Target is not a file."
                ),
            )

        content = request.parameters.get(
            "content"
        )

        if not isinstance(
            content,
            str,
        ):
            return ActionResult(
                action_id=request.id,
                status=ActionStatus.FAILED,
                error=(
                    "Updated file content "
                    "must be a string."
                ),
            )

        target_path.write_text(
            content,
            encoding="utf-8",
        )

        return ActionResult(
            action_id=request.id,
            status=ActionStatus.SUCCEEDED,
            output={
                "path": str(
                    target_path
                ),
                "updated": True,
            },
        )

    def _create_directory(
        self,
        request: ActionRequest,
        target_path: Path,
    ) -> ActionResult:
        """
        Create a directory.
        """

        if target_path.exists():
            return ActionResult(
                action_id=request.id,
                status=ActionStatus.FAILED,
                error=(
                    "Directory already exists."
                ),
            )

        target_path.mkdir(
            parents=True,
            exist_ok=True,
        )

        return ActionResult(
            action_id=request.id,
            status=ActionStatus.SUCCEEDED,
            output={
                "path": str(
                    target_path
                ),
                "created": True,
            },
        )

    def _list_directory(
        self,
        request: ActionRequest,
        target_path: Path,
    ) -> ActionResult:
        """
        List the contents of a directory.
        """

        if not target_path.exists():
            return ActionResult(
                action_id=request.id,
                status=ActionStatus.FAILED,
                error=(
                    "Directory does not exist."
                ),
            )

        if not target_path.is_dir():
            return ActionResult(
                action_id=request.id,
                status=ActionStatus.FAILED,
                error=(
                    "Target is not a directory."
                ),
            )

        entries = [
            {
                "name": entry.name,
                "type": (
                    "directory"
                    if entry.is_dir()
                    else "file"
                ),
            }
            for entry in sorted(
                target_path.iterdir(),
                key=lambda item: item.name.lower(),
            )
        ]

        return ActionResult(
            action_id=request.id,
            status=ActionStatus.SUCCEEDED,
            output={
                "path": str(
                    target_path
                ),
                "entries": entries,
            },
        )