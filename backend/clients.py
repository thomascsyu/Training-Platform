import stripe
from openai import OpenAI

from config import DEEPSEEK_API_KEY, STRIPE_API_KEY

deepseek_client = None
if DEEPSEEK_API_KEY:
    deepseek_client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

if STRIPE_API_KEY:
    stripe.api_key = STRIPE_API_KEY
