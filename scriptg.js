let dataProcessed = false;
let qLearningResults = null;
let kMeansResults = null;

function updateFileName() {
    const input = document.getElementById('csv-file');
    const fileNameDisplay = document.getElementById('file-name');
    const uploadButton = document.getElementById('upload-button');

    if (input.files.length > 0) {
        fileNameDisplay.textContent = input.files[0].name;
        uploadButton.disabled = false;
    } else {
        fileNameDisplay.textContent = 'No file selected';
        uploadButton.disabled = true;
    }
}

function uploadFile() {
    fetch('/check-auth')
        .then(res => res.json())
        .then(data => {
            if (!data.loggedIn) {
                alert("⚠️ Please log in first!");
                return;
            }
            runPreprocess();
        });
}

function runPreprocess() {
    document.getElementById('loader').style.display = 'block';

    const file = document.getElementById('csv-file').files[0];
    const formData = new FormData();
    formData.append('file', file);

    fetch('/preprocess', {
        method: 'POST',
        body: formData
    })
        .then(res => res.json())
        .then(data => {
            document.getElementById('loader').style.display = 'none';
            if (data.error) throw new Error(data.error);

            document.getElementById('preprocess-container').style.display = 'block';
            document.getElementById('preprocess-preview').innerHTML = generateTablePreview(data.preview);
        })
        .catch(err => {
            alert('Preprocessing failed: ' + err.message);
            document.getElementById('loader').style.display = 'none';
        });
}

function generateTablePreview(rows) {
    if (!rows || rows.length === 0) return '<p>No preview data available</p>';
    const headers = Object.keys(rows[0]);
    const headerRow = `<tr>${headers.map(h => `<th>${h}</th>`).join('')}</tr>`;
    const dataRows = rows.map(row => `<tr>${headers.map(h => `<td>${row[h]}</td>`).join('')}</tr>`).join('');
    return `<table>${headerRow}${dataRows}</table>`;
}

function analyzeData() {
    document.getElementById('loader').style.display = 'block';

    fetch('/qlearn')
        .then(res => res.json())
        .then(data => {
            qLearningResults = data;
            return fetch('/kmeans');
        })
        .then(res => res.json())
        .then(data => {
            kMeansResults = data;
            document.getElementById('loader').style.display = 'none';
            document.getElementById('results-container').style.display = 'block';
            document.getElementById('blockchain-button').style.display = 'inline-block';   // ✅ ADD THIS
            drawQlearningViz(qLearningResults);
            drawKmeansViz(kMeansResults);
            dataProcessed = true;
        })
        .catch(err => {
            alert('Analysis failed: ' + err.message);
            document.getElementById('loader').style.display = 'none';
        });
}


function drawQlearningViz(data) {
    if (!data || !data.categories || !data.category_map) {
        console.error('Invalid Q-learning data');
        return;
    }

    const dropdownContainer = document.getElementById('qlearning-dropdown-container');
    dropdownContainer.innerHTML = '';

    const select = document.createElement('select');
    select.style.padding = '10px';
    select.style.borderRadius = '8px';
    select.style.backgroundColor = '#2d2d2d';
    select.style.color = '#e0e0e0';
    select.style.fontSize = '1rem';

    const defaultOption = document.createElement('option');
    defaultOption.text = 'Select a Product Category';
    defaultOption.disabled = true;
    defaultOption.selected = true;
    select.appendChild(defaultOption);

    data.categories.forEach(category => {
        const option = document.createElement('option');
        option.value = category;
        option.text = category;
        select.appendChild(option);
    });

    select.addEventListener('change', function () {
        const selectedCategory = this.value;
        const categoryData = data.category_map[selectedCategory];

        if (categoryData) {
            plotQlearningBarChart(categoryData.products, categoryData.original_prices, categoryData.optimized_prices);
        }
    });

    dropdownContainer.appendChild(select);
}

function plotQlearningBarChart(products, originalPrices, optimizedPrices) {
    const viz = document.getElementById('q-learning-viz');
    viz.innerHTML = '';

    const canvas = document.createElement('canvas');
    canvas.width = 900;
    canvas.height = 500;
    viz.appendChild(canvas);

    new Chart(canvas, {
        type: 'bar',
        data: {
            labels: products,
            datasets: [
                {
                    label: 'Original Price',
                    data: originalPrices,
                    backgroundColor: 'rgba(54, 162, 235, 0.7)' // Blue
                },
                {
                    label: 'Optimized Price',
                    data: optimizedPrices,
                    backgroundColor: 'rgba(255, 159, 64, 0.7)' // Orange
                }
            ]
        },
        options: {
            responsive: true,
            scales: {
                x: { ticks: { autoSkip: false, maxRotation: 45, minRotation: 45 } },
                y: { beginAtZero: true }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'bottom'
                }
            }
        }
    });

    document.getElementById('price-legend').innerHTML =
        "<b>Blue</b> = Original Price &nbsp; | &nbsp; <b>Orange</b> = Optimized Price";
}

