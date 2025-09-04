from django.db import models


class PurchaseOrder(models.Model):
    STATUS_PENDIENTE = 0
    STATUS_GENERADA = 1
    STATUS_APROBADA = 2
    STATUS_RECHAZADA = 3

    STATUS_CHOICES = [
        (STATUS_GENERADA, 'Pendiente de aprobar'),
        (STATUS_PENDIENTE, 'Borrador'),
        (STATUS_APROBADA, 'Aprobada'),
        (STATUS_RECHAZADA, 'Cancelada'),
    ]

    SIN_ENTREGAR = 0
    ENTREGADO_PARCIAL = 1
    ENTREGADO_TOTAL = 2

    DELIVERED_CHOICES = [
        (SIN_ENTREGAR, 'Pendiente'),
        (ENTREGADO_PARCIAL, 'Entrega parcial'),
        (ENTREGADO_TOTAL, 'Entrega total'),
    ]

    FACTURA_PENDIENTE = 0
    FACTURA_ENTREGADA = 1
    FACTURA_PAGADA = 2

    INVOICED_CHOICES = [
        (FACTURA_PENDIENTE, 'Pendiente'),
        (FACTURA_ENTREGADA, 'Entregada'),
        (FACTURA_PAGADA, 'Pagada'),
    ]

    _id = models.CharField(max_length=50)
    home_production_id = models.CharField(max_length=50)
    linked_id = models.CharField(max_length=50, null=True)
    company_id = models.CharField(max_length=50, null=True)
    project = models.CharField(max_length=50)
    number = models.CharField(max_length=25)
    folio = models.SmallIntegerField()
    lots = models.JSONField(null=True)
    supplier_id = models.CharField(max_length=50)
    subject = models.CharField(max_length=255, null=True)
    request_by = models.CharField(max_length=50)
    approved_by = models.CharField(max_length=50, null=True)
    created = models.DateField()
    estimated_delivery = models.DateField(null=True)
    division = models.JSONField(null=True)
    items = models.JSONField(null=True)
    selected_rows = models.JSONField(null=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    iva = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    excel_file = models.CharField(max_length=255, null=True)
    pdf_file = models.CharField(max_length=255, null=True)
    payment_method = models.CharField(max_length=50, null=True)
    payment_form = models.CharField(max_length=50, null=True)
    cfdi = models.CharField(max_length=50, null=True)
    invoice_email = models.CharField(max_length=50, null=True)
    status = models.IntegerField(
        choices=STATUS_CHOICES, default=STATUS_GENERADA)
    invoiced_status = models.IntegerField(
        choices=INVOICED_CHOICES, default=FACTURA_PENDIENTE)
    delivered_status = models.IntegerField(
        choices=DELIVERED_CHOICES, default=SIN_ENTREGAR)
    invoice_pdf_file = models.CharField(max_length=255, null=True)
    invoice_xml_file = models.CharField(max_length=255, null=True)
    paid = models.BooleanField(default=False)
    type = models.CharField(max_length=2)
    created_at = models.DateTimeField(null=True)
    updated_at = models.DateTimeField(null=True)
