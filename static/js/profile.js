document.addEventListener("DOMContentLoaded", function() {
    let fileInput = document.getElementById("id_profile_picture");

    fileInput.addEventListener("change", function() {
        if (fileInput.files.length > 0) {
            let formData = new FormData();
            formData.append("profile_picture", fileInput.files[0]);

            // Get CSRF token
            let csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;
            formData.append("csrfmiddlewaretoken", csrfToken);

            fetch("/upload-profile-picture/", {
                method: "POST",
                body: formData
            }).then(response => {
                if (response.ok) {
                    location.reload(); // Reload page after successful upload
                } else {
                    alert("Failed to upload image.");
                }
            }).catch(error => console.error("Error:", error));
        }
    });
});

function toggleEdit() {
    let viewMode = document.querySelector(".view-mode");
    let editMode = document.querySelector(".edit-mode");

    viewMode.classList.toggle("hidden");
    editMode.classList.toggle("hidden");
}
