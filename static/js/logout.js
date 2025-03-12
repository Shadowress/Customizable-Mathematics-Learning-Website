function logout() {
    fetch(logoutUrl, {
        method: "POST",
        headers: {
            "X-CSRFToken": getCSRFToken(),
        },
    })
    .then(response => {
        if (response.ok) {
            window.location.href = "/";
        } else {
            console.error("Logout failed.");
        }
    })
    .catch(error => console.error("Error logging out:", error));
}

function getCSRFToken() {
    return document.cookie
        .split("; ")
        .find(row => row.startsWith("csrftoken="))
        ?.split("=")[1] || "";
}