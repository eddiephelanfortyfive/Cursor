// Fetch and update system metrics
async function updateSystemMetrics() {
    const response = await fetch('/metrics/system/history/24');
    const data = await response.json();
    
    const timestamps = data.map(d => new Date(d.timestamp).toLocaleTimeString());
    const cpuData = data.map(d => d.cpu_percent);
    const memoryData = data.map(d => d.memory_percent);

    updateChart(cpuChart, timestamps, cpuData, 'CPU Usage %');
    updateChart(memoryChart, timestamps, memoryData, 'Memory Usage %');
}

// Fetch and update stock metrics
async function updateStockMetrics() {
    const response = await fetch('/metrics/stocks/current');
    const data = await response.json();
    
    const datasets = Object.keys(data).map(symbol => ({
        label: symbol,
        data: [data[symbol].price],
        borderColor: getRandomColor(),
        fill: false
    }));

    updateStockChart(stockChart, datasets);
}

// Helper function to update charts
function updateChart(chart, labels, data, label) {
    chart.data.labels = labels;
    chart.data.datasets[0].data = data;
    chart.data.datasets[0].label = label;
    chart.update();
}

function updateStockChart(chart, datasets) {
    chart.data.datasets = datasets;
    chart.update();
}

// Initialize charts
const cpuChart = new Chart(document.getElementById('cpuChart'), {
    type: 'line',
    data: {
        labels: [],
        datasets: [{
            data: [],
            borderColor: 'rgb(75, 192, 192)',
            tension: 0.1
        }]
    }
});

const memoryChart = new Chart(document.getElementById('memoryChart'), {
    type: 'line',
    data: {
        labels: [],
        datasets: [{
            data: [],
            borderColor: 'rgb(255, 99, 132)',
            tension: 0.1
        }]
    }
});

const stockChart = new Chart(document.getElementById('stockChart'), {
    type: 'line',
    data: {
        labels: [],
        datasets: []
    }
});

// Update charts every minute
setInterval(updateSystemMetrics, 60000);
setInterval(updateStockMetrics, 60000);  // Update every minute

// Initial update
updateSystemMetrics();
updateStockMetrics(); 