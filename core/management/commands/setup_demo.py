"""
Setup demo data for hackathon presentation.
Creates trusted contacts, an active journey, and fake call profiles.
Run: python manage.py setup_demo
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from core.models import (
    TrustedContact, Journey, FakeCallProfile, ArrivalConfirmation,
    SafeNetworkMember, TransportLog
)


class Command(BaseCommand):
    help = 'Setup demo data for hackathon presentation'

    def handle(self, *args, **options):
        user = User.objects.get(username='demo')
        self.stdout.write('Setting up demo for hackathon...')

        # ========================================
        # Trusted Contacts
        # ========================================
        TrustedContact.objects.filter(user=user).delete()
        contacts = [
            {'name': 'Ammi (Mother)', 'phone': '+92 300 1234567', 'email': 'ammi@family.pk', 'relationship': 'Mother', 'is_primary': True},
            {'name': 'Abu (Father)', 'phone': '+92 321 9876543', 'email': 'abu@family.pk', 'relationship': 'Father', 'is_primary': False},
            {'name': 'Fatima (Sister)', 'phone': '+92 333 4567890', 'email': 'fatima@family.pk', 'relationship': 'Sister', 'is_primary': False},
            {'name': 'Ayesha (Best Friend)', 'phone': '+92 345 1112233', 'email': 'ayesha@friend.pk', 'relationship': 'Best Friend', 'is_primary': False},
        ]
        for c in contacts:
            TrustedContact.objects.create(user=user, **c)
        self.stdout.write(f'  Created {len(contacts)} trusted contacts')

        # ========================================
        # Active Journey (for demo)
        # ========================================
        Journey.objects.filter(user=user, status='active').delete()
        journey = Journey.objects.create(
            user=user,
            source_lat=31.5620,
            source_lng=74.3150,
            dest_lat=31.5170,
            dest_lng=74.3460,
            source_name='Anarkali Bazaar',
            dest_name='Kalma Chowk',
            current_lat=31.5450,
            current_lng=74.3300,
            status='active',
            safety_score=72.5,
            eta_minutes=18,
            started_at=timezone.now() - timedelta(minutes=7),
            checkin_interval=15,
            last_checkin=timezone.now() - timedelta(minutes=5),
            next_checkin_due=timezone.now() + timedelta(minutes=10),
        )
        # Add shared contacts
        journey.shared_contacts.set(TrustedContact.objects.filter(user=user))

        # Arrival confirmation
        ArrivalConfirmation.objects.create(
            journey=journey,
            confirmation_due_at=timezone.now() + timedelta(minutes=20),
        )
        self.stdout.write(f'  Created active journey: {journey.tracking_id}')
        self.stdout.write(f'    Tracking URL: /track/{journey.tracking_id}/')

        # ========================================
        # Fake Call Profiles
        # ========================================
        FakeCallProfile.objects.filter(user=user).delete()
        profiles = [
            {'caller_name': 'Ammi', 'caller_number': '+92 300 1234567', 'caller_photo': 'female1', 'delay_seconds': 3, 'ringtone': 'default'},
            {'caller_name': 'Abu', 'caller_number': '+92 321 9876543', 'caller_photo': 'male1', 'delay_seconds': 5, 'ringtone': 'loud'},
            {'caller_name': 'Office HR', 'caller_number': '+92 42 35761234', 'caller_photo': 'female2', 'delay_seconds': 10, 'ringtone': 'default'},
        ]
        for p in profiles:
            FakeCallProfile.objects.create(user=user, **p)
        self.stdout.write(f'  Created {len(profiles)} fake call profiles')

        # ========================================
        # Safe Network Profile
        # ========================================
        SafeNetworkMember.objects.filter(user=user).delete()
        SafeNetworkMember.objects.create(
            user=user,
            is_verified=True,
            status='available',
            latitude=31.5497,
            longitude=74.3436,
            bio='SafePath community volunteer',
            helped_count=3,
        )
        self.stdout.write('  Created safe network profile (verified)')

        # ========================================
        # Transport Log (recent ride)
        # ========================================
        TransportLog.objects.filter(user=user).delete()
        TransportLog.objects.create(
            user=user,
            transport_type='careem',
            plate_number='LEA-4521',
            driver_name='Muhammad Akram',
            driver_phone='+92 311 5556677',
            vehicle_color='White',
            vehicle_description='Toyota Corolla 2019, Careem sticker on windshield',
            pickup_lat=31.5620,
            pickup_lng=74.3150,
            pickup_address='Anarkali Bazaar, Lahore',
            destination_address='Kalma Chowk, Gulberg',
            status='completed',
            expected_duration_minutes=20,
            completed_at=timezone.now() - timedelta(hours=2),
        )
        TransportLog.objects.create(
            user=user,
            transport_type='rickshaw',
            plate_number='LHR-7789',
            driver_name='',
            vehicle_color='Yellow/Green',
            vehicle_description='Auto rickshaw, standard',
            pickup_lat=31.5170,
            pickup_lng=74.3460,
            pickup_address='Kalma Chowk',
            destination_address='Model Town',
            status='active',
            expected_duration_minutes=15,
        )
        self.stdout.write('  Created transport logs (1 completed, 1 active)')

        # ========================================
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write(self.style.SUCCESS('DEMO READY FOR HACKATHON!'))
        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write('')
        self.stdout.write('Demo Credentials:')
        self.stdout.write('  Username: demo')
        self.stdout.write('  Password: demo123')
        self.stdout.write('')
        self.stdout.write('Demo Flow (3-minute presentation):')
        self.stdout.write('  1. / (Home) -> Show stats & quick search')
        self.stdout.write('  2. /route-planner/ -> Analyze route (31.56,74.31 to 31.52,74.35)')
        self.stdout.write('  3. /journey/start/ -> Show journey creation')
        self.stdout.write(f'  4. /journey/{journey.tracking_id}/ -> Live tracking')
        self.stdout.write(f'  5. /track/{journey.tracking_id}/ -> Public tracking link')
        self.stdout.write('  6. /sos/ -> SOS button + contacts')
        self.stdout.write('  7. /siren/ -> Emergency siren demo')
        self.stdout.write('  8. /fake-call/ -> Fake call demo')
        self.stdout.write('  9. /disguise/ -> Type 1122 in calculator')
        self.stdout.write(' 10. /transport/ -> Show logged ride')
        self.stdout.write(' 11. /evidence/ -> Quick record demo')
        self.stdout.write(' 12. /ai-assistant/ -> Ask "What is SafePath?"')
        self.stdout.write(' 13. /legal-rights/ -> Show Pakistani laws')
        self.stdout.write(' 14. /dashboard/ -> Analytics overview')
