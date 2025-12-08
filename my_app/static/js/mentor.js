async function fetchUserClassrooms() {
    try {
        const res = await fetch("/api/mentor-classrooms/", { cache: "no-store" });
        if (!res.ok) throw new Error("Failed to fetch user classrooms");
        const data = await res.json();
        return data.classrooms || [];
    } catch (err) {
        console.error("Error fetching user classrooms:", err);
        return [];
    }
}

function updateHomeClassroomsUI(classrooms) {
    const container = document.querySelector("#classrooms-container");
    if (!container) return;

    if (!classrooms.length) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📘</div>
                <h3>You haven't joined any classrooms yet</h3>
                <p>Join a classroom to start learning!</p>
            </div>
        `;
        return;
    }

    container.innerHTML = classrooms.map(c => {
        const name = c.name ?? "Unnamed Classroom";
        const description = c.description ?? "No description available";
        const mentor = c.mentor ?? "Unknown Mentor";
        const members = c.members_count ?? 0;
        const challenges = c.total_challenges ?? 0;
        const level = c.level ?? "Beginner";
        const updated = c.updated_at ?? "N/A";
        const classroomId = c.id ?? "#";

        return `
        <div class="classroom-card animate-fade-in">
            <div class="classroom-card-header">
                <h3>${name}</h3>
                <p>${description}</p>
            </div>
            <div class="classroom-card-body">
                <div class="classroom-meta">
                    <div class="classroom-meta-item">
                        <i class="fas fa-user-tie"></i>
                        <span>${mentor}</span>
                    </div>
                    <div class="classroom-meta-item">
                        <i class="fas fa-users"></i>
                        <span>${members} members</span>
                    </div>
                </div>
                <div class="classroom-meta">
                    <div class="classroom-meta-item">
                        <i class="fas fa-code"></i>
                        <span>${challenges} challenges</span>
                    </div>
                    <div class="classroom-meta-item">
                        <i class="fas fa-signal"></i>
                        <span>${level}</span>
                    </div>
                </div>
            </div>
            <div class="classroom-card-footer">
                <span style="font-size: 0.875rem; color: var(--text-secondary);">
                    <i class="fas fa-clock"></i> Updated ${updated}
                </span>
                <button class="btn-modern btn-primary" onclick="window.location.href='/classroom/${classroomId}'">
                    <i class="fas fa-arrow-right"></i> View
                </button>
            </div>
        </div>
        `;
    }).join("");
}

document.addEventListener("DOMContentLoaded", async function() {
    const classrooms = await fetchUserClassrooms();
    updateHomeClassroomsUI(classrooms);
});
