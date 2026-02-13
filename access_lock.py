import streamlit as st
import requests
import uuid

BACKEND_URL = "https://global-job-aggregator-production.up.railway.app"

def verify_access():
    params = st.query_params

    token = params.get("token")

    if not token:
        st.error("❌ Missing access token. Please purchase access first.")
        st.stop()

    # Create persistent session id
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())

    payload = {
        "token": token,
        "session_id": st.session_state.session_id
    }

    try:
        response = requests.post(
            f"{BACKEND_URL}/verify-access",
            json=payload,
            timeout=10
        )

        data = response.json()

        if not data.get("allowed"):
            st.error("🚫 Maximum users reached for this access token.")
            st.stop()

    except Exception:
        st.error("⚠️ Unable to verify access. Please try again later.")
        st.stop()
