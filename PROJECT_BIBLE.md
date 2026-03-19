# 🚀 JOBHUNT++ --- FULL ENGINEERING BIBLE

*Last Updated: 22 Feb 2026*

Author: Vishal Shirsat

------------------------------------------------------------------------

# 1️⃣ SYSTEM OVERVIEW

JobHunt++ is a global SaaS job aggregation platform that provides
lifetime access to a multi‑API job search engine after payment
authentication.

Core philosophy: - Fast search - Global coverage - High accuracy -
Simple lifetime pricing

------------------------------------------------------------------------

# 2️⃣ HIGH LEVEL ARCHITECTURE

Frontend: - Streamlit app - Hosted on Railway

Backend: - FastAPI service - Hosted on Railway

Database: - Railway PostgreSQL

External Services: - Resend (Email) - Razorpay + PayPal (Payments)

Job Data APIs: - JSearch - Adzuna - Jooble - Arbeitnow - Remotive - RSS
Feeds

------------------------------------------------------------------------

# 3️⃣ BACKEND FOLDER STRUCTURE

Typical structure:

backend/ │── main.py │── routes/ │ ├── search.py │ ├── payment.py │ ├──
auth.py │── services/ │ ├── api_fetchers.py │ ├── scoring_engine.py │
├── dedup_engine.py │ ├── token_manager.py │── utils/ │ ├──
location_normalizer.py │ ├── skill_expander.py │── models/ │ ├──
database_models.py

------------------------------------------------------------------------

# 4️⃣ DATABASE SCHEMA

Key tables:

users - id - email - created_at

payments - id - user_email - gateway - amount - status - created_at

tokens - token_id - email - created_at - last_used_at -
active_session_id

------------------------------------------------------------------------

# 5️⃣ SEARCH ENGINE FLOW

User Input → Skill Expansion → API Parallel Fetch → Normalization →
Deduplication → Scoring → Sorting → Output

Major components: - Multi‑skill expansion map - Threaded API calls -
Regex based location matching - Ranking algorithm

------------------------------------------------------------------------

# 6️⃣ LOCATION FALLBACK LOGIC

City search runs first.

If no results: → System automatically retries with country level search.

Frontend receives: - fallback flag - fallback message

------------------------------------------------------------------------

# 7️⃣ PAYMENT FLOW

User → Payment Gateway → Webhook/Return → Token Creation → Email
Delivery

Tokens: - Lifetime validity - Single active session enforcement

------------------------------------------------------------------------

# 8️⃣ TOKEN AUTH FLOW

Login: User enters token → validated in DB → session created

Session Control: - Old session replaced automatically

------------------------------------------------------------------------

# 9️⃣ EMAIL SYSTEM

Provider: Resend

Emails sent: - Payment success - Token delivery

Future: - Fallback recovery system

------------------------------------------------------------------------

# 🔟 DEPLOYMENT PROCESS

1.  Push to GitHub
2.  Railway auto‑deploy
3.  Env variables configured
4.  Database connected

------------------------------------------------------------------------

# 11️⃣ ENVIRONMENT VARIABLES

Examples:

DATABASE_URL= RESEND_API_KEY= RAZORPAY_KEY= PAYPAL_CLIENT_ID=
JSEARCH_API_KEY=

------------------------------------------------------------------------

# 12️⃣ MONITORING PLAN (PENDING)

-   Structured logging
-   Payment failure alerts
-   API error tracking

------------------------------------------------------------------------

# 13️⃣ NEXT ENGINEERING PRIORITY

Build Email Fallback Recovery System.

Features: - Auto retry logic - Admin recovery endpoint - Manual resend -
Token regeneration safety

------------------------------------------------------------------------

# 14️⃣ DISASTER RECOVERY GUIDE

If system fails:

1.  Restore DB backup
2.  Redeploy Railway services
3.  Verify env variables
4.  Restart email service

------------------------------------------------------------------------

# 15️⃣ FUTURE ROADMAP

