import os
import razorpay
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

# DB imports
from backend.payments.db import save_payment
from backend.payments.db import get_db

# 🆕 Email service import
from backend.services.email_service import send_access_email, send_admin_alert


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
        raise HTTPException(status_code=19900, detail="Razorpay not configured")
    return razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))



# ===============================
# CREATE ORDER
# ===============================
@router.post("/create-order")
def create_order(email: str):

    client = get_client()
    amount = 500   # ₹1 = 100 paise
    
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
        try:
            send_access_email(data.email, access_token)
        except Exception as e:
            print("⚠️ Email send failed:", e)

        redirect_url = f"{TOOL_URL}?token={access_token}"

        return {
            "success": True,
            "redirect_url": redirect_url
        }


    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===============================
# RAZORPAY WEBHOOK (ALERT FOR MISSED VERIFICATION)
# ===============================
@router.post("/webhook")
async def razorpay_webhook(request: Request):

    payload = await request.json()

    try:
        event = payload.get("event")
    
        if event == "payment.captured":
    
            payment = payload["payload"]["payment"]["entity"]
    
            order_id = payment.get("order_id")
            email = payment.get("notes", {}).get("email") or payment.get("email")
    
            if not order_id or not email:
                return {"status": "ignored"}
    
            conn = get_db()
            cur = conn.cursor()

            try:
                cur.execute(
                    "SELECT access_token FROM payments WHERE order_id=%s",
                    (order_id,)
                )
                exists = cur.fetchone()
            finally:
                conn.close()
            
            if not exists:
    
                print("⚠️ Recovering missed payment:", order_id)
    
                access_token = save_payment(email, order_id)
    
                # Send user access email
                try:
                    send_access_email(email, access_token)
                    print("📧 Recovery email sent to:", email)
                except Exception as e:
                    print("User email failed:", e)
    
                # Send admin alert
                try:
                    alert_msg = f"""
    ⚠️ Payment auto-recovered.
    
    Order ID: {order_id}
    User Email: {email}
    
    User closed payment tab before verification.
    System generated token automatically.
    """
    
                    send_admin_alert(alert_msg)
                    print("✅ AUTO RECOVERY COMPLETED:", order_id)
                except Exception as e:
                    print("Admin alert failed:", e)
    
    except Exception as e:
        print("Webhook error:", e)
    
    return {"status": "received"}
