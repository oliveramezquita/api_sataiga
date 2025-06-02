import re
from api_sataiga.handlers.mongodb_handler import MongoDBHandler


class InternalCode:
    def __init__(self, name, measurement):
        self.name = name
        self.measurement = measurement
        self.internal_code = self.__create_internal_code()

    def __first_step(self):
        words = self.name.split()
        letters = [p for p in words if re.fullmatch(
            r"[A-Za-zÁÉÍÓÚÑáéíóúñ]+", p)]
        if letters:
            if len(letters[0]) == 1 and len(letters) > 1:
                return (letters[0] + letters[1]).upper()
            return letters[0].upper()
        return None

    def __second_step(self):
        text = self.measurement.strip()
        letters = ''.join(c for c in text if c.isalpha())
        if len(letters) >= 3:
            return letters[:3].upper()
        return letters.upper()

    def __third_step(self, prefix):
        with MongoDBHandler('materials') as db:
            materials = db.extract(
                {"internal_code": {"$regex": f"^{re.escape(prefix)}"}})
            numbers = []
            for material in materials:
                match = re.search(
                    rf"^{re.escape(prefix)}-(\d+)$", material["internal_code"])
                if match:
                    numbers.append(int(match.group(1)))
            if numbers:
                consecutive = max(numbers) + 1
            else:
                consecutive = 1
            return f"{consecutive:03d}"

    def __create_internal_code(self):
        internal_code = ''
        prefix = self.__first_step()
        if prefix:
            prefix = f'{prefix}-{self.__second_step()}'
            internal_code = f'{prefix}-{self.__third_step(prefix)}'
        return internal_code

    def __str__(self):
        return self.internal_code

    def value(self):
        return self.internal_code
