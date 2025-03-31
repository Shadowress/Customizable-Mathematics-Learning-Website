document.addEventListener("DOMContentLoaded", () => {
    const btn = document.getElementById("accessibility-btn");
    const menu = document.getElementById("accessibility-menu");

    // Toggle menu on button click
    btn.addEventListener("click", function () {
        const isExpanded = btn.getAttribute("aria-expanded") === "true";
        btn.setAttribute("aria-expanded", !isExpanded);
        menu.classList.toggle("show");
    });

    // Close menu if clicked outside
    document.addEventListener("click", function (event) {
        if (!btn.contains(event.target) && !menu.contains(event.target)) {
            menu.classList.remove("show");
            btn.setAttribute("aria-expanded", "false");
        }
    });

    // Dark mode toggle
    document.getElementById("dark-mode-toggle").addEventListener("change", function () {
        document.body.classList.toggle("dark-mode", this.checked);
    });

    // Color theme change
    document.getElementById("color-theme").addEventListener("change", function () {
        document.documentElement.style.setProperty("--secondary-color", this.value);
    });

    // Font size change
    document.getElementById("font-size").addEventListener("input", function () {
        document.documentElement.style.setProperty("--font-size", `${this.value}px`);
    });

    // Spacing change
    document.getElementById("spacing").addEventListener("input", function () {
        document.documentElement.style.setProperty("--line-spacing", `${this.value}em`);
    });
});
