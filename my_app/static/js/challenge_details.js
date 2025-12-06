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

        //❗ 2-second industrial delay for spinner viewing
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


//using Judge0 CE API 
//using Judge0 CE API 
async function runCode(stdin = "") {
    const code = document.getElementById("code-editor").value;
    const language = document.querySelector("select.filter-select").value;

    // Specify the language number at Judge0
    const languageIds = {
        python: 71,
        javascript: 63,
        java: 62,
        cpp: 54
    };

    const selectedLanguageId = languageIds[language];

    // Data to be sent to Judge0
    const payload = {
        source_code: code,
        language_id: selectedLanguageId,
        stdin: stdin
    };

    // Send the first request to create submission
    const createResponse = await fetch("https://ce.judge0.com/submissions/?base64_encoded=false&wait=false", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    });

    const createData = await createResponse.json();

    const token = createData.token;

    //Waiting for execution (Polling)
    let result;
    while (true) {
        const getResponse = await fetch(`https://ce.judge0.com/submissions/${token}?base64_encoded=false`);
        const getData = await getResponse.json();

        if (getData.status && getData.status.id >= 3) {
            result = getData;
            break;
        }

        await new Promise(resolve => setTimeout(resolve, 500));
    }

    return result;
}

//run test script
function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function runTests(button) {
    const spinner = button.querySelector('.spinner');
    spinner.style.display = 'inline-block';

    // Optional: render "Running..."
    const resultsDiv = document.getElementById("test-results");
    resultsDiv.innerHTML = `<p style="color: yellow;">Running code...</p>`;

    // Allow spinner to show
    await new Promise(res => setTimeout(res, 100));

    let result;
    try {
        result = await runCode();
    } catch (err) {
        resultsDiv.innerHTML = `<p style="color:red;">Error running tests: ${err}</p>`;
        spinner.style.display = 'none';
        return;
    }

    // Safely extract output
    const output = 
        result?.stdout ??
        result?.stderr ??
        result?.compile_output ??
        "No output";

    // Determine status
    let status = "failed";

    if (result.compile_output && result.compile_output.trim() !== "") {
        status = "failed";
    } else if (result.stderr && result.stderr.trim() !== "") {
        status = "failed";
    } else if (result.stdout && result.stdout.trim() !== "") {
        status = "passed";
    } else {
        status = "failed";
    }

    lastTestStatus = status;
    // console.log("Status updated to:", status);
    
    resultsDiv.innerHTML = `
        <div style="padding: 1rem; background: rgba(99, 102, 241, 0.1); border-radius: 8px;">
            <strong>Status:</strong> ${status} <br>
            <strong>Result:</strong>
            <pre>${output}</pre>
        </div>
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
        // إضافة التعليق الجديد للـ DOM بدون reload
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

document.getElementById('submission-list').addEventListener('click', (e) => {
    const button = e.target.closest('.view-code-btn');
    if (!button) return; // إذا ما كان الزر لم نضغط على شيء آخر

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