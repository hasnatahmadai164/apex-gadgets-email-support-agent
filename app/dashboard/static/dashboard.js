const STAT_CARDS = [
    { key: 'total', label: 'Emails Received', accent: '#4fd8c4' },
    { key: 'replied', label: 'Auto-Replied', accent: '#4fd8c4' },
    { key: 'handled', label: 'AI Resolved', accent: '#34d399' },
    { key: 'needs_review', label: 'Needs Review', accent: '#f5a623' },
    { key: 'irrelevant', label: 'Filtered Out', accent: '#64748b' },
];

let chartInstance = null;

function renderCards(stats) {
    const container = document.getElementById('cards');
    container.innerHTML = STAT_CARDS.map((card) => `
        <div class="card" style="--card-accent: ${card.accent}">
            <div class="label">${card.label}</div>
            <div class="value">${stats[card.key]}</div>
        </div>
    `).join('');
}

function renderChart(stats) {
    const ctx = document.getElementById('breakdownChart');
    const data = {
        labels: ['AI Resolved', 'Needs Review', 'Filtered Out'],
        datasets: [{
            data: [stats.handled, stats.needs_review, stats.irrelevant],
            backgroundColor: ['#34d399', '#f5a623', '#64748b'],
            borderRadius: 6,
            maxBarThickness: 56,
        }],
    };

    const options = {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
            x: {
                grid: { display: false },
                ticks: { color: '#8592a0', font: { family: 'Inter', size: 12 } },
            },
            y: {
                beginAtZero: true,
                ticks: { color: '#8592a0', precision: 0, font: { family: 'JetBrains Mono', size: 11 } },
                grid: { color: '#232c36' },
            },
        },
    };

    if (chartInstance) {
        chartInstance.data = data;
        chartInstance.update();
    } else {
        chartInstance = new Chart(ctx, { type: 'bar', data, options });
    }
}

function updateTimestamp() {
    const now = new Date();
    document.getElementById('footer').textContent =
        `Apex Gadgets · Internal Operations · Last updated ${now.toLocaleTimeString()}`;
}

async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        if (!response.ok) throw new Error('stats request failed');
        const stats = await response.json();
        renderCards(stats);
        renderChart(stats);
        document.getElementById('statusText').textContent = 'LIVE — MONITORING INBOX';
        updateTimestamp();
    } catch (error) {
        document.getElementById('statusText').textContent = 'CONNECTION ERROR';
    }
}

loadStats();
setInterval(loadStats, 30000);
