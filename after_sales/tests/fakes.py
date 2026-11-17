"""
Doble en memoria del `MongoDBHandler` compartido, para las pruebas de
autenticación. Implementa sólo lo que usa `after_sales.repositories.mongo`:
`extract`, `insert` y `update` (con `$set`, `$inc`, `$setOnInsert`).
"""
import copy
import itertools
from datetime import datetime

_seq = itertools.count(1)


def new_store():
    return {}


def _match(doc, query):
    """Sólo igualdad exacta: es lo único que consultan los repositorios."""
    return all(doc.get(key) == value for key, value in (query or {}).items())


class FakeMongoDBHandler:
    def __init__(self, store, collection_name):
        self._store = store
        self.collection_name = collection_name

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    @property
    def _rows(self):
        return self._store.setdefault(self.collection_name, [])

    def insert(self, data):
        doc = copy.deepcopy(data)
        n = next(_seq)
        doc.setdefault("_id", f"{self.collection_name}:{n}")
        doc["_seq"] = n
        now = datetime.now()
        doc.setdefault("created_at", now)
        doc["updated_at"] = now
        self._rows.append(doc)
        return doc["_id"]

    def extract(self, query=None, order_field=None, order=1, projection=None):
        rows = [copy.deepcopy(d) for d in self._rows if _match(d, query)]
        if order_field:
            rows.sort(
                key=lambda d: (d.get(order_field) is None,
                               d.get(order_field), d.get("_seq", 0)),
                reverse=(order == -1),
            )
        return rows

    def update(self, query, update_data, upsert=False):
        if any(k.startswith("$") for k in update_data):
            ops = update_data
        else:
            ops = {"$set": dict(update_data)}

        target = next((d for d in self._rows if _match(d, query)), None)
        if target is None:
            if not upsert:
                return None
            n = next(_seq)
            target = {
                k: v for k, v in (query or {}).items()
                if not k.startswith("$")
            }
            target.setdefault("_id", f"{self.collection_name}:{n}")
            target["_seq"] = n
            target["created_at"] = datetime.now()
            self._rows.append(target)

        for op, fields in ops.items():
            if op == "$set":
                target.update(fields)
            elif op == "$inc":
                for k, amount in fields.items():
                    target[k] = target.get(k, 0) + amount
            elif op == "$setOnInsert":
                for k, v in fields.items():
                    target.setdefault(k, v)
        target["updated_at"] = datetime.now()
        return copy.deepcopy(target)


def handler_factory(store):
    """Devuelve un callable equivalente a `MongoDBHandler(collection_name)`."""
    def _factory(collection_name):
        return FakeMongoDBHandler(store, collection_name)
    return _factory


class CapturingSms:
    """Recolector de SMS enviados; se usa para parchear `send_verification_sms`."""

    def __init__(self):
        self.sent = []

    def __call__(self, phone, code):
        self.sent.append({"phone": phone, "code": code})
        return True

    @property
    def last_code(self):
        return self.sent[-1]["code"] if self.sent else None