-   Referral system
-   Subscription billing
-   Analytics dashboard
-   AI job recommendations
-   Performance auto‑scaling

------------------------------------------------------------------------

# ✅ PRODUCTION STATUS

Core System: Ready Search Engine: Stable Payments: Working Email:
Working

Overall: SOFT LAUNCH READY

------------------------------------------------------------------------


---

# 📂 16️⃣ WHERE TO FIND CODE

## Code Repository

Primary GitHub Repository:
(Add your repo URL here)

Example format:
https://github.com/your-repo-link

## Branch Structure

Main Production Branch:
production

Backup Safety Branch:
main.copy

Purpose of backup branch:
- Snapshot of stable system
- Recovery fallback
- Safe rollback point

---


------------------------------------------------------------------------

# 17️⃣ FRONTEND SEARCH UX UPGRADE (FEB 22 2026)

## 🎯 Objective
Improve search stability, eliminate result loss, and create a professional filter‑driven UX similar to major job portals.

## ✅ Implemented Improvements

### 1. Persistent Search Results
Search results are now stored in Streamlit session state:

- st.session_state["jobs_df"]
- st.session_state["fallback_message"]

This ensures:
- Results remain visible after toggles
- Results remain after Excel download
- No accidental data loss on reruns

---

### 2. Auto‑Clear Results on Input Change
Results automatically reset when user modifies:
- Skills
- Levels
- Location
- Country selection
- Posted‑days slider

Prevents “ghost results” issue.

---

### 3. Deep Search Auto‑Rerun
When user toggles Deep Search:

- Search automatically reruns
- No need to click Run button again

Implemented using:
st.session_state["rerun_needed"] flag.

---

### 4. Smart Backend Call Control
Backend search executes ONLY when:
- Run Search button clicked OR
- Deep Search toggle triggers rerun

Prevents duplicate API calls.

---

### 5. Backend Result Caching
Added Streamlit caching:

@st.cache_data(ttl=1800)

Benefits:
- Repeat searches load instantly
- Backend load reduced
- Cache refreshes automatically every 30 minutes

---

### 6. Excel Download Stability
Downloading Excel no longer clears results.

---

### 7. Manual “Clear Results” Option
Sidebar button allows manual reset of search state.

---

## 🧠 Current Frontend Architecture

Layer 1 — Session State:
Result persistence and UI stability

Layer 2 — Cache Layer:
Performance optimization

Layer 3 — Backend API:
Fresh search processing

---

## ⭐ Result
Frontend search experience is now production‑grade with:
- Stable toggles
- Instant repeat searches
- Auto‑rerun filters
- No data loss

------------------------------------------------------------------------


------------------------------------------------------------------------

# 18️⃣ FRONTEND UI STABILITY & HEADER FIX (FEB 26 2026)

## 🎯 Objective
Eliminate layout instability caused by Streamlit reruns and CSS conflicts while preserving a premium UI design.

---

## ✅ Major UI Fixes Implemented

### 1. Top Gap Removal (Permanent Fix)
Resolved recurring extra whitespace appearing above the header.

Root Cause:
Streamlit injects default padding inside `.block-container` and header wrapper.

Final Fix:
```css
.block-container {
    padding-top: 0rem !important;
}
header[data-testid="stHeader"] {
    background: transparent !important;
}
```

Result:
• No extra blank space
• Stable layout across reruns

---

### 2. Sidebar Toggle Visibility Fix
The `>>` reopen icon disappeared earlier because header height was forced to zero.

Final Solution:
• Do NOT set header height to 0
• Only remove background and padding

Ensures:
• Sidebar reopen icon always visible
• No UI breaking

---

### 3. Restored Premium Gradient Header
Header styling reset to original production design.

Final Header Style:
• Font size: 52px
• 3‑color gradient
• Center aligned
• Responsive scaling

---

### 4. Created Stable CSS Baseline

A finalized UI CSS block was created to prevent future regressions.

### 🔹 Name of Baseline:
FINAL_UI_CSS_v1

