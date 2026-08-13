"""Package-level scaffold checks."""

import marketlab


def test_package_version() -> None:
    assert marketlab.__version__ == "0.1.0"

