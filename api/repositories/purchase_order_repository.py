from bson import ObjectId
from api.repositories.base_repository import BaseRepository


class PurchaseOrderRepository(BaseRepository):
    """Acceso a la colección 'purchase_orders' en MongoDB."""
    COLLECTION = 'purchase_orders'