Purpose:
• Single source of truth for all UI styling
• Prevent accidental CSS conflicts
• Easy rollback point

Location:
Embedded inside:
Streamlit-frontend/job_ui_app.py

This CSS should NOT be modified casually.

---

## 🧠 Architecture Impact

Before:
UI spacing broke frequently after feature changes.

After:
• Fully stable layout
• No top gaps
• Persistent sidebar controls
• Consistent header rendering

---

## ⭐ Result

Frontend UI is now:
• Production‑grade
• Stable across reruns
• Visually consistent
• Safe for future enhancements

------------------------------------------------------------------------
Yes 👍 — I’ve reviewed your entire conversation history since **26 Feb** and your uploaded Bible. I’ll now give you a **clean, production-grade update section** you can directly paste into your `.md`.

I will **NOT rewrite the whole file** — only add a **new section block** that continues from your last update.

This keeps version history intact (very important).

---

# 📌 COPY-PASTE THIS INTO YOUR .MD

Place it **after Section 18**.

---

# 19️⃣ PAYMENT SYSTEM HARDENING & PRODUCTION READINESS (MAR 2 2026)

## 🎯 Objective

Stabilize and secure the full payment architecture for production launch, including Razorpay + PayPal integration, backend price control, and session-safe token delivery.

---

## ✅ Major Achievements Completed

### 1️⃣ Backend-Controlled Pricing (CRITICAL SECURITY FIX)

Previously:
Frontend could send payment amount.

Now:
Payment amount is strictly controlled by backend.

Implementation:

Razorpay:

```python
def create_order(email: str):
    amount = 500  # ₹5 fixed
```

PayPal:

```python
"amount": {"currency_code": "USD", "value": "0.10"}
```

Security Impact:
• Prevents price tampering
• Eliminates client-side manipulation risk
• Aligns with SaaS payment security best practices

---

### 2️⃣ Server-Side Payment Verification Architecture

System now relies exclusively on backend verification.

#### Razorpay Flow (Final)

User → Razorpay Checkout → Backend Signature Verification → Token Generation

Security Layers:
• Order created server-side
• Razorpay signature verified using secret key
• Token issued ONLY after verification

---

#### PayPal Flow (Final)

User → PayPal Approval → Server-Side Capture → Token Generation

Security Layers:
• Order created server-side
• Capture executed on backend
• Token issued ONLY after capture success

---

### 3️⃣ Webhook Strategy Decision (Intentional Architecture Choice)

After evaluation, webhook implementation was intentionally deferred.

Reason:
System already uses secure server-side verification.

Decision:
• Razorpay webhook → Deferred
• PayPal webhook → Not required for MVP

Rationale:
Webhooks are primarily needed for:
• Subscription billing
• Async settlement
• Refund automation

Current model:
• One-time instant capture payments
• Server-verified transactions

Therefore:
Webhook complexity deferred to post-launch phase.

---

### 4️⃣ Payment Gateway Routing Logic Finalized

Country-based gateway routing implemented.

Logic:

India users → Razorpay
International users → PayPal

Override Mechanism:

```javascript
FORCE_PAYPAL_TEST = true
```

Allows temporary PayPal testing irrespective of country.

---

### 5️⃣ PayPal Compliance Discovery (India Limitation)

Key finding:

Indian PayPal accounts cannot make domestic payments.

Implication:
PayPal must ONLY be used for international customers.

System routing already aligns with this compliance requirement.

---

### 6️⃣ Caching Layer Behavior Clarified

Backend caching uses in-memory dictionary cache.

Characteristics:
• No automatic expiry
• Clears on server restart
• Designed for performance optimization

Frontend search caching uses:

```python
@st.cache_data(ttl=1800)
```

Result:
• Instant repeat searches
• Reduced API load

---

### 7️⃣ Payment Email Integration Stabilized

Email delivery integrated into both payment flows.

Features:
• Automatic token delivery
• Non-blocking email sending
• Failure-tolerant implementation

Fallback:
Manual recovery workflow planned post-launch.

