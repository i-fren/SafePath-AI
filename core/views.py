from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.db.models import Count, Avg
from django.utils import timezone
from .models import (
    CrimeReport, SafetyReport, SafeZone, RouteAnalysis,
    TrustedContact, Journey, EmergencyAlert, JourneyCheckIn,
    ArrivalConfirmation, LocationUpdate, RouteDeviation, ChatMessage,
    FakeCallProfile, TransportLog, EvidenceRecording,
    SafeNetworkMember, SafeNetworkAlert
)
from .forms import TrustedContactForm, SafetyReportForm


def home(request):
    """Landing page with route search."""
    context = {
        'total_reports': SafetyReport.objects.count(),
        'total_crimes': CrimeReport.objects.count(),
        'total_safe_zones': SafeZone.objects.filter(is_active=True).count(),
        'total_analyses': RouteAnalysis.objects.count(),
        'total_journeys': Journey.objects.count(),
        'active_journeys': Journey.objects.filter(status='active').count(),
    }
    return render(request, 'core/home.html', context)


def route_planner(request):
    """Interactive route planner with map."""
    safe_zones = SafeZone.objects.filter(is_active=True)
    crime_reports = CrimeReport.objects.all()[:100]
    context = {
        'safe_zones': safe_zones,
        'crime_reports': crime_reports,
    }
    return render(request, 'core/route_planner.html', context)


def community_reports(request):
    """Community safety reports page."""
    reports = SafetyReport.objects.all()[:50]
    return render(request, 'core/community_reports.html', {'reports': reports})


@login_required
def submit_report(request):
    """Submit a new safety report."""
    if request.method == 'POST':
        form = SafetyReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.user = request.user
            report.save()
            messages.success(request, 'Report submitted successfully! Thank you for keeping the community safe.')
            return redirect('community_reports')
    else:
        form = SafetyReportForm()
    return render(request, 'core/submit_report.html', {'form': form})


@login_required
def dashboard(request):
    """Admin/user dashboard with analytics."""
    crime_by_type = CrimeReport.objects.values('crime_type').annotate(
        count=Count('id')
    ).order_by('-count')

    reports_by_type = SafetyReport.objects.values('report_type').annotate(
        count=Count('id')
    ).order_by('-count')

    recent_reports = SafetyReport.objects.all()[:10]
    recent_crimes = CrimeReport.objects.all()[:10]
    active_journeys = Journey.objects.filter(status='active')
    sos_alerts = EmergencyAlert.objects.filter(status='active')
    recent_alerts = EmergencyAlert.objects.all()[:10]

    context = {
        'crime_by_type': list(crime_by_type),
        'reports_by_type': list(reports_by_type),
        'recent_reports': recent_reports,
        'recent_crimes': recent_crimes,
        'total_crimes': CrimeReport.objects.count(),
        'total_reports': SafetyReport.objects.count(),
        'total_safe_zones': SafeZone.objects.filter(is_active=True).count(),
        'avg_safety_score': RouteAnalysis.objects.aggregate(avg=Avg('safety_score'))['avg'] or 0,
        'total_journeys': Journey.objects.count(),
        'active_journeys': active_journeys,
        'active_journey_count': active_journeys.count(),
        'sos_alerts': sos_alerts,
        'sos_alert_count': sos_alerts.count(),
        'recent_alerts': recent_alerts,
    }
    return render(request, 'core/dashboard.html', context)


def register(request):
    """User registration."""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'core/register.html', {'form': form})


def safety_tips(request):
    """Safety tips and resources page."""
    return render(request, 'core/safety_tips.html')


# ============================================================
# TRUSTED CONTACTS
# ============================================================

@login_required
def trusted_contacts(request):
    """Manage trusted contacts."""
    contacts = TrustedContact.objects.filter(user=request.user)
    return render(request, 'core/trusted_contacts.html', {'contacts': contacts})


@login_required
def add_trusted_contact(request):
    """Add a new trusted contact."""
    if request.method == 'POST':
        form = TrustedContactForm(request.POST)
        if form.is_valid():
            contact = form.save(commit=False)
            contact.user = request.user
            contact.save()
            messages.success(request, f'{contact.name} added as trusted contact.')
            return redirect('trusted_contacts')
    else:
        form = TrustedContactForm()
    return render(request, 'core/add_trusted_contact.html', {'form': form})


