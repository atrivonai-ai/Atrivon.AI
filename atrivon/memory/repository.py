from abc import ABC, abstractmethod

from atrivon.domain.memory import MemoryRecord


class MemoryRepository(ABC):
    """
    Abstract contract for Atrivon's persistent memory storage.

    The repository defines what the Memory system can do,
    without defining how or where the data is stored.

    Future implementations may use:
    - JSON
    - SQLite
    - PostgreSQL
    - Distributed databases
    - Cloud storage
    """

    @abstractmethod
    def save(
        self,
        record: MemoryRecord,
    ) -> MemoryRecord:
        """
        Save a new memory record or update an existing record.
        """
        raise NotImplementedError

    @abstractmethod
    def get(
        self,
        record_id: str,
    ) -> MemoryRecord | None:
        """
        Retrieve a memory record by ID.
        """
        raise NotImplementedError

    @abstractmethod
    def list_records(
        self,
        memory_type: str | None = None,
        owner_id: str | None = None,
        source_id: str | None = None,
    ) -> list[MemoryRecord]:
        """
        List memory records with optional filters.
        """
        raise NotImplementedError

    @abstractmethod
    def delete(
        self,
        record_id: str,
    ) -> bool:
        """
        Delete a memory record by ID.

        Returns:
            True if the record existed and was deleted.
            False otherwise.
        """
        raise NotImplementedError