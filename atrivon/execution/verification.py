from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from atrivon.domain.models import generate_id
from atrivon.execution.observation import Observation


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class VerificationStatus(str, Enum):
    VERIFIED = "verified"
    FAILED = "failed"
    PARTIAL = "partial"
    UNKNOWN = "unknown"


@dataclass
class VerificationResult:
    status: VerificationStatus
    expected: dict[str, Any]
    observed: dict[str, Any]
    confidence: float

    matched_fields: list[str] = field(default_factory=list)
    mismatched_fields: list[str] = field(default_factory=list)
    missing_fields: list[str] = field(default_factory=list)
    reasoning: list[str] = field(default_factory=list)

    id: str = field(default_factory=generate_id)
    verified_at: datetime = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "status": self.status.value,
            "expected": self.expected,
            "observed": self.observed,
            "confidence": self.confidence,
            "matched_fields": self.matched_fields,
            "mismatched_fields": self.mismatched_fields,
            "missing_fields": self.missing_fields,
            "reasoning": self.reasoning,
            "verified_at": self.verified_at.isoformat(),
        }


class VerificationEngine:
    """
    Verifies whether observed reality matches the expected outcome.
    """

    def verify(
        self,
        expected: dict[str, Any],
        observation: Observation,
    ) -> VerificationResult:

        observed = observation.value

        if not isinstance(observed, dict):
            observed = {}

        matched: list[str] = []
        mismatched: list[str] = []
        missing: list[str] = []
        reasoning: list[str] = []

        for key, expected_value in expected.items():

            if key not in observed:
                missing.append(key)
                reasoning.append(
                    f"Missing expected field '{key}'."
                )
                continue

            observed_value = observed[key]

            if observed_value == expected_value:
                matched.append(key)
                reasoning.append(
                    f"{key} matched."
                )
            else:
                mismatched.append(key)
                reasoning.append(
                    f"{key}: expected {expected_value!r}, observed {observed_value!r}."
                )

        total = len(expected)

        if total == 0:
            confidence = 1.0
            status = VerificationStatus.UNKNOWN
        else:
            confidence = len(matched) / total

            if len(matched) == total:
                status = VerificationStatus.VERIFIED
            elif len(matched) == 0:
                status = VerificationStatus.FAILED
            else:
                status = VerificationStatus.PARTIAL

        return VerificationResult(
            status=status,
            expected=expected,
            observed=observed,
            confidence=confidence,
            matched_fields=matched,
            mismatched_fields=mismatched,
            missing_fields=missing,
            reasoning=reasoning,
        )