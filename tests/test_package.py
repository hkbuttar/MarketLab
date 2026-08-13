"""Package-level scaffold checks."""


def test_marketlab_import() -> None:
    import marketlab

    assert marketlab.__version__ == "0.1.0"
