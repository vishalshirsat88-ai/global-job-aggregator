import streamlit as st
import requests
import uuid


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
        st.error("""
    ❌ Access token missing or expired.
    
    🔐 Don’t worry, we’ve got you covered!  
    This is a security feature to prevent misuse.
    
    👉 To access the tool again, simply click the link/button sent to your 📩 email.  
    Your personal lifetime access link has already been sent.
    
    📬 Please check:
    • Inbox  
    • Spam / Junk folder  
    """)
    
        # 🔥 NEW: Resend Access Section (SAFE ADDITION)
        st.markdown("### 📧 Need your access link again?")
    
        user_email = st.text_input("Enter your email to resend access link")
    
        if st.button("📨 Resend Access Link"):
            if user_email:
                st.success("If this email exists, your access link will be sent shortly.")
            else:
                st.warning("Please enter your email.")
    
        st.info("💡 Tip: Bookmark your access email for quick login.")
    
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
        
            #st.info("🚀 You now have lifetime access. Enjoy exploring global job opportunities!")

        # ===============================
        # STEP 5: CLEAN URL (AFTER SAVING TOKEN)
        # ===============================
        if "token" in params:
            st.query_params.clear()

    except Exception:
        st.error("⚠️ Unable to verify access. Please try again later.")
        st.stop()
