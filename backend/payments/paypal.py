import os
import requests
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse

router = APIRouter(prefix="/paypal", tags=["Payments"])

# ===============================
# ENV CONFIG & VALIDATION
# ===============================
PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET")
PAYPAL_MODE = os.getenv("PAYPAL_MODE", "sandbox").lower()
TOOL_URL = os.getenv("TOOL_URL")
BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL")

PAYPAL_API_BASE = "https://api-m.paypal.com" if PAYPAL_MODE == "live" else "https://api-m.sandbox.paypal.com"

def validate_config():
    if not PAYPAL_CLIENT_ID or not PAYPAL_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="PayPal credentials missing")
    if not TOOL_URL:
        raise HTTPException(status_code=500, detail="TOOL_URL missing")

def get_access_token():
    try:
        response = requests.post(
            f"{PAYPAL_API_BASE}/v1/oauth2/token",
            auth=(PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET),
            data={"grant_type": "client_credentials"},
            timeout=15,
        )
        return response.json().get("access_token")
    except Exception as e:
        print(f"❌ Token Error: {e}")
        raise HTTPException(status_code=500, detail="PayPal connection error")

# ===============================
# 1. CREATE ORDER (Fixed)
# ===============================
@router.post("/create-order")
def create_order(email: str):
    validate_config()
    access_token = get_access_token()
    
    # URL to your Netlify file named 'success'
    SUCCESS_URL = "https://dreamy-dodol-6c8de0.netlify.app/success.html"
    
    order_data = {
        "intent": "CAPTURE",
        "purchase_units": [{
            "amount": {"currency_code": "USD", "value": "0.60"},
            "custom_id": email
        }],
        "application_context": {
            "user_action": "PAY_NOW",
            "return_url": SUCCESS_URL,
            "cancel_url": SUCCESS_URL,
            "shipping_preference": "NO_SHIPPING"
        }
    }

    try:
        res = requests.post(
            f"{PAYPAL_API_BASE}/v2/checkout/orders",
            headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
            json=order_data,
            timeout=15
        )
        
        data = res.json()
        if res.status_code not in (200, 201):
            print(f"❌ PayPal Order Error: {res.text}")
            raise HTTPException(status_code=400, detail="Failed to create order")

        # Find the link the user needs to click
        approval_url = next(link["href"] for link in data["links"] if link["rel"] == "approve")
        return {"approval_url": approval_url}

    except Exception as e:
        print(f"❌ Create Order Crash: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===============================
# 2. CAPTURE ORDER (The code your Success page calls)
# ===============================
@router.post("/capture-order")
def capture_order(token: str = Query(...)):
    print(f"💰 Received Capture Request for Token: {token}")
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

        # Check if order was already captured (User refreshed the page)
        if response.status_code == 422:
            print("ℹ️ Order already captured. Redirecting user.")
            return {"success": True, "redirect": TOOL_URL}

        if response.status_code not in (200, 201):
            print(f"❌ Capture Failed: {response.text}")
            return {"success": False, "message": "Capture failed"}

        print("🎉 Payment Successful!")
        return {"success": True, "redirect": TOOL_URL}

    except Exception as e:
        print(f"❌ Capture System Error: {e}")
        return {"success": False, "message": str(e)}

# ===============================
# 3. PASSIVE SUCCESS ROUTE
# ===============================
@router.get("/success")
def paypal_success(token: str = None):
    return {"status": "ready", "token": token}