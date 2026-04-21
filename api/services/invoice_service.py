import os
from datetime import datetime
from typing import Any, Dict
from django.db import transaction
from django.core.files.storage import FileSystemStorage
from rest_framework import exceptions
from api_sataiga.settings import BASE_URL
from api.services.base_service import BaseService
from api.repositories.invoice_repository import InvoiceRepository
from api.repositories.purchase_order_repository import PurchaseOrderRepository
from api.serializers.invoice_serializer import InvoiceSerializer, InvoiceUploadSerializer


class InvoiceService(BaseService):
    """Lógica de negocio pura para Facturas."""

    CACHE_PREFIX = "invoices"

    def __init__(self):
        self.invoice_repo = InvoiceRepository()
        self.purchaseorder_repo = PurchaseOrderRepository()

    @staticmethod
    def _upload_file(invoice_id, invoice_file, file_type):
        fs = FileSystemStorage(
            location=f'media/purchase_orders/invoices/{invoice_id}',
            base_url=f'media/purchase_orders/invoices/{invoice_id}',
        )

        ext = os.path.splitext(invoice_file.name)[1].lower()

        if file_type == 'pdf' and ext != '.pdf':
            raise exceptions.ValidationError("El archivo PDF no es válido.")

        if file_type == 'xml' and ext != '.xml':
            raise exceptions.ValidationError("El archivo XML no es válido.")

        filename = fs.save(invoice_file.name, invoice_file)
        uploaded_file_url = fs.url(filename)

        return f"{BASE_URL}/{uploaded_file_url}"

    def _generate_invoice_folio(self) -> str:
        next_number = self.invoice_repo.get_next_invoice_folio_sequence()
        year = datetime.now().strftime('%y')

        return f"F{year}{next_number:06d}"

    def get_paginated(self, filters: dict, page: int, page_size: int, sort_by: str = 'created_at', order_by: int = 1):
        items = self._get_all_cached(
            self.invoice_repo,
            filters,
            prefix=self.CACHE_PREFIX,
            order_field=sort_by,
            order=order_by
        )

        purchase_order_ids = list({
            item.get('purchase_order_id')
            for item in items
            if item.get('purchase_order_id')
        })

        purchase_orders = self.purchaseorder_repo.find_by_ids(
            purchase_order_ids)

        purchase_order_map = {
            str(po['_id']): po
            for po in purchase_orders
        }

        enriched_items = []
        for item in items:
            purchase_order = purchase_order_map.get(
                item.get('purchase_order_id'))

            item_copy = dict(item)
            po_items = purchase_order.get('items') if purchase_order else []
            item_copy['number'] = purchase_order.get(
                'number') if purchase_order else None
            item_copy['total'] = purchase_order.get(
                'total') if purchase_order else None
            item_copy['project'] = purchase_order.get(
                'project') if purchase_order else None
            item_copy['supplier'] = {
                'name': po_items[0].get('supplier_name')
            } if purchase_order else None

            enriched_items.append(item_copy)

        return self._paginate(enriched_items, page, page_size, serializer=InvoiceSerializer)

    def get_by_id(self, invoice_id: str):
        invoice = self.invoice_repo.find_by_id(invoice_id)

        if not invoice:
            raise LookupError("La factura no existe o no es válida.")

        purchase_order_id = invoice.get('purchase_order_id')
        purchase_order = self.purchaseorder_repo.find_by_id(
            purchase_order_id) if purchase_order_id else None

        if purchase_order:
            items = purchase_order.get('items')
            invoice['number'] = purchase_order.get('number')
            invoice['total'] = purchase_order.get('total')
            invoice['project'] = purchase_order.get('project')
            invoice['supplier'] = {
                'name': items[0].get('supplier_name')
            }

        return InvoiceSerializer(invoice).data

    def get_purchaseorder_list(self, filters: Dict[str, Any]) -> list:
        ids = []
        if not filters:
            return []
        purchase_orders = self.purchaseorder_repo.find_all(filters)
        ids = [str(item['_id']) for item in purchase_orders]
        return ids

    @transaction.atomic
    def save(self, data: Dict[str, Any]) -> str:
        serializer = InvoiceUploadSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        purchase_order_id = validated_data['purchase_order_id']
        pdf_file = validated_data['pdf_file']
        xml_file = validated_data['xml_file']

        purchase_order = self.purchaseorder_repo.find_by_id(purchase_order_id)
        if not purchase_order:
            raise exceptions.ValidationError(
                "La orden de compra seleccionada no existe o no es válida."
            )

        invoice_id = self._create(
            repo=self.invoice_repo,
            data={
                'purchase_order_id': purchase_order_id,
                'folio': self._generate_invoice_folio(),
                'status': 0},
            required_fields=["purchase_order_id"],
            cache_prefix=self.CACHE_PREFIX
        )

        try:
            self._update(
                self.invoice_repo,
                str(invoice_id),
                {
                    'files': [{
                        'uploaded': datetime.now(),
                        'pdf_file': self._upload_file(invoice_id, pdf_file, 'pdf'),
                        'xml_file': self._upload_file(invoice_id, xml_file, 'xml'),
                    }]
                },
                cache_prefix=self.CACHE_PREFIX
            )
        except Exception as e:
            raise exceptions.ValidationError(
                f"Error al guardar los archivos: {str(e)}"
            )

        return str(invoice_id)

    @transaction.atomic
    def update(self, invoice_id: str, status: int | bool) -> str:
        if isinstance(status, bool):
            status = int(status)
        elif status not in (0, 1, 2):
            raise ValueError("Estatus inválido, solo se permite: 0, 1 y 2.")

        self._update(
            self.invoice_repo,
            invoice_id,
            {'status': status},
            cache_prefix=self.CACHE_PREFIX)

        return (
            "Factura eliminada correctamente."
            if status == 2
            else "Factura actualizada correctamente."
        )

    @transaction.atomic
    def upload(self, invoice_id: str, data: Dict[str, Any]):
        serializer = InvoiceUploadSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        pdf_file = validated_data['pdf_file']
        xml_file = validated_data['xml_file']

        invoice = self.invoice_repo.find_by_id(invoice_id)
        if not invoice:
            raise LookupError("La factura no existe.")

        try:
            files = invoice.get('files', [])
            files.append({
                'uploaded': datetime.now(),
                'pdf_file': self._upload_file(invoice_id, pdf_file, 'pdf'),
                'xml_file': self._upload_file(invoice_id, xml_file, 'xml')})
            self._update(self.invoice_repo, invoice_id, {
                         'files': files}, cache_prefix=self.CACHE_PREFIX)
        except Exception as e:
            raise exceptions.ValidationError(
                f"Error al guardar los archivos: {str(e)}"
            )

        return 'Los archivos de la factura se han cargado correctamente.'
