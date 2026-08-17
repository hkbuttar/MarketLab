"""Prepare persistent state and replace this process with Render's API server."""

import os

from scripts.create_database_schema import main as create_schema
from scripts.prepare_render_storage import main as prepare_storage


def uvicorn_command(port_value: str | None) -> list[str]:
    """Build a validated Uvicorn command from Render's assigned port."""

    value = port_value or "10000"
    try:
        port = int(value)
    except ValueError as error:
        raise RuntimeError("PORT must be an integer") from error
    if not 1 <= port <= 65_535:
        raise RuntimeError("PORT must be between 1 and 65535")
    return [
        "uvicorn",
        "backend.api.app:app",
        "--host",
        "0.0.0.0",
        "--port",
        str(port),
    ]


def main() -> int:
    prepare_storage()
    create_schema()
    command = uvicorn_command(os.getenv("PORT"))
    os.execvp(command[0], command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
