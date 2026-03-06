import streamlit as st
from urllib.parse import quote

def show_getting_started_panel():
    st.markdown("## 🎉 Welcome to JobHunt++ — You’re All Set!")

    st.success("Your lifetime access is now active.")

    st.markdown("""
### 📩 Check Your Email (Important)
Your personal lifetime access link has been sent to your email.

Please check:
- Inbox  
- Spam / Junk folder

---

### ⭐ Bookmark Your Access Link FIRST
Open the link from your email and **bookmark it immediately.**

👉 Always use this bookmarked link to open the tool.

---

### 🔁 If You Ever See “Invalid Token”
No worries.

Just:
- Open your email again  
- Click your access link  
- Bookmark again  

---


### 🎁 Your Bonus Career Kit (Included)

✔ 25 Resume Templates  
✔ 20 Cover Letter Templates  
✔ HR Interview Q&A Guide
""")

    token = st.session_state.get("token") or st.session_state.get("access_token")
    
    if token:
        download_link = f"https://global-job-aggregator-production.up.railway.app/download/bonus-kit?token={quote(token)}"
        
        st.link_button(
            "⬇ Download Bonus Career Kit",
            download_link,
            use_container_width=True
        )

    st.markdown("""
---
### 🔗 Refer Friends
Share our website:

👉 https://avantara.co.in

Each user receives their own lifetime access link after purchase.

---

💡 **Pro Tip:**  
Always open JobHunt++ using your bookmarked link.
""")
