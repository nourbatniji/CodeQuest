// SUBMISSION + CHALLENGE LOGIC

// Expose runTests globally for the button onclick
window.runTests = async function (button) {
    const codeEditor = document.getElementById("code-editor");
    const challengeData = document.getElementById("challenge-data");
    const resultsDiv = document.getElementById("test-results");
    const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]")?.value;

    if (!codeEditor || !challengeData || !resultsDiv || !csrfToken) return;

    const spinner = button.querySelector(".spinner");
    const challengeSlug = challengeData.dataset.slug;
    const code = codeEditor.value.trim();

    if (!code) {
        resultsDiv.innerHTML = `<p style="color:red;">Please enter code before running tests.</p>`;
        return;
    }

    spinner.style.display = "inline-block";
    resultsDiv.innerHTML = `<p style="color:var(--text-secondary);">Running tests...</p>`;

    const formData = new FormData();
    formData.append("code", code);

    try {
        const response = await fetch(`/challenge/${challengeSlug}/run-tests/`, {
            method: "POST",
            headers: {
                "X-CSRFToken": csrfToken,
                "X-Requested-With": "XMLHttpRequest",
            },
            body: formData,
        });

        const isJson = response.headers.get("content-type")?.includes("application/json");
        if (!isJson) {
            throw new Error("Non-JSON response from server");
        }

        const data = await response.json(); // { status, results }

        if (!response.ok) {
            resultsDiv.innerHTML = `<p style="color:red;">${data.error || "Failed to run tests."}</p>`;
            return;
        }

        let html = `
            <div style="margin-bottom:1rem;">
                <strong>Overall status:</strong> ${data.status === "passed" ? "✅ passed" : "❌ failed"}
            </div>
        `;

        data.results.forEach((t, idx) => {
            const userOut = t.user_output || t.output || "";
            html += `
                <div style="padding:0.75rem;margin-bottom:0.75rem;
                            border:1px solid ${t.passed ? "#16a34a" : "#e11d48"};
                            border-radius:8px;">
                    <strong>Test ${idx + 1} – ${t.passed ? "✅ Passed" : "❌ Failed"}</strong><br>
                    <strong>Input:</strong>
                    <pre>${t.input}</pre>
                    <strong>Expected output:</strong>
                    <pre>${t.expected}</pre>
                    <strong>Your output:</strong>
                    <pre>${userOut}</pre>
                </div>
            `;
        });

        resultsDiv.innerHTML = html;
    } catch (err) {
        console.error(err);
        resultsDiv.innerHTML = `<p style="color:red;">An error occurred while running tests.</p>`;
    } finally {
        spinner.style.display = "none";
    }
};

// ===================================
// DARK MODE FUNCTIONALITY
// ===================================

function initTheme() {
    const savedTheme = localStorage.getItem("theme");
    const systemPrefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;

    if (savedTheme) {
        document.documentElement.setAttribute("data-theme", savedTheme);
    } else if (systemPrefersDark) {
        document.documentElement.setAttribute("data-theme", "dark");
    } else {
        document.documentElement.setAttribute("data-theme", "light");
    }

    updateThemeIcon();
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute("data-theme");
    const newTheme = currentTheme === "dark" ? "light" : "dark";

    document.documentElement.setAttribute("data-theme", newTheme);
    localStorage.setItem("theme", newTheme);
    updateThemeIcon();
}

function updateThemeIcon() {
    const theme = document.documentElement.getAttribute("data-theme");
    const themeIcon = document.getElementById("theme-icon");

    if (themeIcon) {
        themeIcon.className = theme === "dark" ? "fas fa-sun" : "fas fa-moon";
    }
}

// ===================================
// UTILITY FUNCTIONS
// ===================================

function smoothScrollTo(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.scrollIntoView({ behavior: "smooth", block: "start" });
    }
}

function showToast(message, type = "info") {
    const toast = document.createElement("div");
    toast.className = `toast-notification toast-${type}`;
    toast.textContent = message;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.classList.add("show");
    }, 100);

    setTimeout(() => {
        toast.classList.remove("show");
        setTimeout(() => {
            document.body.removeChild(toast);
        }, 300);
    }, 3000);
}

function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;

    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 7) {
        return date.toLocaleDateString();
    } else if (days > 0) {
        return `${days} day${days > 1 ? "s" : ""} ago`;
    } else if (hours > 0) {
        return `${hours} hour${hours > 1 ? "s" : ""} ago`;
    } else if (minutes > 0) {
        return `${minutes} minute${minutes > 1 ? "s" : ""} ago`;
    } else {
        return "Just now";
    }
}

function copyToClipboard(text) {
    navigator.clipboard
        .writeText(text)
        .then(() => {
            showToast("Copied to clipboard!", "success");
        })
        .catch(() => {
            showToast("Failed to copy", "error");
        });
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function updateActiveNavLink() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll(".navbar-codequest .nav-link");

    navLinks.forEach((link) => {
        const linkPath = new URL(link.href).pathname;
        if (linkPath === currentPath) {
            link.classList.add("active");
        } else {
            link.classList.remove("active");
        }
    });
}

// ===================================
// SINGLE DOMContentLoaded INITIALIZER
// ===================================

document.addEventListener("DOMContentLoaded", () => {
    // ---------- Challenge submission logic ----------
    const submitBtn = document.getElementById("submit-btn");
    const codeEditor = document.getElementById("code-editor");
    const resultDiv = document.getElementById("submission-result");
    const challengeData = document.getElementById("challenge-data");
    const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]")?.value;
    const submissionList = document.getElementById("submission-list");

    if (submitBtn && codeEditor && resultDiv && challengeData && csrfToken && submissionList) {
        const spinner = submitBtn.querySelector(".spinner");
        const btnText = submitBtn.querySelector(".btn-text");

    
        // View / hide code in history
        submissionList.addEventListener("click", (e) => {
            const button = e.target.closest(".view-code-btn");
            if (!button) return;

            const submissionItem = button.closest(".submission-item");
            const codeBlock = submissionItem.querySelector(".submission-code");
            if (!codeBlock) return;

            const isOpen = codeBlock.classList.toggle("show");
            button.innerHTML = isOpen
                ? '<i class="fas fa-eye-slash"></i> Hide Code'
                : '<i class="fas fa-eye"></i> View Code';

            // Close others
            document.querySelectorAll(".submission-item .submission-code").forEach((other) => {
                if (other !== codeBlock) {
                    other.classList.remove("show");
                    const otherBtn = other.closest(".submission-item").querySelector(".view-code-btn");
                    if (otherBtn) {
                        otherBtn.innerHTML = '<i class="fas fa-eye"></i> View Code';
                    }
                }
            });
        });
    }

    // ---------- Theme + navbar logic ----------
    initTheme();

    const themeToggle = document.getElementById("theme-toggle");
    if (themeToggle) {
        themeToggle.addEventListener("click", toggleTheme);
    }

    window
        .matchMedia("(prefers-color-scheme: dark)")
        .addEventListener("change", (e) => {
            if (!localStorage.getItem("theme")) {
                document.documentElement.setAttribute("data-theme", e.matches ? "dark" : "light");
                updateThemeIcon();
            }
        });

    updateActiveNavLink();
});
