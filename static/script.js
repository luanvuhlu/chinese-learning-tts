/**
 * Chinese TTS Video Generator - Frontend Script
 */

// ============ DOM ELEMENTS ============
const speechSpeedSlider = document.getElementById('speechSpeed');
const delaySlider = document.getElementById('delaySlider');
const speedValue = document.getElementById('speedValue');
const delayValue = document.getElementById('delayValue');
const contentTextarea = document.getElementById('content');
const charCount = document.getElementById('charCount');
const generateBtn = document.getElementById('generateBtn');
const resultSection = document.getElementById('resultSection');
const progressContainer = document.getElementById('progressContainer');
const videoContainer = document.getElementById('videoContainer');
const audioContainer = document.getElementById('audioContainer');
const pinyinContainer = document.getElementById('pinyinContainer');
const pinyinText = document.getElementById('pinyinText');
const errorContainer = document.getElementById('errorContainer');
const videoPlayer = document.getElementById('videoPlayer');
const audioPlayer = document.getElementById('audioPlayer');
const downloadBtn = document.getElementById('downloadBtn');
const downloadAudioBtn = document.getElementById('downloadAudioBtn');
const newGenerateBtn = document.getElementById('newGenerateBtn');
const newGenerateAudioBtn = document.getElementById('newGenerateAudioBtn');
const newGeneratePinyinBtn = document.getElementById('newGeneratePinyinBtn');
const copyPinyinBtn = document.getElementById('copyPinyinBtn');
const errorText = document.getElementById('errorText');
const retryBtn = document.getElementById('retryBtn');
const formTitle = document.getElementById('formTitle');
const bgImageGroup = document.getElementById('bgImageGroup');
const bgImageInput = document.getElementById('bgImageInput');
const imageFileName = document.getElementById('imageFileName');
const subtitleColorGroup = document.getElementById('subtitleColorGroup');
const subtitleColorInput = document.getElementById('subtitleColor');
const colorLabel = document.querySelector('.color-label');
const subtitleSizeGroup = document.getElementById('subtitleSizeGroup');
const subtitleSizeSlider = document.getElementById('subtitleSize');
const sizeValue = document.getElementById('sizeValue');
const showPinyinGroup = document.getElementById('showPinyinGroup');
const showPinyinCheckbox = document.getElementById('showPinyinCheckbox');
const formatRadios = document.querySelectorAll('input[name="output_format"]');

// ============ STATE ============
let currentJobId = null;
let currentOutputFormat = 'video';
let statusCheckInterval = null;

// ============ EVENT LISTENERS ============

// Update speech speed display
speechSpeedSlider.addEventListener('input', (e) => {
    const value = parseFloat(e.target.value);
    speedValue.textContent = value.toFixed(1) + 'x';
});

// Update delay display
delaySlider.addEventListener('input', (e) => {
    const value = parseFloat(e.target.value);
    delayValue.textContent = value.toFixed(1) + 's';
});

// Update character counter
contentTextarea.addEventListener('input', (e) => {
    charCount.textContent = e.target.value.length;
});

// Format selector change
formatRadios.forEach(radio => {
    radio.addEventListener('change', (e) => {
        currentOutputFormat = e.target.value;
        updateFormatUI();
    });
});

// File input change
bgImageInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        imageFileName.textContent = `✅ Selected: ${e.target.files[0].name}`;
    } else {
        imageFileName.textContent = '';
    }
});

// Drag & drop for file input
const fileInputLabel = document.querySelector('.file-input-label');
if (fileInputLabel) {
    fileInputLabel.addEventListener('dragover', (e) => {
        e.preventDefault();
        fileInputLabel.classList.add('drag-over');
    });

    fileInputLabel.addEventListener('dragleave', () => {
        fileInputLabel.classList.remove('drag-over');
    });

    fileInputLabel.addEventListener('drop', (e) => {
        e.preventDefault();
        fileInputLabel.classList.remove('drag-over');
        
        if (e.dataTransfer.files.length > 0) {
            bgImageInput.files = e.dataTransfer.files;
            imageFileName.textContent = `✅ Selected: ${e.dataTransfer.files[0].name}`;
        }
    });
}

// Subtitle color change
if (subtitleColorInput) {
    subtitleColorInput.addEventListener('change', (e) => {
        const colorName = getColorName(e.target.value);
        if (colorLabel) {
            colorLabel.textContent = colorName;
        }
    });
}

