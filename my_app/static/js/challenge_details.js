let lastTestStatus = "pending";  // global variable to track last Run Test result


//submission solve of challenge in submission table instantly 
document.addEventListener("DOMContentLoaded", function () {
    const submitBtn = document.getElementById("submit-btn");
    const codeEditor = document.getElementById("code-editor");
    const resultDiv = document.getElementById("submission-result");
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    const challengeSlug = document.getElementById("challenge-data").dataset.slug;

    const spinner = submitBtn.querySelector(".spinner");
    const btnText = submitBtn.querySelector(".btn-text");

    submitBtn.addEventListener("click", async (e) => {
        e.preventDefault();
        
        // if (submitBtn.disabled) return; // double-check

        const code = codeEditor.value.trim();
        if (!code) {
            resultDiv.textContent = "Please enter code before submitting.";
            return;
        }

        // Run the spinner
        submitBtn.disabled = true;
        spinner.style.display = "inline-block";
        btnText.textContent = "Submitting...";

        // 2-second industrial delay for spinner viewing
        await new Promise(resolve => setTimeout(resolve, 5000));

        try {
            const response = await fetch(`/api/challenge/${challengeSlug}/submit/`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken
                },
                body: JSON.stringify({ code: code, language: "python",status: lastTestStatus })
            });

            const data = await response.json();
            

            if (response.ok) {
                resultDiv.innerHTML = `<span style="color:green;">${data.submission.message}</span><br>ID: ${data.submission.id}, Status: ${data.submission.status}`;
                codeEditor.value = "";
                //adding new submession card
                const submissionData = data.submission;
                const submissionList = document.getElementById("submission-list");
                const noSubMsg = document.getElementById("no-submissions");
                if (noSubMsg) noSubMsg.remove();
                const newCard = document.createElement("div");
                newCard.className = "submission-item animate-fade-in";
                newCard.dataset.id = submissionData.id;

                newCard.innerHTML = `
                    <div>
                        <div style="font-weight: 600; color: var(--text-primary); margin-bottom: 0.25rem;">
                            Submission #${submissionData.id}
                        </div>
                        <div style="font-size: 0.875rem; color: var(--text-secondary);">
                            <i class="fas fa-clock"></i> just now
                        </div>
                    </div>
                    <pre class="submission-code"><code class="language-python">${submissionData.code}</code></pre>
                    <div style="display: flex; gap: 1rem; align-items: center;">
                        <span class="badge-modern" style="background-color: rgba(16, 185, 129, 0.1); color: var(--success);">
                            <i class="fas fa-check-circle"></i> ${submissionData.status}
                        </span>
                        <button class="view-code-btn btn-modern btn-secondary" style="padding: 0.5rem 1rem;">
                            <i class="fas fa-eye"></i> View Code
                        </button>
                    </div>
                `;
                submissionList.prepend(newCard);
            } else {
                resultDiv.innerHTML = `<span style="color:red;">${data.error}</span>`;
            }

        } catch (error) {
            console.error(error);
            resultDiv.innerHTML = `<span style="color:red;">An unexpected error occurred.</span>`;
        }

        //Stop the spinner
        spinner.style.display = "none";
        btnText.textContent = "Submit Solution";
        submitBtn.disabled = false;
    });
});


// Calls Judge0 once with given stdin, returns the result JSON
async function runCode(stdin = "") {
    // 1) Get the code from textarea
    const code = document.getElementById("code-editor").value;

    // 2) Get selected language from dropdown
    const language = document.querySelector("select.filter-select").value;

    // 3) Map language name -> Judge0 language_id
    const languageIds = {
        python: 71,
        javascript: 63,
        java: 62,
        cpp: 54
    };

    const selectedLanguageId = languageIds[language];

    // 4) Prepare the body we send to Judge0
    const payload = {
        source_code: code,            // user code
        language_id: selectedLanguageId,
        stdin: stdin                  // 🚨 THIS is the input() data
    };

    // 5) First request: create submission
    const createResponse = await fetch(
        "https://ce.judge0.com/submissions/?base64_encoded=false&wait=false",
        {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        }
    );

    const createData = await createResponse.json();
    const token = createData.token;   // Judge0 id for this run

    // 6) Poll Judge0 until code finishes running
    let result;
    while (true) {
        const getResponse = await fetch(
            `https://ce.judge0.com/submissions/${token}?base64_encoded=false`
        );
        const getData = await getResponse.json();

        if (getData.status && getData.status.id >= 3) {
            // 3 = finished, 4 = wrong answer, 5 = time limit, etc.
            result = getData;
            break;
        }

        // wait 0.5s before checking again
        await new Promise(resolve => setTimeout(resolve, 500));
    }

    return result;   // contains stdout, stderr, compile_output, status, ...
}


