// Configuration
const API_BASE_URL = window.location.hostname === 'localhost' 
    ? (window.location.port === '8080' ? 'http://localhost:5000/api' : 'http://localhost:5000/api') 
    : '/api';
const DEFAULT_TIMEOUT = 60;

// Application state
let puzzleData = [];
let chainResult = null;
let isProcessing = false;
let currentDataset = null;

// Initialize the application when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Initial UI setup
    updateStatus('Ready to load puzzles');
    setupEventListeners();
    loadAvailableDatasets();
    updateUIState();
});

function setupEventListeners() {
    // Dataset selection and loading
    document.getElementById('predefined-datasets')?.addEventListener('change', handlePredefinedDatasetChange);
    document.getElementById('dataset-file')?.addEventListener('change', handleFileSelection);
    document.getElementById('load-dataset-btn')?.addEventListener('click', handleLoadDataset);
    
    // Chain finding
    document.getElementById('find-chain-btn')?.addEventListener('click', handleFindChain);
    document.getElementById('export-chain-btn')?.addEventListener('click', handleExportChain);
    
    // Input validation
    document.getElementById('timeout')?.addEventListener('input', validateTimeoutInput);
}

// Dataset Handling Functions
async function loadAvailableDatasets() {
    try {
        updateStatus('Loading available datasets...');
        isProcessing = true;
        updateUIState();
        
        const response = await fetch(`${API_BASE_URL}/datasets`);
        
        if (!response.ok) {
            throw new Error(`HTTP error ${response.status}`);
        }
        
        const datasets = await response.json();
        const select = document.getElementById('predefined-datasets');
        
        if (select) {
            // Clear existing options except the first one
            while (select.options.length > 1) {
                select.remove(1);
            }
            
            // Add dataset options
            for (const [name, info] of Object.entries(datasets)) {
                if (info.exists) {
                    const option = document.createElement('option');
                    option.value = name;
                    option.textContent = `${name} (${info.puzzle_count} puzzles)`;
                    select.appendChild(option);
                }
            }
            
            updateStatus('Available datasets loaded');
        }
    } catch (error) {
        console.error('Error loading datasets:', error);
        updateStatus(`Failed to load available datasets: ${error.message}`, true);
    } finally {
        isProcessing = false;
        updateUIState();
    }
}

function handlePredefinedDatasetChange(e) {
    const datasetName = e.target.value;
    if (datasetName) {
        loadPredefinedDataset(datasetName);
    }
}

function handleFileSelection(e) {
    const fileName = e.target.files[0]?.name || 'No file selected';
    document.getElementById('file-name').textContent = fileName;
}

function validateTimeoutInput(e) {
    const value = parseInt(e.target.value);
    if (isNaN(value) || value <= 0) {
        e.target.value = DEFAULT_TIMEOUT;
    } else if (value > 600) { // Cap at 10 minutes
        e.target.value = 600;
    }
}

async function handleLoadDataset() {
    const fileInput = document.getElementById('dataset-file');
    
    if (!fileInput.files || fileInput.files.length === 0) {
        updateStatus('Please select a file first', true);
        return;
    }
    
    try {
        updateStatus('Reading file...');
        isProcessing = true;
        updateUIState();
        
        const file = fileInput.files[0];
        const content = await readFileAsync(file);
        
        // Validate the file content
        const lines = content.split(/\r?\n/).filter(line => line.trim());
        const validLines = lines.filter(line => /^\d{6}$/.test(line.trim()));
        
        if (validLines.length === 0) {
            throw new Error('No valid puzzles found in file. Puzzles must be 6-digit numbers.');
        }
        
        // Create form data for upload
        const formData = new FormData();
        formData.append('file', file);
        
        // Since our backend doesn't have a file upload endpoint yet,
        // we'll just display the results directly
        document.getElementById('puzzle-count').textContent = validLines.length;
        document.getElementById('current-dataset').textContent = file.name;
        currentDataset = {
            name: file.name,
            count: validLines.length
        };
        
        // Enable chain finding
        document.getElementById('find-chain-btn').disabled = false;
        
        updateStatus(`Loaded ${validLines.length} puzzles from ${file.name}`);
    } catch (error) {
        console.error('Error processing file:', error);
        updateStatus(`Error: ${error.message}`, true);
    } finally {
        isProcessing = false;
        updateUIState();
    }
}

