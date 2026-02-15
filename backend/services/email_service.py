import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

TOOL_URL = os.getenv("TOOL_URL")
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")


def send_access_email(email: str, token: str):
    """
    Sends lifetime access email to user via Gmail SMTP
    """

    access_link = f"{TOOL_URL}?token={token}"

    html_content = f"""
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

    send_email_gmail(
        to_email=email,
        subject="🎉 Your JobHunt++ Access is Ready!",
        html_content=html_content
    )


def send_email_gmail(to_email: str, subject: str, html_content: str):
    """
    Generic Gmail SMTP sender
    """
    try:
        msg = MIMEMultipart()
        msg["From"] = f"NextGen Labs <{SMTP_EMAIL}>"
        msg["To"] = to_email
        msg["Subject"] = subject

        msg.attach(MIMEText(html_content, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.send_message(msg)

        print("✅ Gmail email sent successfully")

    except Exception as e:
        print("❌ Gmail email failed:", str(e))
