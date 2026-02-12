import os
import requests
from fastapi import APIRouter, HTTPException, Query
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
    
    print(f"📦 Creating PayPal order for: {email}")

    order_data = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "amount": {"currency_code": "USD", "value": "0.60"},
                "custom_id": email
            }
        ],
        "application_context": {
            "user_action": "PAY_NOW",
            "landing_page": "BILLING",
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
            timeout=15
        )

        if response.status_code not in (200, 201):
            print("❌ Create order failed:", response.text)
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
# CAPTURE ORDER (Restored with Checks)
# ===============================
@router.post("/capture-order")
def capture_order(token: str = Query(...)):
    print(f"💰 Frontend capture request for token: {token}")
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
        
        # Check if already captured (prevents error if user refreshes success page)
        if response.status_code == 422:
            data = response.json()
            if any(d.get('issue') == 'ORDER_ALREADY_CAPTURED' for d in data.get('details', [])):
                print("ℹ️ Order already captured, proceeding to tool.")
                return {"success": True, "redirect": TOOL_URL}

        if response.status_code not in (200, 201):
            print("❌ Capture failed:", response.text)
            raise HTTPException(status_code=400, detail="Capture failed")

        data = response.json()
        if data.get("status") != "COMPLETED":
            raise HTTPException(status_code=400, detail="Payment not completed")

        print("🎉 Payment successful!")
        return {"success": True, "redirect": TOOL_URL}

    except requests.RequestException as e:
        print("❌ Capture error:", str(e))
        raise HTTPException(status_code=500, detail="Capture connection error")

# ===============================
# SUCCESS REDIRECT (Simplified to prevent loop)
# ===============================
@router.get("/success")
def paypal_success(token: str = None):
    """
    This route now simply confirms the token exists. 
    The success.html frontend will handle the actual capture.
    """
    if not token:
        return RedirectResponse(url="/?error=missing_token")
    
    print(f"🔥 Success landing hit for token: {token}")
    # We return nothing complex here because success.html is now the 'boss'
    return {"status": "ready_for_capture", "token": token}