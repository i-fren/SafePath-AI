from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('route-planner/', views.route_planner, name='route_planner'),
    path('community-reports/', views.community_reports, name='community_reports'),
    path('submit-report/', views.submit_report, name='submit_report'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('register/', views.register, name='register'),
    path('safety-tips/', views.safety_tips, name='safety_tips'),

    # Trusted Contacts
    path('contacts/', views.trusted_contacts, name='trusted_contacts'),
    path('contacts/add/', views.add_trusted_contact, name='add_trusted_contact'),
    path('contacts/<int:pk>/edit/', views.edit_trusted_contact, name='edit_trusted_contact'),
    path('contacts/<int:pk>/delete/', views.delete_trusted_contact, name='delete_trusted_contact'),

    # Journey / Live Tracking
    path('journey/start/', views.start_journey, name='start_journey'),
    path('journey/my/', views.my_journeys, name='my_journeys'),
    path('journey/<uuid:tracking_id>/', views.journey_detail, name='journey_detail'),
    path('journey/<uuid:tracking_id>/complete/', views.complete_journey, name='complete_journey'),
    path('track/<uuid:tracking_id>/', views.track_journey, name='track_journey'),

    # SOS
    path('sos/', views.sos_page, name='sos_page'),

    # AI Assistant
    path('ai-assistant/', views.ai_assistant, name='ai_assistant'),

    # Nearby Safe Places
    path('nearby-safe-places/', views.nearby_safe_places, name='nearby_safe_places'),

    # Fake Call
    path('fake-call/', views.fake_call, name='fake_call'),
    path('fake-call/save/', views.save_fake_call_profile, name='save_fake_call_profile'),

    # Transport Verification
    path('transport/', views.transport_verify, name='transport_verify'),
    path('transport/log/', views.log_transport, name='log_transport'),
    path('transport/<int:pk>/complete/', views.complete_transport, name='complete_transport'),

    # Evidence Recording
    path('evidence/', views.evidence_recorder, name='evidence_recorder'),

    # Safe Network
    path('safe-network/', views.safe_network, name='safe_network'),

    # Safe Time Analysis
    path('safe-time/', views.safe_time_analysis, name='safe_time_analysis'),

    # Siren & Flashlight
    path('siren/', views.siren, name='siren'),

    # Legal Rights
    path('legal-rights/', views.legal_rights, name='legal_rights'),

    # Self Defense
    path('self-defense/', views.self_defense, name='self_defense'),

    # Panic Disguise Mode
    path('disguise/', views.disguise_mode, name='disguise_mode'),

    # Safe Pickup Points
    path('safe-pickup/', views.safe_pickup, name='safe_pickup'),

    # Crowd Alerts
    path('crowd-alerts/', views.crowd_alerts, name='crowd_alerts'),
]