@login_required
def edit_trusted_contact(request, pk):
    """Edit a trusted contact."""
    contact = get_object_or_404(TrustedContact, pk=pk, user=request.user)
    if request.method == 'POST':
        form = TrustedContactForm(request.POST, instance=contact)
        if form.is_valid():
            form.save()
            messages.success(request, f'{contact.name} updated successfully.')
            return redirect('trusted_contacts')
    else:
        form = TrustedContactForm(instance=contact)
    return render(request, 'core/edit_trusted_contact.html', {'form': form, 'contact': contact})


@login_required
def delete_trusted_contact(request, pk):
    """Delete a trusted contact."""
    contact = get_object_or_404(TrustedContact, pk=pk, user=request.user)
    if request.method == 'POST':
        name = contact.name
        contact.delete()
        messages.success(request, f'{name} removed from trusted contacts.')
    return redirect('trusted_contacts')


# ============================================================
# JOURNEY / LIVE TRACKING
# ============================================================

@login_required
def start_journey(request):
    """Start a new journey with tracking."""
    contacts = TrustedContact.objects.filter(user=request.user)
    if request.method == 'POST':
        journey = Journey.objects.create(
            user=request.user,
            source_lat=float(request.POST.get('source_lat', 0)),
            source_lng=float(request.POST.get('source_lng', 0)),
            dest_lat=float(request.POST.get('dest_lat', 0)),
            dest_lng=float(request.POST.get('dest_lng', 0)),
            source_name=request.POST.get('source_name', ''),
            dest_name=request.POST.get('dest_name', ''),
            status='active',
            started_at=timezone.now(),
            checkin_interval=int(request.POST.get('checkin_interval', 0)),
            current_lat=float(request.POST.get('source_lat', 0)),
            current_lng=float(request.POST.get('source_lng', 0)),
            eta_minutes=int(request.POST.get('eta_minutes', 30)),
        )
        # Set check-in timer
        if journey.checkin_interval > 0:
            journey.last_checkin = timezone.now()
            journey.next_checkin_due = timezone.now() + timezone.timedelta(minutes=journey.checkin_interval)
            journey.save()

        # Create arrival confirmation
        eta = timezone.now() + timezone.timedelta(minutes=journey.eta_minutes)
        ArrivalConfirmation.objects.create(
            journey=journey,
            confirmation_due_at=eta + timezone.timedelta(minutes=5),
        )

        # Add shared contacts
        contact_ids = request.POST.getlist('contacts')
        if contact_ids:
            journey.shared_contacts.set(TrustedContact.objects.filter(id__in=contact_ids, user=request.user))

        messages.success(request, 'Journey started! Share your tracking link with trusted contacts.')
        return redirect('journey_detail', tracking_id=journey.tracking_id)

    return render(request, 'core/start_journey.html', {'contacts': contacts})


@login_required
def my_journeys(request):
    """List user's journeys."""
    journeys = Journey.objects.filter(user=request.user)
    return render(request, 'core/my_journeys.html', {'journeys': journeys})


@login_required
def journey_detail(request, tracking_id):
    """Journey detail for the owner."""
    journey = get_object_or_404(Journey, tracking_id=tracking_id, user=request.user)
    safe_zones = SafeZone.objects.filter(is_active=True)
    return render(request, 'core/journey_detail.html', {'journey': journey, 'safe_zones': safe_zones})


def track_journey(request, tracking_id):
    """Public tracking page - anyone with the link can view."""
    journey = get_object_or_404(Journey, tracking_id=tracking_id)
    return render(request, 'core/track_journey.html', {'journey': journey})


@login_required
def complete_journey(request, tracking_id):
    """Mark journey as completed / confirm arrival."""
    journey = get_object_or_404(Journey, tracking_id=tracking_id, user=request.user)
    journey.status = 'completed'
    journey.completed_at = timezone.now()
    journey.save()

    # Update arrival confirmation
    if hasattr(journey, 'arrival_confirmation'):
        journey.arrival_confirmation.status = 'confirmed'
        journey.arrival_confirmation.confirmed_at = timezone.now()
        journey.arrival_confirmation.save()

    messages.success(request, 'Journey completed! Glad you arrived safely.')
    return redirect('my_journeys')


# ============================================================
# SOS EMERGENCY
# ============================================================

@login_required
def sos_page(request):
    """SOS emergency page."""
    contacts = TrustedContact.objects.filter(user=request.user)
    active_journey = Journey.objects.filter(user=request.user, status='active').first()
    nearby_zones = SafeZone.objects.filter(is_active=True)[:10]
    return render(request, 'core/sos.html', {
        'contacts': contacts,
        'active_journey': active_journey,
        'nearby_zones': nearby_zones,
    })


# ============================================================
# AI SAFETY ASSISTANT
# ============================================================

