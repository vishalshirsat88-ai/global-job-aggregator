import os
import requests
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

router = APIRouter()

PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET")

PAYPAL_API_BASE = "https://api-m.sandbox.paypal.com"
TOOL_URL = "https://your-streamlit-tool-url"


def get_access_token():
    resp = requests.post(
        f"{PAYPAL_API_BASE}/v1/oauth2/token",
        auth=(PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET),
        data={"grant_type": "client_credentials"},
        timeout=10
    )

    if resp.status_code != 200:
        raise HTTPException(status_code=500, detail="PayPal auth failed")

    return resp.json().get("access_token")


@router.get("/paypal/success")
def paypal_success(token: str, email: str):
    access_token = get_access_token()

    capture = requests.post(
        f"{PAYPAL_API_BASE}/v2/checkout/orders/{token}/capture",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
        },
        timeout=10
    )

    data = capture.json()

    # 🔒 STRONG VERIFICATION
    if (
        capture.status_code in (200, 201)
        and data.get("status") == "COMPLETED"
    ):
        # TODO (later): save email + payment details
        return RedirectResponse(url=TOOL_URL, status_code=302)

    raise HTTPException(
        status_code=400,
        detail=f"Payment verification failed: {data}"
    )
