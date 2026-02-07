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
    )
    return resp.json()["access_token"]

@router.get("/paypal/success")
def paypal_success(token: str):
    access_token = get_access_token()

    capture = requests.post(
        f"{PAYPAL_API_BASE}/v2/checkout/orders/{token}/capture",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
        },
    )

    data = capture.json()

    if capture.status_code == 201:
        return RedirectResponse(url=TOOL_URL, status_code=302)

    raise HTTPException(status_code=400, detail="Payment verification failed")
