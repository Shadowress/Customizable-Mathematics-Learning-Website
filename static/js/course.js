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
    });

    // Course Scheduling
    const scheduleModal = document.getElementById('scheduleCourseModal');
    const rescheduleBtn = document.getElementById('rescheduleBtn');
    const scheduleActionInput = document.getElementById('scheduleAction');
    const scheduledTimeInput = document.getElementById('scheduled_time');
    const confirmRescheduleBtn = document.getElementById('confirmRescheduleBtn');
    const rescheduleInputDiv = document.getElementById('rescheduleForm');

    function setMinDateTime(input) {
        const now = new Date();
        now.setMinutes(now.getMinutes() + 30);
        now.setSeconds(0);
        now.setMilliseconds(0);
        now.setMinutes(now.getMinutes() - now.getTimezoneOffset()); // adjust for timezone

        const minDateTime = now.toISOString().slice(0, 16);
        input.min = minDateTime;
        input.value = minDateTime;

        // Clear previous messages
        input.setCustomValidity('');

        input.addEventListener('input', () => {
            if (input.value < minDateTime) {
                input.setCustomValidity("The date and time selected must be at least 30 minutes from now.");
            } else {
                input.setCustomValidity('');
            }
        });
    }

    // When modal is shown
    if (scheduleModal) {
        scheduleModal.addEventListener('show.bs.modal', () => {
            // Initial setup for datetime-local inputs
            if (scheduledTimeInput) {
                setMinDateTime(scheduledTimeInput);
            }

            // Reset to default modal state
            if (rescheduleInputDiv) {
                rescheduleInputDiv.classList.add('d-none');
            }

            if (confirmRescheduleBtn) {
                confirmRescheduleBtn.classList.add('d-none');
            }

            if (scheduleActionInput) {
                scheduleActionInput.value = 'view'; // default
            }
        });
    }

    // When Reschedule is clicked
    if (rescheduleBtn) {
        rescheduleBtn.addEventListener('click', () => {
            if (rescheduleInputDiv && confirmRescheduleBtn && scheduleActionInput) {
                rescheduleInputDiv.classList.remove('d-none');
                confirmRescheduleBtn.classList.remove('d-none');
                scheduleActionInput.value = 'reschedule';

                const input = rescheduleInputDiv.querySelector('#scheduled_time');
                if (input) {
                    setMinDateTime(input);
                }
            }
        });
    }

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
