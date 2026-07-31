import json
from datetime import datetime
from pathlib import Path

from atrivon.domain.memory import MemoryRecord
from atrivon.memory.repository import MemoryRepository


class JsonMemoryRepository(MemoryRepository):
    """
    JSON-based implementation of Atrivon's MemoryRepository.

    This is the first persistence backend for Atrivon.

    The rest of Atrivon interacts with the abstract
    MemoryRepository contract, so the storage implementation
    can later be replaced without changing the intelligence layer.
    """

    def __init__(
        self,
        storage_path: str | Path,
    ):
        self.storage_path = Path(
            storage_path
        )

        self.storage_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if not self.storage_path.exists():
            self._write_records([])

    def save(
        self,
        record: MemoryRecord,
    ) -> MemoryRecord:
        """
        Save a new memory record or update an existing record.
        """

        if not isinstance(
            record,
            MemoryRecord,
        ):
            raise TypeError(
                "JsonMemoryRepository.save() "
                "requires a MemoryRecord."
            )

        records = self._load_records()

        record_data = record.to_dict()

        updated = False

        for index, existing_record in enumerate(
            records
        ):
            if (
                existing_record.get("id")
                == record.id
            ):
                records[index] = record_data
                updated = True
                break

        if not updated:
            records.append(
                record_data
            )

        self._write_records(
            records
        )

        return record

    def get(
        self,
        record_id: str,
    ) -> MemoryRecord | None:
        """
        Retrieve a memory record by ID.
        """

        records = self._load_records()

        for record in records:
            if record.get("id") == record_id:
                return self._deserialize(
                    record
                )

        return None

    def list_records(
        self,
        memory_type: str | None = None,
        owner_id: str | None = None,
        source_id: str | None = None,
    ) -> list[MemoryRecord]:
        """
        List memory records with optional filters.
        """

        records = self._load_records()

        matching_records = []

        for record in records:
            if (
                memory_type is not None
                and record.get("memory_type")
                != memory_type
            ):
                continue

            if (
                owner_id is not None
                and record.get("owner_id")
                != owner_id
            ):
                continue

            if (
                source_id is not None
                and record.get("source_id")
                != source_id
            ):
                continue

            matching_records.append(
                self._deserialize(
                    record
                )
            )

        return matching_records

    def delete(
        self,
        record_id: str,
    ) -> bool:
        """
        Delete a memory record by ID.
        """

        records = self._load_records()

        filtered_records = [
            record
            for record in records
            if record.get("id")
            != record_id
        ]

        if len(filtered_records) == len(
            records
        ):
            return False

        self._write_records(
            filtered_records
        )

        return True

    def _load_records(
        self,
    ) -> list[dict]:
        """
        Load raw memory records from JSON storage.
        """

        try:
            content = self.storage_path.read_text(
                encoding="utf-8"
            )

            if not content.strip():
                return []

            data = json.loads(
                content
            )

        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "Atrivon memory storage contains "
                "invalid JSON."
            ) from exc

        if not isinstance(
            data,
            list,
        ):
            raise RuntimeError(
                "Atrivon memory storage must "
                "contain a JSON list."
            )

        return data

    def _write_records(
        self,
        records: list[dict],
    ) -> None:
        """
        Atomically write memory records to JSON storage.

        Writing to a temporary file first reduces the risk
        of leaving a partially written memory file if the
        process is interrupted during a write.
        """

        temporary_path = self.storage_path.with_suffix(
            ".tmp"
        )

        serialized = json.dumps(
            records,
            indent=4,
            ensure_ascii=False,
        )

        temporary_path.write_text(
            serialized,
            encoding="utf-8",
        )

        temporary_path.replace(
            self.storage_path
        )

    def _deserialize(
        self,
        data: dict,
    ) -> MemoryRecord:
        """
        Convert stored JSON data back into a MemoryRecord.
        """

        created_at = datetime.fromisoformat(
            data["created_at"]
        )

        updated_at = datetime.fromisoformat(
            data["updated_at"]
        )

        return MemoryRecord(
            id=data["id"],
            memory_type=data["memory_type"],
            content=data["content"],
            owner_id=data.get(
                "owner_id"
            ),
            source_id=data.get(
                "source_id"
            ),
            metadata=data.get(
                "metadata",
                {},
            ),
            created_at=created_at,
            updated_at=updated_at,
        )