//run test script
function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}


async function runTests(button) {
    const spinner = button.querySelector('.spinner');
    const resultsDiv = document.getElementById("test-results");
    spinner.style.display = 'inline-block';
    resultsDiv.innerHTML = `<p style="color: var(--text-secondary);">Running tests...</p>`;

    // 1) Read hidden tests from JSON script tag
    const hiddenTestsScript = document.getElementById("hidden-tests-data");
    let tests = [];
    if (hiddenTestsScript) {
        try {
            tests = JSON.parse(hiddenTestsScript.textContent) || [];
        } catch (e) {
            console.error("Error parsing hidden tests JSON:", e);
        }
    }

    if (!tests || tests.length === 0) {
        resultsDiv.innerHTML = `<p style="color:red;">No tests configured for this challenge.</p>`;
        spinner.style.display = 'none';
        lastTestStatus = "failed";
        return;
    }

    let allPassed = true;
    let html = "";

    // 2) Run user code once per test
    for (let i = 0; i < tests.length; i++) {
        const t = tests[i];

        // test.input and test.output come directly from DB
        const stdin = t.input || "";
        const expected = (t.output || "").trim();   // what we expect user to print

        let judgeResult;
        try {
            judgeResult = await runCode(stdin);      // 👈 send stdin to Judge0
        } catch (err) {
            allPassed = false;
            html += `
                <div style="padding:0.75rem; margin-bottom:0.75rem; border:1px solid #e11d48;">
                    <strong>Test ${i + 1} – ❌ Error calling Judge0</strong><br>
                    <pre>${err}</pre>
                </div>
            `;
            continue;
        }

        // 3) Extract what the program printed
        const stdout = (judgeResult.stdout || "").trim();
        const stderr = (judgeResult.stderr || "").trim();
        const compileOutput = (judgeResult.compile_output || "").trim();

        let kind = "ok";
        let actual = stdout;

        if (compileOutput) {
            kind = "compile_error";
            actual = compileOutput;
        } else if (stderr) {
            kind = "runtime_error";
            actual = stderr;
        }

        const passed = (kind === "ok" && actual === expected);
        if (!passed) allPassed = false;

        // 4) Build HTML for this test
        html += `
            <div style="padding:0.75rem; margin-bottom:0.75rem; border:1px solid ${passed ? '#16a34a' : '#e11d48'}; border-radius:8px;">
                <strong>Test ${i + 1} – ${passed ? "✅ Passed" : "❌ Failed"}</strong><br>
                <strong>Input:</strong>
                <pre>${stdin}</pre>
                <strong>Expected output:</strong>
                <pre>${expected}</pre>
                <strong>Your output (${kind}):</strong>
                <pre>${actual}</pre>
            </div>
        `;
    }

    lastTestStatus = allPassed ? "passed" : "failed";

    resultsDiv.innerHTML = `
        <div style="margin-bottom:1rem;">
            <strong>Overall status:</strong> ${allPassed ? "✅ passed" : "❌ failed"}
        </div>
        ${html}
    `;

    spinner.style.display = 'none';
}




//method edit time format to time created comment
function timeSince(dateString) {
    // تحويل التاريخ من الـ UTC إلى التاريخ المحلي
    const date = new Date(dateString);
    const localDate = new Date(date.getTime() - date.getTimezoneOffset() * 60000);

    const now = new Date();
    const seconds = Math.floor((now - localDate) / 1000);

    if (seconds < 1) return "just now";

    let interval = Math.floor(seconds / 86400); // أيام
    if (interval >= 1) return `${interval} day${interval > 1 ? 's' : ''} ago`;

    interval = Math.floor(seconds / 3600); // ساعات
    if (interval >= 1) return `${interval} hour${interval > 1 ? 's' : ''} ago`;

    interval = Math.floor(seconds / 60); // دقائق
    if (interval >= 1) return `${interval} minute${interval > 1 ? 's' : ''} ago`;

    return `${seconds} second${seconds !== 1 ? 's' : ''} ago`;
}

