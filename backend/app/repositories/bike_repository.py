"""Repository layer for Bike.

The repository is the ONLY place that talks to the database for bikes.
It exposes plain data-access methods and hides SQLAlchemy query details from
the service layer.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.bike import Bike


class BikeRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_all(self) -> list[Bike]:
        """Return all bikes ordered by id."""
        stmt = select(Bike).order_by(Bike.id)
        return list(self.db.scalars(stmt).all())

    def get_by_id(self, bike_id: int) -> Bike | None:
        """Return a single bike by primary key, or None if it does not exist."""
        return self.db.get(Bike, bike_id)

    def count(self) -> int:
        """Return the number of bikes in the table."""
        return self.db.scalar(select(func.count()).select_from(Bike)) or 0
