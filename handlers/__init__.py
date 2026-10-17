"""
THRONE o'yin tizimi.
"""

from .game import router as game_router
from .start import router as start_router

__all__ = ("game_router", "start_router")
__version__ = "1.0.1"
