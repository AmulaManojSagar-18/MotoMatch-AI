"""Service layer for Bike.

Business logic lives here. In Phase 1 the logic is thin (read-only catalog),
but keeping this layer means future recommendation/scoring logic has a natural
home without touching routes or the repository.

The service returns domain objects (or None). It does NOT raise HTTP errors --
that translation is the route's responsibility.
"""

from app.models.bike import Bike
from app.repositories.bike_repository import BikeRepository


class BikeService:
    def __init__(self, repository: BikeRepository) -> None:
        self.repository = repository

    def list_bikes(self) -> list[Bike]:
        """Return the full catalog."""
        return self.repository.get_all()

    def get_bike(self, bike_id: int) -> Bike | None:
        """Return one bike by id, or None if not found."""
        return self.repository.get_by_id(bike_id)
