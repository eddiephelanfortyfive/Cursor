// Fetch and update system metrics
async function updateSystemMetrics() {
    console.log('Fetching system metrics...');
    try {
        const response = await fetch('/metrics/system/history/24');
        if (!response.ok) {
            console.error('Failed to fetch system metrics:', response.statusText);
            return;
        }
        const data = await response.json();
        console.log('System metrics data received:', data);

        const timestamps = data.map(d => new Date(d.timestamp).toLocaleTimeString());
        const cpuData = data.map(d => d.cpu_percent);
        const memoryData = data.map(d => d.memory_percent);

        updateChart(cpuChart, timestamps, cpuData, 'CPU Usage %');
        updateChart(memoryChart, timestamps, memoryData, 'Memory Usage %');
    } catch (error) {
        console.error('Error fetching system metrics:', error);
    }
}

// Fetch and update stock metrics
async function updateStockMetrics() {
    console.log('Fetching stock metrics...');
    try {
        const response = await fetch('/metrics/stocks/current');
        if (!response.ok) {
            console.error('Failed to fetch stock metrics:', response.statusText);
            return;
        }
        const data = await response.json();
        console.log('Stock metrics data received:', data);

        const datasets = Object.keys(data).map(symbol => ({
            label: symbol,
            data: [data[symbol].price],
            borderColor: getRandomColor(),
            fill: false
        }));

        updateStockChart(stockChart, datasets);
    } catch (error) {
        console.error('Error fetching stock metrics:', error);
    }
}

// Helper function to update charts
function updateChart(chart, labels, data, label) {
    if (!chart) {
        console.error("Chart is not initialized.");
        return;
    }
    chart.data.label = label;
    chart.data.datasets[0].data = data;
    chart.data.datasets[0].labels = labels;
    chart.update();
}

function updateStockChart(chart, datasets) {
    if (!chart) {
        console.error("Chart is not initialized.");
        return;
    }
    chart.data.datasets = datasets;
    chart.update();
}

document.addEventListener('DOMContentLoaded', async function() {
    // Select canvas elements
    const cpuChartElement = document.getElementById('cpuChart');
    const memoryChartElement = document.getElementById('memoryChart');
    const stockContainer = document.getElementById('stockContainer');

    if (!cpuChartElement || !memoryChartElement || !stockContainer) {
        console.error("One or more canvas elements not found. Ensure the canvas elements are present in the HTML.");
        return;
    }

    // Initialize system charts
    const cpuChart = new Chart(cpuChartElement, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'CPU Usage %',
                data: [],
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });

    const memoryChart = new Chart(memoryChartElement, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Memory Usage %',
                data: [],
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });

    // Fetch and update system metrics
    await updateSystemMetrics();

    // Fetch and update stock metrics
    try {
        const response = await fetch('/metrics/stocks/symbols');
        if (!response.ok) {
            console.error('Failed to fetch stock symbols:', response.statusText);
            return;
        }
        const symbols = await response.json();
        console.log('Stock symbols received:', symbols);

        symbols.forEach(async (symbol) => {
            const canvas = document.createElement('canvas');
            canvas.id = `${symbol}Chart`;
            canvas.classList.add('chart-container');
            stockContainer.appendChild(canvas);

            try {
                const dataResponse = await fetch(`/metrics/stocks/history/${symbol}`);
                if (!dataResponse.ok) {
                    console.error(`Failed to fetch historical data for ${symbol}:`, dataResponse.statusText);
                    return;
                }
                const data = await dataResponse.json();
                console.log(`Data for ${symbol} received:`, data);

                const timestamps = data.map(d => new Date(d.timestamp).toLocaleTimeString());
                const prices = data.map(d => d.price);

                new Chart(canvas, {
                    type: 'line',
                    data: {
                        labels: timestamps,
                        datasets: [{
                            label: `${symbol} Stock Price`,
                            data: prices,
                            borderColor: 'rgba(75, 192, 192, 1)',
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            x: {
                                type: 'time',
                                time: {
                                    unit: 'minute'
                                },
                                title: {
                                    display: true,
                                    text: 'Time'
                                }
                            },
                            y: {
                                beginAtZero: true,
                                title: {
                                    display: true,
                                    text: 'Price (USD)'
                                }
                            }
                        }
                    }
                });
            } catch (error) {
                console.error(`Error fetching historical data for ${symbol}:`, error);
            }
        });
    } catch (error) {
        console.error('Error fetching stock symbols:', error);
    }
});

function getRandomColor() {
    const letters = '0123456789ABCDEF';
    let color = '#';
    for (let i = 0; i < 6; i++) {
        color += letters[Math.floor(Math.random() * 16)];
    }
    return color;
}

