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
(https://github.com/vishalshirsat88-ai/global-job-aggregator/tree/fastapi-backend)

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
