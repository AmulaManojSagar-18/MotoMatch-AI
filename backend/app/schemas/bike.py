"""Pydantic schemas for the Bike resource.

Schemas define the shape of API responses (and would validate request bodies
if we had write endpoints). They are decoupled from the ORM model so the API
contract can evolve independently of the database.

`protected_namespaces=()` is set because several fields start with "model",
which Pydantic otherwise reserves.
"""

from pydantic import BaseModel, ConfigDict


class BikeBase(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    brand: str
    model: str
    category: str
    price: int | None = None
    engine_cc: float | None = None
    power_ps: float | None = None
    torque_nm: float | None = None
    weight_kg: float | None = None
    seat_height_mm: int | None = None
    fuel_capacity_l: float | None = None
    ground_clearance_mm: int | None = None
    transmission: str | None = None
    abs_type: str | None = None
    mileage: float | None = None
    model_3d_url: str | None = None


class BikeRead(BikeBase):
    """Bike as returned by the API, including its database id."""

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: int
