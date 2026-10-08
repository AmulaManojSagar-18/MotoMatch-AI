"""Create the schema and seed the fixed catalog of 10 motorcycles.

Run from the `backend/` directory:

    python -m scripts.seed            # create tables; insert bikes only if empty
    python -m scripts.seed --reset    # delete existing bikes, then re-insert

This script is the single, explicit place where the database schema is created
and populated for Phase 1.
"""

import argparse

from app.data.catalog import BIKE_CATALOG
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models.bike import Bike


def seed(reset: bool = False) -> None:
    # Create the `bikes` table if it does not already exist.
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        existing = db.query(Bike).count()

        if existing and not reset:
            print(
                f"Database already contains {existing} bike(s). "
                "Nothing to do. Use --reset to re-seed."
            )
            return

        if existing and reset:
            db.query(Bike).delete()
            db.commit()
            print(f"Removed {existing} existing bike(s).")

        db.add_all([Bike(**data) for data in BIKE_CATALOG])
        db.commit()
        print(f"Seeded {len(BIKE_CATALOG)} bikes successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed the MotoMatch bike catalog")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing bikes before seeding",
    )
    args = parser.parse_args()
    seed(reset=args.reset)
