import os
import requests
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

router = APIRouter()

# ===============================
# ENV CONFIG
# ===============================

PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET")

PAYPAL_MODE = os.getenv("PAYPAL_MODE", "sandbox")  # sandbox | live

TOOL_URL = os.getenv(
    "TOOL_URL",
    "https://your-streamlit-tool-url"
)

if not PAYPAL_CLIENT_ID or not PAYPAL_CLIENT_SECRET:
    raise RuntimeError("PayPal credentials not set")

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
        raise HTTPException(
            status_code=500,
            detail="PayPal authentication failed"
        )

    token = resp.json().get("access_token")
    if not token:
        raise HTTPException(
            status_code=500,
            detail="PayPal access token missing"
        )

    return token


# ===============================
# PAYMENT SUCCESS CALLBACK
# ===============================

@router.get("/paypal/success")
def paypal_success(token: str, email: str):
    """
    Verifies PayPal payment and redirects user to tool access
    """

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
        raise HTTPException(
            status_code=400,
            detail="PayPal capture request failed"
        )

    data = capture_resp.json()

    # ===============================
    # STRONG VERIFICATION
    # ===============================

    if data.get("status") != "COMPLETED":
        raise HTTPException(
            status_code=400,
            detail="Payment not completed"
        )

    purchase_units = data.get("purchase_units", [])
    if not purchase_units:
        raise HTTPException(
            status_code=400,
            detail="Invalid PayPal response"
        )

    amount_info = purchase_units[0]["payments"]["captures"][0]["amount"]
    paid_amount = amount_info["value"]
    currency = amount_info["currency_cod_]()_
