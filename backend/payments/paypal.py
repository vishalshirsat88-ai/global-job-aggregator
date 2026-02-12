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

PAYPAL_API_BASE = (
    "https://api-m.paypal.com"
    if PAYPAL_MODE == "live"
    else "https://api-m.sandbox.paypal.com"
)


def validate_config():
    if not PAYPAL_CLIENT_ID or not PAYPAL_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="PayPal not configured")

    if not TOOL_URL:
        raise HTTPException(status_code=500, detail="TOOL_URL not configured")


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
        "application_context": {
            "brand_name": "JobHunt++",
            "landing_page": "LOGIN",
            "user_action": "PAY_NOW",
            "return_url": TOOL_URL,
            "cancel_url": TOOL_URL
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

    print("PAYPAL STATUS:", response.status_code)
    print("PAYPAL RESPONSE:", response.text)

    if response.status_code not in (200, 201):
        raise HTTPException(status_code=400, detail="Failed to create PayPal order")

    data = response.json()

    approval_url = None
    for link in data.get("links", []):
        if link.get("rel") == "approve":
            approval_url = link.get("href")
            break

    if not approval_url:
        raise HTTPException(status_code=500, detail=f"Approval URL missing: {data}")

    return {"approval_url": approval_url}


# ===============================
# SUCCESS CALLBACK
# ===============================

@router.get("/success")
def paypal_success(token: str = None):
    if not token:
        raise HTTPException(status_code=400, detail="Missing token")

    access_token = get_access_token()

    response = requests.post(
        f"{PAYPAL_API_BASE}/v2/checkout/orders/{token}/capture",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        },
        timeout=15,
    )

    if response.status_code not in (200, 201):
        raise HTTPException(status_code=400, detail="Payment capture failed")

    data = response.json()

    if data.get("status") != "COMPLETED":
        raise HTTPException(status_code=400, detail="Payment not completed")

    return RedirectResponse(TOOL_URL)
