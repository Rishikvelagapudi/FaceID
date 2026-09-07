// FaceProof Retro Terminal Application Controller

document.addEventListener('DOMContentLoaded', () => {
    // UI Element References
    const btnModeSingle = document.getElementById('btn-mode-single');
    const btnModeWebcam = document.getElementById('btn-mode-webcam');
    const fileInput = document.getElementById('file-input');
    const previewContainer = document.getElementById('preview-container');
    const canvasOverlay = document.getElementById('canvas-overlay');
    const targetGraphic = document.getElementById('target-graphic');
    const webcamContainer = document.getElementById('webcam-container');
    const webcamVideo = document.getElementById('webcam-video');
    const webcamCanvas = document.getElementById('webcam-canvas');
    const btnSnap = document.getElementById('btn-snap');
    const btnVerify = document.getElementById('btn-verify');
    const verifySpinner = document.getElementById('verify-spinner');
    const verifyText = document.getElementById('verify-text');
    const chkBlockchain = document.getElementById('chk-blockchain');
    const btnSample1 = document.getElementById('btn-sample-1');

    // Right Panel Elements
    const seaStatusBadge = document.getElementById('sea-status-badge');
    const idleScreen = document.getElementById('idle-screen');
    const telemetryScreen = document.getElementById('telemetry-screen');
    const teleStatus = document.getElementById('tele-status');
    const teleScore = document.getElementById('tele-score');
    const teleFaceDetected = document.getElementById('tele-face-detected');
    const teleFaceCount = document.getElementById('tele-face-count');
    const teleSha = document.getElementById('tele-sha');
    const telePhash = document.getElementById('tele-phash');
    const teleSearchCount = document.getElementById('tele-search-count');
    const teleSearchEngine = document.getElementById('tele-search-engine');
    const teleBcStatus = document.getElementById('tele-bc-status');
    const teleBcLink = document.getElementById('tele-bc-link');
    const teleCandidates = document.getElementById('tele-candidates');
    const logLine = document.getElementById('log-line');
    const logTime = document.getElementById('log-time');
    const btnCopyJson = document.getElementById('btn-copy-json');
    const jsonViewer = document.getElementById('json-viewer');

    // State
    let selectedFile = null;
    let base64Snapshot = null;
    let webcamStream = null;
    let currentImageElement = null;

    // Timer Update
    setInterval(() => {
        const now = new Date();
        logTime.textContent = now.toTimeString().split(' ')[0];
    }, 1000);

    // Mode Toggle
    btnModeSingle.addEventListener('click', () => {
        btnModeSingle.className = 'px-3 py-1 font-bold bg-black text-white transition-all';
        btnModeWebcam.className = 'px-3 py-1 font-bold text-slate-800 hover:bg-slate-200 transition-all';

        if (previewContainer.classList.contains('hidden')) {
            targetGraphic.classList.remove('hidden');
        }
        webcamContainer.classList.add('hidden');
        stopWebcam();
    });

    btnModeWebcam.addEventListener('click', async () => {
        btnModeWebcam.className = 'px-3 py-1 font-bold bg-black text-white transition-all';
        btnModeSingle.className = 'px-3 py-1 font-bold text-slate-800 hover:bg-slate-200 transition-all';

        targetGraphic.classList.add('hidden');
        previewContainer.classList.add('hidden');
        webcamContainer.classList.remove('hidden');
        startWebcam();
    });

    // File Upload Handlers
    targetGraphic.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files[0]) {
            handleFileSelect(e.target.files[0]);
        }
    });

    function handleFileSelect(file) {
        selectedFile = file;
        base64Snapshot = null;
        const reader = new FileReader();
        reader.onload = (event) => {
            displayPreview(event.target.result);
        };
        reader.readAsDataURL(file);
    }

    function displayPreview(dataUrl) {
        const img = new Image();
        img.onload = () => {
            currentImageElement = img;
            canvasOverlay.width = img.width;
            canvasOverlay.height = img.height;
            const ctx = canvasOverlay.getContext('2d');
            ctx.drawImage(img, 0, 0);

            previewContainer.classList.remove('hidden');
            targetGraphic.classList.add('hidden');
            logLine.textContent = `> IMAGE LOADED: ${img.width}x${img.height} PX. READY FOR SCAN.`;
        };
        img.src = dataUrl;
    }

    // Quick Sample Loading
    btnSample1.addEventListener('click', async () => {
        logLine.textContent = '> LOADING SAMPLE SCAN PROFILE...';
        try {
            const res = await fetch('/static/sample_preview.jpg');
            if (res.ok) {
                const blob = await res.blob();
                handleFileSelect(new File([blob], 'sample.jpg', { type: 'image/jpeg' }));
            } else {
                // Generate quick canvas image if sample_preview.jpg is not present
                const tempCanvas = document.createElement('canvas');
                tempCanvas.width = 400;
                tempCanvas.height = 400;
                const ctx = tempCanvas.getContext('2d');
                ctx.fillStyle = '#F0E6D2';
                ctx.fillRect(0, 0, 400, 400);
                ctx.fillStyle = '#333';
                ctx.beginPath();
                ctx.arc(150, 160, 20, 0, Math.PI * 2);
                ctx.arc(250, 160, 20, 0, Math.PI * 2);
                ctx.fill();
                displayPreview(tempCanvas.toDataURL('image/jpeg'));
                base64Snapshot = tempCanvas.toDataURL('image/jpeg');
            }
        } catch (err) {
            logLine.textContent = `> ERROR LOADING SAMPLE: ${err.message}`;
        }
    });

    // Webcam Controls
    async function startWebcam() {
        try {
            webcamStream = await navigator.mediaDevices.getUserMedia({ video: { width: 1280, height: 720 } });
            webcamVideo.srcObject = webcamStream;
            logLine.textContent = '> WEBCAM LIVE STREAM ACTIVE.';
        } catch (err) {
            console.error(err);
            logLine.textContent = '> WEBCAM ACCESS DENIED OR UNAVAILABLE.';
            alert('Unable to access webcam. Please check camera permissions.');
        }
    }

    function stopWebcam() {
        if (webcamStream) {
            webcamStream.getTracks().forEach(track => track.stop());
            webcamStream = null;
        }
    }

    btnSnap.addEventListener('click', () => {
        if (!webcamVideo.videoWidth) return;
        webcamCanvas.width = webcamVideo.videoWidth;
        webcamCanvas.height = webcamVideo.videoHeight;
        const ctx = webcamCanvas.getContext('2d');
        ctx.drawImage(webcamVideo, 0, 0);

        base64Snapshot = webcamCanvas.toDataURL('image/jpeg', 0.95);
        selectedFile = null;
        displayPreview(base64Snapshot);

        btnModeSingle.click();
        logLine.textContent = '> FACIAL FRAME CAPTURED FROM WEBCAM STREAM.';
    });

    // Verification Pipeline Execution
    btnVerify.addEventListener('click', async () => {
        // Auto snapshot webcam frame if active
        if (!selectedFile && !base64Snapshot && webcamVideo.videoWidth) {
            webcamCanvas.width = webcamVideo.videoWidth;
            webcamCanvas.height = webcamVideo.videoHeight;
            const ctx = webcamCanvas.getContext('2d');
            ctx.drawImage(webcamVideo, 0, 0);

            base64Snapshot = webcamCanvas.toDataURL('image/jpeg', 0.95);
            selectedFile = null;
            displayPreview(base64Snapshot);
            btnModeSingle.click();
        }

        if (!selectedFile && !base64Snapshot) {
            alert('Please select a facial image or capture a webcam photo first.');
            return;
        }

        setLoading(true);
        logLine.textContent = '> EXECUTING LOCAL ARCFACE & REVERSE PROVENANCE SEARCH...';
        seaStatusBadge.textContent = 'SCANNING...';
        seaStatusBadge.className = 'font-mono text-[10px] font-bold bg-amber-400 text-black px-2 py-0.5 uppercase tracking-wider animate-pulse';

        const writeBlockchain = chkBlockchain.checked;
        const startTime = Date.now();

        try {
            let response;
            if (selectedFile) {
                const formData = new FormData();
                formData.append('file', selectedFile);
                formData.append('write_blockchain', writeBlockchain);
                response = await fetch('/api/verify', { method: 'POST', body: formData });
            } else {
                response = await fetch('/api/verify-base64', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ image_base64: base64Snapshot, write_blockchain: writeBlockchain }),
                });
            }

            const data = await response.json();
            const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);

            if (response.ok) {
                renderTelemetry(data, elapsed);
            } else {
                throw new Error(data.detail || 'Verification error');
            }
        } catch (err) {
            logLine.textContent = `> PIPELINE ERROR: ${err.message}`;
            seaStatusBadge.textContent = 'SCAN ERROR';
            seaStatusBadge.className = 'font-mono text-[10px] font-bold bg-red-600 text-white px-2 py-0.5 uppercase tracking-wider';
            alert(`Pipeline Error: ${err.message}`);
        } finally {
            setLoading(false);
        }
    });

    function setLoading(isLoading) {
        btnVerify.disabled = isLoading;
        if (isLoading) {
            verifySpinner.classList.remove('hidden');
            verifyText.textContent = 'PROCESSING PIPELINE...';
        } else {
            verifySpinner.classList.add('hidden');
            verifyText.textContent = 'RUN PROVENANCE VERIFICATION →';
        }
    }

    // Render Telemetry Results
    function renderTelemetry(data, elapsed) {
        idleScreen.classList.add('hidden');
        telemetryScreen.classList.remove('hidden');

        const face = data.face || {};
        const img = data.image || {};
        const search = data.reverse_search || {};
        const v = data.verification || {};
        const bc = data.blockchain || {};

        // 1. Status Pill
        if (v.status === 'VERIFIED') {
            seaStatusBadge.textContent = 'PROOF VERIFIED';
            seaStatusBadge.className = 'font-mono text-[10px] font-bold bg-emerald-500 text-black px-2 py-0.5 uppercase tracking-wider';
            teleStatus.textContent = 'VERIFIED MATCH DETECTED';
            teleStatus.className = 'text-sm font-extrabold text-emerald-400 tracking-wider';
        } else {
            seaStatusBadge.textContent = 'ORIGINAL UNBOUND';
            seaStatusBadge.className = 'font-mono text-[10px] font-bold bg-amber-400 text-black px-2 py-0.5 uppercase tracking-wider';
            teleStatus.textContent = 'NO CONFIRMED MATCH (LOCAL ORIGINAL)';
            teleStatus.className = 'text-sm font-extrabold text-amber-300 tracking-wider';
        }

        const scorePercent = ((v.best_similarity || 0) * 100).toFixed(1);
        teleScore.textContent = `${scorePercent}%`;

        // 2. Modules
        teleFaceDetected.textContent = `Detected: ${face.detected ? 'YES' : 'NO'}`;
        teleFaceCount.textContent = `Faces Found: ${face.count || 0}`;

        teleSha.textContent = img.sha256 ? img.sha256.substring(0, 20) + '...' : 'N/A';
        telePhash.textContent = img.phash || 'N/A';

        if (search.error) {
            teleSearchCount.textContent = `Error: ${search.error.substring(0, 30)}...`;
        } else {
            teleSearchCount.textContent = `Candidates Found: ${search.count || 0}`;
        }
        teleSearchEngine.textContent = `Engine: ${search.provider || 'Google Lens'}`;

        if (bc.submitted) {
            teleBcStatus.textContent = `Status: ANCHORED (${bc.network})`;
            teleBcLink.innerHTML = `<a href="${bc.explorer_url}" target="_blank" class="underline text-amber-300 font-bold">Tx: ${bc.tx_hash.substring(0, 14)}... ↗</a>`;
        } else {
            teleBcStatus.textContent = `Status: NOT SUBMITTED`;
            teleBcLink.textContent = `Tx: N/A`;
        }

        // 3. Candidate Grid
        const matches = data.matches || [];
        if (matches.length > 0) {
            teleCandidates.innerHTML = matches.map(m => `
                <div class="border border-emerald-500/40 bg-[#0A2D22] p-2 space-y-1">
                    <div class="flex items-center justify-between text-[11px] font-bold text-emerald-300">
                        <span class="truncate max-w-[140px]">${m.title || 'Candidate'}</span>
                        <span class="text-amber-300 font-mono">${((m.visual_similarity || 0) * 100).toFixed(1)}%</span>
                    </div>
                    <a href="${m.link}" target="_blank" class="text-[10px] text-emerald-400 underline block truncate">Source Link ↗</a>
                </div>
            `).join('');
        } else {
            teleCandidates.innerHTML = `<span class="text-emerald-700 italic text-[11px]">No external candidate matches returned.</span>`;
        }

        // 4. Bounding Boxes Overlay
        if (currentImageElement && face.face_boxes) {
            drawBoundingBoxes(face.face_boxes, face.landmarks);
        }

        // 5. JSON Viewer & Log
        jsonViewer.textContent = JSON.stringify(data, null, 2);
        logLine.textContent = `> SCAN COMPLETED IN ${elapsed}S. STATUS: ${v.status}`;
    }

    function drawBoundingBoxes(boxes, landmarks) {
        if (!currentImageElement) return;
        const ctx = canvasOverlay.getContext('2d');
        ctx.drawImage(currentImageElement, 0, 0);

        boxes.forEach((box, idx) => {
            const [x1, y1, x2, y2] = box;
            const width = x2 - x1;
            const height = y2 - y1;

            // Draw thick retro bounding box
            ctx.strokeStyle = '#10b981';
            ctx.lineWidth = 4;
            ctx.strokeRect(x1, y1, width, height);

            ctx.fillStyle = '#10b981';
            ctx.fillRect(x1, y1 - 22, 100, 22);
            ctx.fillStyle = '#000000';
            ctx.font = 'bold 11px JetBrains Mono';
            ctx.fillText(`FACE #${idx + 1}`, x1 + 4, y1 - 6);
        });

        if (landmarks && landmarks.length > 0) {
            landmarks.forEach(kpsGroup => {
                kpsGroup.forEach(([x, y]) => {
                    ctx.beginPath();
                    ctx.arc(x, y, 5, 0, 2 * Math.PI);
                    ctx.fillStyle = '#fbbf24';
                    ctx.fill();
                    ctx.lineWidth = 1.5;
                    ctx.strokeStyle = '#000000';
                    ctx.stroke();
                });
            });
        }
    }

    // Copy JSON button
    btnCopyJson.addEventListener('click', () => {
        navigator.clipboard.writeText(jsonViewer.textContent).then(() => {
            alert('Provenance JSON audit report copied to clipboard!');
        });
    });
});
