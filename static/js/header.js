document.addEventListener('DOMContentLoaded', function () {
    const darkToggle = document.getElementById('dark-mode-toggle');
    const fontSizeInput = document.getElementById('font-size-input');
    const spacingInput = document.getElementById('spacing-input');
    const themeSelect = document.getElementById('color-theme');

    const FONT_MIN = 14;
    const FONT_MAX = 24;
    const SPACING_MIN = 1;
    const SPACING_MAX = 3;

    // Load saved settings
    if (localStorage.getItem('darkMode') === 'true') {
        document.documentElement.setAttribute('data-theme', 'dark');
        darkToggle.classList.add('active');
    }

    if (localStorage.getItem('userFontSize')) {
        const size = parseInt(localStorage.getItem('userFontSize'));
        document.documentElement.style.setProperty('--user-font-size', size + 'px');
        fontSizeInput.value = size;
    }

    if (localStorage.getItem('userSpacing')) {
        const spacing = parseFloat(localStorage.getItem('userSpacing'));
        document.documentElement.style.setProperty('--user-spacing', spacing);
        spacingInput.value = spacing;
    }

    if (localStorage.getItem('colorTheme')) {
        applyColorTheme(localStorage.getItem('colorTheme'));
        themeSelect.value = localStorage.getItem('colorTheme');
    }

    // Dark mode toggle
    darkToggle.addEventListener('click', () => {
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        if (isDark) {
            document.documentElement.removeAttribute('data-theme');
            localStorage.setItem('darkMode', 'false');
            darkToggle.classList.remove('active');
        } else {
            document.documentElement.setAttribute('data-theme', 'dark');
            localStorage.setItem('darkMode', 'true');
            darkToggle.classList.add('active');
        }
    });

    // Font size update
    fontSizeInput.addEventListener('input', () => {
        let size = parseInt(fontSizeInput.value);
        size = Math.max(FONT_MIN, Math.min(FONT_MAX, size));
        fontSizeInput.value = size;
        document.documentElement.style.setProperty('--user-font-size', size + 'px');
        localStorage.setItem('userFontSize', size);
    });

    // Text spacing update
    spacingInput.addEventListener('input', () => {
        let spacing = parseFloat(spacingInput.value);
        spacing = Math.max(SPACING_MIN, Math.min(SPACING_MAX, spacing));
        spacingInput.value = spacing;
        document.documentElement.style.setProperty('--user-spacing', spacing);
        localStorage.setItem('userSpacing', spacing);
    });

    // Color theme update
    themeSelect.addEventListener('change', () => {
        const theme = themeSelect.value;
        applyColorTheme(theme);
        localStorage.setItem('colorTheme', theme);
    });

    // 🔵 Only modify the secondary color
    function applyColorTheme(theme) {
        const secondaryColors = {
            default: '#6c757d',       // Bootstrap default secondary (gray)
            blue: '#0d6efd',          // Bootstrap Primary Blue
            purple: '#6f42c1',        // Bootstrap Purple
            orange: '#fd7e14',        // Bootstrap Orange
            green: '#198754',         // Bootstrap Green
            red: '#dc3545'            // Bootstrap Danger Red
        };

        const color = secondaryColors[theme] || secondaryColors['default'];
        document.documentElement.style.setProperty('--secondary-color', color);
    }
});
