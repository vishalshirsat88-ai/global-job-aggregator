import streamlit as st


def get_help_html():

    return """
<style>

/* Overlay */
.modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0,0,0,0.55);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 9999;
}

/* Modal Box */
.modal-box {
    background: white;
    width: 75%;
    max-width: 800px;
    max-height: 85vh;
    overflow-y: auto;
    padding: 28px;
    border-radius: 12px;
    position: relative;
    animation: fadeIn 0.3s ease;
}

/* Mobile Responsive */
@media (max-width: 768px) {
    .modal-box {
        width: 92%;
        padding: 20px;
    }
}

/* Close Button */
.close-btn {
    position: absolute;
    right: 16px;
    top: 12px;
    font-size: 22px;
    cursor: pointer;
    font-weight: bold;
}

/* Animation */
@keyframes fadeIn {
    from {opacity: 0; transform: scale(0.95);}
    to {opacity: 1; transform: scale(1);}
}

</style>


<div id="helpModal" class="modal-overlay" onclick="outsideClick(event)">
    <div class="modal-box">

        <div class="close-btn" onclick="closeModal()">✖</div>

        <h2>🎉 Welcome to JobHunt++ — You’re All Set!</h2>

        <div style="background:#E8F5E9;padding:12px;border-radius:8px;margin-bottom:20px;">
            Your lifetime access is now active.
        </div>

        <h3>📩 Check Your Email (Important)</h3>
        <p>Your personal lifetime access link has been sent to your email.</p>
        <ul>
            <li>Bookmark the link immediately</li>
            <li>If token shows invalid → reopen email link</li>
            <li>Check Spam/Junk folder</li>
        </ul>

        <h3>🎁 Free Perks Included</h3>
        <ul>
            <li>Unlimited job searches</li>
            <li>Global job coverage</li>
            <li>Lifetime access</li>
        </ul>

        <h3>🔗 Share With Friends</h3>
        <p>Send them to: <b>https://avantara.co.in</b></p>

        <hr>

        <p>
        💡 <b>Pro Tip:</b><br>
        Always open JobHunt++ using your bookmarked link.
        </p>

    </div>
</div>


<script>

function closeModal() {
    document.getElementById("helpModal").style.display = "none";
}

function outsideClick(event) {
    if (event.target.id === "helpModal") {
        closeModal();
    }
}

/* Escape Key Support */
document.addEventListener("keydown", function(event) {
    if (event.key === "Escape") {
        closeModal();
    }
});

</script>
"""
