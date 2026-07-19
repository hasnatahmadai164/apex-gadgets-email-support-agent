async function loadStats() {
    const response = await fetch('/api/stats');
    const stats = await response.json();

    const cards = [
        { label: 'Total received', value: stats.total },
        { label: 'Replied', value: stats.replied },
        { label: 'AI handled', value: stats.handled },
        { label: 'Needs review', value: stats.needs_review },
        { label: 'Irrelevant', value: stats.irrelevant },
    ];

    const cardsContainer = document.getElementById('cards');
    cardsContainer.innerHTML = cards
        .map((card) => `<div class="card"><div class="label">${card.label}</div><div class="value">${card.value}</div></div>`)
        .join('');

    new Chart(document.getElementById('breakdownChart'), {
        type: 'bar',
        data: {
            labels: ['AI handled', 'Needs review', 'Irrelevant'],
            datasets: [{
                label: 'Emails today',
                data: [stats.handled, stats.needs_review, stats.irrelevant],
                backgroundColor: ['#34c759', '#ff9500', '#8e8e93'],
            }],
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
        },
    });
}

loadStats();