// Subtitle size change
if (subtitleSizeSlider) {
    subtitleSizeSlider.addEventListener('input', (e) => {
        const value = parseInt(e.target.value);
        if (sizeValue) {
            sizeValue.textContent = value + 'px';
        }
    });
}

// Generate button click
generateBtn.addEventListener('click', handleGenerateClick);

// Download buttons
if (downloadBtn) downloadBtn.addEventListener('click', handleDownloadClick);
if (downloadAudioBtn) downloadAudioBtn.addEventListener('click', handleDownloadAudioClick);

// New generate buttons
if (newGenerateBtn) newGenerateBtn.addEventListener('click', resetForm);
if (newGenerateAudioBtn) newGenerateAudioBtn.addEventListener('click', resetForm);
if (newGeneratePinyinBtn) newGeneratePinyinBtn.addEventListener('click', resetForm);

// Copy button
if (copyPinyinBtn) copyPinyinBtn.addEventListener('click', handleCopyPinyinClick);

// Retry button
if (retryBtn) retryBtn.addEventListener('click', resetForm);

// ============ FUNCTIONS ============

/**
 * Update UI based on output format
 */
function updateFormatUI() {
    if (currentOutputFormat === 'audio') {
        formTitle.textContent = 'Generate Audio';
        generateBtn.textContent = 'Generate Audio';
        bgImageGroup.style.display = 'none';
        if (subtitleColorGroup) subtitleColorGroup.style.display = 'none';
        if (subtitleSizeGroup) subtitleSizeGroup.style.display = 'none';
    } else if (currentOutputFormat === 'pinyin') {
        formTitle.textContent = 'Generate Pinyin';
        generateBtn.textContent = 'Generate Pinyin';
        bgImageGroup.style.display = 'none';
        if (subtitleColorGroup) subtitleColorGroup.style.display = 'none';
        if (subtitleSizeGroup) subtitleSizeGroup.style.display = 'none';
        if (showPinyinGroup) showPinyinGroup.style.display = 'none';
    } else {
        formTitle.textContent = 'Generate Video';
        generateBtn.textContent = 'Generate Video';
        bgImageGroup.style.display = 'block';
        if (subtitleColorGroup) subtitleColorGroup.style.display = 'block';
        if (subtitleSizeGroup) subtitleSizeGroup.style.display = 'block';
        if (showPinyinGroup) showPinyinGroup.style.display = 'block';
    }
}

/**
 * Handle generate button click
 */
async function handleGenerateClick() {
    const content = contentTextarea.value.trim();
    const speechSpeed = parseFloat(speechSpeedSlider.value);
    const delay = parseFloat(delaySlider.value);

    // Validate input
    if (!content) {
        showError('Please enter some Chinese text');
        return;
    }

    if (content.length > 1000) {
        showError('Content must not exceed 1000 characters');
        return;
    }

    // Disable button and show progress
    generateBtn.disabled = true;
    if (currentOutputFormat === 'audio') {
        generateBtn.textContent = 'Generating Audio...';
    } else if (currentOutputFormat === 'pinyin') {
        generateBtn.textContent = 'Generating Pinyin...';
    } else {
        generateBtn.textContent = 'Generating Video...';
    }

    try {
        console.log('📤 Sending request to API...');
        console.log({
            content_length: content.length,
            speech_speed: speechSpeed,
            delay: delay,
            output_format: currentOutputFormat
        });

        // Prepare FormData for multipart request
        const formData = new FormData();
        formData.append('content', content);
        formData.append('speech_speed', speechSpeed);
        formData.append('delay', delay);
        formData.append('output_format', currentOutputFormat);

        // Add background image if video format and file selected
        if (currentOutputFormat === 'video' && bgImageInput.files.length > 0) {
            formData.append('background_image', bgImageInput.files[0]);
            console.log('📸 Background image added:', bgImageInput.files[0].name);
        }

        // Add subtitle options if video format
        if (currentOutputFormat === 'video') {
            const subtitleColor = subtitleColorInput ? subtitleColorInput.value : '#000000';
            const subtitleSize = subtitleSizeSlider ? parseInt(subtitleSizeSlider.value) : 100;
            const showPinyin = showPinyinCheckbox ? showPinyinCheckbox.checked : true;
            formData.append('subtitle_color', subtitleColor);
            formData.append('subtitle_size', subtitleSize);
            formData.append('show_pinyin', showPinyin);
            console.log('🎨 Subtitle options:', { color: subtitleColor, size: subtitleSize, showPinyin });
        }

        // Call API to generate video/audio
        const response = await fetch('/api/generate', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `HTTP ${response.status}`);
        }

        const data = await response.json();
        currentJobId = data.job_id;
        
        console.log('✅ Job created:', currentJobId, 'Format:', data.output_format);

        // Show result section with progress
        resultSection.style.display = 'block';
        progressContainer.style.display = 'block';
        videoContainer.style.display = 'none';
        audioContainer.style.display = 'none';
        pinyinContainer.style.display = 'none';
        errorContainer.style.display = 'none';

        // Scroll to result section
        resultSection.scrollIntoView({ behavior: 'smooth', block: 'start' });

        // Poll for status
        pollJobStatus();

    } catch (error) {
        console.error('❌ Error:', error);
        generateBtn.disabled = false;
        if (currentOutputFormat === 'audio') {
            generateBtn.textContent = 'Generate Audio';
        } else if (currentOutputFormat === 'pinyin') {
            generateBtn.textContent = 'Generate Pinyin';
        } else {
            generateBtn.textContent = 'Generate Video';
        }
        showError(error.message || `Failed to generate ${currentOutputFormat}`);
    }
}

