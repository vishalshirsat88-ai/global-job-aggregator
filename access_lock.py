import streamlit as st
import requests
import uuid
from info_panel import show_getting_started_panel

BACKEND_URL = "https://global-job-aggregator-production.up.railway.app"


def verify_access():
    params = st.query_params

    
    # ===============================
    # 🟢 DEV MODE BYPASS
    # ===============================
    if params.get("dev") == "true":
        st.session_state["access_token"] = "DEV_MODE"
        st.session_state["session_id"] = "DEV_SESSION"
        st.toast("🛠️ Dev Mode Active — Access Bypassed")
        return

    # ===============================
    # STEP 1: GET TOKEN FROM URL OR SESSION
    # ===============================
    token = params.get("token")

    # If token not in URL, try session storage
    if not token:
        token = st.session_state.get("access_token")

    if not token:
        st.error("❌ Missing access token. Please purchase access first.")
        st.stop()

    # Save token to session permanently
    st.session_state["access_token"] = token

    # ===============================
    # STEP 2: SESSION ID CREATION
    # ===============================
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())

    session_id = st.session_state.session_id

    # ===============================
    # STEP 3: VERIFY WITH BACKEND
    # ===============================
    try:
        response = requests.get(
            f"{BACKEND_URL}/payments/paypal/verify-access",
            params={
                "token": token,
                "session_id": session_id
            },
            timeout=10
        )

        data = response.json()

        if not data.get("valid"):
            st.error(f"🚫 {data.get('message', 'Access denied')}")
            st.stop()
        
        if data["valid"]:
            if data["message"] == "Session replaced":
                st.toast(
                    "⚠️ You opened JobHunt++ on another device. "
                    "An older session was automatically logged out."
                )

        # ===============================
        # STEP 4: SHOW WELCOME MESSAGE ONCE
        # ===============================
        if "welcome_shown" not in st.session_state:
            st.session_state.welcome_shown = True
        
            # Open help popup automatically
            st.session_state["show_help_card"] = True



            #st.info("🚀 You now have lifetime access. Enjoy exploring global job opportunities!")

        # ===============================
        # STEP 5: CLEAN URL (AFTER SAVING TOKEN)
        # ===============================
        if "token" in params:
            st.query_params.clear()

    except Exception:
        st.error("⚠️ Unable to verify access. Please try again later.")
        st.stop()
