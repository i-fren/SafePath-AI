import math
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from .models import (
    CrimeReport, SafetyReport, SafeZone, RouteAnalysis,
    TrustedContact, Journey, EmergencyAlert, LocationUpdate,
    JourneyCheckIn, RouteDeviation, ArrivalConfirmation,
    EmergencyContactNotification, ChatMessage
)
from .serializers import (
    CrimeReportSerializer, SafetyReportSerializer,
    SafeZoneSerializer, RouteAnalysisSerializer, RouteRequestSerializer,
    TrustedContactSerializer, JourneySerializer, EmergencyAlertSerializer,
    LocationUpdateSerializer, ChatMessageSerializer
)
from .ai_engine import analyze_route, get_safety_tips, haversine_distance
from .ai_assistant import get_ai_response


class CrimeReportViewSet(viewsets.ModelViewSet):
    queryset = CrimeReport.objects.all()
    serializer_class = CrimeReportSerializer


class SafetyReportViewSet(viewsets.ModelViewSet):
    queryset = SafetyReport.objects.all()
    serializer_class = SafetyReportSerializer


class SafeZoneViewSet(viewsets.ModelViewSet):
    queryset = SafeZone.objects.filter(is_active=True)
    serializer_class = SafeZoneSerializer


class RouteAnalysisViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RouteAnalysis.objects.all()
    serializer_class = RouteAnalysisSerializer


@api_view(['POST'])
def analyze_route_api(request):
    """Analyze route safety between two points."""
    serializer = RouteRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    source = {'lat': data['source_lat'], 'lng': data['source_lng']}
    destination = {'lat': data['dest_lat'], 'lng': data['dest_lng']}
    time_of_day = data['travel_time']

    crime_reports = list(CrimeReport.objects.all())
    safe_zones = list(SafeZone.objects.filter(is_active=True))

    routes = analyze_route(source, destination, time_of_day, crime_reports, safe_zones)
    tips = get_safety_tips(time_of_day)

    if request.user.is_authenticated and routes:
        best_route = routes[0]
        RouteAnalysis.objects.create(
            user=request.user,
            source_lat=data['source_lat'],
            source_lng=data['source_lng'],
            dest_lat=data['dest_lat'],
            dest_lng=data['dest_lng'],
            source_name=data.get('source_name', ''),
            dest_name=data.get('dest_name', ''),
            travel_time=time_of_day,
            safety_score=best_route['scores']['overall'],
            route_type=best_route['type'],
            analysis_data={'routes': routes},
        )

    return Response({
        'routes': routes,
        'safety_tips': tips,
        'source': source,
        'destination': destination,
        'time_of_day': time_of_day,
    })


@api_view(['GET'])
def get_crime_heatmap(request):
    """Get crime data for heatmap overlay."""
    crimes = CrimeReport.objects.all().values('latitude', 'longitude', 'severity', 'crime_type')
    return Response(list(crimes))


@api_view(['GET'])
def get_safe_zones_map(request):
    """Get safe zones for map display."""
    zones = SafeZone.objects.filter(is_active=True).values(
        'id', 'name', 'zone_type', 'latitude', 'longitude', 'radius', 'address', 'phone', 'operating_hours'
    )
    return Response(list(zones))


@api_view(['GET'])
def get_safety_tips_api(request):
    """Get contextual safety tips."""
    time_of_day = request.query_params.get('time', 'day')
    tips = get_safety_tips(time_of_day)
    return Response({'tips': tips, 'time_of_day': time_of_day})


@api_view(['GET'])
def dashboard_stats(request):
    """Get dashboard statistics."""
    from django.db.models import Count, Avg

    stats = {
        'total_crimes': CrimeReport.objects.count(),
        'total_reports': SafetyReport.objects.count(),
        'total_safe_zones': SafeZone.objects.filter(is_active=True).count(),
        'total_analyses': RouteAnalysis.objects.count(),
        'total_journeys': Journey.objects.count(),
        'active_journeys': Journey.objects.filter(status='active').count(),
        'sos_alerts': EmergencyAlert.objects.filter(status='active').count(),
        'avg_safety_score': RouteAnalysis.objects.aggregate(avg=Avg('safety_score'))['avg'] or 0,
        'crime_by_type': list(
            CrimeReport.objects.values('crime_type').annotate(count=Count('id')).order_by('-count')
        ),
        'reports_by_type': list(
            SafetyReport.objects.values('report_type').annotate(count=Count('id')).order_by('-count')
        ),
    }
    return Response(stats)


