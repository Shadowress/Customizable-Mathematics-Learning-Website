document.addEventListener("DOMContentLoaded", function () {
    // === SECTION: DOM Elements ===
    const sectionContainer = document.getElementById("sections");
    const addSectionBtn = document.getElementById("add-section-btn");
    const addTextBtn = document.getElementById("add-text-btn");
    const addImageBtn = document.getElementById("add-image-btn");
    const addVideoBtn = document.getElementById("add-video-btn");
    const addQuizBtn = document.getElementById("add-quiz-btn");
    const totalForms = document.getElementById("id_sections-TOTAL_FORMS");
    const emptyFormTemplate = document.getElementById("empty-section-form").innerHTML;

    let currentSection = null;

    // === SECTION: Utility Functions ===
    function updateSectionNumbers() {
        const sectionForms = Array.from(document.querySelectorAll(".section-form"))
            .filter(form => !form.closest("#empty-section-form"));

        sectionForms.forEach((form, index) => {
            const sectionHeader = form.querySelector("h3");
            sectionHeader.textContent = `Section ${index + 1}`;

            const orderField = form.querySelector('input[name$="order"]');
            if (orderField) {
                orderField.value = index;
            }
        });
    }

    function updateContentNumbers() {
        document.querySelectorAll(".section-form").forEach((section) => {
            const contentForms = Array.from(section.querySelectorAll(".content-form, .image-form, .video-form"))
                .filter(form => !form.closest('[id^="empty-"]'));

            contentForms.forEach((content, index) => {
                const orderField = content.querySelector('input[name$="order"]');
                if (orderField) {
                    orderField.value = index;
                }

                content.querySelectorAll("[name]").forEach((input) => {
                    input.name = input.name.replace(/\d+/, index);
                });
            });
        });
    }

    function updateQuizNumbers() {
        document.querySelectorAll(".section-form").forEach((section) => {
            const quizForms = Array.from(section.querySelectorAll(".quiz-form"))
                .filter(form => !form.closest("#empty-quiz-form"));

            quizForms.forEach((quiz, index) => {
                const orderField = quiz.querySelector('input[name$="order"]');
                if (orderField) {
                    orderField.value = index;
                }

                quiz.querySelectorAll("[name]").forEach((input) => {
                    input.name = input.name.replace(/\d+/, index);
                });
            });
        });
    }

    function setActiveSection(section) {
        currentSection = section;
        document.querySelectorAll(".section-form").forEach(s => s.classList.remove("active"));
        section.classList.add("active");
    }

    function addContent(contentType) {
        if (!currentSection) return alert("Please select a section first.");

        let contentContainer = currentSection.querySelector(".section-contents");
        if (!contentContainer) {
            contentContainer = document.createElement("div");
            contentContainer.classList.add("section-contents");
            currentSection.appendChild(contentContainer);
        }

        let formId, formClass;
        switch (contentType) {
            case "text":
                formId = "empty-content-form";
                formClass = "content-form";
                break;
            case "image":
                formId = "empty-image-content-form";
                formClass = "image-form";
                break;
            case "video":
                formId = "empty-video-content-form";
                formClass = "video-form";
                break;
            case "quiz":
                formId = "empty-quiz-form";
                formClass = "quiz-form";
                break;
            default:
                return;
        }

        // Clone and append the appropriate content form
        const wrapper = document.createElement("div");
        wrapper.innerHTML = document.getElementById(formId).innerHTML;

        const contentForm = wrapper.querySelector(".content-form") || wrapper.querySelector(".quiz-form");
        contentForm.style.display = "block";
        contentContainer.appendChild(contentForm);
        updateContentNumbers();
    }

    // === SECTION: Add Section ===
    addSectionBtn.addEventListener("click", function () {
        let formIndex = document.querySelectorAll(".section-form").length; // Ensure accurate count
        let newFormHtml = emptyFormTemplate
            .replace(/__num__/g, formIndex)
            .replace(/__prefix__/g, formIndex);

        const tempDiv = document.createElement("div");
        tempDiv.innerHTML = newFormHtml;
        const newForm = tempDiv.firstElementChild;
        sectionContainer.appendChild(newForm);

        totalForms.value = formIndex + 1;
        updateSectionNumbers();
    });

    // === SECTION: Remove Section ===
    sectionContainer.addEventListener("click", function (event) {
        if (event.target.classList.contains("remove-section")) {
            const sectionDiv = event.target.closest(".section-form");
            sectionDiv.remove();

            let sectionForms = document.querySelectorAll(".section-form");
            totalForms.value = sectionForms.length; // Update count based on remaining forms
            currentSection = null;

            updateSectionNumbers();
        }
    });

    // === SECTION: Set Current Active Section on Click ===
    sectionContainer.addEventListener("click", (event) => {
        const clickedSection = event.target.closest(".section-form");
        if (!clickedSection || !sectionContainer.contains(clickedSection)) return;

        currentSection = clickedSection;

        // Remove active from all, then add to the clicked one
        document.querySelectorAll(".section-form").forEach(s => s.classList.remove("active"));
        clickedSection.classList.add("active");
    });

    // === SECTION: Global Add Bar Buttons ===
    // Add Text Content
    addTextBtn.addEventListener("click", () => addContent("text"));

    // Add Image Content
    addImageBtn.addEventListener("click", () => addContent("image"));

    // Add Video Content
    addVideoBtn.addEventListener("click", () => addContent("video"));

    // Add Quiz Content
    addQuizBtn.addEventListener("click", () => addContent("quiz"));

    // === CONTENT | QUIZ: Remove Content or Quiz ===
    document.addEventListener("click", function (event) {
        if (event.target.classList.contains("remove-content")) {
            const contentDiv = event.target.closest(".content-form");
            if (contentDiv && !contentDiv.closest("#empty-content-form")) {
                contentDiv.remove();
            }
            updateContentNumbers();
        }

        if (event.target.classList.contains("remove-quiz")) {
            const quizDiv = event.target.closest(".quiz-form");
            if (quizDiv && !quizDiv.closest("#empty-quiz-form")) {
                quizDiv.remove();
            }
            updateQuizNumbers();
        }
    });

    // === Init on Page Load ===
    updateSectionNumbers();
});
