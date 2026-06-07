document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const uploadForm = document.getElementById('upload-form');
    const submitBtn = document.getElementById('submit-btn');
    const fileListContainer = document.getElementById('file-list-container');
    const fileList = document.getElementById('file-list');
    const fileCountSpan = document.getElementById('file-count');
    const totalSizeBadge = document.getElementById('total-size-badge');
    const sizeErrorBanner = document.getElementById('size-error-banner');
    
    // Stage Panels
    const conversionStage = document.getElementById('conversion-stage');
    const loadingPanel = document.getElementById('loading-panel');
    const resultsPanel = document.getElementById('results-panel');
    const progressBar = document.getElementById('progress-bar');
    
    // Result details
    const resultsList = document.getElementById('results-list');
    const downloadAllBtn = document.getElementById('download-all-btn');
    const resetBtn = document.getElementById('reset-btn');

    let queuedFiles = [];

    // Drag and Drop Event Listeners
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.add('drag-over');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.remove('drag-over');
        }, false);
    });

    dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = Array.from(dt.files);
        handleFilesSelection(files);
    });

    dropZone.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput.addEventListener('change', () => {
        const files = Array.from(fileInput.files);
        handleFilesSelection(files);
        fileInput.value = ''; // Reset to allow re-selection
    });

    // File Selection and Validation Queue
    function handleFilesSelection(files) {
        // Filter only PDF files
        const pdfFiles = files.filter(file => file.name.toLowerCase().endsWith('.pdf'));
        
        if (pdfFiles.length < files.length) {
            alert('Only PDF files are supported. Non-PDF files have been ignored.');
        }

        pdfFiles.forEach(file => {
            // Check if file is already queued
            const isDuplicate = queuedFiles.some(qf => qf.name === file.name && qf.size === file.size);
            if (!isDuplicate) {
                queuedFiles.push(file);
            }
        });

        updateQueueUI();
    }

    // Update Upload Queue DOM elements
    function updateQueueUI() {
        fileList.innerHTML = '';
        
        if (queuedFiles.length === 0) {
            fileListContainer.style.display = 'none';
            submitBtn.disabled = true;
            return;
        }

        fileListContainer.style.display = 'block';
        fileCountSpan.textContent = queuedFiles.length;

        let totalBytes = 0;

        queuedFiles.forEach((file, index) => {
            totalBytes += file.size;
            
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item';
            
            const fileInfo = document.createElement('div');
            fileInfo.className = 'file-info';
            
            const docIcon = document.createElement('span');
            docIcon.textContent = '📄';
            
            const nameSpan = document.createElement('span');
            nameSpan.className = 'file-name';
            nameSpan.textContent = file.name;
            nameSpan.title = file.name;
            
            const sizeSpan = document.createElement('span');
            sizeSpan.className = 'file-size';
            sizeSpan.textContent = formatBytes(file.size);
            
            fileInfo.appendChild(docIcon);
            fileInfo.appendChild(nameSpan);
            fileInfo.appendChild(sizeSpan);
            
            const removeBtn = document.createElement('button');
            removeBtn.type = 'button';
            removeBtn.className = 'remove-file-btn';
            removeBtn.innerHTML = '✕';
            removeBtn.addEventListener('click', () => {
                removeFileFromQueue(index);
            });
            
            fileItem.appendChild(fileInfo);
            fileItem.appendChild(removeBtn);
            
            fileList.appendChild(fileItem);
        });

        // 50MB Limit Validation Check (50 * 1024 * 1024 bytes)
        const limitBytes = 50 * 1024 * 1024;
        const totalMB = (totalBytes / (1024 * 1024)).toFixed(2);
        totalSizeBadge.textContent = `${totalMB} MB / 50 MB`;

        if (totalBytes > limitBytes) {
            totalSizeBadge.className = 'badge error';
            sizeErrorBanner.style.display = 'flex';
            submitBtn.disabled = true;
        } else {
            totalSizeBadge.className = 'badge';
            sizeErrorBanner.style.display = 'none';
            submitBtn.disabled = false;
        }
    }

    function removeFileFromQueue(index) {
        queuedFiles.splice(index, 1);
        updateQueueUI();
    }

    function formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // Submit and Upload processing
    uploadForm.addEventListener('submit', (e) => {
        e.preventDefault();
        if (queuedFiles.length === 0) return;

        // Collect form settings
        const formatSelect = document.getElementById('format');
        const dpiSelect = document.getElementById('dpi');
        
        const formData = new FormData();
        formData.append('format', formatSelect.value);
        formData.append('dpi', dpiSelect.value);
        
        queuedFiles.forEach(file => {
            formData.append('files', file);
        });

        // Transition to loader stage
        conversionStage.style.display = 'none';
        loadingPanel.style.display = 'block';
        progressBar.style.width = '0%';

        // Animate the progress bar upload stages (0% -> 90% dynamic loader)
        let currentProgress = 0;
        const progressInterval = setInterval(() => {
            if (currentProgress < 85) {
                currentProgress += Math.random() * 8;
                progressBar.style.width = `${Math.min(currentProgress, 85)}%`;
            }
        }, 300);

        // Fetch request submission
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => { throw new Error(err.error || 'Server error occurred') });
            }
            return response.json();
        })
        .then(data => {
            clearInterval(progressInterval);
            progressBar.style.width = '100%';
            
            // Wait slightly for progress animation to complete
            setTimeout(() => {
                renderResults(data);
            }, 400);
        })
        .catch(err => {
            clearInterval(progressInterval);
            alert(`Error: ${err.message}`);
            // Restore conversion form
            loadingPanel.style.display = 'none';
            conversionStage.style.display = 'block';
        });
    });

    // Render results panel
    function renderResults(data) {
        loadingPanel.style.display = 'none';
        resultsPanel.style.display = 'block';
        resultsList.innerHTML = '';

        if (data.zip_url) {
            downloadAllBtn.href = data.zip_url;
            downloadAllBtn.style.display = 'inline-flex';
        } else {
            downloadAllBtn.style.display = 'none';
        }

        data.results.forEach(res => {
            const item = document.createElement('div');
            item.className = 'result-item';

            const itemInfo = document.createElement('div');
            itemInfo.className = 'result-item-info';

            const origName = document.createElement('span');
            origName.className = 'result-orig-name';
            origName.textContent = res.original;

            const metaSpan = document.createElement('span');
            metaSpan.className = 'result-meta';

            const statusText = document.createElement('span');
            statusText.className = `result-status-text ${res.status}`;
            
            if (res.status === 'success') {
                statusText.textContent = 'Success';
                metaSpan.appendChild(statusText);
                metaSpan.appendChild(document.createTextNode(` | Output: ${res.converted}`));
            } else {
                statusText.textContent = 'Failed';
                metaSpan.appendChild(statusText);
                metaSpan.appendChild(document.createTextNode(` | Error: ${res.error_message}`));
            }

            itemInfo.appendChild(origName);
            itemInfo.appendChild(metaSpan);
            item.appendChild(itemInfo);

            if (res.status === 'success') {
                const downloadBtn = document.createElement('a');
                downloadBtn.href = res.url;
                downloadBtn.className = 'download-single-btn';
                downloadBtn.textContent = 'Download 📥';
                downloadBtn.setAttribute('download', res.converted);
                item.appendChild(downloadBtn);
            }

            resultsList.appendChild(item);
        });
    }

    // Reset Page state
    resetBtn.addEventListener('click', () => {
        queuedFiles = [];
        fileList.innerHTML = '';
        fileInput.value = '';
        fileListContainer.style.display = 'none';
        submitBtn.disabled = true;
        
        resultsPanel.style.display = 'none';
        conversionStage.style.display = 'block';
    });
});
