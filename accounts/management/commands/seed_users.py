from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone


class Command(BaseCommand):
    help = 'Seed the database with sample users for testing and demos'

    def handle(self, *args, **options):
        User = get_user_model()

        samples = [
            {
                'username': 'alex',
                'email': 'alex@example.com',
                'first_name': 'Alex',
                'last_name': 'Kaboré',
                'gender': 'M',
                'bio': 'Enjoys hiking and photography.',
                'location': 'Zone 1',
                'is_online': True,
            },
            {
                'username': 'sophie',
                'email': 'sophie@example.com',
                'first_name': 'Sophie',
                'last_name': 'Ouédraogo',
                'gender': 'F',
                'bio': 'Yoga lover and foodie.',
                'location': 'Tampouy',
                'is_online': True,
            },
            {
                'username': 'chris',
                'email': 'chris@example.com',
                'first_name': 'Chris',
                'last_name': 'Sawadogo',
                'gender': 'M',
                'bio': 'Tech enthusiast and gamer.',
                'location': 'Rimkieta',
                'is_online': False,
            },
            {
                'username': 'maya',
                'email': 'maya@example.com',
                'first_name': 'Maya',
                'last_name': 'Traoré',
                'gender': 'F',
                'bio': 'Passionate about art and travel.',
                'location': 'Ouaga 2000',
                'is_online': True,
            },
            {
                'username': 'leo',
                'email': 'leo@example.com',
                'first_name': 'Leo',
                'last_name': 'Zongo',
                'gender': 'M',
                'bio': 'Music producer and coffee addict.',
                'location': 'Tanghin',
                'is_online': False,
            },
        ]

        created = 0
        for data in samples:
            user, was_created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    'email': data['email'],
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'gender': data.get('gender', ''),
                    'bio': data.get('bio', ''),
                    'location': data.get('location', ''),
                    'is_online': data.get('is_online', False),
                    'last_activity': timezone.now(),
                }
            )

            if was_created:
                user.set_password('Password123!')
                user.save()
                created += 1

        self.stdout.write(self.style.SUCCESS(f'Seed complete. Created {created} users.'))
























