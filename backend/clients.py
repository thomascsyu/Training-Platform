import stripe

from ai_settings import get_active_client, get_client_for_provider
from config import STRIPE_API_KEY

if STRIPE_API_KEY:
    stripe.api_key = STRIPE_API_KEY


__all__ = ["get_active_client", "get_client_for_provider", "stripe"]
