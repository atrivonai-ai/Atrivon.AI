from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from atrivon.domain.models import generate_id


def utc_now() -> datetime:
    """
    Return the current UTC timestamp.
    """

    return datetime.now(
        timezone.utc
    )


class ObservationStatus(str, Enum):
    """
    Canonical states for an Atrivon observation.
    """

    OBSERVED = "observed"
    NOT_FOUND = "not_found"
    CHANGED = "changed"
    UNCHANGED = "unchanged"
    ERROR = "error"


@dataclass
class Observation:
    """
    Canonical representation of something Atrivon observed
    in the real world.

    An Observation describes what was actually observed.

    It does not decide whether the observation is good,
    bad, successful, or sufficient.

    Verification is a separate responsibility.
    """

    observation_type: str

    subject: str

    status: ObservationStatus

    value: Any = None

    source: str = ""

    confidence: float = 1.0

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    id: str = field(
        default_factory=generate_id
    )

    observed_at: datetime = field(
        default_factory=utc_now
    )

    def __post_init__(self):
        if not self.observation_type.strip():
            raise ValueError(
                "Observation type cannot be empty."
            )

        if not self.subject.strip():
            raise ValueError(
                "Observation subject cannot be empty."
            )

        if not isinstance(
            self.status,
            ObservationStatus,
        ):
            self.status = ObservationStatus(
                self.status
            )

        if not (
            0.0
            <= self.confidence
            <= 1.0
        ):
            raise ValueError(
                "Observation confidence must be "
                "between 0.0 and 1.0."
            )

        if not isinstance(
            self.metadata,
            dict,
        ):
            raise TypeError(
                "Observation metadata must be a dictionary."
            )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        """
        Convert the Observation into a
        serialization-friendly dictionary.
        """

        return {
            "id": self.id,
            "observation_type": (
                self.observation_type
            ),
            "subject": self.subject,
            "status": self.status.value,
            "value": self.value,
            "source": self.source,
            "confidence": self.confidence,
            "metadata": self.metadata,
            "observed_at": (
                self.observed_at.isoformat()
            ),
        }