from .health import router as health_router
from .users import router as users_router
from .devices import router as devices_router

__all__ = ["health_router", "users_router", "devices_router"]