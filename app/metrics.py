"""Metrics computed live in the app from exported held-out predictions (numpy only)."""
import numpy as np

# Outcome labels, adapted from the slides' "Who gets a call?" grid to readmission.
GROUPS = [
    ("called_readmitted", "Called, and was readmitted"),
    ("called_not", "Called, but was not readmitted"),
    ("not_called_readmitted", "Not called, and was readmitted"),
    ("not_called_not", "Not called, and was not readmitted"),
]


def baseline_accuracy(y) -> float:
    """Accuracy of a 'model' that predicts nobody is readmitted."""
    return 1 - float(np.mean(y))


def call_outcomes(p, y, calls_per_1000: int) -> dict:
    """Phone the highest-risk patients, up to a fixed capacity, and count outcomes per 1,000.

    Follows the slides' method: scale the held-out test set to 1,000 patients and round
    so the four counts add up to exactly 1,000. Ties are broken by a stable sort.
    These are historical outcomes: who WAS readmitted, not readmissions a call prevented.
    """
    p = np.asarray(p, dtype=float)
    y = np.asarray(y, dtype=int)
    n = len(y)
    calls = int(np.clip(calls_per_1000, 0, 1000))
    n_called = int(round(n * calls / 1000))
    called = np.zeros(n, dtype=bool)
    called[np.argsort(-p, kind="stable")[:n_called]] = True

    would_be = int(round(y.mean() * 1000))
    called_readmitted = int(round((called & (y == 1)).sum() * 1000 / n))
    called_readmitted = min(called_readmitted, calls, would_be)
    out = {
        "called_readmitted": called_readmitted,
        "called_not": calls - called_readmitted,
        "not_called_readmitted": would_be - called_readmitted,
        "not_called_not": 1000 - calls - (would_be - called_readmitted),
    }
    assert sum(out.values()) == 1000
    out.update(
        calls=calls,
        readmitted_total=would_be,
        cutoff=float(p[called].min()) if n_called else None,
        precision=called_readmitted / calls if calls else None,
        recall=called_readmitted / would_be if would_be else None,
        accuracy=(out["called_readmitted"] + out["not_called_not"]) / 1000,
        random_precision=would_be / 1000,
    )
    return out
