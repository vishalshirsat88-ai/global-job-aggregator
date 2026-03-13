import streamlit as st
from urllib.parse import quote

def show_getting_started_panel():

    st.markdown("## 🎉 Welcome to JobHunt++ — You’re All Set!")

    # 🎁 BONUS KIT AT THE TOP
    st.markdown("""
### 🎁 Your Bonus Career Kit (Included)

✔ AI Negotiation Simulator
✔ 25 Resume Templates  
✔ 20 Cover Letter Templates  

""")

    token = st.session_state.get("token") or st.session_state.get("access_token")

    if token:
        download_link = f"https://global-job-aggregator-production.up.railway.app/download/bonus-kit?token={quote(token)}"

        st.markdown(f"""
        <a href="{download_link}" target="_blank">
            <button style="
                width:100%;
                padding:14px;
                font-size:16px;
                font-weight:600;
                border-radius:12px;
                border:none;
                color:white;
                background:linear-gradient(135deg,#4F6CF7,#7A6FF0);
                box-shadow:0 6px 18px rgba(79,108,247,0.4);
                cursor:pointer;
                margin-top:8px;
                margin-bottom:20px;
            ">
            Download Kit
            </button>
        </a>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # EMAIL SECTION
    st.markdown("""
### 📩 Check Your Email (Important)
Your personal lifetime access link has been sent to your email.

Please check:
- Inbox  
- Spam / Junk folder
""")

    st.markdown("---")

    st.markdown("""
### ⭐ Bookmark Your Access Link FIRST
Open the link from your email and **bookmark it immediately.**

👉 Always use this bookmarked link to open the tool.
""")

    st.markdown("---")

    st.markdown("""
### 🔁 If You Ever See “Invalid Token”

No worries.

Just:
- Open your email again  
- Click your access link  
- Bookmark again
""")

    st.markdown("---")

    st.markdown("""
### 🔗 Refer Friends

Share our website:

👉 https://avantara.co.in

Each user receives their own lifetime access link after purchase.
""")

    st.markdown("---")

    st.markdown("""
💡 **Pro Tip:**  
Always open JobHunt++ using your bookmarked link.
""")
