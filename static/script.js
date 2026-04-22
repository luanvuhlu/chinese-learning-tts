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
const errorContainer = document.getElementById('errorContainer');
const videoPlayer = document.getElementById('videoPlayer');
const downloadBtn = document.getElementById('downloadBtn');
const newGenerateBtn = document.getElementById('newGenerateBtn');
const errorText = document.getElementById('errorText');
const retryBtn = document.getElementById('retryBtn');

// ============ STATE ============
let currentJobId = null;
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

// Generate button click
generateBtn.addEventListener('click', handleGenerateClick);

// Download button click
downloadBtn.addEventListener('click', handleDownloadClick);

// New generate button
newGenerateBtn.addEventListener('click', resetForm);

// Retry button
retryBtn.addEventListener('click', resetForm);

// ============ FUNCTIONS ============

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
    generateBtn.textContent = 'Generating...';

    try {
        console.log('📤 Sending request to API...');
        console.log({
            content_length: content.length,
            speech_speed: speechSpeed,
            delay: delay
        });

        // Call API to generate video
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                content: content,
                speech_speed: speechSpeed,
                delay: delay
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `HTTP ${response.status}`);
        }

        const data = await response.json();
        currentJobId = data.job_id;
        
        console.log('✅ Job created:', currentJobId);

        // Show result section with progress
        resultSection.style.display = 'block';
        progressContainer.style.display = 'block';
        videoContainer.style.display = 'none';
        errorContainer.style.display = 'none';

        // Scroll to result section
        resultSection.scrollIntoView({ behavior: 'smooth', block: 'start' });

        // Poll for status
        pollJobStatus();

    } catch (error) {
        console.error('❌ Error:', error);
        generateBtn.disabled = false;
        generateBtn.textContent = 'Generate Video';
        showError(error.message || 'Failed to generate video');
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
            
            // Update progress text based on elapsed time
            const createdAt = new Date(job.created_at);
            const elapsedSeconds = Math.floor((Date.now() - createdAt) / 1000);
            let progressMsg = `Generating video... (${elapsedSeconds}s elapsed)`;
            
            if (elapsedSeconds > 30) {
                progressMsg += '\n(Usually takes 1-5 minutes depending on text length)';
            }
            
            document.getElementById('progressText').textContent = progressMsg;

            if (job.status === 'completed') {
                clearInterval(statusCheckInterval);
                console.log('✅ Video generation completed');
                showVideo();
            } else if (job.status === 'failed') {
                clearInterval(statusCheckInterval);
                console.error('❌ Video generation failed:', job.error);
                showError(job.error || 'Video generation failed');
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
 * Show video player
 */
function showVideo() {
    progressContainer.style.display = 'none';
    videoContainer.style.display = 'block';
    errorContainer.style.display = 'none';

    // Set video source
    const videoUrl = `/api/videos/${currentJobId}`;
    videoPlayer.src = videoUrl;

    // Scroll to video
    videoContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });

    // Re-enable generate button
    generateBtn.disabled = false;
    generateBtn.textContent = 'Generate Video';
}

/**
 * Show error message
 */
function showError(message) {
    resultSection.style.display = 'block';
    progressContainer.style.display = 'none';
    videoContainer.style.display = 'none';
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
    generateBtn.textContent = 'Generate Video';

    // Scroll to error
    setTimeout(() => {
        errorContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
}

/**
 * Handle download button click
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
 * Reset form to initial state
 */
function resetForm() {
    // Reset values
    speechSpeedSlider.value = '0.9';
    delaySlider.value = '0.2';
    contentTextarea.value = '';
    charCount.textContent = '0';

    // Update displays
    speedValue.textContent = '0.9x';
    delayValue.textContent = '0.2s';

    // Hide result section
    resultSection.style.display = 'none';
    progressContainer.style.display = 'none';
    videoContainer.style.display = 'none';
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

document.getElementById("copyPromptBtn").addEventListener("click", async () => {
    const text = document.getElementById("promptText").innerText;
    const btn = document.getElementById("copyPromptBtn");

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
async function loadVideos() {
    const list = document.getElementById("videoHistoryList");
    list.innerHTML = "Loading...";

    try {
        const res = await fetch("/api/videos");
        const data = await res.json();

        if (!data.videos.length) {
            list.innerHTML = "<p>No videos yet.</p>";
            return;
        }

        list.innerHTML = data.videos.map(video => `
            <div class="video-item">
                <div>
                    <strong>${video.filename}</strong>
                    <div class="video-meta">
                        ${(video.size / 1024 / 1024).toFixed(2)} MB · 
                        ${new Date(video.created_at).toLocaleString()}
                    </div>
                </div>

                <div class="video-actions">
                    <a href="${video.url}" target="_blank">▶ Play</a>
                    <a href="${video.url}" download>⬇ Download</a>
                </div>
            </div>
        `).join("");

    } catch (err) {
        list.innerHTML = "<p>Failed to load videos.</p>";
    }
}

document.getElementById("refreshVideosBtn")
    .addEventListener("click", loadVideos);

loadVideos();