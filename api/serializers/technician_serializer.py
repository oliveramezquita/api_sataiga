from rest_framework import serializers
from after_sales.models import Technician


class TechnicianSerializer(serializers.ModelSerializer):

    schedule = serializers.SerializerMethodField(
        "get_schedule"
    )

    blocked_dates = serializers.SerializerMethodField(
        "get_blocked_dates"
    )

    def get_schedule(self, data):
        schedule = data.get('schedule')
        if serializers:
            return {
                day: [
                    f"{slot['start']}-{slot['end']}"
                    for slot in times
                ]
                for day, times in schedule.items()
            }
        return None

    def get_blocked_dates(self, data):
        blocked_dates = data.get('blocked_dates')
        if blocked_dates:
            return ", ".join(blocked_dates)

    class Meta:
        model = Technician
        fields = '__all__'
