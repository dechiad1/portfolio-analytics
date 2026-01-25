from api.routers.analytics import router as analytics_router
from api.routers.auth import router as auth_router
from api.routers.oauth import router as oauth_router
from api.routers.portfolios import router as portfolios_router
from api.routers.tickers import router as tickers_router
from api.routers.simulations import router as simulations_router

__all__ = [
    "analytics_router",
    "auth_router",
    "oauth_router",
    "portfolios_router",
    "tickers_router",
    "simulations_router",
]
