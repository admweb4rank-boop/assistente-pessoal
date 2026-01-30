# 📚 Igor Assistant - API Documentation

## Overview

Igor is a personal AI assistant with comprehensive integrations for Google services, task management, health tracking, and autonomous intelligence.

**Base URL:** `http://localhost:8090/api/v1`

**Authentication:** JWT Bearer Token + Supabase Auth

---

## 🔐 Authentication

### Headers Required

```http
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

---

## 📍 Endpoints Summary

| Category | Endpoints | Description |
|----------|-----------|-------------|
| 🏥 Health Check | 3 | System health monitoring |
| 📥 Inbox | 6 | Message and inbox management |
| ✅ Tasks | 8 | Task CRUD and completion |
| 📁 Projects | 7 | Project management |
| 📅 Calendar | 6 | Google Calendar integration |
| 📧 Gmail | 8 | Email management |
| 📂 Drive | 6 | File management |
| ✍️ Content | 5 | AI content generation |
| 💰 Finance | 8 | Financial tracking |
| 🧠 Memory | 6 | Context and memory |
| 💡 Insights | 6 | Analytics and patterns |
| 🤖 Autonomy | 6 | Autonomous actions |
| 🏋️ Health Tracking | 12 | Personal health monitoring |

**Total: 122+ Endpoints**

---

## 🏥 Health Check Endpoints

### GET `/health`
Basic health check.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### GET `/health/detailed`
Detailed component health status.

**Response:**
```json
{
  "status": "healthy",
  "components": {
    "database": { "status": "healthy", "latency_ms": 15 },
    "redis": { "status": "healthy", "latency_ms": 2 },
    "gemini": { "status": "healthy", "latency_ms": 150 },
    "telegram": { "status": "healthy" }
  },
  "uptime_seconds": 86400
}
```

---

## 📥 Inbox Endpoints

### GET `/inbox`
Get inbox messages with pagination.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| page | int | 1 | Page number |
| per_page | int | 20 | Items per page |
| status | string | all | Filter: pending, processed, archived |

### POST `/inbox`
Create new inbox message.

**Body:**
```json
{
  "content": "Message content",
  "source": "telegram|web|api",
  "priority": "low|medium|high"
}
```

### POST `/inbox/process`
Process inbox message with AI.

**Body:**
```json
{
  "message_id": "uuid",
  "action": "classify|extract|respond"
}
```

---

## ✅ Tasks Endpoints

### GET `/tasks`
Get all tasks with filters.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| status | string | pending, completed, all |
| priority | string | low, medium, high |
| project_id | uuid | Filter by project |
| due_date | date | Filter by due date |
| sort | string | created_at, due_date, priority |

### POST `/tasks`
Create new task.

**Body:**
```json
{
  "title": "Task title",
  "description": "Optional description",
  "due_date": "2024-01-20T10:00:00Z",
  "priority": "medium",
  "project_id": "uuid",
  "estimated_minutes": 30,
  "tags": ["work", "urgent"]
}
```

### PUT `/tasks/{id}`
Update task.

### DELETE `/tasks/{id}`
Delete task.

### POST `/tasks/{id}/complete`
Mark task as complete.

### POST `/tasks/suggest`
Get AI task suggestions based on context.

### POST `/tasks/batch`
Batch operations on multiple tasks.

---

## 📅 Calendar Endpoints

### GET `/calendar/events`
Get calendar events.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| start_date | datetime | Range start |
| end_date | datetime | Range end |
| calendar_id | string | Specific calendar |

### POST `/calendar/events`
Create calendar event.

**Body:**
```json
{
  "title": "Meeting",
  "description": "Weekly sync",
  "start_time": "2024-01-15T14:00:00Z",
  "end_time": "2024-01-15T15:00:00Z",
  "attendees": ["email@example.com"],
  "location": "Zoom",
  "reminders": [10, 30]
}
```

### PUT `/calendar/events/{id}`
Update event.

### DELETE `/calendar/events/{id}`
Delete event.

### GET `/calendar/free-slots`
Find free time slots.

### POST `/calendar/sync`
Force calendar sync.

---

## 📧 Gmail Endpoints

### GET `/gmail/messages`
Get email messages.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| query | string | Gmail search query |
| max_results | int | Maximum results |
| label | string | Filter by label |

### GET `/gmail/messages/{id}`
Get specific email.

### POST `/gmail/send`
Send email.

**Body:**
```json
{
  "to": ["recipient@example.com"],
  "cc": [],
  "subject": "Email subject",
  "body": "Email body content",
  "html": false
}
```

### POST `/gmail/draft`
Create draft.

### DELETE `/gmail/messages/{id}`
Delete/trash email.

### POST `/gmail/labels`
Manage labels.

### GET `/gmail/summary`
AI summary of recent emails.

---

## 📂 Drive Endpoints

### GET `/drive/files`
List files.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| folder_id | string | Parent folder |
| query | string | Search query |
| mime_type | string | Filter by type |

### GET `/drive/files/{id}`
Get file metadata.

### POST `/drive/files/upload`
Upload file.

### DELETE `/drive/files/{id}`
Delete file.

### POST `/drive/files/{id}/share`
Share file.

### GET `/drive/files/{id}/download`
Download file.

---

## ✍️ Content Endpoints

### POST `/content/generate`
Generate content with AI.

**Body:**
```json
{
  "type": "email|post|article|summary",
  "context": "Context for generation",
  "tone": "formal|casual|professional",
  "length": "short|medium|long"
}
```

### POST `/content/variations`
Generate content variations.

### POST `/content/improve`
Improve existing content.

### POST `/content/summarize`
Summarize text.

### GET `/content/templates`
Get content templates.

---

## 💰 Finance Endpoints

### GET `/finance/transactions`
Get transactions.

### POST `/finance/transactions`
Create transaction.

**Body:**
```json
{
  "amount": 150.00,
  "type": "income|expense",
  "category": "salary|food|transport",
  "description": "Description",
  "date": "2024-01-15"
}
```

### GET `/finance/summary`
Get financial summary.

### GET `/finance/budget`
Get budget status.

### POST `/finance/budget`
Set budget.

### GET `/finance/goals`
Get financial goals.

### POST `/finance/goals`
Create financial goal.

### GET `/finance/insights`
AI financial insights.

---

## 🧠 Memory Endpoints

### GET `/memory/context`
Get current context.

### POST `/memory/store`
Store memory.

**Body:**
```json
{
  "type": "preference|fact|interaction",
  "content": "User prefers morning meetings",
  "importance": 0.8
}
```

### GET `/memory/search`
Search memories.

### DELETE `/memory/{id}`
Forget memory.

### GET `/memory/summary`
Get memory summary.

### POST `/memory/consolidate`
Consolidate memories.

---

## 💡 Insights Endpoints

### GET `/insights/dashboard`
Get insights dashboard.

### GET `/insights/patterns`
Get behavior patterns.

### GET `/insights/predictions`
Get predictions.

### GET `/insights/recommendations`
Get recommendations.

### GET `/insights/score`
Get productivity score.

### POST `/insights/analyze`
Analyze specific data.

---

## 🤖 Autonomy Endpoints

### GET `/autonomy/queue`
Get pending autonomous actions.

### POST `/autonomy/execute`
Execute autonomous action.

### GET `/autonomy/history`
Get action history.

### PUT `/autonomy/preferences`
Set autonomy preferences.

### GET `/autonomy/suggestions`
Get proactive suggestions.

### POST `/autonomy/learn`
Submit learning feedback.

---

## 🏋️ Health Tracking Endpoints

### GET `/health/checkins`
Get check-in history.

### POST `/health/checkins`
Create check-in.

**Body:**
```json
{
  "mood": 4,
  "energy": 3,
  "stress": 2,
  "sleep_hours": 7.5,
  "sleep_quality": 4,
  "notes": "Feeling good today"
}
```

### GET `/health/goals`
Get health goals.

### POST `/health/goals`
Create health goal.

### GET `/health/correlations`
Get health correlations.

### GET `/health/trends`
Get health trends.

### GET `/health/summary`
Get health summary.

### POST `/health/reminders`
Set health reminders.

---

## 🔴 Error Responses

### Standard Error Format

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": {}
  },
  "request_id": "uuid",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| UNAUTHORIZED | 401 | Invalid/missing token |
| FORBIDDEN | 403 | Insufficient permissions |
| NOT_FOUND | 404 | Resource not found |
| VALIDATION_ERROR | 422 | Invalid request data |
| RATE_LIMITED | 429 | Too many requests |
| INTERNAL_ERROR | 500 | Server error |
| SERVICE_UNAVAILABLE | 503 | External service down |

---

## 📊 Rate Limits

| Endpoint Type | Limit |
|---------------|-------|
| General | 60 req/min |
| AI Generation | 20 req/min |
| File Upload | 10 req/min |
| Auth | 10 req/min |

---

## 🔗 Webhooks

### Supported Events

- `task.created`
- `task.completed`
- `inbox.received`
- `calendar.event.created`
- `autonomy.action.executed`

### Webhook Payload

```json
{
  "event": "task.completed",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {},
  "signature": "sha256=..."
}
```

---

## 📱 Telegram Commands

| Command | Description |
|---------|-------------|
| `/start` | Initialize bot |
| `/ajuda` | Show help |
| `/tarefas` | List tasks |
| `/nova` | Create task |
| `/inbox` | Show inbox |
| `/calendario` | Show calendar |
| `/rotina` | Execute routine |
| `/saude` | Health status |
| `/checkin` | Create check-in |
| `/metas` | Health goals |
| `/projetos` | List projects |
| `/financas` | Financial summary |
| `/insights` | Get insights |

**Total: 29 Commands**

---

## 🔧 SDK Examples

### Python

```python
import requests

client = IgorClient(api_key="your_key")

# Create task
task = client.tasks.create(
    title="Review docs",
    due_date="2024-01-20",
    priority="high"
)

# Get insights
insights = client.insights.dashboard()
```

### JavaScript

```javascript
const igor = new IgorClient({ apiKey: 'your_key' });

// Create task
const task = await igor.tasks.create({
  title: 'Review docs',
  dueDate: '2024-01-20',
  priority: 'high'
});

// Get insights
const insights = await igor.insights.dashboard();
```

---

## 📞 Support

- **Documentation:** https://docs.igor.assistant
- **GitHub Issues:** https://github.com/igor-assistant/issues
- **Email:** support@igor.assistant
