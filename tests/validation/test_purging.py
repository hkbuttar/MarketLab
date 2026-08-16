"""Tests for overlapping-label purging and embargo controls."""

import numpy as np

from marketlab.validation.purging import purged_train_indices


def test_purging_removes_label_overlap_and_embargo_boundary() -> None:
    calendar = [f"2024-01-{day:02d}" for day in range(1, 16)]
    dates = np.asarray([calendar[3], calendar[4], calendar[5]])
    candidates = np.asarray([0, 1, 2])

    kept = purged_train_indices(
        dates,
        candidates,
        test_start=calendar[9],
        calendar=calendar,
        label_horizon_sessions=3,
        embargo_sessions=2,
    )

    assert list(kept) == [0]