/**
 * Poll job status
 */
function pollJobStatus() {
    if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
    }

    // Start polling
    statusCheckInterval = setInterval(async () => {
        try {
            const response = await fetch(`/api/status/${currentJobId}`);

            if (!response.ok) {
                throw new Error(`Status check failed: ${response.status}`);
            }

            const job = await response.json();
            
            // Update progress text based on elapsed time (created_at is Unix timestamp in milliseconds)
            const elapsedSeconds = Math.floor((Date.now() - job.created_at) / 1000);
            let formatType = 'video';
            if (job.output_format === 'audio') {
                formatType = 'audio';
            } else if (job.output_format === 'pinyin') {
                formatType = 'pinyin';
            }
            let progressMsg = `Generating ${formatType}... (${elapsedSeconds}s elapsed)`;
            
            if (elapsedSeconds > 30) {
                progressMsg += '\n(Usually takes 1-5 minutes depending on text length)';
            }
            
            document.getElementById('progressText').textContent = progressMsg;

            if (job.status === 'completed') {
                clearInterval(statusCheckInterval);
                console.log('✅ Generation completed');
                showResult(job);
            } else if (job.status === 'failed') {
                clearInterval(statusCheckInterval);
                console.error('❌ Generation failed:', job.error);
                showError(job.error || 'Generation failed');
            } else {
                console.log(`⏳ Job status: ${job.status}`);
            }
        } catch (error) {
            clearInterval(statusCheckInterval);
            console.error('❌ Status check error:', error);
            showError(`Error checking status: ${error.message}`);
        }
    }, 2000); // Poll every 2 seconds
}

/**
 * Show result (video or audio)
 */