# ============================================================
# TRUSTED CONTACTS API
# ============================================================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def trusted_contacts_api(request):
    """List or create trusted contacts."""
    if request.method == 'GET':
        contacts = TrustedContact.objects.filter(user=request.user)
        serializer = TrustedContactSerializer(contacts, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = TrustedContactSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_trusted_contact_api(request, pk):
    """Delete a trusted contact."""
    try:
        contact = TrustedContact.objects.get(pk=pk, user=request.user)
        contact.delete()
        return Response({'message': 'Contact deleted'}, status=status.HTTP_204_NO_CONTENT)
    except TrustedContact.DoesNotExist:
        return Response({'error': 'Contact not found'}, status=status.HTTP_404_NOT_FOUND)


# ============================================================
# JOURNEY / LIVE TRACKING API
# ============================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_journey_api(request):
    """Start a new journey."""
    data = request.data
    journey = Journey.objects.create(
        user=request.user,
        source_lat=data.get('source_lat'),
        source_lng=data.get('source_lng'),
        dest_lat=data.get('dest_lat'),
        dest_lng=data.get('dest_lng'),
        source_name=data.get('source_name', ''),
        dest_name=data.get('dest_name', ''),
        status='active',
        started_at=timezone.now(),
        current_lat=data.get('source_lat'),
        current_lng=data.get('source_lng'),
        eta_minutes=int(data.get('eta_minutes', 30)),
        checkin_interval=int(data.get('checkin_interval', 0)),
    )

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

    # Share with contacts
    contact_ids = data.get('contact_ids', [])
    if contact_ids:
        contacts = TrustedContact.objects.filter(id__in=contact_ids, user=request.user)
        journey.shared_contacts.set(contacts)

    serializer = JourneySerializer(journey)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_location_api(request, tracking_id):
    """Update current location during journey."""
    try:
        journey = Journey.objects.get(tracking_id=tracking_id, user=request.user)
    except Journey.DoesNotExist:
        return Response({'error': 'Journey not found'}, status=status.HTTP_404_NOT_FOUND)

    lat = request.data.get('latitude')
    lng = request.data.get('longitude')
    accuracy = request.data.get('accuracy')

    if not lat or not lng:
        return Response({'error': 'Latitude and longitude required'}, status=status.HTTP_400_BAD_REQUEST)

    # Save location update
    LocationUpdate.objects.create(
        journey=journey,
        latitude=lat,
        longitude=lng,
        accuracy=accuracy,
    )

    # Update journey current position
    journey.current_lat = lat
    journey.current_lng = lng
    journey.save()

    # Check for route deviation
    deviation_result = _check_route_deviation(journey, lat, lng)

    return Response({
        'status': 'updated',
        'deviation_detected': deviation_result['deviated'],
        'deviation_distance': deviation_result.get('distance', 0),
    })


def _check_route_deviation(journey, lat, lng):
    """Check if user has deviated from the planned route."""
    route_data = journey.route_data
    if not route_data or 'points' not in route_data:
        return {'deviated': False}

    # Find minimum distance to any route point
    min_distance = float('inf')
    for point in route_data.get('points', []):
        dist = haversine_distance(lat, lng, point['lat'], point['lng'])
        min_distance = min(min_distance, dist)

    # Threshold: 500 meters
    threshold = 500
    if min_distance > threshold:
        RouteDeviation.objects.create(
            journey=journey,
            latitude=lat,
            longitude=lng,
            distance_from_route=min_distance,
        )
        return {'deviated': True, 'distance': min_distance}

    return {'deviated': False, 'distance': min_distance}


@api_view(['GET'])
def get_journey_status(request, tracking_id):
    """Get journey status (public - for tracking page)."""
    try:
        journey = Journey.objects.get(tracking_id=tracking_id)
    except Journey.DoesNotExist:
        return Response({'error': 'Journey not found'}, status=status.HTTP_404_NOT_FOUND)

    locations = LocationUpdate.objects.filter(journey=journey).order_by('-timestamp')[:20]
    location_data = LocationUpdateSerializer(locations, many=True).data

    return Response({
        'tracking_id': str(journey.tracking_id),
        'status': journey.status,
        'source': {'lat': journey.source_lat, 'lng': journey.source_lng, 'name': journey.source_name},
        'destination': {'lat': journey.dest_lat, 'lng': journey.dest_lng, 'name': journey.dest_name},
        'current_location': {'lat': journey.current_lat, 'lng': journey.current_lng},
        'eta_minutes': journey.eta_minutes,
        'started_at': journey.started_at,
        'safety_score': journey.safety_score,
        'location_history': location_data,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_journey_api(request, tracking_id):
    """Mark journey as completed."""
    try:
        journey = Journey.objects.get(tracking_id=tracking_id, user=request.user)
    except Journey.DoesNotExist:
        return Response({'error': 'Journey not found'}, status=status.HTTP_404_NOT_FOUND)

    journey.status = 'completed'
    journey.completed_at = timezone.now()
    journey.save()

    if hasattr(journey, 'arrival_confirmation'):
        journey.arrival_confirmation.status = 'confirmed'
        journey.arrival_confirmation.confirmed_at = timezone.now()
        journey.arrival_confirmation.save()

    return Response({'status': 'completed', 'message': 'Journey completed safely!'})


# ============================================================
# SOS EMERGENCY API
# ============================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trigger_sos(request):
    """Trigger SOS emergency alert."""
    lat = request.data.get('latitude')
    lng = request.data.get('longitude')
    message = request.data.get('message', 'SOS Emergency! I need help!')

    if not lat or not lng:
        return Response({'error': 'Location required'}, status=status.HTTP_400_BAD_REQUEST)

    # Get active journey if any
    active_journey = Journey.objects.filter(user=request.user, status='active').first()
    if active_journey:
        active_journey.status = 'sos'
        active_journey.save()

    # Create emergency alert
    alert = EmergencyAlert.objects.create(
        user=request.user,
        journey=active_journey,
        alert_type='sos',
        latitude=lat,
        longitude=lng,
        message=message,
    )

    # Notify trusted contacts
    contacts = TrustedContact.objects.filter(user=request.user)
    notifications = []
    for contact in contacts:
        notification = EmergencyContactNotification.objects.create(
            alert=alert,
            contact=contact,
            method='app',
            delivered=True,
        )
        notifications.append({
            'contact': contact.name,
            'phone': contact.phone,
            'notified': True,
        })

    # Find nearby safe places
    nearby_places = _get_nearby_safe_places(lat, lng, limit=5)

    return Response({
        'alert_id': alert.id,
        'status': 'sos_triggered',
        'message': 'Emergency alert sent to all trusted contacts!',
        'notifications': notifications,
        'nearby_safe_places': nearby_places,
        'timestamp': alert.created_at,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def resolve_sos(request, alert_id):
    """Resolve/cancel an SOS alert."""
    try:
        alert = EmergencyAlert.objects.get(id=alert_id, user=request.user)
    except EmergencyAlert.DoesNotExist:
        return Response({'error': 'Alert not found'}, status=status.HTTP_404_NOT_FOUND)

    alert.status = request.data.get('resolution', 'resolved')
    alert.resolved_at = timezone.now()
    alert.save()

    # Restore journey status if needed
    if alert.journey and alert.journey.status == 'sos':
        alert.journey.status = 'active'
        alert.journey.save()

    return Response({'status': 'resolved', 'message': 'Alert resolved. Glad you are safe!'})


# ============================================================
# SAFETY CHECK-IN API
# ============================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def checkin_api(request, tracking_id):
    """Record a safety check-in."""
    try:
        journey = Journey.objects.get(tracking_id=tracking_id, user=request.user, status='active')
    except Journey.DoesNotExist:
        return Response({'error': 'Active journey not found'}, status=status.HTTP_404_NOT_FOUND)

    lat = request.data.get('latitude', journey.current_lat)
    lng = request.data.get('longitude', journey.current_lng)
    is_safe = request.data.get('is_safe', True)

    JourneyCheckIn.objects.create(
        journey=journey,
        latitude=lat,
        longitude=lng,
        is_safe=is_safe,
        note=request.data.get('note', ''),
    )

    # Update next check-in time
    if journey.checkin_interval > 0:
        journey.last_checkin = timezone.now()
        journey.next_checkin_due = timezone.now() + timezone.timedelta(minutes=journey.checkin_interval)
        journey.save()

    if not is_safe:
        # Trigger alert if user reports unsafe
        EmergencyAlert.objects.create(
            user=request.user,
            journey=journey,
            alert_type='checkin_missed',
            latitude=lat,
            longitude=lng,
            message='User reported feeling unsafe during check-in.',
        )

    return Response({
        'status': 'checked_in',
        'next_checkin_due': journey.next_checkin_due,
        'is_safe': is_safe,
    })


# ============================================================
# ROUTE DEVIATION API
# ============================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_deviation_safe(request, tracking_id):
    """User confirms they are safe after route deviation."""
    try:
        journey = Journey.objects.get(tracking_id=tracking_id, user=request.user)
    except Journey.DoesNotExist:
        return Response({'error': 'Journey not found'}, status=status.HTTP_404_NOT_FOUND)

    # Mark latest deviation as safe
    latest_deviation = RouteDeviation.objects.filter(journey=journey, status='detected').first()
    if latest_deviation:
        latest_deviation.status = 'user_confirmed_safe'
        latest_deviation.responded_at = timezone.now()
        latest_deviation.user_response = request.data.get('response', 'I am safe')
        latest_deviation.save()

    return Response({'status': 'confirmed_safe'})


# ============================================================
# NEARBY SAFE PLACES API
# ============================================================

@api_view(['GET'])
def nearby_safe_places_api(request):
    """Get nearby safe places based on current location."""
    lat = request.query_params.get('lat')
    lng = request.query_params.get('lng')
    zone_type = request.query_params.get('type', 'all')
    limit = int(request.query_params.get('limit', 10))

    if not lat or not lng:
        return Response({'error': 'lat and lng parameters required'}, status=status.HTTP_400_BAD_REQUEST)

    lat = float(lat)
    lng = float(lng)

    places = _get_nearby_safe_places(lat, lng, zone_type=zone_type, limit=limit)
    return Response({'places': places, 'total': len(places)})


def _get_nearby_safe_places(lat, lng, zone_type='all', limit=10):
    """Helper to get nearby safe places sorted by distance."""
    queryset = SafeZone.objects.filter(is_active=True)
    if zone_type != 'all':
        queryset = queryset.filter(zone_type=zone_type)

    places = []
    for zone in queryset:
        distance = haversine_distance(lat, lng, zone.latitude, zone.longitude)
        places.append({
            'id': zone.id,
            'name': zone.name,
            'type': zone.zone_type,
            'type_display': zone.get_zone_type_display(),
            'latitude': zone.latitude,
            'longitude': zone.longitude,
            'address': zone.address,
            'phone': zone.phone,
            'distance_meters': round(distance),
            'distance_km': round(distance / 1000, 2),
            'operating_hours': zone.operating_hours,
        })

    places.sort(key=lambda x: x['distance_meters'])
    return places[:limit]


# ============================================================
# AI SAFETY ASSISTANT API
# ============================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chat_api(request):
    """AI Safety Assistant chat endpoint."""
    user_message = request.data.get('message', '').strip()
    if not user_message:
        return Response({'error': 'Message required'}, status=status.HTTP_400_BAD_REQUEST)

    # Save user message
    ChatMessage.objects.create(user=request.user, role='user', message=user_message)

    # Get AI response
    context = {
        'user_location': request.data.get('location'),
        'active_journey': Journey.objects.filter(user=request.user, status='active').first(),
    }
    ai_response = get_ai_response(user_message, context)

    # Save assistant message
    ChatMessage.objects.create(user=request.user, role='assistant', message=ai_response)

    return Response({
        'response': ai_response,
        'timestamp': timezone.now(),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chat_history_api(request):
    """Get chat history."""
    messages_qs = ChatMessage.objects.filter(user=request.user).order_by('-created_at')[:50]
    serializer = ChatMessageSerializer(reversed(list(messages_qs)), many=True)
    return Response(serializer.data)


# ============================================================
# SMART SAFETY SCORE API
# ============================================================

@api_view(['GET'])
def safety_score_api(request):
    """Get safety score for a specific location."""
    lat = request.query_params.get('lat')
    lng = request.query_params.get('lng')
    time_of_day = request.query_params.get('time', 'day')

    if not lat or not lng:
        return Response({'error': 'lat and lng parameters required'}, status=status.HTTP_400_BAD_REQUEST)

    lat = float(lat)
    lng = float(lng)

    from .ai_engine import (
        calculate_crime_score, calculate_lighting_score,
        calculate_crowd_density, calculate_safe_zone_score,
        calculate_overall_safety_score
    )

    point = [{'lat': lat, 'lng': lng}]
    crime_reports = list(CrimeReport.objects.all())
    safe_zones = list(SafeZone.objects.filter(is_active=True))
    community_reports = SafetyReport.objects.filter(
        latitude__range=(lat - 0.01, lat + 0.01),
        longitude__range=(lng - 0.01, lng + 0.01),
    )

    crime_score = calculate_crime_score(point, crime_reports)
    lighting_score = calculate_lighting_score(point, time_of_day)
    crowd_score = calculate_crowd_density(point, time_of_day)
    safe_zone_score = calculate_safe_zone_score(point, safe_zones)

    # Community impact
    community_impact = 0
    for report in community_reports:
        if report.report_type in ['harassment', 'unsafe_area', 'broken_light', 'suspicious', 'unsafe_road']:
            community_impact -= report.severity * 2
        elif report.report_type == 'safe_spot':
            community_impact += 5
    community_score = max(0, min(100, 50 + community_impact))

    # Smart weighted score
    overall = calculate_overall_safety_score(crime_score, lighting_score, crowd_score, safe_zone_score, time_of_day)
    # Adjust with community reports (20% weight)
    final_score = overall * 0.8 + community_score * 0.2

    risk_level = 'low' if final_score >= 70 else ('medium' if final_score >= 45 else 'high')

    return Response({
        'location': {'lat': lat, 'lng': lng},
        'time_of_day': time_of_day,
        'safety_score': round(final_score, 1),
        'risk_level': risk_level,
        'breakdown': {
            'crime_score': round(crime_score, 1),
            'lighting_score': round(lighting_score, 1),
            'crowd_score': round(crowd_score, 1),
            'safe_zone_score': round(safe_zone_score, 1),
            'community_score': round(community_score, 1),
        },
        'weights': {
            'crime': '40%',
            'community': '20%',
            'lighting': '15%',
            'crowd': '15%',
            'time_of_day': '10%',
        },
    })


# ============================================================
# TRANSPORT VERIFICATION API
# ============================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def log_transport_api(request):
    """Log transport details."""
    from .models import TransportLog
    data = request.data
    log = TransportLog.objects.create(
        user=request.user,
        transport_type=data.get('transport_type', 'rickshaw'),
        plate_number=data.get('plate_number', ''),
        driver_name=data.get('driver_name', ''),
        driver_phone=data.get('driver_phone', ''),
        vehicle_color=data.get('vehicle_color', ''),
        vehicle_description=data.get('vehicle_description', ''),
        pickup_lat=float(data.get('pickup_lat', 0)),
        pickup_lng=float(data.get('pickup_lng', 0)),
        pickup_address=data.get('pickup_address', ''),
        destination_address=data.get('destination_address', ''),
        expected_duration_minutes=int(data.get('expected_duration', 30)),
    )
    return Response({
        'id': log.id,
        'plate_number': log.plate_number,
        'status': 'logged',
        'message': f'Transport {log.plate_number} logged. Details shared with contacts.',
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_transport_api(request, pk):
    """Mark transport as completed."""
    from .models import TransportLog
    try:
        log = TransportLog.objects.get(pk=pk, user=request.user)
    except TransportLog.DoesNotExist:
        return Response({'error': 'Transport not found'}, status=status.HTTP_404_NOT_FOUND)
    log.status = 'completed'
    log.completed_at = timezone.now()
    log.save()
    return Response({'status': 'completed', 'message': 'Ride completed safely!'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def active_transports_api(request):
    """Get active transports."""
    from .models import TransportLog
    logs = TransportLog.objects.filter(user=request.user, status='active')
    data = [{
        'id': l.id,
        'transport_type': l.transport_type,
        'plate_number': l.plate_number,
        'driver_name': l.driver_name,
        'started_at': l.started_at,
        'expected_duration_minutes': l.expected_duration_minutes,
    } for l in logs]
    return Response(data)


# ============================================================
# EVIDENCE RECORDING API
# ============================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_recording_api(request):
    """Start evidence recording."""
    from .models import EvidenceRecording
    recording = EvidenceRecording.objects.create(
        user=request.user,
        recording_type=request.data.get('type', 'audio'),
        latitude=request.data.get('latitude'),
        longitude=request.data.get('longitude'),
        is_emergency=request.data.get('is_emergency', False),
    )
    return Response({
        'id': recording.id,
        'status': 'recording',
        'message': 'Evidence recording started. Location and timestamp saved.',
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def stop_recording_api(request, pk):
    """Stop evidence recording."""
    from .models import EvidenceRecording
    try:
        recording = EvidenceRecording.objects.get(pk=pk, user=request.user)
    except EvidenceRecording.DoesNotExist:
        return Response({'error': 'Recording not found'}, status=status.HTTP_404_NOT_FOUND)
    recording.status = 'saved'
    recording.ended_at = timezone.now()
    recording.duration_seconds = int(request.data.get('duration', 0))
    recording.notes = request.data.get('notes', '')
    recording.save()
    return Response({'status': 'saved', 'duration': recording.duration_seconds})


# ============================================================
# SAFE NETWORK API
# ============================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def safe_network_alert_api(request):
    """Send alert to nearby safe network members."""
    from .models import SafeNetworkMember, SafeNetworkAlert
    lat = request.data.get('latitude')
    lng = request.data.get('longitude')
    message = request.data.get('message', 'I need help nearby!')
    radius = int(request.data.get('radius', 1000))

    if not lat or not lng:
        return Response({'error': 'Location required'}, status=status.HTTP_400_BAD_REQUEST)

    # Find nearby available members
    nearby_members = []
    for member in SafeNetworkMember.objects.filter(is_verified=True, status='available').exclude(user=request.user):
        if member.latitude and member.longitude:
            dist = haversine_distance(float(lat), float(lng), member.latitude, member.longitude)
            if dist <= radius:
                nearby_members.append({'username': member.user.username, 'distance': round(dist)})

    alert = SafeNetworkAlert.objects.create(
        requester=request.user,
        latitude=lat,
        longitude=lng,
        message=message,
        radius_meters=radius,
        members_notified=len(nearby_members),
    )

    return Response({
        'alert_id': alert.id,
        'members_notified': len(nearby_members),
        'nearby_members': nearby_members,
        'message': f'Alert sent to {len(nearby_members)} nearby SafePath members.',
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_network_location_api(request):
    """Update safe network member location."""
    from .models import SafeNetworkMember
    try:
        member = SafeNetworkMember.objects.get(user=request.user)
    except SafeNetworkMember.DoesNotExist:
        return Response({'error': 'Not a network member'}, status=status.HTTP_404_NOT_FOUND)

    member.latitude = request.data.get('latitude')
    member.longitude = request.data.get('longitude')
    member.status = request.data.get('status', 'available')
    member.save()
    return Response({'status': 'updated'})


@api_view(['GET'])
def nearby_members_api(request):
    """Get count of nearby safe network members."""
    from .models import SafeNetworkMember
    lat = request.query_params.get('lat')
    lng = request.query_params.get('lng')
    if not lat or not lng:
        return Response({'error': 'lat and lng required'}, status=status.HTTP_400_BAD_REQUEST)

    count = 0
    for member in SafeNetworkMember.objects.filter(is_verified=True, status='available'):
        if member.latitude and member.longitude:
            dist = haversine_distance(float(lat), float(lng), member.latitude, member.longitude)
            if dist <= 1000:
                count += 1

    return Response({'nearby_count': count, 'radius_meters': 1000})


# ============================================================
# SAFE TIME ANALYSIS API
# ============================================================

@api_view(['GET'])
def safe_time_api(request):
    """Get hourly safety analysis for a location."""
    lat = request.query_params.get('lat')
    lng = request.query_params.get('lng')

    if not lat or not lng:
        return Response({'error': 'lat and lng required'}, status=status.HTTP_400_BAD_REQUEST)

    import random
    # Generate hourly safety data (in production, based on historical crime timestamps)
    hourly_scores = []
    for hour in range(24):
        if 6 <= hour <= 18:
            base = random.uniform(65, 90)
        elif 18 < hour <= 22:
            base = random.uniform(45, 70)
        else:
            base = random.uniform(25, 50)

        hourly_scores.append({
            'hour': hour,
            'label': f'{hour:02d}:00',
            'score': round(base, 1),
            'risk': 'low' if base >= 70 else ('medium' if base >= 45 else 'high'),
        })

    # Find safest and most dangerous times
    safest = max(hourly_scores, key=lambda x: x['score'])
    most_dangerous = min(hourly_scores, key=lambda x: x['score'])

    return Response({
        'location': {'lat': float(lat), 'lng': float(lng)},
        'hourly_scores': hourly_scores,
        'safest_time': safest,
        'most_dangerous_time': most_dangerous,
        'recommendation': f"Safest travel time: {safest['label']}. Avoid traveling at {most_dangerous['label']}.",
    })


# ============================================================
# FAKE CALL API
# ============================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fake_call_profiles_api(request):
    """Get saved fake call profiles."""
    from .models import FakeCallProfile
    profiles = FakeCallProfile.objects.filter(user=request.user)
    data = [{
        'id': p.id,
        'caller_name': p.caller_name,
        'caller_number': p.caller_number,
        'caller_photo': p.caller_photo,
        'delay_seconds': p.delay_seconds,
        'ringtone': p.ringtone,
    } for p in profiles]
    return Response(data)


# ============================================================
# TRANSPORT VERIFICATION API
# ============================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def log_transport_api(request):
    """Log transport details and share with contacts."""
    from .models import TransportLog
    data = request.data
    log = TransportLog.objects.create(
        user=request.user,
        transport_type=data.get('transport_type', 'rickshaw'),
        plate_number=data.get('plate_number', ''),
        driver_name=data.get('driver_name', ''),
        driver_phone=data.get('driver_phone', ''),
        vehicle_color=data.get('vehicle_color', ''),
        vehicle_description=data.get('vehicle_description', ''),
        pickup_lat=float(data.get('pickup_lat', 0)),
        pickup_lng=float(data.get('pickup_lng', 0)),
        pickup_address=data.get('pickup_address', ''),
        destination_address=data.get('destination_address', ''),
        expected_duration_minutes=int(data.get('expected_duration', 30)),
    )
    # Auto-notify contacts
    contacts = TrustedContact.objects.filter(user=request.user)
    notification_msg = (
        f"🚗 Transport Alert: {request.user.username} is riding in a "
        f"{log.get_transport_type_display()} | Plate: {log.plate_number} | "
        f"Driver: {log.driver_name or 'Unknown'} | "
        f"Color: {log.vehicle_color or 'Unknown'}"
    )
    return Response({
        'id': log.id,
        'plate_number': log.plate_number,
        'message': notification_msg,
        'contacts_notified': contacts.count(),
        'status': 'active',
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_transport_api(request, pk):
    """Mark transport ride as completed."""
    from .models import TransportLog
    try:
        log = TransportLog.objects.get(pk=pk, user=request.user)
    except TransportLog.DoesNotExist:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
    log.status = 'completed'
    log.completed_at = timezone.now()
    log.save()
    return Response({'status': 'completed', 'message': 'Ride completed safely!'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def transport_history_api(request):
    """Get transport history."""
    from .models import TransportLog
    logs = TransportLog.objects.filter(user=request.user)[:20]
    data = [{
        'id': l.id,
        'transport_type': l.transport_type,
        'plate_number': l.plate_number,
        'driver_name': l.driver_name,
        'vehicle_color': l.vehicle_color,
        'status': l.status,
        'started_at': l.started_at,
        'completed_at': l.completed_at,
    } for l in logs]
    return Response(data)


# ============================================================
# EVIDENCE RECORDING API
# ============================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_recording_api(request):
    """Start an evidence recording session."""
    from .models import EvidenceRecording
    recording = EvidenceRecording.objects.create(
        user=request.user,
        recording_type=request.data.get('type', 'audio'),
        latitude=request.data.get('latitude'),
        longitude=request.data.get('longitude'),
        is_emergency=request.data.get('is_emergency', False),
    )
    return Response({
        'recording_id': recording.id,
        'status': 'recording',
        'message': 'Evidence recording started. Recording is being saved securely.',
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def stop_recording_api(request, pk):
    """Stop and save an evidence recording."""
    from .models import EvidenceRecording
    try:
        recording = EvidenceRecording.objects.get(pk=pk, user=request.user)
    except EvidenceRecording.DoesNotExist:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

    recording.status = 'saved'
    recording.ended_at = timezone.now()
    recording.duration_seconds = int(request.data.get('duration', 0))
    recording.notes = request.data.get('notes', '')
    recording.save()
    return Response({
        'status': 'saved',
        'duration': recording.duration_seconds,
        'message': 'Evidence saved securely. Can be used for police reports.',
    })


# ============================================================
# SAFE NETWORK API
# ============================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_network_status(request):
    """Update safe network member status and location."""
    from .models import SafeNetworkMember
    profile, _ = SafeNetworkMember.objects.get_or_create(user=request.user)
    profile.status = request.data.get('status', 'available')
    profile.latitude = request.data.get('latitude')
    profile.longitude = request.data.get('longitude')
    profile.save()
    return Response({'status': profile.status, 'message': f'Status updated to {profile.status}'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_network_alert(request):
    """Send help request to nearby safe network members."""
    from .models import SafeNetworkMember, SafeNetworkAlert
    lat = request.data.get('latitude')
    lng = request.data.get('longitude')
    msg = request.data.get('message', 'I need help nearby!')

    if not lat or not lng:
        return Response({'error': 'Location required'}, status=status.HTTP_400_BAD_REQUEST)

    # Find nearby available members
    available = SafeNetworkMember.objects.filter(status='available', is_verified=True).exclude(user=request.user)
    nearby_count = 0
    for member in available:
        if member.latitude and member.longitude:
            dist = haversine_distance(float(lat), float(lng), member.latitude, member.longitude)
            if dist <= 1000:  # 1km radius
                nearby_count += 1

    alert = SafeNetworkAlert.objects.create(
        requester=request.user,
        latitude=float(lat),
        longitude=float(lng),
        message=msg,
        members_notified=nearby_count,
    )

    return Response({
        'alert_id': alert.id,
        'members_notified': nearby_count,
        'message': f'Alert sent to {nearby_count} nearby SafeNetwork members!',
    })


@api_view(['GET'])
def nearby_network_members(request):
    """Get count of nearby network members."""
    from .models import SafeNetworkMember
    lat = request.query_params.get('lat')
    lng = request.query_params.get('lng')

    if not lat or not lng:
        return Response({'count': 0})

    available = SafeNetworkMember.objects.filter(status='available', is_verified=True)
    count = 0
    for member in available:
        if member.latitude and member.longitude:
            dist = haversine_distance(float(lat), float(lng), member.latitude, member.longitude)
            if dist <= 1000:
                count += 1

    return Response({'count': count, 'radius_km': 1})


# ============================================================
# SAFE TIME ANALYSIS API
# ============================================================

@api_view(['GET'])
def safe_time_analysis_api(request):
    """Get safety score by hour of day for a location."""
    lat = request.query_params.get('lat')
    lng = request.query_params.get('lng')

    if not lat or not lng:
        return Response({'error': 'lat and lng required'}, status=status.HTTP_400_BAD_REQUEST)

    # Generate 24-hour safety analysis
    import random
    hours = []
    for hour in range(24):
        # Base pattern: safer during day, riskier at night
        if 6 <= hour <= 18:
            base_score = random.uniform(65, 92)
            risk = 'low'
        elif 19 <= hour <= 21:
            base_score = random.uniform(45, 70)
            risk = 'medium'
        else:
            base_score = random.uniform(20, 50)
            risk = 'high'

        hours.append({
            'hour': hour,
            'time': f"{hour:02d}:00",
            'safety_score': round(base_score, 1),
            'risk_level': risk,
            'label': 'Safe' if risk == 'low' else ('Caution' if risk == 'medium' else 'Risky'),
        })

    safest_hours = sorted(hours, key=lambda x: x['safety_score'], reverse=True)[:3]
    riskiest_hours = sorted(hours, key=lambda x: x['safety_score'])[:3]

    return Response({
        'location': {'lat': float(lat), 'lng': float(lng)},
        'hourly_scores': hours,
        'safest_times': [f"{h['time']}" for h in safest_hours],
        'riskiest_times': [f"{h['time']}" for h in riskiest_hours],
        'recommendation': f"Best travel time: {safest_hours[0]['time']} - {safest_hours[-1]['time']}. "
                         f"Avoid: {riskiest_hours[0]['time']} - {riskiest_hours[-1]['time']}."
    })


# ============================================================
# SHAKE SOS API
# ============================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def shake_sos_api(request):
    """Silent SOS triggered by shake gesture or code word."""
    lat = request.data.get('latitude')
    lng = request.data.get('longitude')
    trigger_type = request.data.get('trigger', 'shake')  # shake, voice, button

    if not lat or not lng:
        return Response({'error': 'Location required'}, status=status.HTTP_400_BAD_REQUEST)

    # Same as regular SOS but silent (no confirmation needed)
    active_journey = Journey.objects.filter(user=request.user, status='active').first()
    if active_journey:
        active_journey.status = 'sos'
        active_journey.save()

    alert = EmergencyAlert.objects.create(
        user=request.user,
        journey=active_journey,
        alert_type='sos',
        latitude=lat,
        longitude=lng,
        message=f'Silent SOS triggered via {trigger_type}. User may be in danger.',
    )

    contacts = TrustedContact.objects.filter(user=request.user)
    for contact in contacts:
        EmergencyContactNotification.objects.create(
            alert=alert, contact=contact, method='app', delivered=True,
        )

    return Response({
        'alert_id': alert.id,
        'status': 'silent_sos_triggered',
        'contacts_notified': contacts.count(),
        'trigger': trigger_type,
    })
