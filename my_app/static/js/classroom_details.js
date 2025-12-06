document.addEventListener("DOMContentLoaded", function() {
    // رابط API الصف (يمكن تغييره حسب المشروع)
    const url = "/api/classroom/1/";  // مثال، استخدم ID الصف الصحيح أو slug

    fetch(url)
        .then(response => response.json())
        .then(data => {
            // نعرض البيانات في الصفحة
            document.getElementById("classroom-name").textContent = data.name;
            document.getElementById("classroom-desc").textContent = data.description;
            document.getElementById("classroom-mentor").textContent = data.mentor;

            // عرض الإحصائيات
            document.getElementById("members-count").textContent = data.stats.members_count;
            document.getElementById("challenges-count").textContent = data.stats.challenges_count;
            document.getElementById("comments-count").textContent = data.stats.comments_count;
        })
        .catch(error => console.error("Error fetching classroom data:", error));
});
