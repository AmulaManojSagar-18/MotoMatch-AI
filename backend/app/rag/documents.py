"""Bike knowledge documents for RAG.

Each of the 10 catalog bikes becomes one short, factual document built from the
same data that seeds PostgreSQL. These documents are the ONLY source the
knowledge answers are grounded in -- the LLM must not add specs beyond them.

RAG here is a *supporting* knowledge feature (answering "what engine does the
Hunter have?"). It never selects the recommended bike.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.data.catalog import BIKE_CATALOG


@dataclass(frozen=True)
class BikeDocument:
    bike_id: int
    name: str
    text: str


def _format_bike(bike_id: int, data: dict) -> BikeDocument:
    name = f"{data['brand']} {data['model']}"

    def val(key: str, suffix: str = "") -> str:
        v = data.get(key)
        return f"{v}{suffix}" if v is not None else "not available"

    text = (
        f"{name} (id {bike_id}). "
        f"Brand: {data['brand']}. Model: {data['model']}. "
        f"Category: {data['category']}. "
        f"Ex-showroom price: approximately INR {val('price')}. "
        f"Engine displacement: {val('engine_cc', ' cc')}. "
        f"Power: {val('power_ps', ' PS')}. "
        f"Torque: {val('torque_nm', ' Nm')}. "
        f"Kerb weight: {val('weight_kg', ' kg')}. "
        f"Seat height: {val('seat_height_mm', ' mm')}. "
        f"Fuel tank capacity: {val('fuel_capacity_l', ' litres')}. "
        f"Ground clearance: {val('ground_clearance_mm', ' mm')}. "
        f"Transmission: {val('transmission')}. "
        f"ABS: {val('abs_type')}. "
        f"Mileage: {val('mileage', ' kmpl')}."
    )
    return BikeDocument(bike_id=bike_id, name=name, text=text)


def build_bike_documents() -> list[BikeDocument]:
    """Build one document per catalog bike (ids follow catalog/seed order)."""
    return [_format_bike(i + 1, data) for i, data in enumerate(BIKE_CATALOG)]
