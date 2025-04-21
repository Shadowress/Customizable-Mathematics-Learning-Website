document.addEventListener("DOMContentLoaded", function () {
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

    function getCSRFToken() {
        const cookieValue = document.cookie.match('(^|;)\\s*csrftoken\\s*=\\s*([^;]+)');
        return cookieValue ? cookieValue.pop() : '';
    }

    function submitQuizAnswer(quizId) {
        const answerInput = document.getElementById(`answer-input-${quizId}`);
        const userAnswer = answerInput.value.trim();

        fetch("/courses/submit-quiz-answer/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCSRFToken()
            },
            body: JSON.stringify({
                quiz_id: quizId,
                answer: userAnswer
            })
        })
        .then(response => response.json())
        .then(data => {
            const quizArea = document.getElementById(`quiz-input-area-${quizId}`);

            if (data.success && data.is_correct) {
                // Replace the input area with the correct answer
                quizArea.innerHTML = `<p class="quiz-answer">Answer: ${data.correct_answer}</p>`;
            } else if (data.success) {
                // Show incorrect answer feedback without replacing the input
                const feedbackContainer = document.getElementById(`quiz-feedback-${quizId}`);
                feedbackContainer.innerHTML = `<p class="text-danger">${data.message || "Incorrect answer."}</p>`;
            } else {
                // General error message
                const feedbackContainer = document.getElementById(`quiz-feedback-${quizId}`);
                feedbackContainer.innerHTML = `<p class="text-danger">${data.message || "Something went wrong."}</p>`;
            }
        })
        .catch(error => {
            console.error("Error submitting answer:", error);
            const feedbackContainer = document.getElementById(`quiz-feedback-${quizId}`);
            feedbackContainer.innerHTML = `<p class="text-danger">Something went wrong. Try again later.</p>`;
        });
    }

    document.body.addEventListener('click', function (event) {
        if (event.target && event.target.classList.contains('quiz-submit-btn')) {
            event.preventDefault();

            const quizBlock = event.target.closest('.quiz-block');
            const quizIdInput = quizBlock.querySelector('input[name="quiz_id"]');

            if (!quizIdInput) {
                console.warn("Quiz ID input not found.");
                return;
            }

            const quizId = quizIdInput.value;
            submitQuizAnswer(quizId);
        }
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

    // Sync Video and Transcription
    if (!window.YT) {
        const tag = document.createElement('script');
        tag.src = "https://www.youtube.com/iframe_api";
        document.head.appendChild(tag);
    }

    const players = {};
    const highlightIntervals = {};

    window.onYouTubeIframeAPIReady = function () {
        const iframes = document.querySelectorAll("iframe[id^='youtube-']");

        iframes.forEach((iframe) => {
            const videoId = iframe.id.split("-")[1];

            players[videoId] = new YT.Player(iframe.id, {
                events: {
                    onReady: (event) => setupHighlighting(videoId, event.target)
                }
            });
        });
    };

    function setupHighlighting(videoId, player) {
        const segments = document.querySelectorAll(`#transcription-${videoId} .transcript-segment`);

        if (!segments.length) return;

        highlightIntervals[videoId] = setInterval(() => {
            const time = player.getCurrentTime();

            segments.forEach((segment) => {
                const start = parseFloat(segment.dataset.startTime);
                const end = parseFloat(segment.dataset.endTime);

                if (time >= start && time <= end) {
                    segment.classList.add("highlight");
                } else {
                    segment.classList.remove("highlight");
                }
            });
        }, 300);
    }

    document.querySelectorAll(".transcript-segment").forEach(segment => {
        segment.addEventListener("click", function () {
            const startTime = parseFloat(this.dataset.startTime);
            const transcriptionContainer = this.closest(".video-transcription-slideout");
            const transcriptionId = transcriptionContainer?.id;

            if (!transcriptionId) return;

            const videoId = transcriptionId.replace("transcription-", "");
            const player = players[videoId];

            if (player && typeof player.seekTo === "function") {
                player.seekTo(startTime, true);
            }
        });
    });
});