function showResult(job) {
    const outputFormat = job.output_format || job.file_type;
    progressContainer.style.display = 'none';
    errorContainer.style.display = 'none';

    if (outputFormat === 'audio') {
        videoContainer.style.display = 'none';
        audioContainer.style.display = 'block';
        pinyinContainer.style.display = 'none';

        // Set audio source
        const audioUrl = `/api/videos/${currentJobId}`;
        audioPlayer.src = audioUrl;

        // Scroll to audio player
        audioContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } else if (outputFormat === 'pinyin') {
        videoContainer.style.display = 'none';
        audioContainer.style.display = 'none';
        pinyinContainer.style.display = 'block';

        // Display pinyin text directly from job data
        pinyinText.textContent = job.pinyin_text || 'No pinyin text available';

        // Scroll to pinyin display
        pinyinContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } else {
        audioContainer.style.display = 'none';
        pinyinContainer.style.display = 'none';
        videoContainer.style.display = 'block';

        // Set video source
        const videoUrl = `/api/videos/${currentJobId}`;
        videoPlayer.src = videoUrl;

        // Scroll to video player
        videoContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    // Re-enable generate button
    generateBtn.disabled = false;
    if (currentOutputFormat === 'audio') {
        generateBtn.textContent = 'Generate Audio';
    } else if (currentOutputFormat === 'pinyin') {
        generateBtn.textContent = 'Generate Pinyin';
    } else {
        generateBtn.textContent = 'Generate Video';
    }
}

/**
 * Show error message
 */
function showError(message) {
    resultSection.style.display = 'block';
    progressContainer.style.display = 'none';
    videoContainer.style.display = 'none';
    audioContainer.style.display = 'none';
    pinyinContainer.style.display = 'none';
    errorContainer.style.display = 'block';
    
    // Truncate very long error messages
    const displayMessage = message.length > 500 
        ? message.substring(0, 500) + '...' 
        : message;
    errorText.textContent = displayMessage;
    
    console.error('Error:', message);

    if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
    }

    // Re-enable button
    generateBtn.disabled = false;
    if (currentOutputFormat === 'audio') {
        generateBtn.textContent = 'Generate Audio';
    } else if (currentOutputFormat === 'pinyin') {
        generateBtn.textContent = 'Generate Pinyin';
    } else {
        generateBtn.textContent = 'Generate Video';
    }

    // Scroll to error
    setTimeout(() => {
        errorContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
}

/**
 * Handle video download button click
 */
function handleDownloadClick() {
    if (!currentJobId) return;

    const videoUrl = `/api/videos/${currentJobId}?download=true`;
    const link = document.createElement('a');
    link.href = videoUrl;
    link.download = `generated_${currentJobId.substring(0, 8)}.mp4`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

/**
 * Handle audio download button click
 */
function handleDownloadAudioClick() {
    if (!currentJobId) return;

    const audioUrl = `/api/videos/${currentJobId}?download=true`;
    const link = document.createElement('a');
    link.href = audioUrl;
    link.download = `generated_${currentJobId.substring(0, 8)}.mp3`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

/**
 * Handle pinyin copy button click
 */
function handleCopyPinyinClick() {
    if (!pinyinText || !pinyinText.textContent) return;

    const textToCopy = pinyinText.textContent;
    
    // Use the modern Clipboard API if available
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(textToCopy).then(() => {
            // Show success feedback
            const originalText = copyPinyinBtn.textContent;
            copyPinyinBtn.textContent = '✅ Copied!';
            copyPinyinBtn.classList.add('btn-success');
            
            setTimeout(() => {
                copyPinyinBtn.textContent = originalText;
                copyPinyinBtn.classList.remove('btn-success');
            }, 2000);
        }).catch(err => {
            console.error('Failed to copy text: ', err);
            fallbackCopyTextToClipboard(textToCopy);
        });
    } else {
        // Fallback for older browsers
        fallbackCopyTextToClipboard(textToCopy);
    }
}

/**
 * Fallback copy function for older browsers
 */
function fallbackCopyTextToClipboard(text) {
    const textArea = document.createElement("textarea");
    textArea.value = text;
    
    // Avoid scrolling to bottom
    textArea.style.top = "0";
    textArea.style.left = "0";
    textArea.style.position = "fixed";
    textArea.style.opacity = "0";

    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();

    try {
        const successful = document.execCommand('copy');
        if (successful) {
            // Show success feedback
            const originalText = copyPinyinBtn.textContent;
            copyPinyinBtn.textContent = '✅ Copied!';
            copyPinyinBtn.classList.add('btn-success');
            
            setTimeout(() => {
                copyPinyinBtn.textContent = originalText;
                copyPinyinBtn.classList.remove('btn-success');
            }, 2000);
        } else {
            alert('Failed to copy text. Please copy manually.');
        }
    } catch (err) {
        console.error('Fallback copy failed: ', err);
        alert('Failed to copy text. Please copy manually.');
    }

    document.body.removeChild(textArea);
}

/**
 * Reset form to initial state
 */
function resetForm() {
    // Reset values
    speechSpeedSlider.value = '0.9';
    delaySlider.value = '0.2';
    contentTextarea.value = '';
    charCount.textContent = '0';
    currentOutputFormat = 'video';
    
    // Reset format selector
    document.querySelector('input[name="output_format"][value="video"]').checked = true;
    
    // Reset file input
    bgImageInput.value = '';
    imageFileName.textContent = '';
    
    // Reset subtitle controls
    if (subtitleColorInput) subtitleColorInput.value = '#000000';
    if (subtitleSizeSlider) subtitleSizeSlider.value = '100';
    if (showPinyinCheckbox) showPinyinCheckbox.checked = true;
    if (colorLabel) colorLabel.textContent = 'Black';
    if (sizeValue) sizeValue.textContent = '100px';

    // Update displays
    speedValue.textContent = '0.9x';
    delayValue.textContent = '0.2s';
    updateFormatUI();

    // Hide result section
    resultSection.style.display = 'none';
    progressContainer.style.display = 'none';
    videoContainer.style.display = 'none';
    audioContainer.style.display = 'none';
    errorContainer.style.display = 'none';

    // Clear states
    currentJobId = null;
    if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
    }

    // Reset button
    generateBtn.disabled = false;
    generateBtn.textContent = 'Generate Video';

    // Focus textarea
    contentTextarea.focus();

    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ============ INITIALIZATION ============

document.addEventListener('DOMContentLoaded', () => {
    // Initialize slider displays
    speedValue.textContent = speechSpeedSlider.value + 'x';
    delayValue.textContent = delaySlider.value + 's';

    // Initialize format UI
    updateFormatUI();

    // Focus on textarea
    contentTextarea.focus();

    // Add keyboard shortcut (Ctrl+Enter to generate)
    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            if (!generateBtn.disabled) {
                handleGenerateClick();
            }
        }
    });
});

