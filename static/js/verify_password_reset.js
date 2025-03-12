function checkVerificationStatus() {
    fetch("/check-password-reset-verification/")
        .then(response => response.json())
        .then(data => {
            if (data.status === "verified") {
                window.location.href = data.redirect_url;
            } else {
                setTimeout(checkVerificationStatus, 3000);
            }
        })
        .catch(error => console.error("❌ Error checking verification status:", error));
}

document.addEventListener("DOMContentLoaded", checkVerificationStatus);

let canResend = true;

function resendEmail() {
    if (!canResend) {
        console.log("⏳ Please wait before resending.");
        return;
    }

    canResend = false;

    fetch("/resend-password-reset-verification/", {
        method: "POST",
        headers: {
            "X-CSRFToken": getCSRFToken(),
            "Content-Type": "application/json"
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            console.log("✅", data.message);
        } else {
            console.log("❌", data.error || "An error occurred.");
        }
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
