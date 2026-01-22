import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import (
    sessions_router,
    analytics_router,
    auth_router,
    portfolios_router,
)
from dependencies import load_config


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    config = load_config()

    app = FastAPI(
        title="Portfolio Analytics API",
        description="Backend API for portfolio analytics platform",
        version="2.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.server.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Auth routes (no auth required)
    app.include_router(auth_router)

    # Portfolio routes (auth required)
    app.include_router(portfolios_router)

    # Legacy routes (to be deprecated)
    app.include_router(sessions_router)
    app.include_router(analytics_router)

    @app.get("/health", tags=["health"])
    def health_check() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "healthy"}

    return app


app = create_app()


if __name__ == "__main__":
    config = load_config()
    uvicorn.run(
        "main:app",
        host=config.server.host,
        port=config.server.port,
        reload=True,
    )
