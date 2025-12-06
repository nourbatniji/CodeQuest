// classroom_details.js

document.addEventListener('DOMContentLoaded', () => {
    const classroomId = window.location.pathname.split('/')[2]; // assuming /classroom/1/
    const apiUrl = `/api/classroom/${classroomId}/`; // endpoint to fetch classroom details

    fetch(apiUrl)
        .then(response => {
            if (!response.ok) throw new Error('Failed to fetch classroom data');
            return response.json();
        })
        .then(data => {
            // Fill HTML
            document.getElementById('classroom-name').textContent = data.name;
            document.getElementById('classroom-desc').textContent = data.description;
            document.getElementById('classroom-mentor').textContent = data.mentor;
            document.getElementById('members-count').textContent = data.stats.members_count;
            document.getElementById('challenges-count').textContent = data.stats.challenges_count;
            document.getElementById('comments-count').textContent = data.stats.comments_count;

            // Draw chart
            const ctx = document.createElement('canvas');
            ctx.id = 'statsChart';
            document.getElementById('classroom-stats').appendChild(ctx);

            new Chart(ctx.getContext('2d'), {
                type: 'bar',
                data: {
                    labels: ['Members', 'Challenges', 'Comments'],
                    datasets: [{
                        label: 'Classroom Stats',
                        data: [
                            data.stats.members_count,
                            data.stats.challenges_count,
                            data.stats.comments_count
                        ],
                        backgroundColor: ['#36a2eb', '#ff6384', '#cc65fe']
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        y: { beginAtZero: true }
                    }
                }
            });
        })
        .catch(err => {
            console.error('Error:', err);
            alert('Failed to load classroom details.');
        });
});
