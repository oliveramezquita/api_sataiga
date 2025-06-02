from rest_framework import serializers
from api.models import Lot


class LotSerializer(serializers.ModelSerializer):
    current_status = serializers.SerializerMethodField(
        "get_current_status"
    )

    def get_current_status(self, data):
        result = {
            "area": None,
            "status": None,
            "percentage": None
        }

        for area, statuses in data['status'].items():
            if area == "total" or not isinstance(statuses, dict):
                continue
            for status, value in statuses.items():
                if status == "total":
                    continue
                if value != 0:
                    result = {
                        "area": area,
                        "status": status,
                        "percentage": value
                    }
        return result

    class Meta:
        model = Lot
        fields = '__all__'