@login_required
def ai_assistant(request):
    """AI Safety Assistant chatbot page."""
    chat_history = ChatMessage.objects.filter(user=request.user).order_by('-created_at')[:50]
    return render(request, 'core/ai_assistant.html', {'chat_history': reversed(list(chat_history))})


# ============================================================
# NEARBY SAFE PLACES
# ============================================================

def nearby_safe_places(request):
    """Nearby safe places map."""
    safe_zones = SafeZone.objects.filter(is_active=True)
    zone_types = SafeZone.ZONE_TYPES
    return render(request, 'core/nearby_safe_places.html', {
        'safe_zones': safe_zones,
        'zone_types': zone_types,
    })


# ============================================================
# FAKE CALL GENERATOR
# ============================================================

@login_required
def fake_call(request):
    """Fake call generator page."""
    from .models import FakeCallProfile
    profiles = FakeCallProfile.objects.filter(user=request.user)
    return render(request, 'core/fake_call.html', {'profiles': profiles})


@login_required
def save_fake_call_profile(request):
    """Save a fake call profile."""
    from .models import FakeCallProfile
    if request.method == 'POST':
        FakeCallProfile.objects.create(
            user=request.user,
            caller_name=request.POST.get('caller_name', 'Mom'),
            caller_number=request.POST.get('caller_number', '+92 300 0000000'),
            delay_seconds=int(request.POST.get('delay_seconds', 5)),
            ringtone=request.POST.get('ringtone', 'default'),
        )
        messages.success(request, 'Fake call profile saved!')
    return redirect('fake_call')


# ============================================================
# TRANSPORT VERIFICATION
# ============================================================

@login_required
def transport_verify(request):
    """Transport verification page."""
    from .models import TransportLog
    active_rides = TransportLog.objects.filter(user=request.user, status='active')
    recent_rides = TransportLog.objects.filter(user=request.user)[:10]
    contacts = TrustedContact.objects.filter(user=request.user)
    return render(request, 'core/transport_verify.html', {
        'active_rides': active_rides,
        'recent_rides': recent_rides,
        'contacts': contacts,
    })


@login_required
def log_transport(request):
    """Log a new transport."""
    from .models import TransportLog
    if request.method == 'POST':
        log = TransportLog.objects.create(
            user=request.user,
            transport_type=request.POST.get('transport_type', 'rickshaw'),
            plate_number=request.POST.get('plate_number', ''),
            driver_name=request.POST.get('driver_name', ''),
            driver_phone=request.POST.get('driver_phone', ''),
            vehicle_color=request.POST.get('vehicle_color', ''),
            vehicle_description=request.POST.get('vehicle_description', ''),
            pickup_lat=float(request.POST.get('pickup_lat', 0)),
            pickup_lng=float(request.POST.get('pickup_lng', 0)),
            pickup_address=request.POST.get('pickup_address', ''),
            destination_address=request.POST.get('destination_address', ''),
            expected_duration_minutes=int(request.POST.get('expected_duration', 30)),
        )
        messages.success(request, f'Transport logged! Plate: {log.plate_number}. Details shared with contacts.')
        return redirect('transport_verify')
    return redirect('transport_verify')


@login_required
def complete_transport(request, pk):
    """Mark transport as completed."""
    from .models import TransportLog
    log = get_object_or_404(TransportLog, pk=pk, user=request.user)
    log.status = 'completed'
    log.completed_at = timezone.now()
    log.save()
    messages.success(request, 'Ride completed safely!')
    return redirect('transport_verify')


# ============================================================
# EVIDENCE RECORDING
# ============================================================

@login_required
def evidence_recording(request):
    """Evidence recording page."""
    from .models import EvidenceRecording
    recordings = EvidenceRecording.objects.filter(user=request.user)[:20]
    return render(request, 'core/evidence_recording.html', {'recordings': recordings})


# ============================================================
# SAFE NETWORK
# ============================================================

@login_required
def safe_network(request):
    """Safe network - women helping women."""
    from .models import SafeNetworkMember, SafeNetworkAlert
    try:
        profile = SafeNetworkMember.objects.get(user=request.user)
    except SafeNetworkMember.DoesNotExist:
        profile = None
    members_count = SafeNetworkMember.objects.filter(is_verified=True, status='available').count()
    recent_alerts = SafeNetworkAlert.objects.filter(is_resolved=False)[:5]
    return render(request, 'core/safe_network.html', {
        'profile': profile,
        'members_count': members_count,
        'recent_alerts': recent_alerts,
    })


