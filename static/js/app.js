(function () {
    const uploadForm = document.getElementById('upload-form');
    const fileInput = document.getElementById('file-input');
    const uploadStatus = document.getElementById('upload-status');
    const fileActions = document.getElementById('file-actions');
    const previewRowsInput = document.getElementById('preview-rows');
    const previewButton = document.getElementById('preview-button');
    const previewSection = document.getElementById('preview-section');
    const previewOutput = document.getElementById('preview-output');
    const closePreview = document.getElementById('close-preview');
    const convertForm = document.getElementById('convert-form');
    const outputFormat = document.getElementById('output-format');
    const includeMetadata = document.getElementById('include-metadata');
    const prettyPrint = document.getElementById('pretty-print');
    const conversionSection = document.getElementById('conversion-status');
    const conversionOutput = document.getElementById('conversion-output');
    const downloadSection = document.getElementById('download-section');
    const downloadLink = document.getElementById('download-link');

    const state = {
        fileId: null,
        jobId: null,
        pollTimer: null,
    };

    function setStatus(target, message, type) {
        if (!target) {
            return;
        }
        target.textContent = message;
        target.classList.remove('success', 'error');
        if (type) {
            target.classList.add(type);
        }
    }

    function toggleSection(section, show) {
        if (!section) {
            return;
        }
        section.classList.toggle('hidden', !show);
        section.setAttribute('aria-hidden', String(!show));
    }

    function stopPolling() {
        if (state.pollTimer) {
            clearInterval(state.pollTimer);
            state.pollTimer = null;
        }
    }

    async function handleUpload(event) {
        event.preventDefault();

        if (!fileInput || !fileInput.files || !fileInput.files[0]) {
            setStatus(uploadStatus, 'Please choose a file before uploading.', 'error');
            return;
        }

        const formData = new FormData();
        formData.append('file', fileInput.files[0]);

        setStatus(uploadStatus, 'Uploading file...', '');
        toggleSection(fileActions, false);
        toggleSection(previewSection, false);
        toggleSection(conversionSection, false);
        downloadSection && toggleSection(downloadSection, false);
        stopPolling();

        try {
            const response = await fetch('/api/v1/files/upload', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const errorBody = await response.json().catch(() => ({}));
                const message = errorBody?.message || errorBody?.detail?.message || 'File upload failed.';
                throw new Error(message);
            }

            const data = await response.json();
            state.fileId = data.file_id;
            setStatus(uploadStatus, `File uploaded successfully. File ID: ${state.fileId}`, 'success');
            toggleSection(fileActions, true);
        } catch (error) {
            console.error(error);
            setStatus(uploadStatus, error.message || 'Unable to upload file.', 'error');
            state.fileId = null;
        }
    }

    async function handlePreview() {
        if (!state.fileId) {
            setStatus(uploadStatus, 'Upload a file before requesting a preview.', 'error');
            return;
        }

        const maxRows = Math.min(Math.max(Number(previewRowsInput.value) || 50, 1), 1000);
        previewRowsInput.value = maxRows;
        setStatus(conversionOutput, '', '');
        toggleSection(conversionSection, false);

        try {
            const response = await fetch(`/api/v1/process/preview/${state.fileId}?max_rows=${maxRows}`);
            if (!response.ok) {
                const errorBody = await response.json().catch(() => ({}));
                const message = errorBody?.message || errorBody?.detail?.message || 'Failed to generate preview.';
                throw new Error(message);
            }

            const data = await response.json();
            previewOutput.textContent = JSON.stringify(data, null, 2);
            toggleSection(previewSection, true);
        } catch (error) {
            console.error(error);
            setStatus(uploadStatus, error.message || 'Preview request failed.', 'error');
        }
    }

    async function handleConversion(event) {
        event.preventDefault();
        if (!state.fileId) {
            setStatus(uploadStatus, 'Upload a file before starting a conversion.', 'error');
            return;
        }

        const payload = {
            output_format: outputFormat.value,
            include_metadata: includeMetadata.checked,
            pretty_print: prettyPrint.checked,
        };

        setStatus(conversionOutput, 'Starting conversion job...', '');
        toggleSection(conversionSection, true);
        toggleSection(downloadSection, false);
        stopPolling();

        try {
            const response = await fetch(`/api/v1/process/convert/${state.fileId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload),
            });

            if (!response.ok) {
                const errorBody = await response.json().catch(() => ({}));
                const message = errorBody?.message || errorBody?.detail?.message || 'Failed to start conversion.';
                throw new Error(message);
            }

            const data = await response.json();
            state.jobId = data.job_id;
            setStatus(conversionOutput, data.message || 'Conversion job started.', 'success');
            state.pollTimer = setInterval(checkJobStatus, 2000);
        } catch (error) {
            console.error(error);
            setStatus(conversionOutput, error.message || 'Conversion failed to start.', 'error');
            stopPolling();
        }
    }

    async function checkJobStatus() {
        if (!state.jobId) {
            stopPolling();
            return;
        }

        try {
            const response = await fetch(`/api/v1/process/status/${state.jobId}`);
            if (!response.ok) {
                const errorBody = await response.json().catch(() => ({}));
                const message = errorBody?.message || errorBody?.detail?.message || 'Unable to get job status.';
                throw new Error(message);
            }

            const data = await response.json();
            if (data.status === 'completed') {
                setStatus(conversionOutput, data.message || 'Conversion completed successfully.', 'success');
                toggleSection(downloadSection, true);
                if (downloadLink && state.fileId) {
                    downloadLink.href = `/api/v1/download/${state.fileId}`;
                }
                stopPolling();
            } else if (data.status === 'failed') {
                const message = data.error || 'Conversion job failed.';
                setStatus(conversionOutput, message, 'error');
                toggleSection(downloadSection, false);
                stopPolling();
            } else {
                const statusMessage = data.message || `Job status: ${data.status}`;
                setStatus(conversionOutput, statusMessage, '');
            }
        } catch (error) {
            console.error(error);
            setStatus(conversionOutput, error.message || 'Unable to get job status.', 'error');
            stopPolling();
        }
    }

    if (uploadForm) {
        uploadForm.addEventListener('submit', handleUpload);
    }

    if (previewButton) {
        previewButton.addEventListener('click', handlePreview);
    }

    if (closePreview) {
        closePreview.addEventListener('click', function () {
            toggleSection(previewSection, false);
        });
    }

    if (convertForm) {
        convertForm.addEventListener('submit', handleConversion);
    }

    window.addEventListener('beforeunload', stopPolling);
})();
