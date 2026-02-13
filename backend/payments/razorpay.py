import os
import razorpay
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/razorpay", tags=["Razorpay Payments"])

# ===============================
# ENV CONFIG
# ===============================

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

# ===============================
# CLIENT INITIALIZATION
# ===============================

def get_client():
    if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
        raise HTTPException(status_code=500, detail="Razorpay not configured")

    return razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))


# ===============================
# CREATE ORDER ROUTE
# ===============================

@router.post("/create-order")
def create_order(amount: int):
    """
    Creates Razorpay order.
    Amount must be in paise (₹100 = 10000)
    """

    client = get_client()

    try:
        order_data = {
            "amount": amount,
            "currency": "INR",
            "payment_capture": 1
        }

        order = client.order.create(data=order_data)

        return {
            "order_id": order["id"],
            "amount": order["amount"],
            "currency": order["currency"],
            "key": RAZORPAY_KEY_ID
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
