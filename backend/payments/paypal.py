import os
import requests
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

router = APIRouter(prefix="/paypal", tags=["Payments"])

# ===============================
# ENV CONFIG
# ===============================

PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET")
PAYPAL_MODE = os.getenv("PAYPAL_MODE", "sandbox").lower()
TOOL_URL = os.getenv("TOOL_URL")

def validate_config():
    if not PAYPAL_CLIENT_ID or not PAYPAL_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="PayPal not configured")

    if not TOOL_URL:
        raise HTTPException(status_code=500, detail="TOOL_URL not configured")


PAYPAL_API_BASE = (
    "https://api-m.paypal.com"
    if PAYPAL_MODE == "live"
    else "https://api-m.sandbox.paypal.com"
)

# ===============================
# PAYPAL AUTH
# ===============================

def get_access_token():
    response = requests.post(
        f"{PAYPAL_API_BASE}/v1/oauth2/token",
        auth=(PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET),
        data={"grant_type": "client_credentials"},
        timeout=15,
    )

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="PayPal authentication failed")

    return response.json().get("access_token")


# ===============================
# CREATE ORDER
# ===============================

@router.post("/create-order")
def create_order(email: str):
    validate_config()

    """
    Creates PayPal order and returns approval URL
    """

    access_token = get_access_token()

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
        "payment_source": {
            "paypal": {
                "experience_context": {
                    "payment_method_preference": "IMMEDIATE_PAYMENT_REQUIRED",
                    "brand_name": "JobHunt++",
                    "locale": "en-US",
                    "landing_page": "LOGIN",
                    "shipping_preference": "NO_SHIPPING",
                    "user_action": "PAY_NOW",
                    "return_url": TOOL_URL,
                    "cancel_url": TOOL_URL
                }
            }
        }
    }


    response = requests.post(
        f"{PAYPAL_API_BASE}/v2/checkout/orders",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        },
        json=order_data,
        timeout=15,
    )

    if response.status_code not in (200, 201):
        raise HTTPException(status_code=400, detail="Failed to create PayPal order")

    data = response.json()

    approval_url = next(
        link["href"] for link in data["links"]
        if link["rel"] == "approve"
    )

    return {
        "approval_url": approval_url,
        "order_id": data["id"]
    }


# ===============================
# CAPTURE ORDER
# ===============================

@router.post("/capture-order")
def capture_order(order_id: str):
    validate_config()

    """
    Captures PayPal order after user approval
    """

    access_token = get_access_token()

    response = requests.post(
        f"{PAYPAL_API_BASE}/v2/checkout/orders/{order_id}/capture",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        },
        timeout=15,
    )

    if response.status_code not in (200, 201):
        raise HTTPException(status_code=400, detail="Capture failed")

    data = response.json()

    if data.get("status") != "COMPLETED":
        raise HTTPException(status_code=400, detail="Payment not completed")

    # Extract payment details safely
    purchase_unit = data["purchase_units"][0]
    capture_info = purchase_unit["payments"]["captures"][0]

    return {
        "status": "success",
        "order_id": order_id,
        "amount": capture_info["amount"]["value"],
        "currency": capture_info["amount"]["currency_code"],
        "payer_email": purchase_unit.get("custom_id")
    }
from fastapi.responses import RedirectResponse

@router.get("/success")
def paypal_success(token: str = None):

    if not token:
        raise HTTPException(status_code=400, detail="Missing token")

    # Capture order
    result = capture_order(token)

    # Redirect to Streamlit tool
    return RedirectResponse(
        "https://streamlit-frontend-production-1667.up.railway.app"
    )
