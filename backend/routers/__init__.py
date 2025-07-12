# Permite importação de routers customizados
try:
    from .agno_router import router as agno_router
except ImportError as e:
    import logging
    logging.getLogger(__name__).error(f"Error importing agno_router: {e}")

try:
    from .proxy_router import proxy_router
except ImportError as e:
    import logging
    logging.getLogger(__name__).warning(f"Error importing proxy_router: {e}")
