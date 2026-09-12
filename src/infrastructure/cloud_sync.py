"""
Proxy / Re-exportación de CloudSyncManager en el paquete de infraestructura.
Permite importar tanto desde 'server.cloud_sync' como desde 'src.infrastructure.cloud_sync'.
"""

from server.cloud_sync import CloudSyncManager, DEFAULT_SERVER_URL

__all__ = ["CloudSyncManager", "DEFAULT_SERVER_URL"]
