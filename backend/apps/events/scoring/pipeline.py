from dataclasses import dataclass, field
from typing import List

from .steps import DEFAULT_PIPELINE


@dataclass
class ScoreResult:
    score: int
    reasons: List[str] = field(default_factory=list)


def score_event(event, context, pipeline=None):
    pipeline = pipeline if pipeline is not None else DEFAULT_PIPELINE
    total = 0
    reasons = []
    for step in pipeline:
        points, reason = step.score(event, context)
        total += points
        if reason:
            reasons.append(reason)
    return ScoreResult(score=total, reasons=reasons)
