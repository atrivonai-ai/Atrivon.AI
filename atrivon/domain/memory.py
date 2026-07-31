from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from atrivon.domain.models import generate_id


def utc_now() -> datetime:
    """
    Return the current UTC timestamp.
    """

    return datetime.now(timezone.utc)


@dataclass
class MemoryRecord:
    """
    Canonical Atrivon memory record.

    A MemoryRecord represents a persistent piece of information
    that Atrivon wants to retain.

    The record is intentionally storage-independent.
    Repositories and databases store these records, but they
    do not define the meaning of the memory itself.
    """

    memory_type: str
    content: dict[str, Any]

    id: str = field(
        default_factory=generate_id
    )

    owner_id: str | None = None

    source_id: str | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    created_at: datetime = field(
        default_factory=utc_now
    )

    updated_at: datetime = field(
        default_factory=utc_now
    )

    def __post_init__(self):
        if not self.memory_type.strip():
            raise ValueError(
                "Memory type cannot be empty."
            )

        if not isinstance(
            self.content,
            dict,
        ):
            raise TypeError(
                "Memory content must be a dictionary."
            )

    def update_content(
        self,
        content: dict[str, Any],
    ) -> None:
        """
        Replace the memory content and update the timestamp.
        """

        if not isinstance(
            content,
            dict,
        ):
            raise TypeError(
                "Memory content must be a dictionary."
            )

        self.content = content
        self.updated_at = utc_now()

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the memory record into a
        serialization-friendly dictionary.
        """

        return {
            "id": self.id,
            "memory_type": self.memory_type,
            "content": self.content,
            "owner_id": self.owner_id,
            "source_id": self.source_id,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }