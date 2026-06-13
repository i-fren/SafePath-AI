import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class CrimeReport(models.Model):
    """Crime incidents data - uses sample data for hackathon."""
    CRIME_TYPES = [
        ('harassment', 'Harassment'),
        ('theft', 'Theft'),
        ('assault', 'Assault'),
        ('robbery', 'Robbery'),
        ('stalking', 'Stalking'),
        ('vandalism', 'Vandalism'),
        ('other', 'Other'),
    ]
    SEVERITY_CHOICES = [
        (1, 'Low'),
        (2, 'Medium'),
        (3, 'High'),
        (4, 'Critical'),
    ]

    title = models.CharField(max_length=200)
    crime_type = models.CharField(max_length=20, choices=CRIME_TYPES)
    severity = models.IntegerField(choices=SEVERITY_CHOICES, default=2)
    latitude = models.FloatField()
    longitude = models.FloatField()
    description = models.TextField(blank=True)
    date_reported = models.DateTimeField(auto_now_add=True)
    date_occurred = models.DateTimeField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)

    class Meta:
        ordering = ['-date_reported']

    def __str__(self):
        return f"{self.get_crime_type_display()} - {self.title}"


class SafetyReport(models.Model):
    """Community-submitted safety reports."""
    REPORT_TYPES = [
        ('harassment', 'Harassment'),
        ('stalking', 'Stalking'),
        ('unsafe_area', 'Unsafe Area'),
        ('broken_light', 'Broken Streetlight'),
        ('suspicious', 'Suspicious Activity'),
        ('unsafe_road', 'Unsafe Road'),
        ('safe_spot', 'Safe Spot'),
        ('other', 'Other'),
    ]
    SEVERITY_CHOICES = [
        (1, 'Low'),
        (2, 'Medium'),
        (3, 'High'),
        (4, 'Critical'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    severity = models.IntegerField(choices=SEVERITY_CHOICES, default=2)
    title = models.CharField(max_length=200)
    description = models.TextField()
    latitude = models.FloatField()
    longitude = models.FloatField()
    date_reported = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)
    upvotes = models.IntegerField(default=0)

    class Meta:
        ordering = ['-date_reported']

    def __str__(self):
        return f"{self.get_report_type_display()} - {self.title}"


class SafeZone(models.Model):
    """Known safe zones - police stations, hospitals, public areas."""
    ZONE_TYPES = [
        ('police', 'Police Station'),
        ('hospital', 'Hospital'),
        ('pharmacy', 'Pharmacy'),
        ('fire_station', 'Fire Station'),
        ('public_space', 'Public Space'),
        ('shopping', 'Shopping Area'),
        ('transit', 'Transit Station'),
        ('community_center', 'Community Center'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=200)
    zone_type = models.CharField(max_length=20, choices=ZONE_TYPES)
    latitude = models.FloatField()
    longitude = models.FloatField()
    radius = models.FloatField(default=200, help_text="Safety radius in meters")
    description = models.TextField(blank=True)
    address = models.CharField(max_length=300, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    operating_hours = models.CharField(max_length=100, blank=True, default="24/7")

    def __str__(self):
        return f"{self.get_zone_type_display()} - {self.name}"


class RouteAnalysis(models.Model):
    """Stored route analysis results."""
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    source_lat = models.FloatField()
    source_lng = models.FloatField()
    dest_lat = models.FloatField()
    dest_lng = models.FloatField()
    source_name = models.CharField(max_length=300, blank=True)
    dest_name = models.CharField(max_length=300, blank=True)
    travel_time = models.CharField(max_length=10, choices=[('day', 'Day'), ('night', 'Night')])
    safety_score = models.FloatField(default=0)
    route_type = models.CharField(max_length=20, default='safest')
    analysis_data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Route: {self.source_name} -> {self.dest_name} (Score: {self.safety_score})"


class AreaSafetyScore(models.Model):
    """Pre-calculated area safety scores for grid cells."""
    latitude = models.FloatField()
    longitude = models.FloatField()
    crime_score = models.FloatField(default=50)
    lighting_score = models.FloatField(default=50)
    crowd_score = models.FloatField(default=50)
    overall_score = models.FloatField(default=50)
    time_period = models.CharField(max_length=10, choices=[('day', 'Day'), ('night', 'Night')])
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['latitude', 'longitude', 'time_period']

    def __str__(self):
        return f"Area ({self.latitude}, {self.longitude}) - Score: {self.overall_score}"


# ============================================================
# FEATURE 1: Trusted Contacts System
# ============================================================

class TrustedContact(models.Model):
    """Trusted contacts for emergency notifications."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trusted_contacts')
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    relationship = models.CharField(max_length=50, blank=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_primary', 'name']

    def __str__(self):
        return f"{self.name} ({self.phone}) - {self.user.username}"


# ============================================================
# FEATURE 2: Live Location Sharing / Journey Tracking
# ============================================================

class Journey(models.Model):
    """Active journey with live tracking."""
    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('sos', 'SOS Triggered'),
        ('unconfirmed', 'Arrival Unconfirmed'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='journeys')
    tracking_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    source_lat = models.FloatField()
    source_lng = models.FloatField()
    dest_lat = models.FloatField()
    dest_lng = models.FloatField()
    source_name = models.CharField(max_length=300, blank=True)
    dest_name = models.CharField(max_length=300, blank=True)
    current_lat = models.FloatField(null=True, blank=True)
    current_lng = models.FloatField(null=True, blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='planned')
    safety_score = models.FloatField(default=0)
    route_data = models.JSONField(default=dict)
    eta_minutes = models.IntegerField(default=0)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    shared_contacts = models.ManyToManyField(TrustedContact, blank=True, related_name='shared_journeys')

    # Check-in timer
    checkin_interval = models.IntegerField(default=0, help_text="Check-in interval in minutes (0=disabled)")
    last_checkin = models.DateTimeField(null=True, blank=True)
    next_checkin_due = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Journey {self.tracking_id} - {self.get_status_display()}"

    @property
    def tracking_url(self):
        return f"/track/{self.tracking_id}/"

    @property
    def is_active(self):
        return self.status == 'active'


class LocationUpdate(models.Model):
    """Location updates for journey tracking."""
    journey = models.ForeignKey(Journey, on_delete=models.CASCADE, related_name='location_updates')
    latitude = models.FloatField()
    longitude = models.FloatField()
    accuracy = models.FloatField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"Location ({self.latitude}, {self.longitude}) at {self.timestamp}"


# ============================================================
# FEATURE 3: SOS Emergency System
# ============================================================

class EmergencyAlert(models.Model):
    """SOS emergency alerts."""
    ALERT_TYPES = [
        ('sos', 'SOS Emergency'),
        ('checkin_missed', 'Missed Check-In'),
        ('deviation', 'Route Deviation'),
        ('arrival_unconfirmed', 'Arrival Not Confirmed'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('acknowledged', 'Acknowledged'),
        ('resolved', 'Resolved'),
        ('false_alarm', 'False Alarm'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='emergency_alerts')
    journey = models.ForeignKey(Journey, on_delete=models.SET_NULL, null=True, blank=True, related_name='alerts')
    alert_type = models.CharField(max_length=25, choices=ALERT_TYPES, default='sos')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='active')
    latitude = models.FloatField()
    longitude = models.FloatField()
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Emergency: {self.get_alert_type_display()} by {self.user.username} at {self.created_at}"


class EmergencyContactNotification(models.Model):
    """Track notifications sent to contacts during emergencies."""
    alert = models.ForeignKey(EmergencyAlert, on_delete=models.CASCADE, related_name='notifications')
    contact = models.ForeignKey(TrustedContact, on_delete=models.CASCADE)
    notified_at = models.DateTimeField(auto_now_add=True)
    method = models.CharField(max_length=10, choices=[('sms', 'SMS'), ('email', 'Email'), ('app', 'App')])
    delivered = models.BooleanField(default=True)

    def __str__(self):
        return f"Notified {self.contact.name} via {self.method}"


# ============================================================
# FEATURE 4: Safe Arrival Confirmation
# ============================================================

class ArrivalConfirmation(models.Model):
    """Track arrival confirmations for journeys."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed Safe'),
        ('unconfirmed', 'Not Confirmed'),
        ('alert_sent', 'Alert Sent to Contacts'),
    ]

    journey = models.OneToOneField(Journey, on_delete=models.CASCADE, related_name='arrival_confirmation')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    confirmation_due_at = models.DateTimeField()
    confirmed_at = models.DateTimeField(null=True, blank=True)
    grace_period_minutes = models.IntegerField(default=5)
    alert_sent = models.BooleanField(default=False)

    def __str__(self):
        return f"Arrival: {self.journey} - {self.get_status_display()}"

    @property
    def is_overdue(self):
        if self.status == 'pending':
            return timezone.now() > self.confirmation_due_at
        return False


# ============================================================
# FEATURE 5: Safety Check-In Timer (integrated into Journey model)
# ============================================================

class JourneyCheckIn(models.Model):
    """Check-in records during a journey."""
    journey = models.ForeignKey(Journey, on_delete=models.CASCADE, related_name='checkins')
    checked_in_at = models.DateTimeField(auto_now_add=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    is_safe = models.BooleanField(default=True)
    note = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['-checked_in_at']

    def __str__(self):
        return f"Check-in at {self.checked_in_at} - {'Safe' if self.is_safe else 'Unsafe'}"


# ============================================================
# FEATURE 6: Route Deviation Detection
# ============================================================

class RouteDeviation(models.Model):
    """Track route deviation events."""
    STATUS_CHOICES = [
        ('detected', 'Detected'),
        ('user_confirmed_safe', 'User Confirmed Safe'),
        ('alert_sent', 'Alert Sent'),
        ('resolved', 'Resolved'),
    ]

    journey = models.ForeignKey(Journey, on_delete=models.CASCADE, related_name='deviations')
    latitude = models.FloatField()
    longitude = models.FloatField()
    distance_from_route = models.FloatField(help_text="Distance from expected route in meters")
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='detected')
    detected_at = models.DateTimeField(auto_now_add=True)
    user_response = models.CharField(max_length=200, blank=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-detected_at']

    def __str__(self):
        return f"Deviation: {self.distance_from_route}m from route at {self.detected_at}"


# ============================================================
# FEATURE 8: AI Safety Assistant (Chat History)
# ============================================================

class ChatMessage(models.Model):
    """AI chatbot conversation history."""
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.role}: {self.message[:50]}"


# ============================================================
# FEATURE: Fake Call Generator
# ============================================================

class FakeCallProfile(models.Model):
    """Saved fake caller profiles."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fake_call_profiles')
    caller_name = models.CharField(max_length=100, default='Ammi')
    caller_number = models.CharField(max_length=20, blank=True, default='+92 300 0000000')
    caller_photo = models.CharField(max_length=10, choices=[
        ('female1', 'Woman 1'),
        ('male1', 'Man 1'),
        ('female2', 'Woman 2'),
        ('male2', 'Man 2'),
    ], default='female1')
    delay_seconds = models.IntegerField(default=5, help_text="Delay before call rings")
    ringtone = models.CharField(max_length=20, choices=[
        ('default', 'Default Ring'),
        ('vibrate', 'Vibrate Only'),
        ('loud', 'Loud Ring'),
        ('silent', 'Silent (Screen Only)'),
    ], default='default')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Fake Call: {self.caller_name} for {self.user.username}"


# ============================================================
# FEATURE: Transport Verification
# ============================================================

class TransportLog(models.Model):
    """Log transport details for safety."""
    TRANSPORT_TYPES = [
        ('rickshaw', 'Auto Rickshaw'),
        ('taxi', 'Taxi/Cab'),
        ('careem', 'Careem'),
        ('indriver', 'InDriver'),
        ('uber', 'Uber'),
        ('bus', 'Public Bus'),
        ('private', 'Private Vehicle'),
        ('other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active Ride'),
        ('completed', 'Completed Safely'),
        ('alert', 'Alert Triggered'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transport_logs')
    journey = models.ForeignKey(Journey, on_delete=models.SET_NULL, null=True, blank=True)
    transport_type = models.CharField(max_length=20, choices=TRANSPORT_TYPES)
    plate_number = models.CharField(max_length=20)
    driver_name = models.CharField(max_length=100, blank=True)
    driver_phone = models.CharField(max_length=20, blank=True)
    vehicle_color = models.CharField(max_length=30, blank=True)
    vehicle_description = models.CharField(max_length=200, blank=True)
    pickup_lat = models.FloatField()
    pickup_lng = models.FloatField()
    pickup_address = models.CharField(max_length=300, blank=True)
    destination_address = models.CharField(max_length=300, blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='active')
    expected_duration_minutes = models.IntegerField(default=30)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    shared_with_contacts = models.BooleanField(default=True)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.get_transport_type_display()} - {self.plate_number} ({self.get_status_display()})"


# ============================================================
# FEATURE: Evidence Recording
# ============================================================

class EvidenceRecording(models.Model):
    """Secret evidence recordings."""
    RECORDING_TYPES = [
        ('audio', 'Audio Recording'),
        ('video', 'Video Recording'),
        ('photo', 'Photo Evidence'),
    ]
    STATUS_CHOICES = [
        ('recording', 'Recording'),
        ('saved', 'Saved'),
        ('uploaded', 'Uploaded to Cloud'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='evidence_recordings')
    recording_type = models.CharField(max_length=10, choices=RECORDING_TYPES)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='recording')
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    duration_seconds = models.IntegerField(default=0)
    file_size_kb = models.IntegerField(default=0)
    notes = models.TextField(blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    is_emergency = models.BooleanField(default=False)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.get_recording_type_display()} at {self.started_at}"


# ============================================================
# FEATURE: Safe Network (Women helping Women)
# ============================================================

class SafeNetworkMember(models.Model):
    """Verified women who volunteer to help nearby users."""
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('busy', 'Busy'),
        ('offline', 'Offline'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='safe_network_profile')
    is_verified = models.BooleanField(default=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='offline')
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    last_active = models.DateTimeField(auto_now=True)
    bio = models.CharField(max_length=200, blank=True)
    helped_count = models.IntegerField(default=0)
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"SafeNetwork: {self.user.username} ({self.get_status_display()})"


class SafeNetworkAlert(models.Model):
    """Alerts sent to nearby safe network members."""
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='network_help_requests')
    latitude = models.FloatField()
    longitude = models.FloatField()
    message = models.CharField(max_length=300, default='I need help nearby!')
    radius_meters = models.IntegerField(default=1000)
    members_notified = models.IntegerField(default=0)
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Network Alert by {self.requester.username} at {self.created_at}"