async function loadPredefinedDataset(datasetName) {
    if (!datasetName) return;
    
    try {
        updateStatus(`Loading dataset: ${datasetName}...`);
        isProcessing = true;
        updateUIState();
        
        const response = await fetch(`${API_BASE_URL}/puzzles?dataset=${datasetName}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error ${response.status}`);
        }
        
        puzzleData = await response.json();
        
        document.getElementById('puzzle-count').textContent = puzzleData.length;
        document.getElementById('current-dataset').textContent = datasetName;
        currentDataset = {
            name: datasetName,
            count: puzzleData.length
        };
        
        updateStatus(`Loaded ${puzzleData.length} puzzles from dataset: ${datasetName}`);
        
        // Enable find chain button
        document.getElementById('find-chain-btn').disabled = false;
    } catch (error) {
        console.error('Error loading dataset:', error);
        updateStatus(`Failed to load dataset: ${error.message}`, true);
    } finally {
        isProcessing = false;
        updateUIState();
    }
}

// Chain Finding Functions
async function handleFindChain() {
    try {
        // Get timeout value, defaulting to 60 seconds
        let timeout = parseInt(document.getElementById('timeout').value) || DEFAULT_TIMEOUT;
        
        // Enforce bounds
        timeout = Math.max(1, Math.min(600, timeout));
        
        updateStatus(`Finding longest chain with ${timeout}s timeout...`);
        isProcessing = true;
        updateUIState();
        
        const startTime = Date.now();
        const response = await fetch(`${API_BASE_URL}/puzzles/longest_chain?timeout=${timeout}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error ${response.status}`);
        }
        
        chainResult = await response.json();
        const endTime = Date.now();
        const clientElapsed = (endTime - startTime) / 1000;
        
        // Update UI with results
        document.getElementById('chain-length').textContent = chainResult.chain_length;
        document.getElementById('processing-time').textContent = 
            `${chainResult.processing_time_seconds.toFixed(2)}s (backend) / ${clientElapsed.toFixed(2)}s (total)`;
        
        // Enable export buttons
        document.getElementById('export-chain-btn').disabled = false;
        
        // Display the chain
        displayChain(chainResult.chain);
        
        updateStatus(`Found chain with ${chainResult.chain_length} puzzles in ${chainResult.processing_time_seconds.toFixed(2)} seconds`);
    } catch (error) {
        console.error('Error finding chain:', error);
        updateStatus(`Failed to find chain: ${error.message}`, true);
    } finally {
        isProcessing = false;
        updateUIState();
    }
}

function displayChain(chain) {
    const chainContainer = document.getElementById('chain-container');
    chainContainer.innerHTML = '';
    
    if (!chain || chain.length === 0) {
        chainContainer.innerHTML = '<p class="no-data">No chain found.</p>';
        return;
    }
    
    // Create table to display chain
    const table = document.createElement('table');
    table.className = 'chain-table';
    
    // Add header
    const thead = document.createElement('thead');
    thead.innerHTML = `
        <tr>
            <th>#</th>
            <th>Puzzle</th>
            <th>Takes</th>
            <th>Gives</th>
            <th>Connection</th>
        </tr>
    `;
    table.appendChild(thead);
    
    // Add rows
    const tbody = document.createElement('tbody');
    chain.forEach((puzzle, index) => {
        const row = document.createElement('tr');
        
        // Connection from previous puzzle
        let connectionCell = '';
        if (index > 0) {
            const prevPuzzle = chain[index - 1];
            if (prevPuzzle.puzzle_sides.gives === puzzle.puzzle_sides.takes) {
                connectionCell = `<span class="valid-connection">${prevPuzzle.puzzle_sides.gives} → ${puzzle.puzzle_sides.takes}</span>`;
            } else {
                connectionCell = `<span class="invalid-connection">${prevPuzzle.puzzle_sides.gives} ≠ ${puzzle.puzzle_sides.takes}</span>`;
            }
        }
        
        row.innerHTML = `
            <td>${index + 1}</td>
            <td>${puzzle.puzzle_number}</td>
            <td>${puzzle.puzzle_sides.takes}</td>
            <td>${puzzle.puzzle_sides.gives}</td>
            <td>${connectionCell}</td>
        `;
        tbody.appendChild(row);
    });
    table.appendChild(tbody);
    
    chainContainer.appendChild(table);
    
    // Add export buttons
    addExportButtons();
    
    // Scroll to chain details
    document.getElementById('chain-details-section').scrollIntoView({ behavior: 'smooth' });
}

