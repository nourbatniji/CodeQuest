// challenge_details.js
document.addEventListener("DOMContentLoaded", () => {
    const submitBtn = document.getElementById("submit-btn");
    const codeEditor = document.getElementById("code-editor");
    const resultDiv = document.getElementById("submission-result");
    const challengeData = document.getElementById("challenge-data");
    const challengeSlug = challengeData.dataset.slug;
    const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;

    const spinner = submitBtn.querySelector(".spinner");
    const btnText = submitBtn.querySelector(".btn-text");

    const submissionList = document.getElementById("submission-list");

    // Hide all submission code blocks initially
    if (submissionList) {
        submissionList.querySelectorAll(".submission-code").forEach(block => {
            block.style.display = "none";
        });
    }

    // Count visible submission cards
    function getCurrentSubmissionCount() {
        if (!submissionList) return 0;
        return submissionList.querySelectorAll(".submission-item").length;
    }

    // ===========================
    // SUBMIT SOLUTION (AJAX)
    // ===========================
    submitBtn.addEventListener("click", async (e) => {
        e.preventDefault();

        const code = codeEditor.value.trim();
        if (!code) {
            resultDiv.innerHTML = `<span style="color:red;">Please enter code before submitting.</span>`;
            return;
        }

        submitBtn.disabled = true;
        spinner.style.display = "inline-block";
        btnText.textContent = "Submitting...";

        const form = submitBtn.closest("form");
        const formData = new FormData(form);

        try {
            const response = await fetch(form.action, {
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

            const data = await response.json(); // { status, results, submission_id, ... }

            if (response.ok) {
                // Next visible number = how many cards are currently on the page + 1
                const nextNumber = getCurrentSubmissionCount() + 1;
                console.log("Next submission number:", nextNumber);

                resultDiv.innerHTML = `
                    <span style="color:${data.status === "passed" ? "green" : "red"};">
                        Submission #${nextNumber}: ${data.status.toUpperCase()}
                    </span>
                `;

                const noSubMsg = document.getElementById("no-submissions");
                if (noSubMsg) noSubMsg.remove();

                const newCard = document.createElement("div");
                newCard.className = "submission-item animate-fade-in";
                newCard.dataset.id = data.submission_id || "";

                const escapedCode = code
                    .replace(/</g, "&lt;")
                    .replace(/>/g, "&gt;");

                newCard.innerHTML = `
                    <div>
                        <div class="submission-header"
                             style="font-weight:600;color:var(--text-primary);margin-bottom:0.25rem;">
                            Submission #${nextNumber}
                        </div>
                        <div style="font-size:0.875rem;color:var(--text-secondary);">
                            <i class="fas fa-clock"></i> just now
                        </div>
                    </div>
                    <pre class="submission-code"><code class="language-python">${escapedCode}</code></pre>
                    <div style="display:flex;gap:1rem;align-items:center;">
                        <span class="badge-modern"
                              style="background-color:${data.status === "passed"
                                  ? "rgba(16,185,129,0.1)" : "rgba(248,113,113,0.1)"};color:var(--success);">
                            <i class="fas fa-check-circle"></i> ${data.status}
                        </span>
                        <button class="view-code-btn btn-modern btn-secondary" style="padding:0.5rem 1rem;">
                            <i class="fas fa-eye"></i> View Code
                        </button>
                    </div>
                `;

                // Hide the code block by default for the new card
                const newCodeBlock = newCard.querySelector(".submission-code");
                if (newCodeBlock) {
                    newCodeBlock.style.display = "none";
                }

                // Put newest on top (same as template order)
                submissionList.prepend(newCard);
                codeEditor.value = "";
            } else {
                resultDiv.innerHTML = `<span style="color:red;">${data.error || "Submission failed."}</span>`;
            }
        } catch (err) {
            console.error(err);
            resultDiv.innerHTML = `<span style="color:red;">An unexpected error occurred while submitting.</span>`;
        } finally {
            spinner.style.display = "none";
            btnText.textContent = "Submit Solution";
            submitBtn.disabled = false;
        }
    });

    // ===========================
    // RUN TESTS (AJAX)
    // ===========================
    window.runTests = async function (button) {
        const spinner = button.querySelector(".spinner");
        const resultsDiv = document.getElementById("test-results");
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

    // ===========================
    // VIEW / HIDE CODE IN HISTORY
    // ===========================
    if (submissionList) {
        submissionList.addEventListener("click", (e) => {
            const button = e.target.closest(".view-code-btn");
            if (!button) return;

            const submissionItem = button.closest(".submission-item");
            const codeBlock = submissionItem.querySelector(".submission-code");
            if (!codeBlock) return;

            const isHidden =
                codeBlock.style.display === "none" ||
                getComputedStyle(codeBlock).display === "none";

            // Hide all other code blocks
            submissionList.querySelectorAll(".submission-code").forEach(block => {
                block.style.display = "none";
            });
            submissionList.querySelectorAll(".view-code-btn").forEach(btn => {
                btn.innerHTML = '<i class="fas fa-eye"></i> View Code';
            });

            if (isHidden) {
                codeBlock.style.display = "block";
                button.innerHTML = '<i class="fas fa-eye-slash"></i> Hide Code';

                if (window.Prism) {
                    const innerCode = codeBlock.querySelector("code");
                    if (innerCode) {
                        Prism.highlightElement(innerCode);
                    }
                }
            } else {
                codeBlock.style.display = "none";
                button.innerHTML = '<i class="fas fa-eye"></i> View Code';
            }
        });
    }
});
