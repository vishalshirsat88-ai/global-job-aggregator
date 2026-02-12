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
        print("❌ PayPal credentials missing")
        raise HTTPException(status_code=500, detail="PayPal not configured")

    if not TOOL_URL:
        print("❌ TOOL_URL missing")
        raise HTTPException(status_code=500, detail="TOOL_URL not configured")

    if not BACKEND_BASE_URL:
        print("❌ BACKEND_BASE_URL missing")
        raise HTTPException(status_code=500, detail="BACKEND_BASE_URL not configured")


# ===============================
# GET PAYPAL ACCESS TOKEN
# ===============================

def get_access_token():
    try:
        response = requests.post(
            f"{PAYPAL_API_BASE}/v1/oauth2/token",
            auth=(PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET),
            data={"grant_type": "client_credentials"},
            timeout=15,
        )

        print("🔐 PayPal Auth Status:", response.status_code)

        if response.status_code != 200:
            print("❌ PayPal Auth Failed:", response.text)
            raise HTTPException(status_code=500, detail="PayPal authentication failed")

        return response.json().get("access_token")

    except requests.RequestException as e:
        print("❌ PayPal token error:", str(e))
        raise HTTPException(status_code=500, detail="PayPal connection error")


# ===============================
# CREATE ORDER
# ===============================

@router.post("/create-order")
def create_order(email: str):
    validate_config()
    access_token = get_access_token()

    print("📦 Creating PayPal order for:", email)
    print("RETURN URL HARDCODED:", "https://dreamy-dodol-6c8de0.netlify.app")

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
            "return_url": "https://dreamy-dodol-6c8de0.netlify.app/success.html",
            "cancel_url": TOOL_URL,
            "shipping_preference": "NO_SHIPPING"
        }

    }

    try:
        response = requests.post(
            f"{PAYPAL_API_BASE}/v2/checkout/orders",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}"
            },
            json=order_data,
            timeout=15,
        )

        print("📦 Order Status:", response.status_code)
        print("📦 Order Response:", response.text)

        if response.status_code not in (200, 201):
            raise HTTPException(status_code=400, detail="Failed to create PayPal order")

        data = response.json()

        approval_url = next(
            (link["href"] for link in data.get("links", []) if link["rel"] == "approve"),
            None,
        )

        if not approval_url:
            raise HTTPException(status_code=500, detail="Approval URL missing")

        return {"approval_url": approval_url}

    except requests.RequestException as e:
        print("❌ Create order error:", str(e))
        raise HTTPException(status_code=500, detail="PayPal connection error")

# ===============================
# CAPTURE ORDER FROM FRONTEND
# ===============================

@router.post("/capture-order")
def capture_order(token: str):
    print("💰 Frontend capture request:", token)

    if not token:
        raise HTTPException(status_code=400, detail="Missing token")

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

        print("💰 Capture Status:", response.status_code)
        print("💰 Capture Response:", response.text)

        if response.status_code not in (200, 201):
            raise HTTPException(status_code=400, detail="Capture failed")

        data = response.json()

        if data.get("status") != "COMPLETED":
            raise HTTPException(status_code=400, detail="Payment not completed")

        return {"success": True, "redirect": TOOL_URL}

    except requests.RequestException as e:
        print("❌ Capture error:", str(e))
        raise HTTPException(status_code=500, detail="Capture failed")

# ===============================
# PAYMENT SUCCESS CALLBACK
# ===============================

@router.get("/success")
def paypal_success(token: str = None):
    print("🔥 SUCCESS ROUTE HIT — REDIRECTING TO:", TOOL_URL)
    print("Token:", token)


    if not token:
        raise HTTPException(status_code=400, detail="Missing token")

    validate_config()
    access_token = get_access_token()

    try:
        print("💰 Capturing order:", token)

        response = requests.post(
            f"{PAYPAL_API_BASE}/v2/checkout/orders/{token}/capture",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}"
            },
            timeout=15,
        )

        print("💰 Capture Status:", response.status_code)
        print("💰 Capture Response:", response.text)

        if response.status_code not in (200, 201):
            print("❌ Capture failed → redirecting anyway")
            return RedirectResponse(TOOL_URL)

        data = response.json()

        if data.get("status") != "COMPLETED":
            print("❌ Payment not completed")
            return RedirectResponse(TOOL_URL)

        print("🎉 Payment successful → redirecting to tool")

        return RedirectResponse(
            TOOL_URL,
            status_code=302
        )

    except requests.RequestException as e:
        print("❌ Capture error:", str(e))
        return RedirectResponse(TOOL_URL)
