document.addEventListener("DOMContentLoaded", function (e) {
    const sectionContainer = document.getElementById("sections");
    const addSectionBtn = document.getElementById("add-section-btn");
    const addTextBtn = document.getElementById("add-text-btn");
    const addImageBtn = document.getElementById("add-image-btn");
    const addVideoBtn = document.getElementById("add-video-btn");
    const addQuizBtn = document.getElementById("add-quiz-btn");

    let currentSection = null;
    let currentModal = null;
    let isTranscribing = false;
    let isDirty = false;
    let isSubmitting = false;

    function setActiveSection(section) {
        currentSection = section;
        document.querySelectorAll(".section-form").forEach(s => s.classList.remove("active"));
        section.classList.add("active");

        document.querySelectorAll(".remove-section").forEach(btn => {
            if (!isInsideHiddenTemplate(btn)) {
                btn.style.display = "none";
            }
        });

        document.querySelectorAll(".remove-content").forEach(btn => {
            if (!isInsideHiddenTemplate(btn)) {
                btn.style.display = "none";
            }
        });

        document.querySelectorAll(".remove-quiz").forEach(btn => {
            if (!isInsideHiddenTemplate(btn)) {
                btn.style.display = "none";
            }
        });

        if (currentSection) {
            const sectionRemoveBtn = currentSection.querySelector(".remove-section");
            const contentRemoveBtns = currentSection.querySelectorAll(".remove-content");
            const quizRemoveBtns = currentSection.querySelectorAll(".remove-quiz");

            if (sectionRemoveBtn) sectionRemoveBtn.style.display = "inline-block";
            contentRemoveBtns.forEach(btn => btn.style.display = "inline-block");
            quizRemoveBtns.forEach(btn => btn.style.display = "inline-block");
        }
    }

    function isInsideHiddenTemplate(el) {
        return (
            el.closest("#empty-section-form") ||
            el.closest("#empty-text-content-form") ||
            el.closest("#empty-image-content-form") ||
            el.closest("#empty-video-content-form") ||
            el.closest("#empty-quiz-form")
        );
    }

    function addSection() {
        const sectionsContainer = document.getElementById("sections");
        const sectionTemplateHTML = document.getElementById("empty-section-form").innerHTML;

        const existingSections = sectionsContainer.querySelectorAll(".section-form");
        const nextOrder = existingSections.length;

        const wrapper = document.createElement("div");
        wrapper.innerHTML = sectionTemplateHTML;
        const newSection = wrapper.querySelector(".section-form");

        updateFormset("section", newSection);

        sectionsContainer.appendChild(newSection);
        setActiveSection(newSection);

        updateSectionOrder();
        addContentOrQuiz("text");
        addContentOrQuiz("quiz");
    }

    function updateFormset(formsetPrefix, newFormElement) {
        const totalFormsInput = document.getElementById(`id_${formsetPrefix}-TOTAL_FORMS`);
        if (!totalFormsInput) {
            console.error(`Management form for ${formsetPrefix} not found`);
            return;
        }

        const newIndex = parseInt(totalFormsInput.value, 10);

        newFormElement.querySelectorAll("input, textarea, select, label").forEach((el) => {
            if (el.name && el.name.includes('__prefix__')) {
                el.name = el.name.replace(/__prefix__/g, newIndex);
            }

            if (el.id && el.id.includes('__prefix__')) {
                el.id = el.id.replace(/__prefix__/g, newIndex);
            }

            if (el.tagName === 'LABEL' && el.htmlFor && el.htmlFor.includes('__prefix__')) {
                el.htmlFor = el.htmlFor.replace(/__prefix__/g, newIndex);
            }
        });

        totalFormsInput.value = newIndex + 1;
    }

    function addContentOrQuiz(contentType) {
        if (!currentSection) return alert("Please select a section first.");

        let templateContainer;
        let templateId;

        // Determine where the content should be added based on the content type
        switch (contentType) {
            case "text":
                templateContainer = currentSection.querySelector(".section-contents");
                templateId = "empty-text-content-form";
                formsetPrefix = "text_content";
                break;
            case "image":
                templateContainer = currentSection.querySelector(".section-contents");
                templateId = "empty-image-content-form";
                formsetPrefix = "image_content";
                break;
            case "video":
                templateContainer = currentSection.querySelector(".section-contents");
                templateId = "empty-video-content-form";
                formsetPrefix = "video_content";
                break;
            case "quiz":
                templateContainer = currentSection.querySelector(".section-quizzes");
                templateId = "empty-quiz-form";
                formsetPrefix = "quiz";
                break;
            default:
                return;
        }

        if (!templateContainer) return;

        const wrapper = document.createElement("div");
        wrapper.innerHTML = document.getElementById(templateId).innerHTML;
        const formElement = wrapper.querySelector("div");

        updateFormset(formsetPrefix, formElement);

        const sectionOrderInput = formElement.querySelector('input[name$="-section_order"]');
        if (sectionOrderInput && currentSection) {
            const sectionIndex = currentSection.querySelector('input[name$="-order"]')?.value;
            if (sectionIndex !== null && sectionIndex !== undefined) {
                sectionOrderInput.value = sectionIndex;
            }
        }

        let maxOrder = -1;

        const forms = templateContainer.querySelectorAll("input[name$='-order']");
        forms.forEach(input => {
            const val = parseInt(input.value);
            if (!isNaN(val) && val > maxOrder) {
                maxOrder = val;
            }
        });

        const orderInput = formElement.querySelector("input[name$='-order']");
        if (orderInput) {
            orderInput.value = maxOrder + 1;
        }

        templateContainer.appendChild(formElement);
    }

    function removeCurrentSection() {
        if (!currentSection) return;

        const deleteCheckbox = currentSection.querySelector('input[type="checkbox"][name$="-DELETE"]');
        if (deleteCheckbox) {
            deleteCheckbox.checked = true;
        }
        currentSection.style.display = "none";

        const contentForms = currentSection.querySelectorAll(
            ".text-content-form, .image-content-form, .video-content-form"
        );
        contentForms.forEach(form => {
            deleteContentOrQuiz(form);
        });

        const quizForms = currentSection.querySelectorAll(".quiz-form");
        quizForms.forEach(form => {
            deleteContentOrQuiz(form);
        });

        currentSection = null;
        document.querySelectorAll(".section-form").forEach(s => s.classList.remove("active"));

        updateSectionOrder();
    }

    function deleteContentOrQuiz(form) {
        const deleteInput = form.querySelector('input[type="checkbox"][name$="-DELETE"]');
        if (deleteInput) {
            deleteInput.checked = true;
            form.style.display = "none";
        }
    }

    function updateOrder(container, itemSelector, orderInputName, titleSelector = null, titlePrefix = "") {
        if (!container) return;

        const items = container.querySelectorAll(itemSelector);
        let order = 0;

        items.forEach(item => {
            const deleteCheckbox = item.querySelector('input[type="checkbox"][name$="-DELETE"]');
            if (deleteCheckbox && deleteCheckbox.checked) return;

            // Update order input
            const orderInput = item.querySelector(`input[name$="${orderInputName}"]`);
            if (orderInput) {
                orderInput.value = order;
            }

            // Update title
            if (titleSelector) {
                const title = item.querySelector(titleSelector);
                if (title) {
                    title.textContent = `${titlePrefix} ${order + 1}`;
                }
            }

            order++;
        });
    }

    function updateSectionOrder() {
        const sectionContainer = document.getElementById("sections");
        updateOrder(sectionContainer, ".section-form", "-order", ".section-title", "Section");
    }

    function updateContentOrder() {
        if (!currentSection) return;
        updateOrder(currentSection, ".text-content-form, .image-content-form, .video-content-form", "-order");
    }

    function updateQuizOrder() {
        if (!currentSection) return;
        updateOrder(currentSection, ".quiz-form", "-order");
    }

    function addTranscriptionRow(videoContentForm) {
        const transcriptionEditor = videoContentForm.querySelector(".transcription-editor");
        const template = document.getElementById("transcription-row-template");

        if (!template || !transcriptionEditor) return;

        const newRow = template.firstElementChild.cloneNode(true);
        transcriptionEditor.appendChild(newRow);
    }

    function removeTranscriptionRow(rowElement) {
        rowElement.remove();
    }

    function renderContentOrQuiz(contentType, dataList) {
        dataList.forEach((data, index) => {
            const sectionOrder = data.section_order;

            const section = [...document.querySelectorAll(".section-form")].find(sec => {
                const orderInput = sec.querySelector('input[name$="-order"]');
                return orderInput && parseInt(orderInput.value) === sectionOrder;
            });

            if (!section) {
                console.warn(`No section found for section_order: ${sectionOrder}`);
                return;
            }

            let container;
            let templateId;
            let formsetPrefix;

            switch (contentType) {
                case "text":
                    container = section.querySelector(".section-contents");
                    templateId = "empty-text-content-form";
                    formsetPrefix = "text_content";
                    break;
                case "image":
                    container = section.querySelector(".section-contents");
                    templateId = "empty-image-content-form";
                    formsetPrefix = "image_content";
                    break;
                case "video":
                    container = section.querySelector(".section-contents");
                    templateId = "empty-video-content-form";
                    formsetPrefix = "video_content";
                    break;
                case "quiz":
                    container = section.querySelector(".section-quizzes");
                    templateId = "empty-quiz-form";
                    formsetPrefix = "quiz";
                    break;
                default:
                    return;
            }

            if (!container || !templateId) return;

            const wrapper = document.createElement("div");
            wrapper.innerHTML = document.getElementById(templateId).innerHTML;
            const formElement = wrapper.querySelector("div");

            updateFormset(formsetPrefix, formElement);

            const idValue = formElement.querySelector('input[name$="-id"]');
            if (idValue) {
                idValue.value = data.id;
            }

            const sectionOrderField = formElement.querySelector('input[name$="-section_order"]');
            if (sectionOrderField) {
                sectionOrderField.value = data.section_order;
            }

            switch (contentType) {
                case "text":
                    const textInput = formElement.querySelector('textarea[name$="-text_content"]');
                    if (textInput) textInput.value = data.text_content || "";
                    break;

                case "image":
                    const imagePreview = formElement.querySelector('img.image-preview');
                    const imageInput = formElement.querySelector('input[type="file"][name$="-image"]');
                    const altInput = formElement.querySelector('input[name$="-alt_text"]');

                    if (imagePreview && data.image) {
                        imagePreview.src = data.image;
                        imagePreview.alt = data.alt_text || "Image preview";
                        imagePreview.style.display = 'block';
                    }

                    if (altInput) {
                        altInput.value = data.alt_text || "";
                    }
                    break;

                case "video":
                    const videoInput = formElement.querySelector('input[type="url"][name$="-video_url"]');
                    const videoPreview = formElement.querySelector('iframe.video-preview');

                    if (videoInput) videoInput.value = data.video_url || "";

                    if (videoPreview && data.video_url) {
                        const videoId = extractYouTubeVideoID(data.video_url);
                        if (videoId) {
                            videoPreview.src = `https://www.youtube.com/embed/${videoId}`;
                            videoPreview.style.display = 'block';
                        } else {
                            videoPreview.src = '';
                            videoPreview.style.display = 'none';
                        }
                    }

                    const transcriptionEditor = formElement.querySelector('.transcription-editor');

                    if (data.video_transcription && data.video_transcription.length > 0) {
                        data.video_transcription.forEach((segment) => {
                            addTranscriptionRow(formElement);  // Pass the full video form

                            const newRow = transcriptionEditor.lastElementChild;

                            const inputs = newRow.querySelectorAll("input");
                            const textarea = newRow.querySelector("textarea");

                            if (inputs.length >= 2 && textarea) {
                                inputs[0].value = formatTime(segment.start_time) || "";
                                inputs[1].value = formatTime(segment.end_time) || "";
                                textarea.value = segment.text || "";
                            }
                        });
                    } else {
                        // No transcription data, load an empty transcription row
                        addTranscriptionRow(transcriptionEditor);
                    }
                    break;

                case "quiz":
                    const questionInput = formElement.querySelector('textarea[name$="-question"]');
                    const correctAnswerInput = formElement.querySelector('textarea[name$="-correct_answer"]');
                    if (questionInput) questionInput.value = data.question || "";
                    if (correctAnswerInput) correctAnswerInput.value = data.correct_answer || "";
                    break;
            }

            container.appendChild(formElement);
        });
    }

    function extractYouTubeVideoID(url) {
        const match = url.match(
            /(?:youtube\.com\/(?:watch\?v=|embed\/)|youtu\.be\/)([\w-]{11})/
        );
        return match ? match[1] : null;
    }

    function handleVideoTranscription(videoForm) {
        if (!videoForm) {
            console.error("Video form not found");
            return;
        }

        const videoInput = videoForm.querySelector('input[type="url"][name$="-video_url"]');
        const transcriptInput = videoForm.querySelector('textarea[name$="-video_transcription"]');

        const modalElement = document.getElementById("transcriptionModal");
        currentModal = new bootstrap.Modal(modalElement);
        currentModal.show();

        const videoURL = videoInput.value.trim();
        if (!videoURL) {
            updateTranscriptionModal("❗ Please enter a YouTube video URL first.", false, "error");
            return;
        }

        updateTranscriptionModal("Transcribing video...", true, "info");
        isTranscribing = true;

        fetch("/courses/transcribe-video/", {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
                "X-CSRFToken": getCSRFToken(),
            },
            body: new URLSearchParams({
                video_url: videoURL,
            }),
        })
        .then((response) => response.json())
        .then((data) => {
            isTranscribing = false;

            if (data.status === "success" && Array.isArray(data.transcription)) {
                const transcriptionEditor = videoForm.querySelector(".transcription-editor");
                if (!transcriptionEditor) {
                    updateTranscriptionModal("❌ Transcription editor not found.", false, "error");
                    return;
                }

                // Clear all existing transcription rows
                transcriptionEditor.innerHTML = "";

                // Add new rows for each transcription entry
                data.transcription.forEach(segment => {
                    addTranscriptionRow(videoForm);
                    const newRow = transcriptionEditor.lastElementChild;

                    const inputs = newRow.querySelectorAll("input");
                    const textarea = newRow.querySelector("textarea");

                    if (inputs.length >= 2 && textarea) {
                        inputs[0].value = formatTime(segment.start);  // Format start time
                        inputs[1].value = formatTime(segment.end);    // Format end time
                        textarea.value = segment.text;
                    }
                });

                updateTranscriptionModal("✅ Transcription complete!", false, "success");
                isDirty = true;
            } else {
                updateTranscriptionModal("❌ Transcription failed: " + data.message, false, "error");
            }

            setTimeout(() => {
                if (currentModal) currentModal.hide();
            }, 2500);
        })
        .catch((error) => {
            isTranscribing = false;
            console.error("Transcription error:", error);
            updateTranscriptionModal("❌ An error occurred while transcribing the video.", false, "error");

            setTimeout(() => {
                if (currentModal) currentModal.hide();
            }, 2500);
        });
    }

    function updateTranscriptionModal(message, showSpinner = true, type = "info") {
        const spinner = document.getElementById("transcriptionSpinner");
        const statusText = document.getElementById("transcriptionStatus");
        const cancelBtn = document.getElementById("cancelTranscriptionBtn");

        if (spinner) spinner.style.display = showSpinner ? "inline-block" : "none";

        if (statusText) {
            statusText.textContent = message;

            // Remove previous status classes
            statusText.classList.remove("text-success", "text-danger", "text-info", "text-warning");

            // Add class based on type
            switch (type) {
                case "success":
                    statusText.classList.add("text-success");
                    break;
                case "error":
                    statusText.classList.add("text-danger");
                    break;
                case "warning":
                    statusText.classList.add("text-warning");
                    break;
                default:
                    statusText.classList.add("text-info");
            }
        }

        if (cancelBtn) {
            cancelBtn.style.display = showSpinner ? "inline-block" : "none";
            cancelBtn.onclick = () => {
                if (currentModal && isTranscribing) {
                    isTranscribing = false;
                    currentModal.hide();
                }
            };
        }
    }

    function formatTime(seconds) {
        const hrs = Math.floor(seconds / 3600);
        const mins = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);

        const paddedSecs = secs.toString().padStart(2, "0");

        if (hrs > 0) {
            const paddedMins = mins.toString().padStart(2, "0");
            return `${hrs}:${paddedMins}:${paddedSecs}`;
        } else {
            return `${mins}:${paddedSecs}`;
        }
    }

    function getCSRFToken() {
        const cookie = document.cookie.match(/csrftoken=([^;]+)/);
        return cookie ? cookie[1] : "";
    }

    function validateCourseBeforeSave() {
        const sectionForms = getValidSections();
        if (sectionForms.length === 0) {
            alert("You must add at least one section.");
            return false;
        }

        for (let i = 0; i < sectionForms.length; i++) {
            const section = sectionForms[i];
            const sectionNumber = i + 1;

            if (!hasValidContent(section)) {
                alert(`Section ${sectionNumber} must have at least one content (text, image, or video).`);
                return false;
            }

            if (!allContentFieldsFilled(section)) {
                alert(`Please fill in all content fields in Section ${sectionNumber}.`);
                return false;
            }

            if (!hasValidQuiz(section)) {
                alert(`Section ${sectionNumber} must have at least one quiz.`);
                return false;
            }

            if (!allQuizFieldsFilled(section)) {
                alert(`Please fill in all quiz fields in Section ${sectionNumber}.`);
                return false;
            }
        }

        return true;
    }

    function getValidSections() {
        return Array.from(document.querySelectorAll(".section-form")).filter(section => {
            if (section.closest("#empty-section-form")) return false;

            const deleteInput = section.querySelector("input[type='checkbox'][name$='-DELETE']");
            return !deleteInput || !deleteInput.checked;
        });
    }

    function isDeleted(formElement) {
        const deleteInput = formElement.querySelector("input[type='checkbox'][name$='-DELETE']");
        return deleteInput && deleteInput.checked;
    }

    function hasValidContent(section) {
        const contentContainer = section.querySelector(".section-contents");
        const contentTypes = ["text-content-form", "image-content-form", "video-content-form"];

        return contentTypes.some(className => {
            return Array.from(contentContainer.querySelectorAll(`.${className}`)).some(el => {
                if (isDeleted(el)) return false;
                return !isInsideTemplate(el);
            });
        });
    }

    function allContentFieldsFilled(section) {
        const contentContainer = section.querySelector(".section-contents");
        const contents = contentContainer.querySelectorAll(".text-content-form, .image-content-form, .video-content-form");

        for (const content of contents) {
            if (isDeleted(content) || isInsideTemplate(content)) continue;
            const inputs = content.querySelectorAll("input, textarea, select");

            for (const input of inputs) {
                if (shouldValidateInput(input) && input.value.trim() === "") {
                    input.focus();
                    return false;
                }
            }
        }

        return true;
    }

    function hasValidQuiz(section) {
        const quizContainer = section.querySelector(".section-quizzes");

        return Array.from(quizContainer.querySelectorAll(".quiz-form")).some(quiz => {
            return !isDeleted(quiz) && !isInsideTemplate(quiz);
        });
    }

    function allQuizFieldsFilled(section) {
        const quizContainer = section.querySelector(".section-quizzes");
        const quizzes = quizContainer.querySelectorAll(".quiz-form");

        for (const quiz of quizzes) {
            if (isDeleted(quiz) || isInsideTemplate(quiz)) continue;
            const inputs = quiz.querySelectorAll("input, textarea, select");

            for (const input of inputs) {
                if (shouldValidateInput(input) && input.value.trim() === "") {
                    input.focus();
                    return false;
                }
            }
        }

        return true;
    }

    function isInsideTemplate(element) {
        return (
            element.closest("#empty-text-content-form") ||
            element.closest("#empty-image-content-form") ||
            element.closest("#empty-video-content-form") ||
            element.closest("#empty-quiz-form")
        );
    }

    function shouldValidateInput(input) {
        return (
            input.offsetParent !== null && // visible
            input.type !== "hidden" &&
            input.name &&
            !input.name.includes("-DELETE")
        );
    }

    function isElementVisible(el) {
        return !!(el.offsetParent || el.closest("[style*='display: none']") === null);
    }

    function beforeUnloadHandler(e) {
        if (isDirty && !isSubmitting) {
            e.preventDefault();
            e.returnValue = "";
        }
    }

    function validateVideoTranscriptions() {
        const videoForms = document.querySelectorAll(".video-content-form");

        const timeFormatRegex = /^(?:\d{1,2}:)?[0-5]?\d:[0-5]\d$/;  // mm:ss or hh:mm:ss

        for (const videoForm of videoForms) {
            if (isDeleted(videoForm) || isInsideTemplate(videoForm)) continue;

            const transcriptionRows = videoForm.querySelectorAll(".transcription-editor .transcription-row");

            // Get parent section's title (e.g. "Section 2")
            const sectionForm = videoForm.closest(".section-form");
            const sectionTitle = sectionForm?.querySelector(".section-title")?.textContent?.trim() || "Unknown Section";

            if (transcriptionRows.length === 0) {
                alert(`${sectionTitle}: Please add at least one transcription row for each video.`);
                return false;
            }

            for (const row of transcriptionRows) {
                const startInput = row.querySelector(".start-time-input");
                const endInput = row.querySelector(".end-time-input");
                const textArea = row.querySelector(".transcription-text");

                const startTime = startInput?.value.trim() || "";
                const endTime = endInput?.value.trim() || "";
                const text = textArea?.value.trim() || "";

                if (!startTime || !endTime || !text) {
                    alert(`Section ${sectionNumber}: All transcription fields (start time, end time, text) must be filled.`);
                    startInput?.focus();
                    return false;
                }

                if (!timeFormatRegex.test(startTime)) {
                    alert(`Section ${sectionNumber}: Invalid start time format "${startTime}". Use hh:mm:ss or mm:ss.`);
                    startInput.focus();
                    return false;
                }

                if (!timeFormatRegex.test(endTime)) {
                    alert(`Section ${sectionNumber}: Invalid end time format "${endTime}". Use hh:mm:ss or mm:ss.`);
                    endInput.focus();
                    return false;
                }
            }
        }

        return true;
    }

    function parseTimeToSeconds(timeStr) {
        const parts = timeStr.split(":").map(Number).reverse();
        let seconds = 0;

        if (parts.length >= 1) seconds += parts[0];             // seconds
        if (parts.length >= 2) seconds += parts[1] * 60;        // minutes
        if (parts.length >= 3) seconds += parts[2] * 3600;      // hours

        return seconds;
    }

    // === Set Current Active Section on Click ===
    sectionContainer.addEventListener("click", (event) => {
        const clickedSection = event.target.closest(".section-form");
        if (
            !clickedSection ||
            !sectionContainer.contains(clickedSection)
        ) return;

        const deleteCheckbox = clickedSection.querySelector('input[type="checkbox"][name$="-DELETE"]');
        if (deleteCheckbox && deleteCheckbox.checked) return;

        setActiveSection(clickedSection);
    });

    // === Global Add Bar Buttons ===
    addTextBtn.addEventListener("click", () => addContentOrQuiz("text"));
    addImageBtn.addEventListener("click", () => addContentOrQuiz("image"));
    addVideoBtn.addEventListener("click", () => addContentOrQuiz("video"));
    addQuizBtn.addEventListener("click", () => addContentOrQuiz("quiz"));
    addSectionBtn.addEventListener("click", () => addSection());

    // === Remove Buttons ===
    document.addEventListener("click", function (event) {
        if (event.target.classList.contains("remove-section")) {
            const sectionElement = event.target.closest(".section");
            removeCurrentSection(sectionElement);
        }

        if (event.target.classList.contains("remove-content")) {
            const contentDiv = event.target.closest(
                ".text-content-form, .image-content-form, .video-content-form"
            );
            if (contentDiv && !contentDiv.closest(
                ":is(#empty-text-content-form, #empty-image-content-form, #empty-video-content-form)"
            )) {
                deleteContentOrQuiz(contentDiv);
            }
            updateContentOrder();
        }

        if (event.target.classList.contains("remove-quiz")) {
            const quizDiv = event.target.closest(".quiz-form");
            if (quizDiv && !quizDiv.closest("#empty-quiz-form")) {
                deleteContentOrQuiz(quizDiv);
            }
            updateQuizOrder();
        }
    });

    // === Add and Remove Transcription Row ===
    document.body.addEventListener("click", function (event) {
        if (event.target.classList.contains("add-transcription-row")) {
            const videoContentForm = event.target.closest(".video-content-form");
            addTranscriptionRow(videoContentForm);
        }

        if (event.target.classList.contains("remove-transcription-row")) {
            const row = event.target.closest(".transcription-row");
            if (row) removeTranscriptionRow(row);
        }
    });

    // === Update Image Preview ===
    document.body.addEventListener('change', function (event) {
        const input = event.target;

        if (
            input.type === 'file' &&
            input.name.endsWith('-image') &&
            input.closest('.image-content-form')
        ) {
            const formElement = input.closest('.image-content-form');
            const previewImg = formElement.querySelector('img.image-preview');

            if (previewImg && input.files && input.files[0]) {
                const file = input.files[0];
                previewImg.src = URL.createObjectURL(file);
                previewImg.alt = file.name;
                previewImg.style.display = 'block';
            }
        }
    });

    // === Page Init ===
    const isCreatePage = window.location.pathname.includes("/create-course");
    if (isCreatePage) {
        addSection();

    } else {
        existingSections.forEach((sectionData) => {
            const sectionTemplate = document.getElementById("empty-section-form");
            const wrapper = document.createElement("div");
            wrapper.innerHTML = sectionTemplate.innerHTML;
            const sectionElement = wrapper.querySelector(".section-form");

            updateFormset("section", sectionElement);

            const idValue = sectionElement.querySelector('input[name$="-id"]');
            if (idValue) {
                idValue.value = sectionData.id;
            }

            const titleInput = sectionElement.querySelector('input[name$="-title"]');
            if (titleInput) {
                titleInput.value = sectionData.title;
            }

            const orderInput = sectionElement.querySelector('input[name$="-order"]');
            if (orderInput) {
                orderInput.value = sectionData.order;
            }

            const displayTitle = sectionElement.querySelector(".section-title");
            if (displayTitle) {
                displayTitle.textContent = `Section ${sectionData.order + 1}`;
            }

            sectionContainer.appendChild(sectionElement);
        });

        renderContentOrQuiz("text", existingTextContents);
        renderContentOrQuiz("image", existingImageContents);
        renderContentOrQuiz("video", existingVideoContents);
        renderContentOrQuiz("quiz", existingQuizzes);

        const firstSection = [...document.querySelectorAll(".section-form")].find((sec) => {
            const orderInput = sec.querySelector('input[name$="-order"]');
            return orderInput && parseInt(orderInput.value) === 0;
        });

        if (firstSection) {
            setActiveSection(firstSection);
        }
    }

    // === Video Transcription ===
    document.addEventListener("click", function(e) {
        if (e.target && e.target.classList.contains("transcribe-video")) {
            const videoForm = e.target.closest(".video-content-form");
            handleVideoTranscription(videoForm);
        }
    });

    // === Track Dirty Changes in the Main Form ===
    const mainForm = document.querySelector("#main-course-form");

    mainForm.querySelectorAll("input, textarea, select").forEach((el) => {
        el.addEventListener("input", () => {
            if (el.value.trim() !== "") {
                isDirty = true;
            }
        });
        el.addEventListener("change", () => {
            if (el.value.trim() !== "") {
                isDirty = true;
            }
        });
    });

    // === Set isSubmitting When Clicking Submit Buttons for Main Form ===
    document.querySelectorAll('button[type="submit"], input[type="submit"]').forEach((btn) => {
        btn.addEventListener("click", () => {
            const form = btn.closest("form");
            const name = btn.getAttribute("name");
            const value = btn.getAttribute("value");

            if (form === mainForm && name === "action" && (value === "publish" || value === "save_draft")) {
                isSubmitting = true;
            }
        });
    });

    // === Handle Main Form Submission with Validation ===
    mainForm.addEventListener("submit", function (e) {
        const activeEl = document.activeElement;
        const name = activeEl?.getAttribute("name");
        const value = activeEl?.getAttribute("value");

        if (name === "action") {
            // Set the hidden input's value
            document.getElementById("form-action").value = value;

            if (value === "publish" || value === "save_draft") {
                e.preventDefault();

                if (value === "publish") {
                    const isValidContent = validateCourseBeforeSave();
                    if (!isValidContent) {
                        isSubmitting = false;
                        return;
                    }

                    const isValidTranscriptions = validateVideoTranscriptions();
                    if (!isValidTranscriptions) {
                        isSubmitting = false;
                        return;
                    }
                }

                const videoInputs = document.querySelectorAll('input[name$="-video_url"]');
                videoInputs.forEach((input) => {
                    const videoId = extractYouTubeVideoID(input.value);
                    if (videoId) {
                        input.value = `https://www.youtube.com/embed/${videoId}`;
                    }
                });

                const videoForms = document.querySelectorAll(".video-content-form");
                videoForms.forEach((videoForm, index) => {
                    if (isDeleted(videoForm) || isInsideTemplate(videoForm)) return;

                    const transcriptionRows = videoForm.querySelectorAll(".transcription-editor .transcription-row");
                    const transcriptionData = [];

                    transcriptionRows.forEach(row => {
                        const startInput = row.querySelector(".start-time-input");
                        const endInput = row.querySelector(".end-time-input");
                        const textArea = row.querySelector(".transcription-text");

                        const startTimeStr = startInput?.value.trim();
                        const endTimeStr = endInput?.value.trim();
                        const text = textArea?.value.trim();

                        if (startTimeStr && endTimeStr && text) {
                            transcriptionData.push({
                                start_time: parseTimeToSeconds(startTimeStr),
                                end_time: parseTimeToSeconds(endTimeStr),
                                text: text
                            });
                        }
                    });

                    const transcriptionJSON = transcriptionData.length > 0 ? JSON.stringify(transcriptionData) : "null";

                    const hiddenInput = videoForm.querySelector(`input[name$='-video_transcription']`);
                    if (hiddenInput) {
                        hiddenInput.value = transcriptionJSON;
                    }
                });

                window.removeEventListener("beforeunload", beforeUnloadHandler);
                mainForm.submit();
            }

            else if (value === "delete_course") {
                const confirmed = confirm("Are you sure you want to delete this course? This action cannot be undone.");
                if (!confirmed) {
                    e.preventDefault();
                    return;
                }

                window.removeEventListener("beforeunload", beforeUnloadHandler);
            }
        }
    });

    // === Warn User Before Unload if Unsaved Changes Exist ===
    window.addEventListener("beforeunload", beforeUnloadHandler);
});
