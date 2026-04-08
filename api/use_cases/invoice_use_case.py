from api.utils.pagination_utils import DummyPaginator, DummyPage
from api.helpers.get_query_params import get_query_params
from api.helpers.http_responses import ok, ok_paginated, bad_request
from api.helpers.formats import to_bool
from api.decorators.service_method import service_method
from api.services.invoice_service import InvoiceService


class InvoiceUseCase:
    def __init__(self, request=None, **kwargs):
        params = get_query_params(request)
        self.q = params["q"]
        self.page = params["page"]
        self.page_size = params["page_size"]
        self.sort_by = params["sort_by"]
        self.order_by = params["order_by"]
        self.supplier_id = params.get('supplier_id', None)
        self.data = kwargs.get('data')
        self.id = kwargs.get("id")
        self.service = InvoiceService()

    def get(self):
        """Método especial con paginación manual."""
        try:
            po_filters = {}
            if self.supplier_id:
                po_filters['supplier_id'] = self.supplier_id
            if self.q:
                q = str(self.q)
                po_filters['$or'] = [
                    {'number': {'$regex': q, '$options': 'i'}},
                    {'project': {'$regex': q, '$options': 'i'}},
                ]

            purchase_orders_ids = self.service.get_purchaseorder_list(
                po_filters)
            invoices_filters = {}
            if len(purchase_orders_ids) > 0:
                invoices_filters = {
                    "purchase_order_id": {
                        "$in": purchase_orders_ids
                    }
                }

            if po_filters and len(purchase_orders_ids) == 0:
                return ok([])

            result = self.service.get_paginated(
                invoices_filters, self.page, self.page_size, self.sort_by, self.order_by
            )
            dummy_paginator = DummyPaginator(
                result["count"], result["total_pages"])
            dummy_page = DummyPage(
                result["current_page"], dummy_paginator, result["results"])
            return ok_paginated(dummy_paginator, dummy_page, result["results"])
        except Exception as e:
            return bad_request(f"Error al obtener las facturas: {e}")

    @service_method()
    def get_by_id(self):
        """Obtiene factura por ID."""
        return self.service.get_by_id(self.id)

    @service_method(success_status="created")
    def save(self):
        """Guarda una nueva factura."""
        return self.service.save(self.data)

    @service_method()
    def update(self):
        "Actualizar el estatus de la factura"
        invoice_status = self.data.get('status', False)
        return self.service.update(self.id, to_bool(invoice_status))

    @service_method()
    def upload(self):
        "Cargar archivos adicionales a la factura."
        return self.service.upload(self.id, self.data)