//scritp ajax to adding comment
document.getElementById('comment-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    const form = e.target;
    const slug = form.dataset.slug;
    const comment = form.querySelector('textarea[name="comment"]').value.trim();
    const csrfToken = form.querySelector('[name=csrfmiddlewaretoken]').value;

    if (!comment) return alert("Comment cannot be empty.");

    const response = await fetch(`/api/challenge/${slug}/comment/`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken
        },
        body: JSON.stringify({ content: comment })
    });

    const data = await response.json();

    if (response.ok) {
        // Add new DOM comment without reload
        const commentsList = document.querySelector('.comments-list');
        const div = document.createElement('div');
        div.classList.add('comment-box');
        div.innerHTML = `
            <div style="display: flex; gap: 1rem; margin-bottom: 0.75rem;">
                <div class="user-avatar"
                    style="width: 40px; height: 40px; background: linear-gradient(135deg, var(--primary-500), var(--primary-700)); border-radius: 50%;">
                </div>
                <div style="flex: 1;">
                    <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.5rem;">
                        <div>
                            <strong style="color: var(--text-primary);">${data.comment.user}</strong>
                            <span style="color: var(--text-tertiary); font-size: 0.875rem; margin-left:0.5rem;">
                                <i class="fas fa-clock"></i> ${timeSince(data.comment.created_at)}
                            </span>
                        </div>
                    </div>
                    <p style="color: var(--text-secondary); margin: 0;">
                        ${data.comment.content}
                    </p>
                </div>
            </div>
        `;
        commentsList.prepend(div);
        form.reset();
    } else {
        alert(data.error || "Failed to post comment.");
    }
});

//script for view/hide Code
document.getElementById('submission-list').addEventListener('click', (e) => {
    const button = e.target.closest('.view-code-btn');
    if (!button) return; // إIf the button is not pressed, we will not press anything else

    const submissionItem = button.closest('.submission-item');
    const codeBlock = submissionItem.querySelector('.submission-code');

    // Toggle current code
    const isOpen = codeBlock.classList.toggle('show');
    button.innerHTML = isOpen ? '<i class="fas fa-eye-slash"></i> Hide Code' : '<i class="fas fa-eye"></i> View Code';

    // Close other open codes
    document.querySelectorAll('.submission-item .submission-code').forEach(otherCode => {
        if (otherCode !== codeBlock) {
            otherCode.classList.remove('show');
            const otherButton = otherCode.closest('.submission-item').querySelector('.view-code-btn');
            otherButton.innerHTML = '<i class="fas fa-eye"></i> View Code';
        }
    });

    // Prism highlight
    if (isOpen) {
        Prism.highlightElement(codeBlock.querySelector('code'));
    }
});


//ajax for comments pagination
document.addEventListener("DOMContentLoaded", function () {
    const commentsContainer = document.getElementById("comments-container");
    const prevBtn = document.getElementById("prev-page");
    const nextBtn = document.getElementById("next-page");

    const challengeSlug = document.getElementById("challenge-data").dataset.slug;

    let currentPage = 1;

    async function loadComments(page = 1) {
        const response = await fetch(`/api/challenge/${challengeSlug}/comments/?page=${page}`);
        const data = await response.json();

        commentsContainer.innerHTML = "";

        if (data.comments.length === 0) {
            commentsContainer.innerHTML = `<p>No comments yet.</p>`;
            return;
        }

        data.comments.forEach(c => {
            commentsContainer.innerHTML +=`
            <div class="comment-box">
                <div style="display: flex; gap: 1rem; margin-bottom: 0.75rem;">
                    <div class="user-avatar"
                        style="width: 40px; height: 40px; background: linear-gradient(135deg, var(--primary-500), var(--primary-700)); border-radius: 50%;">
                    </div>
                    <div style="flex: 1;">
                        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.5rem;">
                            <div>
                                <strong style="color: var(--text-primary);">${c.user}</strong>
                                <span style="color: var(--text-tertiary); font-size: 0.875rem; margin-left:0.5rem;">
                                    <i class="fas fa-clock"></i> ${c.created_at}
                                </span>
                            </div>
                        </div>
                        <p style="color: var(--text-secondary); margin: 0;">
                            ${c.content}
                        </p>
                    </div>
                </div>
            </div>
        `;
        });
        prevBtn.disabled = !data.has_previous;
        nextBtn.disabled = !data.has_next;

        currentPage = data.page;
    }

    // Pagination button actions
    prevBtn.addEventListener("click", () => {
        if (currentPage > 1) loadComments(currentPage - 1);
    });

    nextBtn.addEventListener("click", () => {
        loadComments(currentPage + 1);
    });

    // Load first page
    loadComments();
});
