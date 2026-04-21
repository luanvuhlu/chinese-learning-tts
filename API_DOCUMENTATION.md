# 🔌 API Documentation

## Base URL

```
http://localhost:5000
```

## Authentication

Currently no authentication required (development mode). Implement in production.

---

## Endpoints

### 1. Generate Video

**Endpoint:** `POST /api/generate`

**Description:** Start a background job to generate a video from Chinese text.

**Request Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "content": "大卫：你好，李军。\n李军：你好，大卫。",
  "speech_speed": 0.9,
  "delay": 0.2
}
```

**Request Parameters:**

| Parameter | Type | Range | Default | Required | Description |
|-----------|------|-------|---------|----------|-------------|
| content | string | 1-1000 chars | N/A | Yes | Chinese text (multi-line supported) |
| speech_speed | float | 0.1-2.0 | 0.9 | No | Speech playback speed |
| delay | float | 0-1 | 0.2 | No | Pause between sentences (seconds) |

**Response (202 Accepted):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Video generation started"
}
```

**Response (400 Bad Request):**
```json
{
  "error": "Content must be between 1 and 1000 characters"
}
```

**Response (500 Internal Server Error):**
```json
{
  "error": "Server error: [error details]"
}
```

**Example cURL:**
```bash
curl -X POST http://localhost:5000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "content": "大卫：你好\n李军：你好",
    "speech_speed": 0.9,
    "delay": 0.2
  }'
```

**Example JavaScript:**
```javascript
const response = await fetch('/api/generate', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    content: '大卫：你好\n李军：你好',
    speech_speed: 0.9,
    delay: 0.2
  })
});

const data = await response.json();
console.log(data.job_id); // Use for status checking
```

---

### 2. Check Job Status

**Endpoint:** `GET /api/status/<job_id>`

**Description:** Check the status of a video generation job.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| job_id | string | UUID from generate endpoint |

**Response (200 OK) - Pending:**
```json
{
  "status": "pending",
  "created_at": "2024-04-21T10:30:45.123456"
}
```

**Response (200 OK) - Completed:**
```json
{
  "status": "completed",
  "file_path": "uploads/550e8400-e29b-41d4-a716-446655440000.mp4",
  "completed_at": "2024-04-21T10:35:12.654321"
}
```

**Response (200 OK) - Failed:**
```json
{
  "status": "failed",
  "error": "FFmpeg command failed: [error details]"
}
```

**Response (404 Not Found):**
```json
{
  "error": "Job not found"
}
```

**Example cURL:**
```bash
curl -X GET http://localhost:5000/api/status/550e8400-e29b-41d4-a716-446655440000
```

**Example JavaScript (Polling):**
```javascript
const jobId = '550e8400-e29b-41d4-a716-446655440000';

const checkStatus = setInterval(async () => {
  const response = await fetch(`/api/status/${jobId}`);
  const job = await response.json();
  
  if (job.status === 'completed') {
    clearInterval(checkStatus);
    console.log('Video ready:', job.file_path);
  } else if (job.status === 'failed') {
    clearInterval(checkStatus);
    console.error('Generation failed:', job.error);
  } else {
    console.log('Still generating...');
  }
}, 2000); // Check every 2 seconds
```

---

### 3. Download Video

**Endpoint:** `GET /api/videos/<video_id>`

**Description:** Download or stream a generated video.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| video_id | string | Job ID from generate endpoint |

**Query Parameters:**

| Parameter | Type | Values | Default | Description |
|-----------|------|--------|---------|-------------|
| download | boolean | true/false | false | Force download instead of stream |

**Response (200 OK):**
- Video file (video/mp4)
- Status: 200 OK
- Header: `Content-Type: video/mp4`

**Response (404 Not Found):**
```json
{
  "error": "Video not found"
}
```

**Example cURL (Stream):**
```bash
curl -O http://localhost:5000/api/videos/550e8400-e29b-41d4-a716-446655440000
```

**Example cURL (Download):**
```bash
curl -O http://localhost:5000/api/videos/550e8400-e29b-41d4-a716-446655440000?download=true
```

**Example JavaScript:**
```javascript
const jobId = '550e8400-e29b-41d4-a716-446655440000';
const videoUrl = `/api/videos/${jobId}`;

// Stream in player
const video = document.getElementById('myVideo');
video.src = videoUrl;

// Download
const link = document.createElement('a');
link.href = `${videoUrl}?download=true`;
link.download = `video_${jobId.substring(0, 8)}.mp4`;
link.click();
```

---

### 4. Health Check

**Endpoint:** `GET /api/health`

**Description:** Check if the API is running and healthy.

**Response (200 OK):**
```json
{
  "status": "healthy"
}
```

**Example cURL:**
```bash
curl http://localhost:5000/api/health
```

**Example JavaScript:**
```javascript
async function isServerHealthy() {
  try {
    const response = await fetch('/api/health');
    const data = await response.json();
    return data.status === 'healthy';
  } catch (error) {
    return false;
  }
}
```

---

### 5. Cleanup Old Videos

**Endpoint:** `POST /api/cleanup`

**Description:** Remove videos older than 24 hours (admin endpoint).

**Response (200 OK):**
```json
{
  "cleaned": 5
}
```

