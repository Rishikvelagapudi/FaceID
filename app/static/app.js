// FaceID Retro Terminal Application Controller

document.addEventListener('DOMContentLoaded', () => {
    // UI Element References
    const fileInput = document.getElementById('file-input');
    const dropZone = document.getElementById('drop-zone');
    const previewContainer = document.getElementById('preview-container');
    const canvasOverlay = document.getElementById('canvas-overlay');
    const targetGraphic = document.getElementById('target-graphic');
    const webcamContainer = document.getElementById('webcam-container');
    const webcamVideo = document.getElementById('webcam-video');
    const btnSnapWebcam = document.getElementById('btn-snap-webcam');
    const btnCancelWebcam = document.getElementById('btn-cancel-webcam');
    const btnWebcam = document.getElementById('btn-webcam');
    const btnVerify = document.getElementById('btn-verify');
    const verifySpinner = document.getElementById('verify-spinner');
    const verifyText = document.getElementById('verify-text');
    const chkBlockchain = document.getElementById('chk-blockchain');
    const thresholdSlider = document.getElementById('threshold-slider');
    const thresholdVal = document.getElementById('threshold-val');
    const btnSample1 = document.getElementById('btn-sample-1');
    const btnSample2 = document.getElementById('btn-sample-2');
    const btnDownloadImg = document.getElementById('btn-download-img');

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
    const teleL1Status = document.getElementById('tele-l1-status');
    const teleL1Block = document.getElementById('tele-l1-block');
    const teleBcStatus = document.getElementById('tele-bc-status');
    const teleBcLink = document.getElementById('tele-bc-link');
    const teleDeepfakeLabel = document.getElementById('tele-deepfake-label');
    const teleDeepfakeRisk = document.getElementById('tele-deepfake-risk');
    const teleBestSocial = document.getElementById('tele-best-social');
    const teleCandidates = document.getElementById('tele-candidates');
    const logLine = document.getElementById('log-line');
    const logTime = document.getElementById('log-time');
    const btnCopyJson = document.getElementById('btn-copy-json');
    const jsonViewer = document.getElementById('json-viewer');

    // State
    let selectedFile = null;
    let base64Snapshot = null;
    let currentImageElement = null;
    let webcamStream = null;
    let progressTimer = null;

    // Clock
    setInterval(() => {
        const now = new Date();
        logTime.textContent = now.toTimeString().split(' ')[0];
    }, 1000);

    // Threshold Slider
    if (thresholdSlider && thresholdVal) {
        thresholdSlider.addEventListener('input', (e) => {
            thresholdVal.textContent = parseFloat(e.target.value).toFixed(2);
        });
    }

    // File Input Trigger
    if (targetGraphic) {
        targetGraphic.addEventListener('click', () => fileInput.click());
    }
    if (fileInput) {
        fileInput.addEventListener('change', (e) => {
            if (e.target.files && e.target.files[0]) {
                handleFileSelect(e.target.files[0]);
            }
        });
    }

    // Drag and Drop Handling
    if (dropZone) {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
            }, false);
            document.body.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
            }, false);
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                dropZone.classList.add('bg-emerald-50', 'border-emerald-500');
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                dropZone.classList.remove('bg-emerald-50', 'border-emerald-500');
            }, false);
        });

        dropZone.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            if (files && files.length > 0) {
                handleFileSelect(files[0]);
            }
        });
    }

    function handleFileSelect(file) {
        stopWebcam();
        selectedFile = file;
        base64Snapshot = null;
        const reader = new FileReader();
        reader.onload = (event) => {
            displayPreview(event.target.result);
        };
        reader.readAsDataURL(file);
    }

    function displayPreview(dataUrl) {
        stopWebcam();
        const img = new Image();
        img.onload = () => {
            currentImageElement = img;
            canvasOverlay.width = img.width;
            canvasOverlay.height = img.height;
            const ctx = canvasOverlay.getContext('2d');
            ctx.clearRect(0, 0, img.width, img.height);
            ctx.drawImage(img, 0, 0);

            previewContainer.classList.remove('hidden');
            if (targetGraphic) targetGraphic.classList.add('hidden');
            if (webcamContainer) webcamContainer.classList.add('hidden');
            logLine.textContent = `> IMAGE LOADED: ${img.width}x${img.height} PX. READY FOR VERIFICATION.`;
        };
        img.src = dataUrl;
    }

    // Download Analyzed Facial Image Handler
    if (btnDownloadImg && canvasOverlay) {
        btnDownloadImg.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            try {
                const dataUrl = canvasOverlay.toDataURL('image/jpeg', 0.95);
                const a = document.createElement('a');
                a.href = dataUrl;
                a.download = 'faceid_evidence_scan.jpg';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                logLine.textContent = '> EVIDENCE IMAGE DOWNLOADED (faceid_evidence_scan.jpg).';
            } catch (err) {
                alert('Unable to download image: ' + err.message);
            }
        });
    }

    // Quick Sample 1: Default Portrait
    if (btnSample1) {
        btnSample1.addEventListener('click', async () => {
            logLine.textContent = '> LOADING SAMPLE 1 (PORTRAIT)...';
            try {
                const res = await fetch('/static/sample.jpg');
                if (res.ok) {
                    const blob = await res.blob();
                    handleFileSelect(new File([blob], 'sample.jpg', { type: 'image/jpeg' }));
                } else {
                    throw new Error('Sample 1 not found');
                }
            } catch (err) {
                logLine.textContent = `> ERROR: ${err.message}`;
            }
        });
    }

    // Quick Sample 2: Virat Kohli
    if (btnSample2) {
        btnSample2.addEventListener('click', async () => {
            logLine.textContent = '> LOADING SAMPLE 2 (VIRAT KOHLI)...';
            try {
                const res = await fetch('/static/sample_virat.png');
                if (res.ok) {
                    const blob = await res.blob();
                    handleFileSelect(new File([blob], 'sample_virat.png', { type: 'image/png' }));
                } else {
                    throw new Error('Sample 2 not found');
                }
            } catch (err) {
                logLine.textContent = `> ERROR: ${err.message}`;
            }
        });
    }

    // Live Webcam Handlers
    if (btnWebcam) {
        btnWebcam.addEventListener('click', async () => {
            try {
                if (targetGraphic) targetGraphic.classList.add('hidden');
                if (previewContainer) previewContainer.classList.add('hidden');
                if (webcamContainer) webcamContainer.classList.remove('hidden');
                logLine.textContent = '> INITIALIZING LIVE WEBCAM...';

                webcamStream = await navigator.mediaDevices.getUserMedia({
                    video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' }
                });
                webcamVideo.srcObject = webcamStream;
                logLine.textContent = '> WEBCAM ACTIVE. POSITION FACE & CLICK SNAP.';
            } catch (err) {
                logLine.textContent = `> WEBCAM ERROR: ${err.message}`;
                alert(`Webcam access denied or unavailable: ${err.message}`);
                stopWebcam();
            }
        });
    }

    if (btnCancelWebcam) {
        btnCancelWebcam.addEventListener('click', () => {
            stopWebcam();
            if (currentImageElement) {
                previewContainer.classList.remove('hidden');
            } else if (targetGraphic) {
                targetGraphic.classList.remove('hidden');
            }
        });
    }

    if (btnSnapWebcam) {
        btnSnapWebcam.addEventListener('click', () => {
            if (!webcamVideo.videoWidth) return;
            const tempCanvas = document.createElement('canvas');
            tempCanvas.width = webcamVideo.videoWidth;
            tempCanvas.height = webcamVideo.videoHeight;
            const ctx = tempCanvas.getContext('2d');
            ctx.drawImage(webcamVideo, 0, 0);

            const dataUrl = tempCanvas.toDataURL('image/jpeg', 0.95);
            selectedFile = null;
            base64Snapshot = dataUrl;
            displayPreview(dataUrl);
            stopWebcam();
            logLine.textContent = '> WEBCAM FRAME CAPTURED. READY FOR VERIFICATION.';
        });
    }

    function stopWebcam() {
        if (webcamStream) {
            webcamStream.getTracks().forEach(track => track.stop());
            webcamStream = null;
        }
        if (webcamContainer) webcamContainer.classList.add('hidden');
    }

    // Verification Pipeline Execution
    btnVerify.addEventListener('click', async () => {
        if (!selectedFile && !base64Snapshot) {
            alert('Please select or capture a facial image first.');
            return;
        }

        setLoading(true);
        seaStatusBadge.textContent = 'SCANNING...';
        seaStatusBadge.className = 'font-mono text-[10px] font-bold bg-amber-400 text-black px-2 py-0.5 uppercase tracking-wider animate-pulse';

        const writeBlockchain = chkBlockchain ? chkBlockchain.checked : false;
        const threshold = thresholdSlider ? parseFloat(thresholdSlider.value) : 0.45;
        const startTime = Date.now();

        // Progressive status animation
        const steps = [
            '1/6: Extracting ArcFace 512-D face embedding...',
            '2/6: Querying Google Lens reverse visual index...',
            '3/6: Fetching candidate images in parallel...',
            '4/6: Computing biometric cosine similarity...',
            '5/6: Analyzing ViT deepfake risk...',
            '6/6: Hashing evidence and committing to blockchain...'
        ];
        let stepIdx = 0;
        logLine.textContent = `> ${steps[0]}`;
        progressTimer = setInterval(() => {
            stepIdx = (stepIdx + 1) % steps.length;
            logLine.textContent = `> ${steps[stepIdx]} (${Math.round((Date.now() - startTime) / 1000)}s)`;
        }, 1800);

        try {
            let response;
            if (selectedFile) {
                const formData = new FormData();
                formData.append('file', selectedFile);
                formData.append('write_blockchain', writeBlockchain);
                const url = `/api/verify?write_blockchain=${writeBlockchain}&threshold=${threshold}`;
                response = await fetch(url, { method: 'POST', body: formData });
            } else {
                response = await fetch('/api/verify-base64', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        image_base64: base64Snapshot,
                        write_blockchain: writeBlockchain,
                        threshold: threshold
                    }),
                });
            }

            if (!response.ok) {
                let errorMsg = `Server error (HTTP ${response.status})`;
                try {
                    const errData = await response.json();
                    if (errData && errData.detail) errorMsg = errData.detail;
                } catch (_) {}
                throw new Error(errorMsg);
            }

            const data = await response.json();
            const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
            renderTelemetry(data, elapsed);
        } catch (err) {
            logLine.textContent = `> PIPELINE ERROR: ${err.message}`;
            seaStatusBadge.textContent = 'SCAN ERROR';
            seaStatusBadge.className = 'font-mono text-[10px] font-bold bg-red-600 text-white px-2 py-0.5 uppercase tracking-wider';
            alert(`FaceID Error: ${err.message}`);
        } finally {
            if (progressTimer) clearInterval(progressTimer);
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

        const face = data.face || data.biometrics || {};
        const img = data.image || data.source_image || {};
        const search = data.reverse_search || data.osint_search || {};
        const v = data.verification || {};
        const l1 = data.blockchain_layer1 || {};
        const bc = data.blockchain_layer2 || data.blockchain || {};
        const df = data.deepfake_analysis || {};
        const best = data.best_match || {};

        // 1. Status Banner
        if (v.status === 'VERIFIED') {
            seaStatusBadge.textContent = 'PROOF VERIFIED';
            seaStatusBadge.className = 'font-mono text-[10px] font-bold bg-emerald-500 text-black px-2 py-0.5 uppercase tracking-wider';
            teleStatus.textContent = 'VERIFIED MATCH DETECTED ✓';
            teleStatus.className = 'text-sm font-extrabold text-emerald-400 tracking-wider';
        } else {
            seaStatusBadge.textContent = 'ORIGINAL UNBOUND';
            seaStatusBadge.className = 'font-mono text-[10px] font-bold bg-amber-400 text-black px-2 py-0.5 uppercase tracking-wider';
            teleStatus.textContent = 'NO CONFIRMED MATCH (LOCAL ORIGINAL)';
            teleStatus.className = 'text-sm font-extrabold text-amber-300 tracking-wider';
        }

        const scoreVal = v.best_similarity !== undefined ? v.best_similarity : (best.cosine_similarity || 0);
        teleScore.textContent = `${(scoreVal * 100).toFixed(1)}%`;

        // 2. Module 1: Face Detection
        teleFaceDetected.textContent = `Detected: ${face.detected ? 'YES ✓' : 'NO'}`;
        teleFaceDetected.className = face.detected ? 'text-emerald-300 font-bold' : 'text-amber-300 font-bold';
        teleFaceCount.textContent = `Faces: ${face.count || 0} (score: ${(face.det_score || 0).toFixed(2)})`;

        // Module 2: Hashes
        teleSha.textContent = img.sha256 ? `${img.sha256.substring(0, 16)}...` : 'N/A';
        telePhash.textContent = img.phash || 'N/A';

        // Module 3: Reverse Search
        if (search.error) {
            teleSearchCount.textContent = `Search error: ${search.error.substring(0, 20)}`;
        } else {
            teleSearchCount.textContent = `Candidates Found: ${search.count || search.total_candidates || 0}`;
        }
        teleSearchEngine.textContent = `Engine: ${search.provider || 'Google Lens'}`;

        // Module 4: Local Blockchain L1
        if (teleL1Status) {
            teleL1Status.textContent = l1.verified !== false ? 'Status: RECORDED ✓' : 'Status: NOT RECORDED';
            teleL1Status.className = l1.verified !== false ? 'text-emerald-300 font-bold' : 'text-amber-300 font-bold';
        }
        if (teleL1Block) {
            teleL1Block.textContent = l1.block_index !== undefined ? `Block: #${l1.block_index} (${(l1.block_hash || '').substring(0, 8)}...)` : 'Block: Validated';
        }

        // Module 5: Sepolia Blockchain L2
        if (bc.submitted) {
            teleBcStatus.textContent = `Status: ANCHORED (Sepolia)`;
            teleBcStatus.className = 'text-emerald-300 font-bold';
            teleBcLink.innerHTML = `<a href="${bc.explorer_url}" target="_blank" class="underline text-amber-300 font-bold">Tx: ${bc.tx_hash.substring(0, 14)}... ↗</a>`;
        } else {
            teleBcStatus.textContent = `Status: NOT SUBMITTED (Optional)`;
            teleBcStatus.className = 'text-slate-400 font-bold';
            teleBcLink.textContent = `Layer 1 Immutable Ledger Only`;
        }

        // Module 6: Deepfake Assessment
        if (teleDeepfakeLabel && teleDeepfakeRisk) {
            const riskPct = ((df.risk_score || df.confidence || 0) * 100).toFixed(1);
            const label = df.label || 'Unknown';
            teleDeepfakeLabel.textContent = `Status: ${label.toUpperCase()}`;
            teleDeepfakeLabel.className = df.is_synthetic ? 'text-red-400 font-bold' : 'text-emerald-300 font-bold';
            teleDeepfakeRisk.textContent = `Risk Score: ${riskPct}% (${df.is_synthetic ? 'Manipulated' : 'Authentic'})`;
        }

        // Best Social Link Header
        if (teleBestSocial) {
            if (best.link) {
                const domain = best.platform || best.source || 'Web Source';
                teleBestSocial.innerHTML = `<span class="text-slate-400 font-normal">Top Source:</span> <a href="${best.link}" target="_blank" class="underline hover:text-white">${domain} ↗</a>`;
            } else {
                teleBestSocial.textContent = '';
            }
        }

        // 3. Candidates Matrix
        const matches = data.matches || [];
        if (matches.length > 0) {
            teleCandidates.innerHTML = matches.map(m => {
                const sim = m.cosine_similarity !== null && m.cosine_similarity !== undefined
                    ? m.cosine_similarity
                    : (m.visual_similarity || 0);
                const pct = (sim * 100).toFixed(1);
                const platform = m.social_meta?.platform || m.source || 'Visual Match';
                const isPost = m.social_meta?.is_specific_post ? '★ Social Post' : '';
                return `
                    <div class="border border-emerald-500/40 bg-[#0A2D22] p-2 space-y-1">
                        <div class="flex items-center justify-between text-[11px] font-bold text-emerald-300">
                            <span class="truncate max-w-[140px]" title="${m.title || 'Candidate'}">${m.title || platform}</span>
                            <span class="text-amber-300 font-mono">${pct}%</span>
                        </div>
                        <div class="flex items-center justify-between text-[10px]">
                            <a href="${m.link}" target="_blank" class="text-emerald-400 underline block truncate max-w-[130px]">
                                ${platform} ↗
                            </a>
                            <div class="flex items-center space-x-1.5">
                                ${m.candidate_image_url || m.image_url ? `
                                    <a href="${m.candidate_image_url || m.image_url}" target="_blank" download="candidate_match.jpg" class="text-amber-300 hover:text-white text-[9px] font-mono px-1 py-0.5 bg-black/50 border border-emerald-500/40 rounded-sm" title="Download candidate media">
                                        📥 IMG
                                    </a>
                                ` : ''}
                                <span class="text-amber-400 text-[9px] font-mono">${isPost}</span>
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
        } else {
            teleCandidates.innerHTML = `<span class="text-emerald-700 italic text-[11px]">No external candidate matches returned.</span>`;
        }

        // 4. Bounding Box & Facial Landmark Overlay
        const boxes = face.face_boxes || [];
        const landmarks = face.landmarks || [];
        if (currentImageElement && boxes.length > 0) {
            drawBoundingBoxes(boxes, landmarks);
        }

        // 5. JSON Viewer & Log Line
        jsonViewer.textContent = JSON.stringify(data, null, 2);
        logLine.textContent = `> SCAN COMPLETED IN ${elapsed}S. VERDICT: ${v.status} (SIMILARITY: ${(scoreVal * 100).toFixed(1)}%)`;
    }

    function drawBoundingBoxes(boxes, landmarks) {
        if (!currentImageElement) return;
        const ctx = canvasOverlay.getContext('2d');
        ctx.clearRect(0, 0, canvasOverlay.width, canvasOverlay.height);
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
            ctx.fillRect(x1, Math.max(0, y1 - 22), 100, 22);
            ctx.fillStyle = '#000000';
            ctx.font = 'bold 11px JetBrains Mono, monospace';
            ctx.fillText(`FACE #${idx + 1}`, x1 + 4, Math.max(14, y1 - 6));
        });

        if (landmarks && landmarks.length > 0) {
            landmarks.forEach(kpsGroup => {
                kpsGroup.forEach(([x, y]) => {
                    ctx.beginPath();
                    ctx.arc(x, y, 4, 0, 2 * Math.PI);
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
    if (btnCopyJson && jsonViewer) {
        btnCopyJson.addEventListener('click', () => {
            navigator.clipboard.writeText(jsonViewer.textContent).then(() => {
                alert('Provenance JSON audit report copied to clipboard!');
            });
        });
    }
});
