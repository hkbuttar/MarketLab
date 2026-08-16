"""Tests for strict expanding-window ML training."""

import numpy as np

from marketlab.ml.training import expanding_year_folds


def test_expanding_year_folds_never_train_on_test_or_future_dates() -> None:
    dates = np.asarray(
        [
            "2013-01-31",
            "2017-12-29",
            "2018-01-31",
            "2018-12-31",
            "2019-01-31",
            "2019-12-31",
        ]
    )

    folds = expanding_year_folds(dates, train_start_year=2013, first_test_year=2018)

    assert [fold["test_year"] for fold in folds] == [2018, 2019]
    assert list(folds[0]["train_indices"]) == [0, 1]
    assert list(folds[0]["test_indices"]) == [2, 3]
    assert list(folds[1]["train_indices"]) == [0, 1, 2, 3]
    assert list(folds[1]["test_indices"]) == [4, 5]
    assert folds[0]["train_end"] < "2018-01-01"
    assert folds[1]["train_end"] < "2019-01-01"
