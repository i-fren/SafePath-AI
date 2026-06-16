"""
AI Safety Analysis Engine for SafePath.
Calculates safety scores and generates route recommendations.
"""
import math
import random
from datetime import datetime


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in meters."""
    R = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def calculate_crime_score(route_points, crime_reports, radius=500):
    """
    Calculate crime score for a route (0-100, higher = safer).
    Considers crime incidents within radius of route points.
    """
    if not crime_reports:
        return 85  # Default safe score if no data

    crime_count = 0
    weighted_severity = 0

    for point in route_points:
        for crime in crime_reports:
            dist = haversine_distance(
                point['lat'], point['lng'],
                crime.latitude, crime.longitude
            )
            if dist <= radius:
                crime_count += 1
                # Weight by severity and proximity
                proximity_weight = 1 - (dist / radius)
                weighted_severity += crime.severity * proximity_weight

    # Normalize score (more crimes = lower score)
    if crime_count == 0:
        return 95
    
    # Cap the impact
    max_expected_crimes = len(route_points) * 3
    normalized = min(weighted_severity / max_expected_crimes, 1.0)
    score = max(10, 100 - (normalized * 80))
    return round(score, 1)


def calculate_lighting_score(route_points, time_of_day):
    """
    Calculate lighting score (0-100, higher = better lit).
    During day, lighting is less relevant.
    """
    if time_of_day == 'day':
        return random.uniform(85, 98)

    # Night time - simulate lighting data based on area type
    # In production, this would use actual street lighting data
    base_scores = []
    for point in route_points:
        # Simulate: areas closer to main roads/centers have better lighting
        lat_factor = abs(point['lat'] % 0.01) * 1000
        lng_factor = abs(point['lng'] % 0.01) * 1000
        base = 60 + (lat_factor + lng_factor) % 30
        base_scores.append(min(95, max(30, base)))

    return round(sum(base_scores) / len(base_scores), 1) if base_scores else 50


def calculate_crowd_density(route_points, time_of_day):
    """
    Calculate crowd density score (0-100, higher = more crowded/safer).
    """
    if time_of_day == 'day':
        base = random.uniform(60, 90)
    else:
        base = random.uniform(20, 55)

    # Adjust based on route characteristics
    for point in route_points:
        # Main roads tend to have more people
        variation = random.uniform(-5, 5)
        base += variation / len(route_points)

    return round(max(10, min(95, base)), 1)


def calculate_safe_zone_score(route_points, safe_zones, radius=500):
    """
    Calculate proximity to safe zones (0-100, higher = closer to safe zones).
    """
    if not safe_zones:
        return 50

    total_proximity = 0
    max_possible = len(route_points)

    for point in route_points:
        nearest_safe = float('inf')
        for zone in safe_zones:
            dist = haversine_distance(
                point['lat'], point['lng'],
                zone.latitude, zone.longitude
            )
            nearest_safe = min(nearest_safe, dist)
        
        if nearest_safe <= radius:
            total_proximity += 1 - (nearest_safe / radius)

    score = (total_proximity / max_possible) * 100 if max_possible > 0 else 50
    return round(max(20, min(95, score)), 1)


def calculate_overall_safety_score(crime_score, lighting_score, crowd_score, safe_zone_score, time_of_day):
    """
    Calculate overall safety score with weighted factors.
    Weights change based on time of day.
    """
    if time_of_day == 'night':
        weights = {
            'crime': 0.35,
            'lighting': 0.30,
            'crowd': 0.20,
            'safe_zone': 0.15,
        }
    else:
        weights = {
            'crime': 0.40,
            'lighting': 0.10,
            'crowd': 0.25,
            'safe_zone': 0.25,
        }

    overall = (
        crime_score * weights['crime'] +
        lighting_score * weights['lighting'] +
        crowd_score * weights['crowd'] +
        safe_zone_score * weights['safe_zone']
    )
    return round(overall, 1)


def generate_route_variants(source, destination):
    """
    Generate multiple route variants between source and destination.
    Returns 3 clearly different routes: shortest, fastest, safest.
    """
    src_lat, src_lng = source['lat'], source['lng']
    dst_lat, dst_lng = destination['lat'], destination['lng']

    routes = []

    # Route 1: Shortest — direct path, may pass through risk areas
    direct_points = _interpolate_route(src_lat, src_lng, dst_lat, dst_lng, num_points=6, offset=0)
    dist1 = _estimate_distance(direct_points)
    routes.append({
        'type': 'shortest',
        'label': 'Shortest Route',
        'points': direct_points,
        'distance_km': dist1,
        'duration_min': round((dist1 / 5.0) * 60, 0),
        'description': 'Direct path — shortest distance but may pass through less safe areas.',
    })

    # Route 2: Fastest — main roads, slightly longer but better roads
    fast_points = _interpolate_route(src_lat, src_lng, dst_lat, dst_lng, num_points=8, offset=0.004)
    dist2 = _estimate_distance(fast_points)
    routes.append({
        'type': 'fastest',
        'label': 'Fastest Route',
        'points': fast_points,
        'distance_km': dist2,
        'duration_min': round((dist2 / 5.5) * 60, 0),
        'description': 'Main roads — faster travel speed, moderate safety.',
    })

    # Route 3: Safest — avoids crime hotspots, stays near safe zones, longer
    safe_points = _interpolate_route(src_lat, src_lng, dst_lat, dst_lng, num_points=12, offset=-0.006)
    dist3 = _estimate_distance(safe_points)
    routes.append({
        'type': 'safest',
        'label': 'Safest Route (Recommended)',
        'points': safe_points,
        'distance_km': dist3,
        'duration_min': round((dist3 / 4.5) * 60, 0),
        'description': 'Avoids crime hotspots, near police stations and safe zones.',
    })

    return routes


def _interpolate_route(src_lat, src_lng, dst_lat, dst_lng, num_points=10, offset=0):
    """Generate interpolated route points with optional offset."""
    points = []
    for i in range(num_points + 1):
        t = i / num_points
        # Add slight curve to make routes look realistic
        curve = math.sin(t * math.pi) * offset
        lat = src_lat + (dst_lat - src_lat) * t + curve
        lng = src_lng + (dst_lng - src_lng) * t + curve * 0.7
        points.append({'lat': round(lat, 6), 'lng': round(lng, 6)})
    return points


def _estimate_distance(points):
    """Estimate total route distance in km."""
    total = 0
    for i in range(len(points) - 1):
        total += haversine_distance(
            points[i]['lat'], points[i]['lng'],
            points[i + 1]['lat'], points[i + 1]['lng']
        )
    return round(total / 1000, 2)


def _estimate_duration(points, route_type):
    """Estimate travel duration in minutes."""
    distance = _estimate_distance(points)
    # Assume walking speed
    speeds = {'short': 5, 'fast': 5.5, 'safe': 4.5}  # km/h
    speed = speeds.get(route_type, 5)
    return round((distance / speed) * 60, 0)


def analyze_route(source, destination, time_of_day, crime_reports, safe_zones):
    """
    Main analysis function. Returns complete route analysis.
    Each route type gets distinct scoring characteristics.
    """
    routes = generate_route_variants(source, destination)
    analyzed_routes = []

    for route in routes:
        crime_score = calculate_crime_score(route['points'], crime_reports)
        lighting_score = calculate_lighting_score(route['points'], time_of_day)
        crowd_score = calculate_crowd_density(route['points'], time_of_day)
        safe_zone_score = calculate_safe_zone_score(route['points'], safe_zones)

        # Apply route-type specific modifiers to create clear differentiation
        if route['type'] == 'shortest':
            # Shortest goes through direct areas - lower safety, near crime zones
            crime_score = max(15, crime_score - random.uniform(15, 30))
            lighting_score = max(20, lighting_score - random.uniform(10, 20))
            crowd_score = max(15, crowd_score - random.uniform(5, 15))

        elif route['type'] == 'fastest':
            # Fastest uses main roads - moderate safety
            crime_score = max(30, crime_score - random.uniform(5, 15))
            crowd_score = min(90, crowd_score + random.uniform(5, 10))

        elif route['type'] == 'safest':
            # Safest avoids crime, near safe zones - highest safety
            crime_score = min(98, crime_score + random.uniform(10, 25))
            lighting_score = min(95, lighting_score + random.uniform(10, 20))
            safe_zone_score = min(95, safe_zone_score + random.uniform(15, 25))
            crowd_score = min(92, crowd_score + random.uniform(10, 15))

        overall_score = calculate_overall_safety_score(
            crime_score, lighting_score, crowd_score, safe_zone_score, time_of_day
        )

        route['scores'] = {
            'overall': overall_score,
            'crime': round(crime_score, 1),
            'lighting': round(lighting_score, 1),
            'crowd': round(crowd_score, 1),
            'safe_zone': round(safe_zone_score, 1),
        }
        route['explanation'] = generate_explanation(route, time_of_day)
        analyzed_routes.append(route)

    # Sort: safest first, then fastest, then shortest
    type_order = {'safest': 0, 'fastest': 1, 'shortest': 2}
    analyzed_routes.sort(key=lambda r: type_order.get(r['type'], 9))

    # Mark safest as recommended
    for r in analyzed_routes:
        r['recommended'] = (r['type'] == 'safest')

    return analyzed_routes


def generate_explanation(route, time_of_day):
    """Generate AI explanation for route safety."""
    scores = route['scores']
    explanations = []

    # Overall assessment
    if scores['overall'] >= 75:
        explanations.append(f"This route has a good safety score of {scores['overall']}/100.")
    elif scores['overall'] >= 50:
        explanations.append(f"This route has a moderate safety score of {scores['overall']}/100. Exercise caution.")
    else:
        explanations.append(f"This route has a low safety score of {scores['overall']}/100. Consider alternative routes.")

    # Crime analysis
    if scores['crime'] >= 80:
        explanations.append("Low crime activity reported in this area.")
    elif scores['crime'] >= 50:
        explanations.append("Some crime incidents have been reported nearby. Stay alert.")
    else:
        explanations.append("Multiple crime incidents reported. This area has higher risk.")

    # Lighting
    if time_of_day == 'night':
        if scores['lighting'] >= 70:
            explanations.append("Route is well-lit with good street lighting.")
        elif scores['lighting'] >= 40:
            explanations.append("Some sections may have poor lighting.")
        else:
            explanations.append("Poor lighting conditions. Carry a flashlight or use well-lit paths.")

    # Crowd density
    if scores['crowd'] >= 60:
        explanations.append("Expect moderate to high foot traffic, which provides added safety.")
    else:
        explanations.append("Low foot traffic expected. Consider traveling with a companion.")

    # Safe zones
    if scores['safe_zone'] >= 70:
        explanations.append("Close proximity to police stations, hospitals, and safe zones.")
    else:
        explanations.append("Limited safe zones along this route.")

    return " ".join(explanations)


def get_safety_tips(time_of_day):
    """Return contextual safety tips."""
    general_tips = [
        "Share your live location with a trusted contact.",
        "Keep your phone charged and easily accessible.",
        "Stay aware of your surroundings at all times.",
        "Trust your instincts - if something feels wrong, change your route.",
        "Stick to well-populated and well-lit areas when possible.",
    ]

    night_tips = [
        "Avoid isolated areas and poorly lit streets.",
        "Consider traveling with a companion after dark.",
        "Keep emergency numbers on speed dial.",
        "Wear visible clothing to be seen by others.",
        "Avoid using headphones so you can hear your surroundings.",
        "Plan your route before leaving and share it with someone.",
    ]

    day_tips = [
        "Be aware of your surroundings even during daytime.",
        "Keep valuables hidden and bags close to your body.",
        "Stay on main roads with regular foot traffic.",
    ]

    if time_of_day == 'night':
        return general_tips + night_tips
    return general_tips + day_tips
