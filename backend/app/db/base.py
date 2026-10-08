"""SQLAlchemy declarative base.

All ORM models inherit from `Base`, which collects the table metadata used
to create the schema.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared declarative base for all MotoMatch models."""

    pass
