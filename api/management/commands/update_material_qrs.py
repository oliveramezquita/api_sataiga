from django.core.management.base import BaseCommand

from api_sataiga.handlers.mongodb_handler import MongoDBHandler
from api.use_cases.material_use_case import MaterialUseCase


class Command(BaseCommand):
    help = "Genera/actualiza los códigos QR de todos los materiales."

    def handle(self, *args, **options):
        success = 0
        errors = 0

        with MongoDBHandler("materials") as db:
            materials = db.extract()

        total = len(materials)

        self.stdout.write(
            self.style.SUCCESS(
                f"Se encontraron {total} materiales."
            )
        )

        for index, material in enumerate(materials, start=1):
            material_id = str(material["_id"])

            try:
                MaterialUseCase(
                    id=material_id
                ).create_qr_image()

                success += 1

                self.stdout.write(
                    f"[{index}/{total}] QR actualizado: {material_id}"
                )

            except Exception as e:
                errors += 1

                self.stdout.write(
                    self.style.ERROR(
                        f"[{index}/{total}] Error en {material_id}: {e}"
                    )
                )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Proceso terminado. Exitosos: {success} | Errores: {errors}"
            )
        )
