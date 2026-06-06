document.addEventListener('DOMContentLoaded', () => {
    const themeToggleBtn = document.getElementById('theme-toggle');
    const htmlElement = document.documentElement;
    const bodyElement = document.body;
    
    // Check local storage or system preference
    const storedTheme = localStorage.getItem('theme');
    const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    let currentTheme = 'light';
    
    if (storedTheme) {
        currentTheme = storedTheme;
    } else if (systemPrefersDark) {
        currentTheme = 'dark';
    }
    
    // Apply initial theme
    applyTheme(currentTheme);
    
    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', () => {
            currentTheme = currentTheme === 'light' ? 'dark' : 'light';
            applyTheme(currentTheme);
            localStorage.setItem('theme', currentTheme);
        });
    }
    
    function applyTheme(theme) {
        htmlElement.setAttribute('data-theme', theme);
        
        // Update icon if the button exists
        if (themeToggleBtn) {
            const icon = themeToggleBtn.querySelector('i');
            if (icon) {
                if (theme === 'dark') {
                    icon.classList.remove('fa-moon');
                    icon.classList.add('fa-sun');
                    icon.style.color = '#ecc94b'; // Yellow sun
                } else {
                    icon.classList.remove('fa-sun');
                    icon.classList.add('fa-moon');
                    icon.style.color = '#2d3748'; // Dark moon
                }
            }
        }
    }
});
