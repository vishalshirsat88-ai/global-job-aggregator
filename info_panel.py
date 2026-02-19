def get_help_html():
    return """
<style>
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
    z-index: 9999;
}

@media (max-width: 768px) {
    .help-modal {
        width: 92%;
        padding: 20px;
    }
}
</style>

<div class="help-modal">

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

<p><b>💡 Pro Tip:</b><br>
Always open JobHunt++ using your bookmarked link.
</p>

</div>
"""
