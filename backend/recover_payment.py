from backend.payments.db import save_payment
from backend.services.email_service import send_access_email

email = "user@email.com"
order_id = "order_xxxxx"

token = save_payment(email, order_id)

send_access_email(email, token)

print("Recovered payment. Token:", token)
