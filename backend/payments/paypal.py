import os
import requests
import uuid
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse

# DB imports
from backend.payments.db import save_payment, verify_and_register_session

router = APIRouter(prefix="/paypal", tags=["Payments"])

# ===============================
# ENV CONFIG
# ===============================
PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET")
PAYPAL_MODE = os.getenv("PAYPAL_MODE", "sandbox").lower()
TOOL_URL = os.getenv("TOOL_URL")
BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL")

PAYPAL_API_BASE = (
    "https://api-m.paypal.com"
    if PAYPAL_MODE == "live"
    else "https://api-m.sandbox.paypal.com"
)

# ===============================
# VALIDATION
# ===============================
def validate_config():
    if not PAYPAL_CLIENT_ID or not PAYPAL_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="PayPal credentials missing")
    if not TOOL_URL:
        raise HTTPException(status_code=500, detail="TOOL_URL missing")
    if not BACKEND_BASE_URL:
        raise HTTPException(status_code=500, detail="BACKEND_BASE_URL missing")


# ===============================
# GET ACCESS TOKEN
# ===============================
def get_access_token():
    try:
        response = requests.post(
            f"{PAYPAL_API_BASE}/v1/oauth2/token",
            auth=(PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET),
            data={"grant_type": "client_credentials"},
            timeout=15,
        )

        if response.status_code != 200:
            print("❌ PayPal Auth Failed:", response.text)
            raise HTTPException(status_code=500, detail="PayPal authentication failed")

        return response.json().get("access_token")

    except Exception as e:
        print("❌ Token Error:", e)
        raise HTTPException(status_code=500, detail="PayPal connection error")


# ===============================
# 1️⃣ CREATE ORDER
# ===============================
@router.post("/create-order")
def create_order(email: str):
    validate_config()
    access_token = get_access_token()

    print("📦 Creating PayPal order for:", email)

    order_data = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "amount": {
                    "currency_code": "USD",
                    "value": "0.60"
                },
                "custom_id": email
            }
        ],
        "application_context": {
            "user_action": "PAY_NOW",
            "return_url": f"{BACKEND_BASE_URL}/payments/paypal/success",
            "cancel_url": f"{BACKEND_BASE_URL}/payments/paypal/payment-cancelled",
            "shipping_preference": "NO_SHIPPING"
        }
    }

    try:
        response = requests.post(
            f"{PAYPAL_API_BASE}/v2/checkout/orders",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            },
            json=order_data,
            timeout=15
        )

        data = response.json()

        if response.status_code not in (200, 201):
            print("❌ Order Creation Failed:", response.text)
            raise HTTPException(status_code=400, detail="Failed to create PayPal order")

        approval_url = next(
            (link["href"] for link in data.get("links", []) if link["rel"] == "approve"),
            None,
        )

        if not approval_url:
            raise HTTPException(status_code=500, detail="Approval URL missing")

        return {"approval_url": approval_url}

    except Exception as e:
        print("❌ Create Order Error:", e)
        raise HTTPException(status_code=500, detail=str(e))


# ===============================
# 2️⃣ SUCCESS ROUTE (CAPTURE + TOKEN GENERATION)
# ===============================
@router.get("/success")
def paypal_success(token: str = None):

    print("🔥 PayPal returned with token:", token)

    if not token:
        return RedirectResponse("/")

    validate_config()
    access_token = get_access_token()

    try:
        response = requests.post(
            f"{PAYPAL_API_BASE}/v2/checkout/orders/{token}/capture",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}"
            },
            timeout=15,
        )

        # Already captured
        if response.status_code == 422:
            print("ℹ️ Order already captured")
            return RedirectResponse("/")

        if response.status_code not in (200, 201):
            print("❌ Capture failed:", response.text)
            return RedirectResponse("/")

        data = response.json()

        email = data["purchase_units"][0]["custom_id"]
        order_id = data["id"]

        # Save payment and generate access token
        access_token_value = save_payment(email, order_id)

        print("🎉 Payment successful!")
        print("🔑 Generated Access Token:", access_token_value)

        redirect_url = f"{TOOL_URL}?access={access_token_value}"

        return RedirectResponse(redirect_url)

    except Exception as e:
        print("❌ Capture error:", e)
        return RedirectResponse("/")


# ===============================
# 3️⃣ VERIFY ACCESS (SESSION CONTROL)
# ===============================
@router.get("/verify-access")
def verify_access(
    token: str = Query(...),
    session_id: str = Query(...)
):
    """
    Called by Streamlit to:
    - verify token
    - enforce concurrent session limit
    """

    is_valid, message = verify_and_register_session(token, session_id)

    return {
        "valid": is_valid,
        "message": message
    }


# ===============================
# CANCEL ROUTE
# ===============================
@router.get("/payment-cancelled")
def cancelled():
    return RedirectResponse("/?status=cancelled")

