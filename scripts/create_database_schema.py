"""Create MarketLab metadata tables in the configured PostgreSQL database."""

from backend.database import Base, create_database_engine


def main() -> int:
    engine = create_database_engine()
    Base.metadata.create_all(engine)
    print("Created MarketLab metadata schema.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
