import os
import requests

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
TOOL_URL = os.getenv("TOOL_URL")


def send_access_email(email: str, token: str):
    """
    Sends lifetime access email to user
    """

    if not RESEND_API_KEY:
        print("⚠️ Resend API key missing")
        return

    access_link = f"{TOOL_URL}?token={token}"

    payload = {
        "from": "JobHunt++ <onboarding@resend.dev>",
        "to": [email],
        "subject": "🎉 Your JobHunt++ Access is Ready!",
        "html": f"""
        <h2>Hi there 👋</h2>

        <p>Your payment was successful.</p>

        <p><strong>Click below to access your lifetime dashboard:</strong></p>

        <a href="{access_link}" 
           style="padding:12px 20px;background:#4f46e5;color:white;
                  text-decoration:none;border-radius:8px;">
           Open JobHunt++
        </a>

        <br><br>

        <p><strong>Bonus Materials Included:</strong></p>
        <ul>
            <li>Resume Templates</li>
            <li>Interview Kit</li>
            <li>Cover Letter Guide</li>
        </ul>

        <p>Thanks for choosing JobHunt++ 🚀</p>
        """
    }

    try:
        r = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=15
        )

        print("📧 Email sent:", r.status_code, r.text)

    except Exception as e:
        print("❌ Email sending failed:", e)
