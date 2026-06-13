"""
Management command to load realistic sample data for SafePath AI.
Uses Lahore, Pakistan as the sample location.
"""
import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User
from core.models import CrimeReport, SafetyReport, SafeZone, AreaSafetyScore


class Command(BaseCommand):
    help = 'Load sample data for SafePath AI demo (Pakistan - Lahore)'

    def handle(self, *args, **options):
        self.stdout.write('Loading sample data for Lahore, Pakistan...')

        # Create admin user
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@safepath.ai', 'admin123')
            self.stdout.write(self.style.SUCCESS('Created admin user (admin/admin123)'))

        # Create demo user
        if not User.objects.filter(username='demo').exists():
            User.objects.create_user('demo', 'demo@safepath.ai', 'demo123')
            self.stdout.write(self.style.SUCCESS('Created demo user (demo/demo123)'))

        self._load_crime_reports()
        self._load_safe_zones()
        self._load_safety_reports()
        self._load_area_scores()

        self.stdout.write(self.style.SUCCESS('Sample data loaded successfully!'))

    def _load_crime_reports(self):
        """Load realistic crime report data for Lahore, Pakistan."""
        CrimeReport.objects.all().delete()

        # Lahore area coordinates with realistic crime data
        crimes = [
            {'title': 'Street harassment near Anarkali Bazaar', 'crime_type': 'harassment', 'severity': 2, 'lat': 31.5620, 'lng': 74.3150},
            {'title': 'Mobile snatching on Mall Road', 'crime_type': 'robbery', 'severity': 3, 'lat': 31.5560, 'lng': 74.3400},
            {'title': 'Eve teasing at Lahore Metro Bus Stop', 'crime_type': 'harassment', 'severity': 2, 'lat': 31.5200, 'lng': 74.3500},
            {'title': 'Phone snatching near Liberty Market', 'crime_type': 'robbery', 'severity': 3, 'lat': 31.5150, 'lng': 74.3430},
            {'title': 'Stalking incident near Punjab University', 'crime_type': 'stalking', 'severity': 3, 'lat': 31.5050, 'lng': 74.3100},
            {'title': 'Verbal abuse near Jallo Park', 'crime_type': 'harassment', 'severity': 2, 'lat': 31.5850, 'lng': 74.4100},
            {'title': 'Attempted theft at HBL ATM Gulberg', 'crime_type': 'theft', 'severity': 3, 'lat': 31.5200, 'lng': 74.3550},
            {'title': 'Vandalism of bus stop shelter', 'crime_type': 'vandalism', 'severity': 1, 'lat': 31.5450, 'lng': 74.3300},
            {'title': 'Assault near Data Darbar underpass', 'crime_type': 'assault', 'severity': 4, 'lat': 31.5700, 'lng': 74.3120},
            {'title': 'Robbery on isolated street in Johar Town', 'crime_type': 'robbery', 'severity': 4, 'lat': 31.4700, 'lng': 74.2800},
            {'title': 'Catcalling near Packages Mall', 'crime_type': 'harassment', 'severity': 1, 'lat': 31.4650, 'lng': 74.2750},
            {'title': 'Bag snatching at Kalma Chowk signal', 'crime_type': 'theft', 'severity': 3, 'lat': 31.5170, 'lng': 74.3460},
            {'title': 'Suspicious following reported in Model Town', 'crime_type': 'stalking', 'severity': 3, 'lat': 31.4850, 'lng': 74.3200},
            {'title': 'Group harassment at night near Lakshmi Chowk', 'crime_type': 'harassment', 'severity': 4, 'lat': 31.5580, 'lng': 74.3280},
            {'title': 'Vehicle vandalism in DHA Phase 5', 'crime_type': 'vandalism', 'severity': 2, 'lat': 31.4750, 'lng': 74.3700},
            {'title': 'Theft at Ichra Bazaar', 'crime_type': 'theft', 'severity': 2, 'lat': 31.5250, 'lng': 74.3200},
            {'title': 'Physical assault near old Lahore walled city', 'crime_type': 'assault', 'severity': 4, 'lat': 31.5800, 'lng': 74.3200},
            {'title': 'Harassment on Daewoo bus', 'crime_type': 'harassment', 'severity': 3, 'lat': 31.5100, 'lng': 74.3600},
            {'title': 'Attempted robbery at Thokar Niaz Baig parking', 'crime_type': 'robbery', 'severity': 3, 'lat': 31.4550, 'lng': 74.2200},
            {'title': 'Catcalling near Kinnaird College', 'crime_type': 'harassment', 'severity': 2, 'lat': 31.5400, 'lng': 74.3450},
            {'title': 'Theft from rickshaw in Garhi Shahu', 'crime_type': 'theft', 'severity': 2, 'lat': 31.5650, 'lng': 74.3500},
            {'title': 'Late night stalking near Bahria Town gate', 'crime_type': 'stalking', 'severity': 4, 'lat': 31.4100, 'lng': 74.2100},
            {'title': 'Assault at isolated park in Iqbal Town', 'crime_type': 'assault', 'severity': 4, 'lat': 31.4900, 'lng': 74.2900},
            {'title': 'Verbal harassment at Ferozepur Road taxi stand', 'crime_type': 'harassment', 'severity': 2, 'lat': 31.5100, 'lng': 74.3300},
            {'title': 'Graffiti vandalism in Shahdara underpass', 'crime_type': 'vandalism', 'severity': 1, 'lat': 31.5900, 'lng': 74.3600},
            {'title': 'Mobile snatching near Minar-e-Pakistan', 'crime_type': 'robbery', 'severity': 3, 'lat': 31.5925, 'lng': 74.3095},
            {'title': 'Harassment reported at Wagah Border area', 'crime_type': 'harassment', 'severity': 2, 'lat': 31.6050, 'lng': 74.5700},
            {'title': 'Theft attempt at Fortress Stadium parking', 'crime_type': 'theft', 'severity': 2, 'lat': 31.5300, 'lng': 74.3550},
        ]

        for crime_data in crimes:
            CrimeReport.objects.create(
                title=crime_data['title'],
                crime_type=crime_data['crime_type'],
                severity=crime_data['severity'],
                latitude=crime_data['lat'],
                longitude=crime_data['lng'],
                description=f"Reported incident: {crime_data['title']}. This is sample data for demonstration.",
                date_occurred=timezone.now() - timedelta(days=random.randint(1, 90)),
                is_verified=random.choice([True, True, False]),
            )

        self.stdout.write(f'  Created {len(crimes)} crime reports')

    def _load_safe_zones(self):
        """Load safe zone data for Lahore, Pakistan."""
        SafeZone.objects.all().delete()

        zones = [
            {'name': 'Race Course Police Station', 'zone_type': 'police', 'lat': 31.5350, 'lng': 74.3400, 'radius': 300},
            {'name': 'Gulberg Police Station', 'zone_type': 'police', 'lat': 31.5200, 'lng': 74.3500, 'radius': 300},
            {'name': 'Model Town Police Station', 'zone_type': 'police', 'lat': 31.4850, 'lng': 74.3150, 'radius': 300},
            {'name': 'Civil Lines Police Station', 'zone_type': 'police', 'lat': 31.5550, 'lng': 74.3350, 'radius': 250},
            {'name': 'Mayo Hospital', 'zone_type': 'hospital', 'lat': 31.5700, 'lng': 74.3250, 'radius': 400},
            {'name': 'Services Hospital Lahore', 'zone_type': 'hospital', 'lat': 31.5170, 'lng': 74.3550, 'radius': 400},
            {'name': 'Jinnah Hospital', 'zone_type': 'hospital', 'lat': 31.4950, 'lng': 74.2950, 'radius': 450},
            {'name': 'Shaukat Khanum Hospital', 'zone_type': 'hospital', 'lat': 31.4750, 'lng': 74.2700, 'radius': 400},
            {'name': 'Lahore Rescue 1122 Station - Gulberg', 'zone_type': 'fire_station', 'lat': 31.5220, 'lng': 74.3480, 'radius': 250},
            {'name': 'Lahore Rescue 1122 Station - Mall Road', 'zone_type': 'fire_station', 'lat': 31.5550, 'lng': 74.3400, 'radius': 250},
            {'name': 'Minar-e-Pakistan / Greater Iqbal Park', 'zone_type': 'public_space', 'lat': 31.5925, 'lng': 74.3095, 'radius': 500},
            {'name': 'Shalimar Gardens', 'zone_type': 'public_space', 'lat': 31.5850, 'lng': 74.3800, 'radius': 400},
            {'name': 'Liberty Market', 'zone_type': 'shopping', 'lat': 31.5150, 'lng': 74.3430, 'radius': 400},
            {'name': 'Packages Mall', 'zone_type': 'shopping', 'lat': 31.4650, 'lng': 74.2750, 'radius': 500},
            {'name': 'Emporium Mall', 'zone_type': 'shopping', 'lat': 31.4700, 'lng': 74.2650, 'radius': 500},
            {'name': 'Lahore Metro - Kalma Chowk Station', 'zone_type': 'transit', 'lat': 31.5170, 'lng': 74.3460, 'radius': 200},
            {'name': 'Lahore Metro - MAO College Station', 'zone_type': 'transit', 'lat': 31.5600, 'lng': 74.3300, 'radius': 200},
            {'name': 'Lahore Railway Station', 'zone_type': 'transit', 'lat': 31.5580, 'lng': 74.3160, 'radius': 400},
            {'name': 'Allama Iqbal International Airport', 'zone_type': 'transit', 'lat': 31.5210, 'lng': 74.4040, 'radius': 600},
            {'name': 'Lahore Orange Line - Anarkali Station', 'zone_type': 'transit', 'lat': 31.5620, 'lng': 74.3150, 'radius': 200},
        ]

        for zone_data in zones:
            SafeZone.objects.create(
                name=zone_data['name'],
                zone_type=zone_data['zone_type'],
                latitude=zone_data['lat'],
                longitude=zone_data['lng'],
                radius=zone_data['radius'],
                description=f"{zone_data['name']} - A safe zone in Lahore.",
                is_active=True,
                operating_hours='24/7' if zone_data['zone_type'] in ['police', 'hospital'] else '6:00 AM - 11:00 PM',
            )

        self.stdout.write(f'  Created {len(zones)} safe zones')

    def _load_safety_reports(self):
        """Load community safety reports for Lahore."""
        SafetyReport.objects.all().delete()

        demo_user = User.objects.filter(username='demo').first()

        reports = [
            {'title': 'Broken streetlight on Ferozepur Road', 'report_type': 'broken_light', 'lat': 31.5100, 'lng': 74.3350},
            {'title': 'Poorly lit underpass near Kalma Chowk', 'report_type': 'unsafe_area', 'lat': 31.5170, 'lng': 74.3460},
            {'title': 'Suspicious person loitering at night in Gulberg', 'report_type': 'suspicious', 'lat': 31.5220, 'lng': 74.3520},
            {'title': 'Harassment near Anarkali Bazaar at 9 PM', 'report_type': 'harassment', 'lat': 31.5620, 'lng': 74.3150},
            {'title': 'Multiple lights out in Model Town residential lane', 'report_type': 'broken_light', 'lat': 31.4820, 'lng': 74.3180},
            {'title': 'Liberty Market area - safe and well-patrolled', 'report_type': 'safe_spot', 'lat': 31.5150, 'lng': 74.3430},
            {'title': 'Stray dogs aggressive near Canal Road park', 'report_type': 'unsafe_area', 'lat': 31.5050, 'lng': 74.3300},
            {'title': 'Dark alley behind Ichra Market - avoid at night', 'report_type': 'unsafe_area', 'lat': 31.5250, 'lng': 74.3200},
            {'title': 'Well-patrolled area near Minar-e-Pakistan', 'report_type': 'safe_spot', 'lat': 31.5925, 'lng': 74.3095},
            {'title': 'Suspicious van spotted near DHA Phase 6', 'report_type': 'suspicious', 'lat': 31.4700, 'lng': 74.3800},
            {'title': 'Broken CCTV cameras on MM Alam Road', 'report_type': 'broken_light', 'lat': 31.5180, 'lng': 74.3550},
            {'title': 'Good police patrol presence on Mall Road', 'report_type': 'safe_spot', 'lat': 31.5560, 'lng': 74.3400},
            {'title': 'Unsafe pedestrian crossing at Thokar Niaz Baig', 'report_type': 'unsafe_area', 'lat': 31.4550, 'lng': 74.2200},
            {'title': 'Well-lit and safe area around Packages Mall', 'report_type': 'safe_spot', 'lat': 31.4650, 'lng': 74.2750},
            {'title': 'Broken streetlights in Johar Town Block D', 'report_type': 'broken_light', 'lat': 31.4700, 'lng': 74.2800},
        ]

        for report_data in reports:
            SafetyReport.objects.create(
                user=demo_user,
                title=report_data['title'],
                report_type=report_data['report_type'],
                description=f"Community report: {report_data['title']}. Submitted for awareness.",
                latitude=report_data['lat'],
                longitude=report_data['lng'],
                upvotes=random.randint(0, 25),
                is_resolved=random.choice([True, False, False]),
            )

        self.stdout.write(f'  Created {len(reports)} safety reports')

    def _load_area_scores(self):
        """Pre-calculate area safety scores for grid cells in Lahore."""
        AreaSafetyScore.objects.all().delete()

        # Generate grid scores for the Lahore area
        base_lat = 31.45
        base_lng = 74.25
        count = 0

        for i in range(10):
            for j in range(10):
                lat = base_lat + (i * 0.015)
                lng = base_lng + (j * 0.015)

                for period in ['day', 'night']:
                    crime_s = random.uniform(40, 95)
                    lighting_s = random.uniform(60, 95) if period == 'day' else random.uniform(25, 75)
                    crowd_s = random.uniform(50, 90) if period == 'day' else random.uniform(15, 60)
                    overall = (crime_s * 0.4 + lighting_s * 0.3 + crowd_s * 0.3)

                    AreaSafetyScore.objects.create(
                        latitude=round(lat, 4),
                        longitude=round(lng, 4),
                        crime_score=round(crime_s, 1),
                        lighting_score=round(lighting_s, 1),
                        crowd_score=round(crowd_s, 1),
                        overall_score=round(overall, 1),
                        time_period=period,
                    )
                    count += 1

        self.stdout.write(f'  Created {count} area safety scores')