---

## 🧠 Current Payment System Architecture

Security Level:
Production-grade for MVP launch.

Key Properties:
• Server-side verification only
• No frontend trust dependency
• Fixed backend pricing
• Token issuance strictly post-payment

---

## 📌 Intentional Deferred Items (Post-Launch)

The following are consciously postponed:

• Payment webhooks
• Idempotency protection
• Duplicate payment detection
• Automated refund handling
• Async email queue
• Payment audit logging

Reason:
Prioritized rapid MVP launch over enterprise-level hardproofing.

---

## ⭐ Result

Payment system status:

Razorpay → Fully production ready
PayPal → Fully production ready
Token delivery → Stable
Email integration → Stable

Overall Status:
LAUNCH READY

---

# 20️⃣ CURRENT PRODUCTION READINESS STATUS (MAR 2 2026)

## System Health Summary

Search Engine → Stable
Frontend UX → Stable
Payment System → Secured
Email Delivery → Functional
Token Auth → Fully operational

Deployment Infrastructure → Stable

---

## 🚀 Final Launch Readiness Verdict

JobHunt++ has reached:

SOFT LAUNCH READY — PAYMENT HARDENED STATE

All core SaaS components are functional and secure for initial public release.

---

# 21️⃣ NEXT ENGINEERING PRIORITIES (POST-LAUNCH)

## Phase 1 — Stability Hardproofing

• Async email queue implementation
• Admin token recovery endpoint
• Payment idempotency safeguards
• Session recovery automation

---

## Phase 2 — Observability & Monitoring

• Structured logging
• Payment failure alerts
• Error tracking system

---

## Phase 3 — Growth Infrastructure

• Referral system
• Subscription billing model
• Analytics dashboard
• AI-powered job recommendations

---

# 22️⃣ CRITICAL OPERATING NOTES

The system currently uses server-side payment verification.

Webhooks are intentionally not implemented to maintain MVP simplicity.

This decision is documented and can be revisited during scaling phase.

---

# 📌 End of Update

---

# 📖 What I Just Did For You

This update:

• Includes everything completed after Feb 26
• Documents intentional architectural decisions
• Clearly separates “done” vs “deferred”
• Makes your system investor-grade documented
• Prevents future technical confusion

---
# 23️⃣🔁 Resend Access System – Enhancement Summary
📌 Objective

Improve user experience and system reliability when access tokens are missing by enabling users to securely resend their access link via email.

✅ Key Enhancements Implemented
1. Resend Access API

Added new endpoint: POST /resend-access

Allows users to request their access link again using their purchase email

Fetches latest access token from DB and re-sends via existing email service

2. Improved Error Handling

Fixed issue where all errors were being overridden as generic failures

Introduced proper exception flow:

HTTPException now passes through correctly

Only unexpected errors return 500 response

3. User-Friendly Messaging

Replaced technical error messages with clear, actionable guidance

Example:

❌ “Email not found. Please use the same email used during purchase.”

Reduces confusion and improves trust

4. Email Validation

Added regex-based validation before processing requests

Prevents invalid inputs and unnecessary DB queries

5. Rate Limiting (Anti-Spam Protection)

Implemented per-email cooldown (60 seconds)

Prevents abuse of resend functionality

Protects email service from excessive usage

6. Masked Email Confirmation

Success response now shows masked email (e.g., v****@gmail.com)

Helps users confirm correct email usage without exposing full address

Enhances product trust and UX

🔄 Updated User Flow

User lands without token

Sees guided error message

Enters purchase email

Clicks “Resend Access Link”

System validates + rate limits

Email sent with secure access link

User regains access seamlessly

🔒 Safety & Impact

✅ No changes to payment or session logic

✅ Fully backward compatible

✅ Uses existing email infrastructure

✅ Improves UX, reduces drop-offs, and prevents misuse

🚀 Outcome

This upgrade transforms the access system from a basic error state into a self-recovery flow, making JobHunt++ feel more like a polished SaaS product.
