def get_help_html():

    return """
<style>

/* Overlay */
.help-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0,0,0,0.6);
    z-index: 9999;
}

/* Modal */
.help-modal {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 70%;
    max-width: 800px;
    max-height: 85vh;
    overflow-y: auto;
    background: white;
    padding: 30px;
    border-radius: 12px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.4);
}

/* Mobile */
@media (max-width: 768px) {
    .help-modal {
        width: 92%;
        padding: 20px;
    }
}

/* Close button */
.help-close {
    position: absolute;
    top: 12px;
    right: 16px;
    font-size: 22px;
    font-weight: bold;
}

</style>

<div class="help-overlay"></div>

<div class="help-modal">

<div style="text-align:right">
    <span class="help-close">✖</span>
</div>

<h2>🎉 Welcome to JobHunt++ — You’re All Set!</h2>

<div style="background:#E8F5E9;padding:12px;border-radius:8px;margin-bottom:20px;">
Your lifetime access is now active.
</div>

<h3>📩 Check Your Email (Important
