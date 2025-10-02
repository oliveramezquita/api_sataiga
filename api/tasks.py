import json
import os
import shutil
import zipfile
from celery import shared_task
from pymongo import MongoClient
from datetime import datetime
from django.conf import settings


@shared_task
def backup_mongodb():
    uri = "mongodb://{}:{}@{}:{}?authSource=admin".format(
        settings.MONGO_DB['USER'],
        settings.MONGO_DB['PASS'],
        settings.MONGO_DB['HOST'],
        settings.MONGO_DB['PORT']
    )
    client = MongoClient(uri)
    db = client["bellarti"]

    backup_dir = "backups/mongodb"
    os.makedirs(backup_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_dir = os.path.join(backup_dir, f"temp_{timestamp}")
    os.makedirs(temp_dir, exist_ok=True)

    # Guardar lista de colecciones antes de cerrar conexión
    collections = db.list_collection_names()

    # Crear archivos JSON individuales
    for collection_name in collections:
        collection = db[collection_name]
        data = list(collection.find({}))

        # TODO: Revisar el serialize porque al momento de resturar los ObjectId se pierden
        def serialize(obj):
            if hasattr(obj, "isoformat"):
                return obj.isoformat()
            return str(obj)

        file_path = os.path.join(temp_dir, f"{collection_name}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, default=serialize, ensure_ascii=False, indent=2)

    # Crear archivo ZIP con todos los JSON
    zip_filename = os.path.join(backup_dir, f"backup_{timestamp}.zip")
    with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, temp_dir)
                zipf.write(file_path, arcname)

    # Eliminar carpeta temporal
    shutil.rmtree(temp_dir)

    # Ahora sí, cerrar cliente
    client.close()

    return f"Respaldo creado: {zip_filename} con {len(collections)} colecciones."
