from api.repositories.base_repository import BaseRepository


class InvoiceRepository(BaseRepository):
    """Acceso a la colección 'invoices' en MongoDB."""
    COLLECTION = 'invoices'

    def get_next_invoice_folio_sequence(self):
        with self.db_handler as db:
            return db.set_next_folio('invoice')
