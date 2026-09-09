from rest_framework import serializers


class TechnicianSerializer(serializers.Serializer):
    _id = serializers.CharField()
    name = serializers.CharField()
    email = serializers.EmailField()
    phone = serializers.CharField()
    status = serializers.IntegerField()
    is_deleted = serializers.BooleanField()

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
