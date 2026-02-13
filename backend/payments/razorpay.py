import os
import razorpay
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# DB imports
from backend.payments.db import save_payment

router = APIRouter(prefix="/razorpay", tags=["Razorpay Payments"])

# ===============================
# ENV CONFIG
# ===============================
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")
TOOL_URL = os.getenv("TOOL_URL")


# ===============================
# REQUEST MODEL (NEW)
# ===============================
class RazorpayVerifyRequest(BaseModel):
    razorpay_payment_id: str
    razorpay_order_id: str
    razorpay_signature: str
    email: str


# ===============================
# CLIENT INIT
# ===============================
def get_client():
    if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
        raise HTTPException(status_code=500, detail="Razorpay not configured")
    return razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))


# ===============================
# 1️⃣ CREATE ORDER
# ===============================
@router.post("/create-order")
def create_order(amount: int, email: str):
    """
    Create Razorpay order
    Amount must be in paise
    """

    client = get_client()

    try:
        order_data = {
            "amount": amount,
            "currency": "INR",
            "payment_capture": 1,
            "notes": {
                "email": email
            }
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


# ===============================
# 2️⃣ VERIFY PAYMENT (FIXED)
# ===============================
@router.post("/verify-payment")
def verify_payment(data: RazorpayVerifyRequest):
    """
    Verifies Razorpay payment signature
    Then saves payment & generates token
    """

    client = get_client()

    try:
        params_dict = {
            "razorpay_order_id": data.razorpay_order_id,
            "razorpay_payment_id": data.razorpay_payment_id,
            "razorpay_signature": data.razorpay_signature,
        }

        client.utility.verify_payment_signature(params_dict)

    except Exception:
        raise HTTPException(status_code=400, detail="Payment verification failed")

    try:
        # Save payment
        access_token = save_payment(data.email, data.razorpay_order_id)

        redirect_url = f"{TOOL_URL}?token={access_token}"

        return {
            "success": True,
            "redirect_url": redirect_url
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
