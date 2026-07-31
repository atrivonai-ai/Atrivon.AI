from typing import Any

from atrivon.domain.memory import MemoryRecord
from atrivon.memory.repository import MemoryRepository


class MemoryService:
    """
    Intelligence-facing service for Atrivon's persistent memory.

    The MemoryService coordinates memory operations without
    exposing storage implementation details to the rest of Atrivon.

    The underlying repository may use JSON, SQLite, PostgreSQL,
    or another persistence technology.
    """

    def __init__(
        self,
        repository: MemoryRepository,
    ):
        if not isinstance(
            repository,
            MemoryRepository,
        ):
            raise TypeError(
                "MemoryService requires a "
                "MemoryRepository implementation."
            )

        self.repository = repository

    def remember(
        self,
        memory_type: str,
        content: dict[str, Any],
        owner_id: str | None = None,
        source_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> MemoryRecord:
        """
        Create and persist a new memory record.
        """

        record = MemoryRecord(
            memory_type=memory_type,
            content=content,
            owner_id=owner_id,
            source_id=source_id,
            metadata=metadata or {},
        )

        return self.repository.save(
            record
        )

    def save(
        self,
        record: MemoryRecord,
    ) -> MemoryRecord:
        """
        Save or update an existing MemoryRecord.
        """

        return self.repository.save(
            record
        )

    def get(
        self,
        record_id: str,
    ) -> MemoryRecord | None:
        """
        Retrieve a memory record by ID.
        """

        return self.repository.get(
            record_id
        )

    def list_records(
        self,
        memory_type: str | None = None,
        owner_id: str | None = None,
        source_id: str | None = None,
    ) -> list[MemoryRecord]:
        """
        Retrieve memory records using optional filters.
        """

        return self.repository.list_records(
            memory_type=memory_type,
            owner_id=owner_id,
            source_id=source_id,
        )

    def delete(
        self,
        record_id: str,
    ) -> bool:
        """
        Delete a memory record by ID.
        """

        return self.repository.delete(
            record_id
        )