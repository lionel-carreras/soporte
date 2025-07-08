from azure.messaging.webpubsubservice import WebPubSubServiceClient
from azure.core.credentials import AzureKeyCredential
from django.conf import settings

client = WebPubSubServiceClient(
    endpoint=settings.AZURE_WEBPUBSUB_ENDPOINT,
    credential=AzureKeyCredential(settings.AZURE_WEBPUBSUB_ACCESS_KEY),
    hub=settings.AZURE_WEBPUBSUB_HUB
)


def send_notification(user_id: int, message: str, url: str = '', notification_type: str = 'ticket'):
    content = {
        "message": message,
        "url": url or "",
        "notification_type": notification_type
    }
    group = f"user_{user_id}"
    client.send_to_group(group, content)
