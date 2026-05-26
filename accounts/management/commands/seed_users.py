from django.core.management.base import BaseCommand

from accounts.models import User


class Command(BaseCommand):

    help = 'Create default system users'


    def handle(self, *args, **kwargs):

        users = [

            {
                'username': 'ali',
                'password': '123',
                'role': 'waiter',
            },

            {
                'username': 'sardor',
                'password': '123',
                'role': 'waiter',
            },

            {
                'username': 'chef1',
                'password': '123',
                'role': 'kitchen',
            },

            {
                'username': 'chef2',
                'password': '123',
                'role': 'kitchen',
            },

            {
                'username': 'manager',
                'password': '123',
                'role': 'manager',
            },

        ]


        for user_data in users:

            if not User.objects.filter(
                username=user_data['username']
            ).exists():

                user = User.objects.create_user(
                    username=user_data['username'],
                    password=user_data['password'],
                    role=user_data['role']
                )

                self.stdout.write(

                    self.style.SUCCESS(

                        f"Created: {user.username}"

                    )

                )

            else:

                self.stdout.write(

                    self.style.WARNING(

                        f"Already exists: {user_data['username']}"

                    )

                )