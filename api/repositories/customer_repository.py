from typing import Optional, Callable
from api.repositories.base_repository import BaseRepository


class CustomerRepository(BaseRepository):
    """Acceso a la colección 'customers'."""

    COLLECTION = 'customers'

    def _with_auth_pipeline(self, query=None):
        return [
            {
                "$match": query or {}
            },
            {
                "$lookup": {
                    "from": "auth",
                    "localField": "_id",
                    "foreignField": "user_id",
                    "as": "auth"
                }
            },
            {
                "$unwind": {
                    "path": "$auth",
                    "preserveNullAndEmptyArrays": True
                }
            }
        ]

    def find_one_with_auth(
        self,
        query=None,
        projection=None,
        serializer: Optional[Callable] = None
    ):
        pipeline = self._with_auth_pipeline(query)

        if projection:
            pipeline.append({
                "$project": projection
            })

        with self.db_handler as db:
            result = db.aggregate(pipeline)

        customer = result[0] if result else None

        return serializer(customer).data if serializer else customer

    def find_all_with_auth(
        self,
        query=None,
        order_field=None,
        order=1,
        projection=None
    ):
        pipeline = self._with_auth_pipeline(query)

        if order_field:
            pipeline.append({
                "$sort": {
                    order_field: order
                }
            })

        if projection:
            pipeline.append({
                "$project": projection
            })

        with self.db_handler as db:
            return db.aggregate(pipeline)
