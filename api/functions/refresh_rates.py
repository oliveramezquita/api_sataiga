import logging
import pytz
from api_sataiga.handlers.mongodb_handler import MongoDBHandler
from datetime import datetime
from api.constants import REFRESH_RATES
from dateutil.relativedelta import relativedelta
from bson import ObjectId
from api.helpers.validations import objectid_validation
from celery import shared_task
from api_sataiga.functions import send_notification
from api.helpers.get_message import get_message


log = logging.getLogger(__name__)


def adjust_to_monday(date):
    if date.weekday() == 5:
        date += relativedelta(days=2)
    elif date.weekday() == 6:
        date += relativedelta(days=1)
    return date


def increase_date(date, refresh_rate):
    if refresh_rate in REFRESH_RATES:
        new_date = date + REFRESH_RATES[refresh_rate]
        return adjust_to_monday(new_date)
    return date


def check_supplier(db, supplier_id):
    supplier = MongoDBHandler.find(db, 'suppliers', {'_id': ObjectId(
        supplier_id)}) if objectid_validation(supplier_id) else None
    if supplier:
        return supplier[0]['name']
    return ''


def format_list(suppliers):
    if len(suppliers) > 1:
        return ', '.join(suppliers[:-1]) + ' y ' + suppliers[-1]
    elif len(suppliers) == 1:
        return suppliers[0]
    else:
        return ''


@shared_task
def refresh_rates():
    with MongoDBHandler('refresh_rate') as db:
        data = db.extract()
        suppliers = []
        message = ''
        if data:
            today = datetime.now(pytz.timezone('America/Mexico_City')).date()
            for item in data:
                item_date = datetime.strptime(
                    item['next_date'], '%Y-%m-%d').date()
                if today == item_date:
                    new_date = increase_date(
                        item_date, item['value'])
                    db.update({'_id': item['_id']}, {
                        'next_date': new_date.strftime('%Y-%m-%d')})
                    suppliers.append(check_supplier(db, item['supplier_id']))
            if len(suppliers) > 0:
                message = f"REFRESH_RATES: {len(suppliers)} fecha(s) de la frecuencia de actualización fueron modificadas, proveedores: {format_list(suppliers)}."
                send_notification(get_message(
                    'refresh_rates', f'Los siguientes proveedores requieren actualización de precios en sus materiales: {format_list(suppliers)}.'))
            else:
                message = "REFRESH_RATES: No se reealizaron cambios en la frecuencia de actualización."
            log.info(message)
            return message
        return "REFRESH_RATES: No existen datos en la frecuencia de actualización."
