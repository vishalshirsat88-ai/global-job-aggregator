import os
import requests
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

router = APIRouter(prefix="/paypal", tags=["payments"])

# ===============================
# ENV CONFIG
# ===============================

PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET")
PAYPAL_MODE = os.getenv("PAYPAL_MODE", "sandbox").lower()
TOOL_URL = os.getenv("TOOL_URL", "https://your-streamlit-tool-url")
BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL")

if not BACKEND_BASE_URL:
    raise Exception("BACKEND_BASE_URL not configured")

PAYPAL_API_BASE = (
    "https://api-m.paypal.com"
    if PAYPAL_MODE == "live"
    else "https://api-m.sandbox.paypal.com"
)

# ===============================
# PAYPAL AUTH
# ===============================

def get_access_token() -> str:
    resp = requests.post(
        f"{PAYPAL_API_BASE}/v1/oauth2/token",
        auth=(PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET),
        data={"grant_type": "client_credentials"},
        timeout=10,
    )

    if resp.status_code != 200:
        raise HTTPException(status_code=500, detail="PayPal authentication failed")

    token = resp.json().get("access_token")
    if not token:
        raise HTTPException(status_code=500, detail="PayPal access token missing")

    return token


# ===============================
# CREATE ORDER
# ===============================

@router.post("/create-order")
def create_order(email: str):

    print("=== DEBUG ENV CHECK ===")
    print("CLIENT ID:", PAYPAL_CLIENT_ID)
    print("SECRET EXISTS:", bool(PAYPAL_CLIENT_SECRET))
    print("MODE:", PAYPAL_MODE)
    print("BACKEND_BASE_URL:", BACKEND_BASE_URL)
    print("=======================")

    
    access_token = get_access_token()

    response = requests.post(
        f"{PAYPAL_API_BASE}/v2/checkout/orders",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
        },
        json={
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "amount": {
                        "currency_code": "USD",
                        "value": "10.00"
                    }
                }
            ],
            "application_context": {
                "return_url": f"{BACKEND_BASE_URL}/payments/paypal/success?email={email}",
                "cancel_url": TOOL_URL
            }
        },
        timeout=10,
    )

    if response.status_code not in (200, 201):
        raise HTTPException(status_code=400, detail="Failed to create PayPal order")

    data = response.json()

    approval_url = next(
        link["href"] for link in data["links"]
        if link["rel"] == "approve"
    )

    

    return {"approval_url": approval_url}


# ===============================
# PAYMENT SUCCESS CALLBACK
# ===============================

@router.get("/success")
def paypal_success(token: str, email: str):

    access_token = get_access_token()

    capture_resp = requests.post(
        f"{PAYPAL_API_BASE}/v2/checkout/orders/{token}/capture",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
        },
        timeout=10,
    )

    if capture_resp.status_code not in (200, 201):
        raise HTTPException(status_code=400, detail="PayPal capture request failed")

    data = capture_resp.json()

    if data.get("status") != "COMPLETED":
        raise HTTPException(status_code=400, detail="Payment not completed")

    amount_info = (
        data
        .get("purchase_units", [{}])[0]
        .get("payments", {})
        .get("captures", [{}])[0]
        .get("amount", {})
    )

    currency = amount_info.get("currency_code")
    value = amount_info.get("value")

    if not currency or not value:
        raise HTTPException(status_code=400, detail="Invalid payment amount data")

    return RedirectResponse(url=TOOL_URL, status_code=302)