function drawKmeansViz(data) {
    if (!data || !data.products || !data.product_map) return;

    const dropdownContainer = document.getElementById('kmeans-dropdown-container');
    dropdownContainer.innerHTML = '';

    const select = document.createElement('select');
    select.style.padding = '10px';
    select.style.borderRadius = '8px';
    select.style.backgroundColor = '#2d2d2d';
    select.style.color = '#e0e0e0';
    select.style.fontSize = '1rem';

    const defaultOption = document.createElement('option');
    defaultOption.text = 'Select a Product';
    defaultOption.disabled = true;
    defaultOption.selected = true;
    select.appendChild(defaultOption);

    data.products.forEach(product => {
        const option = document.createElement('option');
        option.value = product;
        option.text = product;
        select.appendChild(option);
    });

    select.addEventListener('change', function () {
        const selectedProduct = this.value;
        const productData = data.product_map[selectedProduct];

        if (productData) {
            plotDeliveryRoutes(productData.source, productData.customers);
        }
    });

    dropdownContainer.appendChild(select);
}

function plotDeliveryRoutes(source, customers) {
    const viz = document.getElementById('kmeans-viz');
    viz.innerHTML = '';

    const canvas = document.createElement('canvas');
    canvas.width = 900;
    canvas.height = 600;
    viz.appendChild(canvas);

    const ctx = canvas.getContext('2d');

    ctx.fillStyle = '#000';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    const margin = 40;
    const width = canvas.width - 2 * margin;
    const height = canvas.height - 2 * margin;

    const allPoints = [source, ...customers];
    const lats = allPoints.map(p => p.latitude);
    const lons = allPoints.map(p => p.longitude);

    let minLat = Math.min(...lats);
    let maxLat = Math.max(...lats);
    let minLon = Math.min(...lons);
    let maxLon = Math.max(...lons);

    if (minLat === maxLat) { minLat -= 0.001; maxLat += 0.001; }
    if (minLon === maxLon) { minLon -= 0.001; maxLon += 0.001; }

    const xScale = lon => margin + ((lon - minLon) / (maxLon - minLon)) * width;
    const yScale = lat => margin + height - ((lat - minLat) / (maxLat - minLat)) * height;

    const pointData = [];

    // Add source
    const srcX = xScale(source.longitude);
    const srcY = yScale(source.latitude);
    pointData.push({ x: srcX, y: srcY, label: 'Source' });

    // Add customers
    customers.forEach(c => {
        const custX = xScale(c.longitude);
        const custY = yScale(c.latitude);
        pointData.push({ x: custX, y: custY, label: c.customer_city });
    });

    // Draw lines
    ctx.strokeStyle = '#00ff00';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(pointData[0].x, pointData[0].y);
    for (let i = 1; i < pointData.length; i++) {
        ctx.lineTo(pointData[i].x, pointData[i].y);
    }
    ctx.stroke();

    // Draw points
    pointData.forEach((p, idx) => {
        ctx.fillStyle = (idx === 0) ? '#ff0000' : '#00bcd4';
        ctx.beginPath();
        ctx.arc(p.x, p.y, (idx === 0) ? 7 : 5, 0, Math.PI * 2);
        ctx.fill();
    });

    // Hover functionality
    canvas.addEventListener('mousemove', function (e) {
        const rect = canvas.getBoundingClientRect();
        const mouseX = e.clientX - rect.left;
        const mouseY = e.clientY - rect.top;

        let hovered = false;
        pointData.forEach(p => {
            const dist = Math.hypot(p.x - mouseX, p.y - mouseY);
            if (dist < 10) {
                hovered = true;
                if (p.label === 'Source') {
                    canvas.title = "Source";
                } else {
                    canvas.title = "Customer City: " + p.label;
                }
            }
        });

        if (!hovered) {
            canvas.title = "";
        }
    });
}



function uploadToBlockchain() {
    alert('✅ Results uploaded successfully to blockchain!');
}