**Example cURL:**
```bash
curl -X POST http://localhost:5000/api/cleanup
```

---

## Error Handling

### Error Response Format

All errors follow this format:

```json
{
  "error": "Human-readable error message"
}
```

### Common Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 400 | Bad Request | Check your request format and parameters |
| 404 | Not Found | Verify the job_id or video_id exists |
| 500 | Server Error | Check server logs, verify dependencies |
| 202 | Accepted | Job submitted successfully (expected for /api/generate) |

---

## Request/Response Examples

### Complete Workflow Example

**Step 1: Request video generation**
```bash
curl -X POST http://localhost:5000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "content": "大卫：你好\n李军：你好，大卫。\n大卫：今天天气怎么样？",
    "speech_speed": 1.0,
    "delay": 0.3
  }'
```

Response:
```json
{
  "job_id": "a1b2c3d4-e5f6-47a8-b9c0-d1e2f3a4b5c6",
  "status": "pending",
  "message": "Video generation started"
}
```

**Step 2: Check status (wait 1-2 minutes)**
```bash
curl http://localhost:5000/api/status/a1b2c3d4-e5f6-47a8-b9c0-d1e2f3a4b5c6
```

Response (after generation):
```json
{
  "status": "completed",
  "file_path": "uploads/a1b2c3d4-e5f6-47a8-b9c0-d1e2f3a4b5c6.mp4",
  "completed_at": "2024-04-21T10:35:12.654321"
}
```

**Step 3: Download video**
```bash
curl -O http://localhost:5000/api/videos/a1b2c3d4-e5f6-47a8-b9c0-d1e2f3a4b5c6?download=true
```

---

## Rate Limiting (Future)

Currently not implemented. Recommended for production:

```
Rate Limit: 10 requests per minute per IP
Burst Limit: 20 requests per minute
Job Timeout: 10 minutes
```

---

## Validation Rules

### Content Validation
- **Min length**: 1 character
- **Max length**: 1000 characters
- **Required**: Yes
- **Format**: Multi-line Chinese text (UTF-8)
- **Allowed**: Chinese characters, numbers, punctuation, line breaks

### Speech Speed Validation
- **Min**: 0.1
- **Max**: 2.0
- **Step**: 0.01
- **Type**: Float
- **Default**: 0.9

### Delay Validation
- **Min**: 0
- **Max**: 1
- **Step**: 0.01
- **Type**: Float
- **Default**: 0.2
- **Unit**: Seconds

---

## Performance Notes

### Expected Response Times

| Endpoint | Time | Notes |
|----------|------|-------|
| POST /api/generate | <100ms | Returns immediately with job_id |
| GET /api/status | <50ms | Instant status lookup |
| GET /api/videos | Varies | Depends on file size (1-10MB) |
| GET /api/health | <10ms | Quick health check |

### Video Generation Time
- Short text (100 chars): 1-2 minutes
- Medium text (500 chars): 2-4 minutes
- Long text (1000 chars): 4-5 minutes

---

## Best Practices

### 1. Polling Strategy
```javascript
// Poll every 2 seconds
setInterval(checkStatus, 2000);

// Or exponential backoff
let interval = 1000;
setInterval(() => {
  checkStatus();
  interval = Math.min(interval * 1.5, 5000);
}, interval);
```

### 2. Error Handling
```javascript
try {
  const response = await fetch('/api/generate', { /* ... */ });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error);
  }
  // Handle success
} catch (error) {
  console.error('API Error:', error.message);
}
```

### 3. Retry Logic
```javascript
async function generateWithRetry(maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await fetch('/api/generate', { /* ... */ });
      if (response.ok) return await response.json();
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await new Promise(r => setTimeout(r, 1000 * (i + 1)));
    }
  }
}
```

---

## Debugging

### Enable Verbose Logging
```bash
export FLASK_ENV=development
export FLASK_DEBUG=True
python app.py
```

### Check API Response Headers
```bash
curl -v http://localhost:5000/api/health
```

### View Request/Response Size
```bash
curl -w "\nSize: %{size_download} bytes\n" http://localhost:5000/api/health
```

---

## WebSocket (Future Enhancement)

For real-time updates instead of polling:

```javascript
// Coming in future version
const ws = new WebSocket('ws://localhost:5000/ws/status');
ws.onmessage = (event) => {
  const status = JSON.parse(event.data);
  console.log('Status update:', status);
};
```

---

## SDK Examples

### Python SDK Example
```python
import requests
import time

def generate_video(text, speed=0.9, delay=0.2):
    response = requests.post('http://localhost:5000/api/generate', json={
        'content': text,
        'speech_speed': speed,
        'delay': delay
    })
    return response.json()['job_id']

def wait_for_video(job_id, timeout=300):
    start = time.time()
    while time.time() - start < timeout:
        response = requests.get(f'http://localhost:5000/api/status/{job_id}')
        status = response.json()
        
        if status['status'] == 'completed':
            return status['file_path']
        elif status['status'] == 'failed':
            raise Exception(status['error'])
        
        time.sleep(2)
    raise TimeoutError('Video generation timed out')

# Usage
job_id = generate_video('大卫：你好')
file_path = wait_for_video(job_id)
print(f'Video ready at: {file_path}')
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024-04-21 | Initial release |

---

**API Documentation Complete! 📚**
