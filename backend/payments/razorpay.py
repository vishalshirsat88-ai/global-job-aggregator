import os
import razorpay
import threading
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

def _send_email_bg(email, token):
    try:
        send_access_email(email, token)
    except Exception as e:
        print("⚠️ Email send failed:", e)


# DB imports
from backend.payments.db import save_payment

# 🆕 Email service import
from backend.services.email_service import send_access_email

router = APIRouter(prefix="/razorpay", tags=["Razorpay Payments"])

# ===============================
# ENV CONFIG
# ===============================
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")
TOOL_URL = os.getenv("TOOL_URL")


# ===============================
# REQUEST MODEL
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
# CREATE ORDER
# ===============================
@router.post("/create-order")
def create_order(amount: int, email: str):

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
# VERIFY PAYMENT + EMAIL SEND
# ===============================
@router.post("/verify-payment")
def verify_payment(data: RazorpayVerifyRequest):

    client = get_client()

    # 🔐 Verify signature
    try:
        params_dict = {
            "razorpay_order_id": data.razorpay_order_id,
            "razorpay_payment_id": data.razorpay_payment_id,
            "razorpay_signature": data.razorpay_signature,
        }

        client.utility.verify_payment_signature(params_dict)

    except Exception:
        raise HTTPException(status_code=400, detail="Payment verification failed")

    # 💾 Save payment + generate token
    try:
        access_token = save_payment(data.email, data.razorpay_order_id)

        # 🆕 SEND EMAIL (non-blocking safe call)
    
        
        threading.Thread(
            target=_send_email_bg,
            args=(data.email, access_token),
            daemon=True
        ).start()


        redirect_url = f"{TOOL_URL}?token={access_token}"

        return {
            "success": True,
            "redirect_url": redirect_url
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
