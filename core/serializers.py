from rest_framework import serializers
from .models import (
    CrimeReport, SafetyReport, SafeZone, RouteAnalysis,
    TrustedContact, Journey, EmergencyAlert, LocationUpdate,
    JourneyCheckIn, RouteDeviation, ArrivalConfirmation, ChatMessage
)


class CrimeReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrimeReport
        fields = '__all__'


class SafetyReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = SafetyReport
        fields = '__all__'


class SafeZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = SafeZone
        fields = '__all__'


class RouteAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = RouteAnalysis
        fields = '__all__'


class RouteRequestSerializer(serializers.Serializer):
    source_lat = serializers.FloatField()
    source_lng = serializers.FloatField()
    dest_lat = serializers.FloatField()
    dest_lng = serializers.FloatField()
    source_name = serializers.CharField(max_length=300, required=False, default='')
    dest_name = serializers.CharField(max_length=300, required=False, default='')
    travel_time = serializers.ChoiceField(choices=['day', 'night'])


class TrustedContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrustedContact
        fields = ['id', 'name', 'phone', 'email', 'relationship', 'is_primary', 'created_at']


class LocationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocationUpdate
        fields = ['latitude', 'longitude', 'accuracy', 'timestamp']


class JourneySerializer(serializers.ModelSerializer):
    tracking_url = serializers.ReadOnlyField()
    shared_contacts = TrustedContactSerializer(many=True, read_only=True)

    class Meta:
        model = Journey
        fields = [
            'id', 'tracking_id', 'source_lat', 'source_lng', 'dest_lat', 'dest_lng',
            'source_name', 'dest_name', 'current_lat', 'current_lng', 'status',
            'safety_score', 'eta_minutes', 'started_at', 'completed_at',
            'checkin_interval', 'next_checkin_due', 'tracking_url', 'shared_contacts'
        ]


class EmergencyAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmergencyAlert
        fields = '__all__'


class JourneyCheckInSerializer(serializers.ModelSerializer):
    class Meta:
        model = JourneyCheckIn
        fields = '__all__'


class RouteDeviationSerializer(serializers.ModelSerializer):
    class Meta:
        model = RouteDeviation
        fields = '__all__'


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['id', 'role', 'message', 'created_at']
