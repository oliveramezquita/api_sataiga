from urllib.parse import parse_qs
from api_sataiga.handlers.mongodb_handler import MongoDBHandler
from api.serializers.quantification_serializer import QuantificationSerializer
from api.helpers.http_responses import ok, not_found
from collections import defaultdict


class QuantificationUseCase:
    def __init__(self, request):
        params = parse_qs(request.META['QUERY_STRING'])
        self.client_id = params['client_id'][0] if 'client_id' in params else None
        self.front = params['front'][0] if 'front' in params else None
        self.prototype = params['prototype'][0] if 'prototype' in params else None

    def get(self):
        with MongoDBHandler('quantification') as db:
            quantification = db.extract({
                'client_id': self.client_id,
                'front': self.front,
                'prototype': self.prototype})
            if quantification:
                return ok(QuantificationSerializer(quantification[0]).data)
            return not_found("No se encontró la cuantificación para los datos proporcionados.")

    def filters(self):
        with MongoDBHandler('quantification') as db:
            quantification = db.extract({'client_id': self.client_id})
            if quantification:
                result = defaultdict(list)
                for item in quantification:
                    result[item['front']].append(item['prototype'])
                output = [{k: v} for k, v in result.items()]
                return ok(output)
            return not_found("No se encontraron elementos con el cliente proporcionado.")