// ============ UTILITY FUNCTIONS ============

/**
 * Format seconds to readable format
 */
function formatTime(seconds) {
    const minutes = Math.floor(seconds / 60);
    const secs = Math.round(seconds % 60);
    return `${minutes}m ${secs}s`;
}

/**
 * Validate Chinese text
 */
function isValidChineseText(text) {
    return /[\u4e00-\u9fff]/.test(text);
}

/**
 * Get color name from hex value
 */
function getColorName(hexColor) {
    const colorMap = {
        '#000000': 'Black',
        '#ffffff': 'White',
        '#ff0000': 'Red',
        '#00ff00': 'Green',
        '#0000ff': 'Blue',
        '#ffff00': 'Yellow',
        '#00ffff': 'Cyan',
        '#ff00ff': 'Magenta',
        '#ffa500': 'Orange',
        '#800080': 'Purple',
        '#ffc0cb': 'Pink',
        '#a52a2a': 'Brown'
    };
    
    const normalizedHex = hexColor.toLowerCase();
    return colorMap[normalizedHex] || normalizedHex;
}

// Copy prompt button
const copyPromptBtn = document.getElementById("copyPromptBtn");
if (copyPromptBtn) {
    copyPromptBtn.addEventListener("click", async () => {
        const text = document.getElementById("promptText").innerText;
        const btn = copyPromptBtn;

        try {
            if (navigator.clipboard && window.isSecureContext) {
                await navigator.clipboard.writeText(text);
            } else {
                // fallback
                const textarea = document.createElement("textarea");
                textarea.value = text;
                document.body.appendChild(textarea);
                textarea.select();
                document.execCommand("copy");
                textarea.remove();
            }

            btn.innerText = "✅ Copied!";
            setTimeout(() => {
                btn.innerText = "📋 Copy";
            }, 1500);

        } catch (err) {
            console.error(err);
            btn.innerText = "❌ Failed";
        }
    });
}
async function loadVideos() {
    const list = document.getElementById("videoHistoryList");
    list.innerHTML = "Loading...";

    try {
        const res = await fetch("/api/videos");
        
        if (!res.ok) {
            throw new Error(`HTTP ${res.status}`);
        }
        
        const data = await res.json();

        if (!data.files || data.files.length === 0) {
            list.innerHTML = "<p>No videos or audio files yet.</p>";
            return;
        }

        list.innerHTML = data.files.map(file => {
            const icon = file.file_type === 'audio' ? '🎵' : '🎬';
            const typeLabel = file.file_type === 'audio' ? 'Audio' : 'Video';
            const ext = file.file_type === 'audio' ? '.mp3' : '.mp4';
            const createdDate = new Date(file.created_at);  // created_at is Unix timestamp in milliseconds
            
            return `
                <div class="video-item">
                    <div>
                        <strong>${icon} ${file.filename}</strong>
                        <div class="video-meta">
                            ${typeLabel} · 
                            ${(file.size / 1024 / 1024).toFixed(2)} MB · 
                            ${createdDate.toLocaleString()}
                        </div>
                    </div>

                    <div class="video-actions">
                        <a href="${file.url}" target="_blank">▶ Play</a>
                        <a href="${file.url}?download=true" download="generated_${file.id.substring(0, 8)}${ext}">⬇ Download</a>
                    </div>
                </div>
            `;
        }).join("");

    } catch (err) {
        console.error('Error loading videos:', err);
        list.innerHTML = `<p>Failed to load files: ${err.message}</p>`;
    }
}

document.getElementById("refreshVideosBtn")
    .addEventListener("click", loadVideos);

loadVideos();