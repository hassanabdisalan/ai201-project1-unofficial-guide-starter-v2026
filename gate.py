"""
The relevance gate.

This runs *before* the model does. It looks at how close the best retrieved
chunk actually is, and if nothing came back close enough it refuses the
question outright.

Why this exists as its own step, rather than just asking the model nicely to
admit when it doesn't know: if you only ask nicely, it will sometimes ignore
you and write something confident and wrong. Those answers are much harder to
catch than obvious errors. Deciding in your own code when there's nothing worth
answering from is more reliable than hoping.

You keep the polite instruction too — it's in generate.py — but as a second
layer. The gate catches the clear misses; the prompt catches the near ones.
"""

from dataclasses import dataclass

import config
from store import Result

REFUSAL = "I don't have enough information about that."


@dataclass
class GateDecision:
    passed: bool
    best_distance: float
    threshold: float

    @property
    def explanation(self) -> str:
        if self.passed:
            return (
                f"best distance {self.best_distance:.3f} "
                f"is under the {self.threshold} cutoff"
            )
        return (
            f"best distance {self.best_distance:.3f} "
            f"is over the {self.threshold} cutoff — refusing"
        )


def check(
    results: list[Result],
    threshold: float | None = None,
    best_distance: float | None = None,
) -> GateDecision:
    """
    Decide whether the retrieved chunks are close enough to answer from.

    Remember: LOWER distance is better. A question passes when its best chunk
    is *under* the threshold.

    `best_distance` (stretch: a second measured improvement) lets a caller
    supply the true semantic nearest-neighbour distance directly — see
    `store.py::semantic_best_distance` — instead of it being recomputed from
    `results`. That matters once retrieval does hybrid fusion (Milestone 4):
    the fused top-k a caller passes in for `results` might not contain the
    single closest chunk in the whole collection at all, if it had no
    keyword overlap with the question. Passing `best_distance` keeps the
    gate checking the one number it was calibrated against, independent of
    whatever ranking `search()` used to pick `results`.
    """
    threshold = config.THRESHOLD if threshold is None else threshold

    if best_distance is None:
        if not results:
            return GateDecision(passed=False, best_distance=1.0, threshold=threshold)
        best_distance = min(r.distance for r in results)

    return GateDecision(
        passed=best_distance < threshold, best_distance=best_distance, threshold=threshold
    )
