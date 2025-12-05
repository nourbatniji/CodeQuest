document.addEventListener("DOMContentLoaded", function () {
    const submitBtn = document.getElementById("submit-btn");
    const codeEditor = document.getElementById("code-editor");
    const resultDiv = document.getElementById("submission-result");
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    const challengeSlug = document.getElementById("challenge-data").dataset.slug;

    const spinner = submitBtn.querySelector(".spinner");
    const btnText = submitBtn.querySelector(".btn-text");

    submitBtn.addEventListener("click", async () => {
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
                body: JSON.stringify({ code: code, language: "python" })
            });

            const data = await response.json();

            if (response.ok) {
                resultDiv.innerHTML = `<span style="color:green;">${data.message}</span><br>ID: ${data.submission_id}, Status: ${data.status}`;
                codeEditor.value = "";
            } else {
                resultDiv.innerHTML = `<span style="color:red;">${data.error}</span>`;
            }

        } catch (error) {
            console.error(error);
            resultDiv.innerHTML = `<span style="color:red;">An unexpected error occurred.</span>`;
        }

        //Stop the spinner
        spinner.style.display = "none";
        btnText.textContent = "Submit";
        submitBtn.disabled = false;
    });
});
