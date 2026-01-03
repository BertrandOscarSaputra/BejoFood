"""
Management command to set up Telegram webhook.
Usage: python manage.py setup_webhook https://your-domain.com/webhook/telegram/
"""
import httpx
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Set up Telegram webhook URL'

    def add_arguments(self, parser):
        parser.add_argument('webhook_url', type=str, help='Full webhook URL')
        parser.add_argument('--delete', action='store_true', help='Delete existing webhook')

    def handle(self, *args, **options):
        token = settings.TELEGRAM_BOT_TOKEN
        if not token:
            self.stderr.write(self.style.ERROR('TELEGRAM_BOT_TOKEN not set'))
            return

        base_url = f"https://api.telegram.org/bot{token}"

        if options['delete']:
            self.delete_webhook(base_url)
        else:
            webhook_url = options['webhook_url']
            self.set_webhook(base_url, webhook_url)

    def set_webhook(self, base_url, webhook_url):
        self.stdout.write(f"Setting webhook to: {webhook_url}")
        
        response = httpx.post(
            f"{base_url}/setWebhook",
            json={
                "url": webhook_url,
                "allowed_updates": ["message", "callback_query"]
            }
        )
        
        result = response.json()
        if result.get('ok'):
            self.stdout.write(self.style.SUCCESS('Webhook set successfully!'))
            self.get_webhook_info(base_url)
        else:
            self.stderr.write(self.style.ERROR(f"Failed: {result.get('description')}"))

    def delete_webhook(self, base_url):
        self.stdout.write("Deleting webhook...")
        
        response = httpx.post(f"{base_url}/deleteWebhook")
        result = response.json()
        
        if result.get('ok'):
            self.stdout.write(self.style.SUCCESS('Webhook deleted!'))
        else:
            self.stderr.write(self.style.ERROR(f"Failed: {result.get('description')}"))

    def get_webhook_info(self, base_url):
        response = httpx.get(f"{base_url}/getWebhookInfo")
        result = response.json()
        
        if result.get('ok'):
            info = result.get('result', {})
            self.stdout.write(f"\nWebhook Info:")
            self.stdout.write(f"  URL: {info.get('url')}")
            self.stdout.write(f"  Pending updates: {info.get('pending_update_count', 0)}")
            if info.get('last_error_message'):
                self.stdout.write(self.style.WARNING(f"  Last error: {info.get('last_error_message')}"))
