from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from atrivon.domain.models import generate_id
from atrivon.execution.observation import (
    Observation,
)


def utc_now() -> datetime:
    """
    Return the current UTC timestamp.
    """

    return datetime.now(
        timezone.utc
    )


@dataclass
class WorldFact:
    """
    A single fact about the world as currently known
    by Atrivon.

    Example:

    subject:
        website/index.html

    predicate:
        exists

    value:
        True
    """

    subject: str

    predicate: str

    value: Any

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
        if not self.subject.strip():
            raise ValueError(
                "WorldFact subject cannot be empty."
            )

        if not self.predicate.strip():
            raise ValueError(
                "WorldFact predicate cannot be empty."
            )

        if not (
            0.0
            <= self.confidence
            <= 1.0
        ):
            raise ValueError(
                "WorldFact confidence must be "
                "between 0.0 and 1.0."
            )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        """
        Convert the WorldFact into a
        serialization-friendly dictionary.
        """

        return {
            "id": self.id,
            "subject": self.subject,
            "predicate": self.predicate,
            "value": self.value,
            "source": self.source,
            "confidence": self.confidence,
            "metadata": self.metadata,
            "observed_at": (
                self.observed_at.isoformat()
            ),
        }


class WorldState:
    """
    Atrivon's current structured representation of known reality.

    WorldState is updated from observations.

    It is deliberately separate from:
    - Goals
    - Plans
    - Tasks
    - Actions
    - Memory

    This distinction allows Atrivon to reason about:

    "What I want"

    versus:

    "What I currently believe is true."

    Facts are keyed by:

        subject + predicate
    """

    def __init__(self):
        self._facts: dict[
            tuple[str, str],
            WorldFact,
        ] = {}

    def update_from_observation(
        self,
        observation: Observation,
    ) -> WorldFact | None:
        """
        Convert an Observation into a WorldFact
        when the observation provides usable information.

        Observations with ERROR or NOT_FOUND status do not
        automatically create a positive fact.
        """

        if not isinstance(
            observation,
            Observation,
        ):
            raise TypeError(
                "update_from_observation() requires "
                "an Observation."
            )

        if observation.status.value in {
            "error",
            "not_found",
        }:
            return None

        predicate = (
            observation.metadata.get(
                "predicate"
            )
        )

        if not predicate:
            predicate = (
                observation.observation_type
            )

        fact = WorldFact(
            subject=observation.subject,
            predicate=predicate,
            value=observation.value,
            source=observation.source,
            confidence=observation.confidence,
            metadata={
                **observation.metadata,
                "observation_id": (
                    observation.id
                ),
            },
            observed_at=(
                observation.observed_at
            ),
        )

        self._facts[
            (
                fact.subject,
                fact.predicate,
            )
        ] = fact

        return fact

    def set_fact(
        self,
        subject: str,
        predicate: str,
        value: Any,
        source: str = "",
        confidence: float = 1.0,
        metadata: dict[str, Any] | None = None,
    ) -> WorldFact:
        """
        Directly set or replace a WorldFact.
        """

        fact = WorldFact(
            subject=subject,
            predicate=predicate,
            value=value,
            source=source,
            confidence=confidence,
            metadata=(
                metadata
                if metadata is not None
                else {}
            ),
        )

        self._facts[
            (
                subject,
                predicate,
            )
        ] = fact

        return fact

    def get_fact(
        self,
        subject: str,
        predicate: str,
    ) -> WorldFact | None:
        """
        Retrieve the latest known fact for a subject
        and predicate.
        """

        return self._facts.get(
            (
                subject,
                predicate,
            )
        )

    def get_value(
        self,
        subject: str,
        predicate: str,
        default: Any = None,
    ) -> Any:
        """
        Retrieve only the value of a known fact.
        """

        fact = self.get_fact(
            subject,
            predicate,
        )

        if fact is None:
            return default

        return fact.value

    def has_fact(
        self,
        subject: str,
        predicate: str,
    ) -> bool:
        """
        Determine whether Atrivon currently has
        a known fact for a subject and predicate.
        """

        return (
            subject,
            predicate,
        ) in self._facts

    def list_facts(
        self,
    ) -> list[WorldFact]:
        """
        Return all currently known WorldFacts.
        """

        return list(
            self._facts.values()
        )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        """
        Serialize the complete WorldState.
        """

        return {
            "facts": [
                fact.to_dict()
                for fact
                in self._facts.values()
            ]
        }