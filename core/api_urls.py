from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

router = DefaultRouter()
router.register(r'crimes', api_views.CrimeReportViewSet)
router.register(r'reports', api_views.SafetyReportViewSet)
router.register(r'safe-zones', api_views.SafeZoneViewSet)
router.register(r'analyses', api_views.RouteAnalysisViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('analyze-route/', api_views.analyze_route_api, name='analyze_route'),
    path('crime-heatmap/', api_views.get_crime_heatmap, name='crime_heatmap'),
    path('safe-zones-map/', api_views.get_safe_zones_map, name='safe_zones_map'),
    path('safety-tips/', api_views.get_safety_tips_api, name='safety_tips_api'),
    path('dashboard-stats/', api_views.dashboard_stats, name='dashboard_stats'),
    path('safety-score/', api_views.safety_score_api, name='safety_score_api'),

    # Trusted Contacts
    path('contacts/', api_views.trusted_contacts_api, name='contacts_api'),
    path('contacts/<int:pk>/delete/', api_views.delete_trusted_contact_api, name='delete_contact_api'),

    # Journey / Tracking
    path('journey/start/', api_views.start_journey_api, name='start_journey_api'),
    path('journey/<uuid:tracking_id>/location/', api_views.update_location_api, name='update_location'),
    path('journey/<uuid:tracking_id>/status/', api_views.get_journey_status, name='journey_status'),
    path('journey/<uuid:tracking_id>/complete/', api_views.complete_journey_api, name='complete_journey_api'),
    path('journey/<uuid:tracking_id>/checkin/', api_views.checkin_api, name='checkin_api'),
    path('journey/<uuid:tracking_id>/deviation-safe/', api_views.confirm_deviation_safe, name='deviation_safe'),

    # SOS
    path('sos/trigger/', api_views.trigger_sos, name='trigger_sos'),
    path('sos/shake/', api_views.shake_sos_api, name='shake_sos'),
    path('sos/<int:alert_id>/resolve/', api_views.resolve_sos, name='resolve_sos'),

    # Nearby Safe Places
    path('nearby-places/', api_views.nearby_safe_places_api, name='nearby_places_api'),

    # AI Assistant
    path('chat/', api_views.chat_api, name='chat_api'),
    path('chat/history/', api_views.chat_history_api, name='chat_history'),

    # Fake Call
    path('fake-call/profiles/', api_views.fake_call_profiles_api, name='fake_call_profiles_api'),

    # Transport Verification
    path('transport/log/', api_views.log_transport_api, name='log_transport_api'),
    path('transport/<int:pk>/complete/', api_views.complete_transport_api, name='complete_transport_api'),
    path('transport/history/', api_views.transport_history_api, name='transport_history_api'),

    # Evidence Recording
    path('evidence/start/', api_views.start_recording_api, name='start_recording_api'),
    path('evidence/<int:pk>/stop/', api_views.stop_recording_api, name='stop_recording_api'),

    # Safe Network
    path('network/status/', api_views.update_network_status, name='network_status'),
    path('network/alert/', api_views.send_network_alert, name='network_alert'),
    path('network/nearby/', api_views.nearby_network_members, name='network_nearby'),

    # Safe Time Analysis
    path('safe-time/', api_views.safe_time_analysis_api, name='safe_time_api'),
]
