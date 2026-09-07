// FaceID Cyber-Forensic Terminal Application Controller

document.addEventListener('DOMContentLoaded', () => {
    // UI Elements
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('file-input');
    const previewContainer = document.getElementById('preview-container');
    const canvasOverlay = document.getElementById('canvas-overlay');
    const targetGraphic = document.getElementById('target-graphic');
    const scanLaser = document.getElementById('scan-laser');
    const previewTag = document.getElementById('preview-tag');
    const fileMetaBar = document.getElementById('file-meta-bar');
    const fileMetaName = document.getElementById('file-meta-name');
    const fileMetaDim = document.getElementById('file-meta-dim');

    const thresholdSlider = document.getElementById('threshold-slider');
    const thresholdVal = document.getElementById('threshold-val');
    const chkBlockchain = document.getElementById('chk-blockchain');
    const btnQuickSample = document.getElementById('btn-quick-sample');
    const btnReset = document.getElementById('btn-reset');
    const btnVerify = document.getElementById('btn-verify');
    const verifySpinner = document.getElementById('verify-spinner');
    const verifyText = document.getElementById('verify-text');

    // Telemetry & Results Elements
    const seaStatusBadge = document.getElementById('sea-status-badge');
    const idleScreen = document.getElementById('idle-screen');
    const telemetryScreen = document.getElementById('telemetry-screen');
    const teleStatus = document.getElementById('tele-status');
    const teleScore = document.getElementById('tele-score');
    const gaugeCircle = document.getElementById('gauge-circle');
    const teleDeepfakeBadge = document.getElementById('tele-deepfake-badge');
    const teleFaceDetected = document.getElementById('tele-face-detected');
    const teleFaceCount = document.getElementById('tele-face-count');
    const teleSha = document.getElementById('tele-sha');
    const telePhash = document.getElementById('tele-phash');
    const teleSearchCount = document.getElementById('tele-search-count');
    const teleSearchEngine = document.getElementById('tele-search-engine');
    const teleBcStatus = document.getElementById('tele-bc-status');
    const teleBcLink = document.getElementById('tele-bc-link');
    const teleCandidates = document.getElementById('tele-candidates');
    const teleCandidateCountBadge = document.getElementById('tele-candidate-count-badge');
    const logLine = document.getElementById('log-line');
    const logTime = document.getElementById('log-time');
    const btnCopyJson = document.getElementById('btn-copy-json');
    const btnCopySha = document.getElementById('btn-copy-sha');
    const jsonViewer = document.getElementById('json-viewer');

    // Stepper elements
    const steps = [
        document.getElementById('step-1'),
        document.getElementById('step-2'),
        document.getElementById('step-3'),
        document.getElementById('step-4'),
        document.getElementById('step-5'),
    ];

    // State Variables
    let selectedFile = null;
    let currentImageElement = null;
    let stepperInterval = null;

    // Real-time Clock
    setInterval(() => {
        const now = new Date();
        logTime.textContent = now.toTimeString().split(' ')[0];
    }, 1000);

    // Threshold Slider Listener
    thresholdSlider.addEventListener('input', (e) => {
        const val = parseFloat(e.target.value);
        let label = `${val.toFixed(2)}`;
        if (val >= 0.95) label += ' (Ultra Strict)';
        else if (val >= 0.88) label += ' (Strict)';
        else if (val >= 0.75) label += ' (Standard)';
        else label += ' (Permissive)';
        thresholdVal.textContent = label;
    });

    // Drag and Drop Handlers
    dropzone.addEventListener('click', () => fileInput.click());

    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.add('drag-active');
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.remove('drag-active');
        });
    });

    dropzone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        if (dt && dt.files && dt.files.length > 0) {
            handleFileSelect(dt.files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files[0]) {
            handleFileSelect(e.target.files[0]);
        }
    });

    // File Selection & Display
    function handleFileSelect(file) {
        if (!file.type.startsWith('image/')) {
            showToast('Invalid file format. Please upload an image.', 'error');
            return;
        }

        selectedFile = file;
        const reader = new FileReader();
        reader.onload = (e) => {
            displayPreview(e.target.result, file.name);
        };
        reader.readAsDataURL(file);
    }

    function displayPreview(dataUrl, fileName = 'image.jpg') {
        const img = new Image();
        img.onload = () => {
            currentImageElement = img;

            // Set canvas dimensions
            canvasOverlay.width = img.width;
            canvasOverlay.height = img.height;
            const ctx = canvasOverlay.getContext('2d');
            ctx.clearRect(0, 0, img.width, img.height);
            ctx.drawImage(img, 0, 0);

            previewContainer.classList.remove('hidden');
            targetGraphic.classList.add('hidden');
            fileMetaBar.classList.remove('hidden');
            fileMetaName.textContent = fileName;
            fileMetaDim.textContent = `${img.width} × ${img.height} PX`;
            previewTag.textContent = 'PROBE READY';
            previewTag.className = 'absolute bottom-2 left-2 bg-slate-900/90 backdrop-blur text-emerald-400 font-mono text-[10px] px-2.5 py-1 rounded border border-emerald-500/40';

            logLine.textContent = `> PROBE LOADED: ${img.width}x${img.height}PX. READY FOR ARCFACE SCAN.`;
            showToast(`Loaded ${fileName} (${img.width}x${img.height})`, 'success');
        };
        img.src = dataUrl;
    }

    // Quick Sample Loading
    btnQuickSample.addEventListener('click', async () => {
        logLine.textContent = '> RETRIEVING BENCHMARK SAMPLE PROBE...';
        try {
            const res = await fetch('/static/sample.jpg');
            if (res.ok) {
                const blob = await res.blob();
                handleFileSelect(new File([blob], 'sample_portrait.jpg', { type: 'image/jpeg' }));
            } else {
                throw new Error('Sample file not reachable');
            }
        } catch (err) {
            logLine.textContent = `> SAMPLE LOAD ERROR: ${err.message}`;
            showToast('Unable to load sample portrait.', 'error');
        }
    });

    // Reset Terminal State
    btnReset.addEventListener('click', () => {
        selectedFile = null;
        currentImageElement = null;
        fileInput.value = '';
        previewContainer.classList.add('hidden');
        targetGraphic.classList.remove('hidden');
        fileMetaBar.classList.add('hidden');
        telemetryScreen.classList.add('hidden');
        idleScreen.classList.remove('hidden');
        seaStatusBadge.textContent = 'AWAITING SCAN';
        seaStatusBadge.className = 'font-mono text-[10px] font-bold bg-slate-800 text-amber-300 border border-amber-500/30 px-2.5 py-0.5 rounded-full uppercase tracking-wider';
        resetStepper();
        logLine.textContent = '> TERMINAL BUFFER CLEARED. AWAITING SCAN COMMAND.';
        showToast('Terminal reset to clean state.', 'info');
    });

    // Stepper Animation Helpers
    function startStepperAnimation() {
        resetStepper();
        let currentStep = 0;
        stepperInterval = setInterval(() => {
            steps.forEach((s, idx) => {
                if (idx < currentStep) {
                    s.className = 'p-1.5 rounded bg-emerald-950/60 border border-emerald-500/60 text-emerald-300 transition-all shadow-[0_0_10px_rgba(16,185,129,0.2)]';
                } else if (idx === currentStep) {
                    s.className = 'p-1.5 rounded bg-cyan-900/60 border border-cyan-400 text-cyan-200 animate-pulse transition-all shadow-[0_0_12px_rgba(6,182,212,0.4)]';
                } else {
                    s.className = 'p-1.5 rounded bg-slate-900 border border-slate-800 text-slate-500 transition-all';
                }
            });
            currentStep = (currentStep + 1) % steps.length;
        }, 600);
    }

    function completeStepper() {
        if (stepperInterval) clearInterval(stepperInterval);
        steps.forEach(s => {
            s.className = 'p-1.5 rounded bg-emerald-950/80 border border-emerald-500/70 text-emerald-300 font-bold transition-all';
        });
    }

    function resetStepper() {
        if (stepperInterval) clearInterval(stepperInterval);
        steps.forEach(s => {
            s.className = 'p-1.5 rounded bg-slate-900 border border-slate-800 text-slate-500 transition-all';
        });
    }

    // Run Provenance Verification Pipeline
    btnVerify.addEventListener('click', async () => {
        if (!selectedFile) {
            showToast('Please select or drop a facial probe image first.', 'warning');
            return;
        }

        setLoading(true);
        startStepperAnimation();
        logLine.textContent = '> EXECUTING ARCFACE 512-D EXTRACTION & REVERSE PROVENANCE SEARCH...';
        seaStatusBadge.textContent = 'SCANNING...';
        seaStatusBadge.className = 'font-mono text-[10px] font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-400 px-2.5 py-0.5 rounded-full uppercase tracking-wider animate-pulse';

        const writeBlockchain = chkBlockchain.checked;
        const threshold = parseFloat(thresholdSlider.value);
        const startTime = Date.now();

        try {
            const formData = new FormData();
            formData.append('file', selectedFile);

            // Pass parameters in query string
            const endpoint = `/api/verify?write_blockchain=${writeBlockchain}&threshold=${threshold}&top_k=10`;
            const response = await fetch(endpoint, {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);

            if (response.ok) {
                completeStepper();
                renderTelemetry(data, elapsed);
                showToast(`Scan complete in ${elapsed}s: ${data.verification?.status || 'PROCESSED'}`, 'success');
            } else {
                throw new Error(data.detail || 'Verification error');
            }
        } catch (err) {
            resetStepper();
            logLine.textContent = `> PIPELINE EXCEPTION: ${err.message}`;
            seaStatusBadge.textContent = 'SCAN ERROR';
            seaStatusBadge.className = 'font-mono text-[10px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/50 px-2.5 py-0.5 rounded-full uppercase tracking-wider';
            showToast(`Pipeline Error: ${err.message}`, 'error');
        } finally {
            setLoading(false);
        }
    });

    function setLoading(isLoading) {
        btnVerify.disabled = isLoading;
        if (isLoading) {
            verifySpinner.classList.remove('hidden');
            verifyText.textContent = 'EXECUTING PROVENANCE ENGINE...';
            scanLaser.classList.remove('hidden');
            dropzone.classList.add('scanning');
            previewTag.textContent = 'SCANNING VECTORS';
            previewTag.className = 'absolute bottom-2 left-2 bg-slate-900/90 backdrop-blur text-cyan-300 font-mono text-[10px] px-2.5 py-1 rounded border border-cyan-400 animate-pulse';
        } else {
            verifySpinner.classList.add('hidden');
            verifyText.textContent = 'RUN PROVENANCE VERIFICATION →';
            scanLaser.classList.add('hidden');
            dropzone.classList.remove('scanning');
            previewTag.textContent = 'ANALYSIS COMPLETE';
            previewTag.className = 'absolute bottom-2 left-2 bg-slate-900/90 backdrop-blur text-emerald-400 font-mono text-[10px] px-2.5 py-1 rounded border border-emerald-500/40';
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
        const bc = data.blockchain || {};
        const df = data.deepfake_analysis || {};

        // 1. Status & Verdict
        const score = v.best_similarity || 0;
        const scorePercent = (score * 100).toFixed(1);
        teleScore.textContent = `${scorePercent}%`;

        // Update Circular Gauge (Circumference is 100)
        const offset = Math.max(0, 100 - score * 100);
        gaugeCircle.style.strokeDashoffset = offset;

        if (v.status === 'VERIFIED') {
            seaStatusBadge.textContent = 'PROOF VERIFIED ✓';
            seaStatusBadge.className = 'font-mono text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/60 px-2.5 py-0.5 rounded-full uppercase tracking-wider shadow-[0_0_12px_rgba(16,185,129,0.3)]';
            
            teleStatus.innerHTML = `<span>VERIFIED MATCH DETECTED</span> <span class="text-xs bg-emerald-500/20 text-emerald-300 px-2 py-0.5 rounded border border-emerald-500/40 font-mono">MATCH ✓</span>`;
            teleStatus.className = 'text-lg font-black text-emerald-400 tracking-wide flex items-center gap-2';
            gaugeCircle.setAttribute('class', 'gauge-circle text-emerald-400');
        } else {
            seaStatusBadge.textContent = 'ORIGINAL UNBOUND';
            seaStatusBadge.className = 'font-mono text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/60 px-2.5 py-0.5 rounded-full uppercase tracking-wider shadow-[0_0_12px_rgba(245,158,11,0.3)]';
            
            teleStatus.innerHTML = `<span>NO CONFIRMED MATCH</span> <span class="text-xs bg-amber-500/20 text-amber-300 px-2 py-0.5 rounded border border-amber-500/40 font-mono">LOCAL ORIGINAL</span>`;
            teleStatus.className = 'text-lg font-black text-amber-300 tracking-wide flex items-center gap-2';
            gaugeCircle.setAttribute('class', 'gauge-circle text-amber-400');
        }

        // Deepfake / Synthetic Detection Badge
        if (df.is_synthetic) {
            teleDeepfakeBadge.innerHTML = `<span>⚠️ Potential Synthetic / Deepfake (Risk: ${(df.risk_score * 100).toFixed(0)}%)</span>`;
            teleDeepfakeBadge.className = 'inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/40 text-[10px]';
        } else {
            const conf = df.confidence ? `${(df.confidence * 100).toFixed(0)}% Conf.` : 'High Confidence';
            teleDeepfakeBadge.innerHTML = `<span>🛡️ Authentic / Real Media (${conf})</span>`;
            teleDeepfakeBadge.className = 'inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 text-[10px]';
        }

        // 2. Modules Telemetry
        const faceDetected = face.detected ? 'True' : 'False';
        teleFaceDetected.innerHTML = `Detected: <span class="${face.detected ? 'text-emerald-300' : 'text-rose-400'} font-bold">${faceDetected}</span>`;
        const detScore = face.det_score ? `(Score: ${(face.det_score * 100).toFixed(1)}%)` : '';
        teleFaceCount.textContent = `Faces Analyzed: ${face.count || face.face_count || 0} ${detScore}`;

        teleSha.textContent = img.sha256 ? `${img.sha256.substring(0, 18)}...` : '--';
        teleSha.title = img.sha256 || '';
        telePhash.textContent = img.phash || '--';

        if (search.error) {
            teleSearchCount.textContent = `Error: ${search.error.substring(0, 26)}...`;
            teleSearchCount.className = 'text-rose-400 font-bold text-[11px]';
        } else {
            teleSearchCount.textContent = `Candidates Found: ${search.count || search.total_candidates || 0}`;
            teleSearchCount.className = 'text-slate-200 font-bold';
        }
        teleSearchEngine.textContent = `Engine: ${search.provider || 'Google Lens via SerpApi'}`;

        if (bc.submitted) {
            teleBcStatus.innerHTML = `Status: <span class="text-emerald-400 font-bold">ANCHORED (${bc.network || 'Sepolia'})</span>`;
            teleBcLink.innerHTML = `<a href="${bc.explorer_url}" target="_blank" class="inline-flex items-center gap-1 text-amber-300 hover:text-amber-200 font-bold underline"><span>Tx: ${bc.tx_hash.substring(0, 14)}...</span> <span>↗</span></a>`;
        } else {
            teleBcStatus.innerHTML = `Status: <span class="text-slate-500">NOT SUBMITTED (Local Chain Only)</span>`;
            teleBcLink.textContent = `Tx: Local Layer 1`;
        }

        // 3. Candidates Matrix Gallery
        const matches = data.matches || [];
        teleCandidateCountBadge.textContent = `${matches.length} MATCHES`;
        if (matches.length > 0) {
            teleCandidates.innerHTML = matches.map((m, idx) => {
                const sim = ((m.visual_similarity || m.cosine_similarity || 0) * 100).toFixed(1);
                const platform = m.social_meta?.platform || m.platform || m.source || 'Web';
                const isVerified = m.verified;
                const badgeColor = isVerified 
                    ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40' 
                    : (sim > 70 ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40' : 'bg-slate-800 text-slate-400 border-slate-700');

                return `
                    <div class="rounded-lg border border-slate-800/80 bg-slate-900/60 p-2.5 space-y-1.5 hover:border-slate-700 transition-all">
                        <div class="flex items-center justify-between">
                            <span class="text-[9px] font-bold px-2 py-0.5 rounded-full border ${badgeColor}">
                                ${platform}
                            </span>
                            <span class="text-[11px] font-bold font-mono ${isVerified ? 'text-emerald-400' : 'text-amber-300'}">${sim}%</span>
                        </div>
                        <div class="text-[11px] font-semibold text-slate-200 truncate" title="${m.title || ''}">${m.title || 'Visual Candidate Match'}</div>
                        <a href="${m.link}" target="_blank" class="text-[10px] text-cyan-400 hover:text-cyan-300 flex items-center gap-1 truncate transition-colors">
                            <span class="truncate">${m.link}</span>
                            <span>↗</span>
                        </a>
                    </div>
                `;
            }).join('');
        } else {
            teleCandidates.innerHTML = `<span class="text-slate-500 italic text-[11px] col-span-2 py-3 text-center">No external visual candidate matches returned.</span>`;
        }

        // 4. Draw Facial Landmarks & Bounding Reticles
        const boxes = face.face_boxes || [];
        const landmarks = face.landmarks || [];
        if (currentImageElement && boxes.length > 0) {
            drawBoundingBoxes(boxes, landmarks);
        }

        // 5. JSON Evidence Viewer
        jsonViewer.textContent = JSON.stringify(data, null, 2);
        logLine.textContent = `> SCAN COMPLETED IN ${elapsed}S. VERDICT: ${v.status}`;
    }

    // High-Tech Cyber Bounding Box Reticles
    function drawBoundingBoxes(boxes, landmarks) {
        if (!currentImageElement) return;
        const ctx = canvasOverlay.getContext('2d');
        ctx.clearRect(0, 0, currentImageElement.width, currentImageElement.height);
        ctx.drawImage(currentImageElement, 0, 0);

        boxes.forEach((box, idx) => {
            const [x1, y1, x2, y2] = box;
            const width = x2 - x1;
            const height = y2 - y1;
            const bracketLen = Math.min(width, height) * 0.22;

            // Semi-transparent scan fill
            ctx.fillStyle = 'rgba(16, 185, 129, 0.08)';
            ctx.fillRect(x1, y1, width, height);

            // Reticle Border
            ctx.strokeStyle = 'rgba(16, 185, 129, 0.5)';
            ctx.lineWidth = 1.5;
            ctx.strokeRect(x1, y1, width, height);

            // Glowing Cyber Corner Brackets
            ctx.strokeStyle = '#10B981';
            ctx.lineWidth = 3.5;

            // Top-Left
            ctx.beginPath();
            ctx.moveTo(x1, y1 + bracketLen);
            ctx.lineTo(x1, y1);
            ctx.lineTo(x1 + bracketLen, y1);
            ctx.stroke();

            // Top-Right
            ctx.beginPath();
            ctx.moveTo(x2 - bracketLen, y1);
            ctx.lineTo(x2, y1);
            ctx.lineTo(x2, y1 + bracketLen);
            ctx.stroke();

            // Bottom-Left
            ctx.beginPath();
            ctx.moveTo(x1, y2 - bracketLen);
            ctx.lineTo(x1, y2);
            ctx.lineTo(x1 + bracketLen, y2);
            ctx.stroke();

            // Bottom-Right
            ctx.beginPath();
            ctx.moveTo(x2 - bracketLen, y2);
            ctx.lineTo(x2, y2);
            ctx.lineTo(x2, y2 - bracketLen);
            ctx.stroke();

            // Face Header HUD Badge
            const badgeW = Math.min(130, width);
            ctx.fillStyle = '#0F172A';
            ctx.fillRect(x1, Math.max(0, y1 - 22), badgeW, 22);
            ctx.strokeStyle = '#10B981';
            ctx.lineWidth = 1;
            ctx.strokeRect(x1, Math.max(0, y1 - 22), badgeW, 22);

            ctx.fillStyle = '#10B981';
            ctx.font = 'bold 10px JetBrains Mono';
            ctx.fillText(`#FACE-0${idx + 1} • 512-D`, x1 + 6, Math.max(14, y1 - 7));
        });

        // Glowing Facial Landmarks
        if (landmarks && landmarks.length > 0) {
            landmarks.forEach(kpsGroup => {
                kpsGroup.forEach(([x, y]) => {
                    // Outer glow
                    ctx.beginPath();
                    ctx.arc(x, y, 6, 0, 2 * Math.PI);
                    ctx.fillStyle = 'rgba(6, 182, 212, 0.35)';
                    ctx.fill();

                    // Core point
                    ctx.beginPath();
                    ctx.arc(x, y, 3, 0, 2 * Math.PI);
                    ctx.fillStyle = '#38BDF8';
                    ctx.fill();
                    ctx.lineWidth = 1;
                    ctx.strokeStyle = '#FFFFFF';
                    ctx.stroke();
                });
            });
        }
    }

    // 1-Click Copy Buttons with Non-blocking Toasts
    btnCopyJson.addEventListener('click', () => {
        navigator.clipboard.writeText(jsonViewer.textContent).then(() => {
            showToast('Audit JSON report copied to clipboard!', 'success');
        });
    });

    btnCopySha.addEventListener('click', (e) => {
        e.stopPropagation();
        const fullSha = teleSha.title || teleSha.textContent;
        if (fullSha && fullSha !== '--') {
            navigator.clipboard.writeText(fullSha).then(() => {
                showToast('SHA-256 hash copied to clipboard!', 'success');
            });
        }
    });

    // Modern Toast Notification Utility
    function showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = 'toast';

        let icon = 'ℹ️';
        if (type === 'success') icon = '✓';
        else if (type === 'warning') icon = '⚠️';
        else if (type === 'error') icon = '✕';

        toast.innerHTML = `<span class="font-bold text-emerald-400">${icon}</span><span>${message}</span>`;
        container.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(10px) scale(0.95)';
            toast.style.transition = 'all 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 3200);
    }
});