async function handleExportChain() {
    if (!chainResult || !chainResult.chain || chainResult.chain.length === 0) {
        alert('No chain results to export.');
        return;
    }
    
    try {
        // Create text content
        let content = 'Puzzle Chain Export\n';
        content += '=================\n\n';
        content += `Date: ${new Date().toLocaleString()}\n`;
        content += `Dataset: ${currentDataset?.name || 'Unknown'}\n`;
        content += `Chain Length: ${chainResult.chain_length}\n`;
        content += `Processing Time: ${chainResult.processing_time_seconds.toFixed(2)} seconds\n\n`;
        content += 'Chain:\n';
        
        // Add each puzzle
        chainResult.chain.forEach((puzzle, index) => {
            content += `${index + 1}. Puzzle #${puzzle.puzzle_number} - Takes: ${puzzle.puzzle_sides.takes}, Gives: ${puzzle.puzzle_sides.gives}\n`;
            
            // Add connection for all but first
            if (index > 0) {
                const prevPuzzle = chainResult.chain[index - 1];
                content += `   Connection: ${prevPuzzle.puzzle_sides.gives} → ${puzzle.puzzle_sides.takes}\n`;
            }
        });
        
        // Create a download link
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const filename = `puzzle-chain-${timestamp}.txt`;
        
        // Create blob and download
        const blob = new Blob([content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        
        // Clean up
        URL.revokeObjectURL(url);
        
        updateStatus(`Exported chain to ${filename}`);
    } catch (error) {
        console.error('Error exporting chain:', error);
        updateStatus(`Failed to export chain: ${error.message}`, true);
    }
}

// Add these functions to your script.js

function addExportButtons() {
    // Find the results-summary div
    const resultsDiv = document.querySelector('.results-summary');
    if (!resultsDiv) return;
    
    // Create export buttons container
    const exportContainer = document.createElement('div');
    exportContainer.className = 'export-container';
    
    // Add Text Export Button
    const textButton = document.createElement('button');
    textButton.id = 'export-txt-btn';
    textButton.className = 'secondary-button';
    textButton.innerHTML = '<span class="icon">📄</span> Export TXT';
    textButton.addEventListener('click', () => {
        const timeout = document.getElementById('timeout').value || 60;
        window.open(`${API_BASE_URL}/puzzles/export/chain.txt?timeout=${timeout}`, '_blank');
    });
    
    // Add JSON Export Button
    const jsonButton = document.createElement('button');
    jsonButton.id = 'export-json-btn';
    jsonButton.className = 'secondary-button';
    jsonButton.innerHTML = '<span class="icon">🔍</span> Export JSON';
    jsonButton.addEventListener('click', () => {
        const timeout = document.getElementById('timeout').value || 60;
        window.open(`${API_BASE_URL}/puzzles/export/chain.json?timeout=${timeout}`, '_blank');
    });
    
    // Add buttons to container
    exportContainer.appendChild(textButton);
    exportContainer.appendChild(jsonButton);
    
    // Add container after the existing export button
    const exportButton = document.getElementById('export-chain-btn');
    if (exportButton) {
        exportButton.parentNode.insertBefore(exportContainer, exportButton.nextSibling);
    } else {
        resultsDiv.appendChild(exportContainer);
    }
}

// Helper functions
function readFileAsync(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = (e) => resolve(e.target.result);
        reader.onerror = (e) => reject(new Error('Error reading file'));
        reader.readAsText(file);
    });
}

function updateStatus(message, isError = false) {
    const statusElement = document.getElementById('status');
    if (statusElement) {
        statusElement.textContent = message;
        statusElement.className = isError ? 'status error' : 'status';
    }
    console.log(isError ? `ERROR: ${message}` : message);
}

function updateUIState() {
    // Update buttons based on processing state
    const buttons = [
        document.getElementById('load-dataset-btn'),
        document.getElementById('find-chain-btn'),
        document.getElementById('export-chain-btn')
    ];
    
    // Update buttons
    if (buttons[0]) buttons[0].disabled = isProcessing;
    if (buttons[1]) buttons[1].disabled = isProcessing || (!currentDataset);
    if (buttons[2]) buttons[2].disabled = isProcessing || (!chainResult?.chain);
    
    // Show/hide loading indicator
    const loadingIndicator = document.getElementById('loading-indicator');
    if (loadingIndicator) {
        loadingIndicator.style.display = isProcessing ? 'block' : 'none';
    }
    
    // Disable inputs during processing
    const inputs = [
        document.getElementById('predefined-datasets'),
        document.getElementById('dataset-file'),
        document.getElementById('timeout')
    ];
    
    inputs.forEach(input => {
        if (input) input.disabled = isProcessing;
    });
}

// Add this at the end for better debugging
window.addEventListener('error', (e) => {
    console.error('Global error:', e.error || e.message);
    updateStatus(`An error occurred: ${e.error?.message || e.message}`, true);
});
