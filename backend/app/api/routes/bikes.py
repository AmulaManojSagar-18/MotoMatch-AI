"""Bike HTTP routes.

The route layer only:
- receives the HTTP request,
- delegates to the service,
- translates results into HTTP responses (including 404 for missing bikes).

It contains no business logic and no direct database access.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_bike_service
from app.schemas.bike import BikeRead
from app.services.bike_service import BikeService

router = APIRouter(prefix="/bikes", tags=["bikes"])


@router.get("", response_model=list[BikeRead], summary="List all bikes")
def list_bikes(service: BikeService = Depends(get_bike_service)) -> list[BikeRead]:
    """Return the full catalog of motorcycles."""
    return service.list_bikes()


@router.get("/{bike_id}", response_model=BikeRead, summary="Get one bike by id")
def get_bike(
    bike_id: int,
    service: BikeService = Depends(get_bike_service),
) -> BikeRead:
    """Return a single motorcycle by id, or 404 if it does not exist."""
    bike = service.get_bike(bike_id)
    if bike is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bike with id {bike_id} not found",
        )
    return bike
