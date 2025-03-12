function checkVerificationStatus() {
    fetch("/check-verification-status/", { method: "GET", redirect: "follow" })
        .then(response => {
            if (response.redirected) {
                window.location.href = response.url;
            } else {
                setTimeout(checkVerificationStatus, 5000);
            }
        })
        .catch(() => setTimeout(checkVerificationStatus, 5000));
}

checkVerificationStatus();

let canResend = true;

function resendEmail() {
    if (!canResend) {
        console.log("⏳ Please wait before resending.");
        return;
    }

    canResend = false;
    fetch(resendUrl, {
        method: "POST",
        headers: {
            "X-CSRFToken": getCSRFToken(),
        },
    })
    .then(response => response.json())
    .then(data => {
        console.log("✅", data.message || "Verification email resent.");
        startCooldown();
    })
    .catch(error => {
        console.error("❌ Error resending email:", error);
        canResend = true;
    });
}

function startCooldown() {
    setTimeout(() => {
        canResend = true;
        console.log("🔄 You can resend the email now.");
    }, 30000);
}

function getCSRFToken() {
    return document.cookie
        .split("; ")
        .find(row => row.startsWith("csrftoken="))
        ?.split("=")[1] || "";
}
