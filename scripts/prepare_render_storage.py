"""Connect MarketLab artifact directories to an attached Render disk."""

import os
from pathlib import Path

from marketlab.deployment import prepare_persistent_storage


def main() -> int:
    configured = os.getenv("MARKETLAB_STORAGE_ROOT")
    if not configured:
        raise RuntimeError("MARKETLAB_STORAGE_ROOT is not configured")
    prepare_persistent_storage(Path(configured), Path.cwd())
    print(f"Prepared persistent artifact storage at {configured}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
