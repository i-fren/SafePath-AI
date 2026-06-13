from django.contrib import admin
from .models import (
    CrimeReport, SafetyReport, SafeZone, RouteAnalysis, AreaSafetyScore,
    TrustedContact, Journey, LocationUpdate, EmergencyAlert,
    EmergencyContactNotification, ArrivalConfirmation, JourneyCheckIn,
    RouteDeviation, ChatMessage
)


@admin.register(CrimeReport)
class CrimeReportAdmin(admin.ModelAdmin):
    list_display = ['title', 'crime_type', 'severity', 'is_verified', 'date_reported']
    list_filter = ['crime_type', 'severity', 'is_verified']
    search_fields = ['title', 'description']


@admin.register(SafetyReport)
class SafetyReportAdmin(admin.ModelAdmin):
    list_display = ['title', 'report_type', 'severity', 'user', 'is_resolved', 'date_reported']
    list_filter = ['report_type', 'severity', 'is_resolved']
    search_fields = ['title', 'description']


@admin.register(SafeZone)
class SafeZoneAdmin(admin.ModelAdmin):
    list_display = ['name', 'zone_type', 'is_active', 'phone', 'operating_hours']
    list_filter = ['zone_type', 'is_active']
    search_fields = ['name', 'address']


@admin.register(RouteAnalysis)
class RouteAnalysisAdmin(admin.ModelAdmin):
    list_display = ['source_name', 'dest_name', 'safety_score', 'travel_time', 'created_at']
    list_filter = ['travel_time', 'route_type']


@admin.register(AreaSafetyScore)
class AreaSafetyScoreAdmin(admin.ModelAdmin):
    list_display = ['latitude', 'longitude', 'overall_score', 'time_period']
    list_filter = ['time_period']


@admin.register(TrustedContact)
class TrustedContactAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'phone', 'email', 'relationship', 'is_primary']
    list_filter = ['is_primary']
    search_fields = ['name', 'phone', 'email']


@admin.register(Journey)
class JourneyAdmin(admin.ModelAdmin):
    list_display = ['user', 'source_name', 'dest_name', 'status', 'safety_score', 'started_at']
    list_filter = ['status']
    search_fields = ['source_name', 'dest_name']
    readonly_fields = ['tracking_id']


@admin.register(LocationUpdate)
class LocationUpdateAdmin(admin.ModelAdmin):
    list_display = ['journey', 'latitude', 'longitude', 'timestamp']
    list_filter = ['timestamp']


@admin.register(EmergencyAlert)
class EmergencyAlertAdmin(admin.ModelAdmin):
    list_display = ['user', 'alert_type', 'status', 'created_at']
    list_filter = ['alert_type', 'status']
    search_fields = ['user__username', 'message']


@admin.register(EmergencyContactNotification)
class EmergencyContactNotificationAdmin(admin.ModelAdmin):
    list_display = ['alert', 'contact', 'method', 'delivered', 'notified_at']
    list_filter = ['method', 'delivered']


@admin.register(ArrivalConfirmation)
class ArrivalConfirmationAdmin(admin.ModelAdmin):
    list_display = ['journey', 'status', 'confirmation_due_at', 'confirmed_at']
    list_filter = ['status']


@admin.register(JourneyCheckIn)
class JourneyCheckInAdmin(admin.ModelAdmin):
    list_display = ['journey', 'is_safe', 'checked_in_at']
    list_filter = ['is_safe']


@admin.register(RouteDeviation)
class RouteDeviationAdmin(admin.ModelAdmin):
    list_display = ['journey', 'distance_from_route', 'status', 'detected_at']
    list_filter = ['status']


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'message', 'created_at']
    list_filter = ['role']
    search_fields = ['message']


# New Feature Models
from .models import FakeCallProfile, TransportLog, EvidenceRecording, SafeNetworkMember, SafeNetworkAlert


@admin.register(FakeCallProfile)
class FakeCallProfileAdmin(admin.ModelAdmin):
    list_display = ['caller_name', 'user', 'caller_number', 'delay_seconds', 'ringtone']
    list_filter = ['ringtone']


@admin.register(TransportLog)
class TransportLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'transport_type', 'plate_number', 'driver_name', 'status', 'started_at']
    list_filter = ['transport_type', 'status']
    search_fields = ['plate_number', 'driver_name']


@admin.register(EvidenceRecording)
class EvidenceRecordingAdmin(admin.ModelAdmin):
    list_display = ['user', 'recording_type', 'status', 'duration_seconds', 'is_emergency', 'started_at']
    list_filter = ['recording_type', 'status', 'is_emergency']


@admin.register(SafeNetworkMember)
class SafeNetworkMemberAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_verified', 'status', 'helped_count', 'last_active']
    list_filter = ['is_verified', 'status']


@admin.register(SafeNetworkAlert)
class SafeNetworkAlertAdmin(admin.ModelAdmin):
    list_display = ['requester', 'members_notified', 'is_resolved', 'created_at']
    list_filter = ['is_resolved']
