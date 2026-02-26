from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

BASE_STYLE = """
<style>
body {
    font-family: Arial, sans-serif;
    margin: 40px auto;
    max-width: 900px;
    line-height: 1.7;
    color: #333;
    padding: 0 20px;
}
h1 {
    color: #0a2540;
}
h2 {
    margin-top: 30px;
    color: #0a2540;
}
</style>
"""

# ================= TERMS =================

@router.get("/terms", response_class=HTMLResponse)
def terms():
    return BASE_STYLE + """
<h1>Terms and Conditions</h1>
<p>Last Updated: February 2026</p>

<h2>1. Nature of Service</h2>
<p>JobHunt++ is a job aggregation platform that collects job listings from third-party sources and APIs.</p>

<h2>2. No Employment Guarantee</h2>
<p>We do not guarantee job availability, hiring outcomes, or interview calls.</p>

<h2>3. Third-Party Data Disclaimer</h2>
<p>All job data belongs to respective sources. We are not responsible for accuracy or validity.</p>

<h2>4. User Access</h2>
<p>Access is granted via unique token after payment. Tokens are non-transferable.</p>

<h2>5. Payments</h2>
<p>Payments are processed through secure third-party gateways.</p>

<h2>6. Limitation of Liability</h2>
<p>We are not liable for job outcomes or indirect damages.</p>

<h2>7. Governing Law</h2>
<p>These terms are governed by the laws of India.</p>

<h2>8. Contact</h2>
<p>Email: support@avantara.co.in</p>
"""

# ================= PRIVACY =================

@router.get("/privacy", response_class=HTMLResponse)
def privacy():
    return BASE_STYLE + """
<h1>Privacy Policy</h1>
<p>Last Updated: February 2026</p>

<h2>1. Information Collected</h2>
<p>Email address, payment confirmation, and usage data.</p>

<h2>2. Usage of Data</h2>
<p>Data is used for account management and service improvement.</p>

<h2>3. Third-Party Sharing</h2>
<p>Limited data shared with payment gateways and API providers.</p>

<h2>4. Data Security</h2>
<p>We implement industry standard security practices.</p>

<h2>5. User Rights</h2>
<p>You may request data access or deletion anytime.</p>

<h2>6. Contact</h2>
<p>Email: support@avantara.co.in</p>
"""

# ================= REFUND =================

@router.get("/refund", response_class=HTMLResponse)
def refund():
    return BASE_STYLE + """
<h1>Refund Policy</h1>
<p>Last Updated: February 2026</p>

<h2>1. Refund Eligibility</h2>
<p>Refunds allowed if token not delivered or technical access failure.</p>

<h2>2. Non-Refundable Cases</h2>
<p>No refund after token usage or successful access.</p>

<h2>3. Timeline</h2>
<p>Refund requests must be submitted within 7 days.</p>

<h2>4. Processing Time</h2>
<p>Approved refunds processed within 7–10 business days.</p>

<h2>5. Contact</h2>
<p>Email: support@avantara.co.in</p>
"""
