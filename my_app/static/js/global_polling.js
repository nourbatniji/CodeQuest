document.addEventListener("DOMContentLoaded", function() {

    const POLLING_INTERVAL = 10000; // polling عادي كل 10 ثواني
    const RETRY_INTERVAL = 15000;   // retry عند فشل الطلب
    let lastPayloadHash = null;
    let active = true;

    // --------------------------
    // حساب hash للبيانات لتجنب إعادة تحديث الـ DOM بلا داعي
    // --------------------------
    function hashObject(obj) {
        return JSON.stringify(obj);
    }

    // --------------------------
    // دوال لتحديث الـ UI
    // --------------------------
    function updateLeaderboardUI(leaderboard) {
        if (!leaderboard || leaderboard.length === 0) return;
        const topUser = leaderboard[0]; 
        const rankEl = document.querySelector("#user_rank");
        const pointsEl = document.querySelector("#user_points");
        if (rankEl) rankEl.textContent = `#${topUser.solved}`;
        if (pointsEl) pointsEl.textContent = topUser.points;
        // تحديد أول ثلاث مستخدمين
    const topThree = leaderboard.slice(0, 3);

    // الميداليات بالترتيب
    const medalClasses = ["gold", "silver", "bronze"];

    topThree.forEach((user, index) => {
        const card = document.querySelector(`.top-performer-card.${medalClasses[index]}`);
        if (!card) return;

        // الاسم
        const nameEl = card.querySelector(".performer-name");
        if (nameEl) nameEl.textContent = user.username;

        // النقاط
        const pointsEl = card.querySelector(".performer-stat-value:nth-child(1)");
        if (pointsEl) pointsEl.textContent = user.points;

        // الحلول
        const solvedEl = card.querySelector(".performer-stat-value:nth-child(2)");
        if (solvedEl) solvedEl.textContent = user.solved;

        // يمكنك إضافة مستوى المستخدم إذا كان موجودًا في payload
        const levelEl = card.querySelector(".user-level");
        if (levelEl) levelEl.textContent = "Coder"; // placeholder أو استخدم user.level
      });
    }

    function updateWeeklyLeaderboard(weekly_leaderboard) {
    const rankChangeEl = document.querySelector("#rank_change");

    if (!rankChangeEl) return; // حماية فقط

    if (!weekly_leaderboard || weekly_leaderboard.length === 0) {
        rankChangeEl.textContent = "+0";   // أو "N/A"
        return;
    }

    const topUser = weekly_leaderboard[0];
    rankChangeEl.textContent = `+${topUser.points}`;
    }

    function updateUserStatsUI(userStats) {
        if (!userStats) return;
        const solved = document.querySelector("#user-solved");
        const points = document.querySelector("#user-points");
        if (solved) solved.textContent = userStats.challenges_solved;
        if (points) points.textContent = userStats.total_points;
    }

    function updateClassroomsUI(classrooms) {
        if (!classrooms) return;
        const container = document.querySelector("#classrooms-container");
        if (!container) return;
        // container.innerHTML = classrooms.map(c =>
        //     `<div class="class-card">
        //         <h4>${c.name}</h4>
        //         <p>Members: ${c.members_count}</p>
        //         <p>Challenges: ${c.total_challenges}</p>
        //         <p>Avg Completion: ${c.avg_completion_percent ?? 0}%</p>
        //     </div>`).join("");
    }

    function updateMentorStatsUI(mentorStats) {
        if (!mentorStats) return;
        const countEl = document.querySelector("#mentor-classrooms-count");
        if (countEl) countEl.textContent = mentorStats.my_classrooms_count;
    }

    // --------------------------
    // جلب البيانات من الـ API
    // --------------------------
    async function fetchGlobalStats() {
        try {
            const res = await fetch("/api/global-stats/", { cache: "no-store" });
            if (!res.ok) throw new Error("Failed to fetch stats");
            const data = await res.json();
            return data;
        } catch (err) {
            console.error("Polling error:", err);
            return null;
        }
    }

    // --------------------------
    // Polling Loop
    // --------------------------
    async function pollStats() {
        if (!active) return;

        const data = await fetchGlobalStats();
        if (!data) {
            setTimeout(pollStats, RETRY_INTERVAL);
            return;
        }

        const newHash = hashObject(data);
        if (newHash !== lastPayloadHash) {
            lastPayloadHash = newHash;
            updateLeaderboardUI(data.leaderboard);
            updateWeeklyLeaderboard(data.weekly_leaderboard)
            updateUserStatsUI(data.user_stats);
            updateClassroomsUI(data.classrooms);
            updateMentorStatsUI(data.mentor_stats);
        }

        setTimeout(pollStats, POLLING_INTERVAL);
    }

    // --------------------------
    // التعامل مع تبويب غير نشط
    // --------------------------
    document.addEventListener("visibilitychange", function() {
        if (document.hidden) {
            active = false;
        } else {
            active = true;
            pollStats(); // فور العودة للتبويب
        }
    });

    // --------------------------
    // بدء Polling فور تحميل الصفحة
    // --------------------------
    pollStats();
});