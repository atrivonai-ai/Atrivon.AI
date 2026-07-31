from dataclasses import dataclass
from typing import Iterable

from atrivon.domain.models import Plan, Task
from atrivon.domain.states import TaskState


@dataclass(frozen=True)
class DependencyValidationResult:
    """
    Result of validating task dependencies.
    """

    valid: bool
    errors: tuple[str, ...] = ()


class DependencyResolver:
    """
    Resolves task dependencies for Atrivon's execution system.

    Responsibilities:
    - Validate dependency references.
    - Detect circular dependencies.
    - Determine which tasks are ready to execute.
    - Determine which tasks are blocked by unfinished dependencies.

    The resolver does not execute tasks.
    It only determines execution readiness.
    """

    def validate_plan(
        self,
        plan: Plan,
    ) -> DependencyValidationResult:
        """
        Validate all task dependencies in a Plan.
        """

        if not isinstance(
            plan,
            Plan,
        ):
            raise TypeError(
                "DependencyResolver.validate_plan() "
                "requires a Plan object."
            )

        tasks = self._collect_tasks(
            plan
        )

        task_ids = {
            task.id
            for task in tasks
        }

        errors: list[str] = []

        for task in tasks:
            for dependency_id in (
                task.dependencies
            ):
                if dependency_id not in task_ids:
                    errors.append(
                        f"Task '{task.title}' "
                        f"references missing dependency "
                        f"'{dependency_id}'."
                    )

        cycle = self._find_cycle(
            tasks
        )

        if cycle:
            cycle_text = " -> ".join(
                cycle
            )

            errors.append(
                "Circular task dependency detected: "
                f"{cycle_text}"
            )

        return DependencyValidationResult(
            valid=not errors,
            errors=tuple(
                errors
            ),
        )

    def get_ready_tasks(
        self,
        plan: Plan,
    ) -> list[Task]:
        """
        Return tasks whose dependencies are all completed
        and which are eligible for execution.
        """

        validation = self.validate_plan(
            plan
        )

        if not validation.valid:
            raise ValueError(
                "Plan dependency validation failed: "
                + " | ".join(
                    validation.errors
                )
            )

        tasks = self._collect_tasks(
            plan
        )

        completed_task_ids = {
            task.id
            for task in tasks
            if task.state
            == TaskState.COMPLETED
        }

        ready_tasks = []

        for task in tasks:
            if (
                task.state
                == TaskState.COMPLETED
            ):
                continue

            if (
                task.state
                in {
                    TaskState.BLOCKED,
                    TaskState.FAILED,
                    TaskState.REQUIRES_INPUT,
                    TaskState.NEEDS_REVISION,
                }
            ):
                continue

            dependencies_satisfied = all(
                dependency_id
                in completed_task_ids
                for dependency_id
                in task.dependencies
            )

            if dependencies_satisfied:
                ready_tasks.append(
                    task
                )

        return ready_tasks

    def get_blocked_tasks(
        self,
        plan: Plan,
    ) -> list[Task]:
        """
        Return tasks that cannot execute yet because
        one or more dependencies are incomplete.
        """

        validation = self.validate_plan(
            plan
        )

        if not validation.valid:
            raise ValueError(
                "Plan dependency validation failed: "
                + " | ".join(
                    validation.errors
                )
            )

        tasks = self._collect_tasks(
            plan
        )

        completed_task_ids = {
            task.id
            for task in tasks
            if task.state
            == TaskState.COMPLETED
        }

        blocked_tasks = []

        for task in tasks:
            if (
                task.state
                == TaskState.COMPLETED
            ):
                continue

            if (
                task.state
                in {
                    TaskState.BLOCKED,
                    TaskState.FAILED,
                    TaskState.REQUIRES_INPUT,
                    TaskState.NEEDS_REVISION,
                }
            ):
                continue

            if not all(
                dependency_id
                in completed_task_ids
                for dependency_id in task.dependencies
            ):
                blocked_tasks.append(
                    task
                )

        return blocked_tasks

    def get_unsatisfied_dependencies(
        self,
        task: Task,
        plan: Plan,
    ) -> list[str]:
        """
        Return the dependency IDs that are not yet completed.
        """

        if not isinstance(
            task,
            Task,
        ):
            raise TypeError(
                "get_unsatisfied_dependencies() "
                "requires a Task object."
            )

        tasks = self._collect_tasks(
            plan
        )

        completed_task_ids = {
            current_task.id
            for current_task in tasks
            if current_task.state
            == TaskState.COMPLETED
        }

        return [
            dependency_id
            for dependency_id
            in task.dependencies
            if dependency_id
            not in completed_task_ids
        ]

    def _collect_tasks(
        self,
        plan: Plan,
    ) -> list[Task]:
        """
        Collect all Tasks from a Plan.
        """

        return [
            task
            for subgoal in plan.subgoals
            for task in subgoal.tasks
        ]

    def _find_cycle(
        self,
        tasks: Iterable[Task],
    ) -> list[str] | None:
        """
        Detect a circular dependency chain.

        Returns:
            A dependency cycle if one exists.
            Otherwise None.
        """

        task_map = {
            task.id: task
            for task in tasks
        }

        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(
            task_id: str,
            path: list[str],
        ) -> list[str] | None:
            if task_id in visiting:
                cycle_start = path.index(
                    task_id
                )

                return (
                    path[cycle_start:]
                    + [task_id]
                )

            if task_id in visited:
                return None

            task = task_map.get(
                task_id
            )

            if task is None:
                return None

            visiting.add(
                task_id
            )

            path.append(
                task_id
            )

            for dependency_id in (
                task.dependencies
            ):
                cycle = visit(
                    dependency_id,
                    path,
                )

                if cycle:
                    return cycle

            path.pop()

            visiting.remove(
                task_id
            )

            visited.add(
                task_id
            )

            return None

        for task in tasks:
            cycle = visit(
                task.id,
                [],
            )

            if cycle:
                return cycle

        return None