"""FastAPI application entry point.

Request flow for the bike endpoints:

    Client -> Route -> Service -> Repository -> SQLAlchemy -> PostgreSQL

Schema creation and seeding are handled explicitly by `scripts/seed.py`
(run it once before starting the API). Keeping DDL out of app startup means
importing the app never requires a live database, which keeps tests fast and
decoupled.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import bikes, chat, recommend
from app.core.config import settings

# Importing the model module ensures the Bike table is registered on the
# shared metadata (useful for tooling that inspects Base.metadata).
from app.models import bike as _bike  # noqa: F401


def create_app() -> FastAPI:
    app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)

    # Allow the local React dev server (Vite) to call the API from the browser.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["health"], summary="Health check")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(bikes.router)
    app.include_router(recommend.router)
    app.include_router(chat.router)
    return app


app = create_app()