@login_required
def join_safe_network(request):
    """Join the safe network."""
    from .models import SafeNetworkMember
    if request.method == 'POST':
        member, created = SafeNetworkMember.objects.get_or_create(user=request.user)
        member.is_verified = True
        member.status = 'available'
        member.bio = request.POST.get('bio', '')
        member.save()
        messages.success(request, 'Welcome to SafePath Network! You can now help women nearby.')
    return redirect('safe_network')


# ============================================================
# SAFE TIME ANALYSIS
# ============================================================

def safe_time_analysis(request):
    """Safe time analysis for routes."""
    return render(request, 'core/safe_time_analysis.html')


# ============================================================
# FAKE CALL GENERATOR
# ============================================================

@login_required
def fake_call(request):
    """Fake call generator page."""
    profiles = FakeCallProfile.objects.filter(user=request.user)
    return render(request, 'core/fake_call.html', {'profiles': profiles})


@login_required
def save_fake_call_profile(request):
    """Save a fake call profile."""
    if request.method == 'POST':
        FakeCallProfile.objects.create(
            user=request.user,
            caller_name=request.POST.get('caller_name', 'Ammi'),
            caller_number=request.POST.get('caller_number', '+92 300 0000000'),
            caller_photo=request.POST.get('caller_photo', 'female1'),
            delay_seconds=int(request.POST.get('delay_seconds', 5)),
            ringtone=request.POST.get('ringtone', 'default'),
        )
        messages.success(request, 'Fake call profile saved!')
    return redirect('fake_call')


# ============================================================
# TRANSPORT VERIFICATION
# ============================================================

@login_required
def transport_verify(request):
    """Transport verification page."""
    active_rides = TransportLog.objects.filter(user=request.user, status='active')
    past_rides = TransportLog.objects.filter(user=request.user).exclude(status='active')[:20]
    contacts = TrustedContact.objects.filter(user=request.user)
    return render(request, 'core/transport_verify.html', {
        'active_rides': active_rides,
        'past_rides': past_rides,
        'contacts': contacts,
    })


@login_required
def log_transport(request):
    """Log a new transport ride."""
    if request.method == 'POST':
        log = TransportLog.objects.create(
            user=request.user,
            transport_type=request.POST.get('transport_type', 'rickshaw'),
            plate_number=request.POST.get('plate_number', ''),
            driver_name=request.POST.get('driver_name', ''),
            driver_phone=request.POST.get('driver_phone', ''),
            vehicle_color=request.POST.get('vehicle_color', ''),
            vehicle_description=request.POST.get('vehicle_description', ''),
            pickup_lat=float(request.POST.get('pickup_lat', 0)),
            pickup_lng=float(request.POST.get('pickup_lng', 0)),
            pickup_address=request.POST.get('pickup_address', ''),
            destination_address=request.POST.get('destination_address', ''),
            expected_duration_minutes=int(request.POST.get('expected_duration', 30)),
        )
        messages.success(request, f'Transport logged! Plate: {log.plate_number}. Shared with your contacts.')
        return redirect('transport_verify')
    return redirect('transport_verify')


@login_required
def complete_transport(request, pk):
    """Mark transport as completed safely."""
    log = get_object_or_404(TransportLog, pk=pk, user=request.user)
    log.status = 'completed'
    log.completed_at = timezone.now()
    log.save()
    messages.success(request, 'Ride completed safely!')
    return redirect('transport_verify')


# ============================================================
# EVIDENCE RECORDING
# ============================================================

@login_required
def evidence_recorder(request):
    """Evidence recording page."""
    recordings = EvidenceRecording.objects.filter(user=request.user)[:20]
    return render(request, 'core/evidence_recorder.html', {'recordings': recordings})


# ============================================================
# SAFE NETWORK
# ============================================================

@login_required
def safe_network(request):
    """Women's safe network page."""
    # Get or create network profile
    profile, created = SafeNetworkMember.objects.get_or_create(
        user=request.user,
        defaults={'status': 'offline'}
    )
    nearby_members = SafeNetworkMember.objects.filter(
        status='available', is_verified=True
    ).exclude(user=request.user)[:20]
    my_alerts = SafeNetworkAlert.objects.filter(requester=request.user)[:10]
    return render(request, 'core/safe_network.html', {
        'profile': profile,
        'nearby_members': nearby_members,
        'my_alerts': my_alerts,
    })


# ============================================================
# SAFE TIME RECOMMENDATIONS
# ============================================================

def safe_time_analysis(request):
    """Safe time analysis for routes."""
    return render(request, 'core/safe_time_analysis.html')
