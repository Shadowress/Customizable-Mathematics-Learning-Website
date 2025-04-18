document.addEventListener("DOMContentLoaded", () => {
    const sections = document.querySelectorAll(".section");
    if (!sections.length) return;

    let currentActiveSection = sections[0]; // Default active section

    // Initially hide all section bodies except the first
    sections.forEach((section, index) => {
        const body = section.querySelector(".section-body");
        if (index !== 0 && body) {
            body.style.display = "none";
        }
    });

    sections.forEach((section) => {
        const titleDiv = section.querySelector(".section-title");
        const body = section.querySelector(".section-body");

        if (!titleDiv || !body) return;

        titleDiv.style.cursor = "pointer";

        titleDiv.addEventListener("click", () => {
            if (section === currentActiveSection) {
                // Toggle off current section
                body.style.display = "none";
                currentActiveSection = null;
                return;
            }

            // Hide the currently active section if any
            if (currentActiveSection) {
                const prevBody = currentActiveSection.querySelector(".section-body");
                if (prevBody) prevBody.style.display = "none";
            }

            // Show the clicked section
            body.style.display = "block";
            currentActiveSection = section;
        });
    });``

    // Open transcription
    document.querySelectorAll('.transcription-toggle-btn').forEach(button => {
        button.addEventListener('click', function () {
            const targetId = this.dataset.target;
            const panel = document.getElementById(targetId);
            if (panel) {
                panel.classList.add('open');
            }
        });
    });

    // Close transcription
    document.querySelectorAll('.transcription-close-btn').forEach(button => {
        button.addEventListener('click', function () {
            const targetId = this.dataset.target;
            const panel = document.getElementById(targetId);
            if (panel) {
                panel.classList.remove('open');
            }
        });
    });
});
