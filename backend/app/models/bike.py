"""Bike ORM model.

This table stores ONLY factual, catalog-level motorcycle specifications.
It intentionally does NOT store derived suitability scores (comfort_score,
touring_score, etc.) -- those are produced later by the recommendation engine.

Fields are nullable where a reliable value may not exist for a given bike.
"""

from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Bike(Base):
    __tablename__ = "bikes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Identity
    brand: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Commercial
    price: Mapped[int | None] = mapped_column(Integer, nullable=True)  # approx ex-showroom INR

    # Engine / performance
    engine_cc: Mapped[float | None] = mapped_column(Float, nullable=True)
    power_ps: Mapped[float | None] = mapped_column(Float, nullable=True)
    torque_nm: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Physical
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    seat_height_mm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fuel_capacity_l: Mapped[float | None] = mapped_column(Float, nullable=True)
    ground_clearance_mm: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Drivetrain / safety
    transmission: Mapped[str | None] = mapped_column(String(50), nullable=True)
    abs_type: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Efficiency
    mileage: Mapped[float | None] = mapped_column(Float, nullable=True)  # kmpl

    # 3D asset reference (placeholder in Phase 1)
    model_3d_url: Mapped[str | None] = mapped_column(String(255), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"<Bike id={self.id} {self.brand} {self.model}>"
