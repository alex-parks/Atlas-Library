# Todos API Documentation

## Overview

The Todos API provides comprehensive task management functionality for the Blacksmith Atlas system. It follows the same patterns and architecture as the existing Assets API, with full CRUD operations, ArangoDB integration, and enterprise-grade error handling.

## Base URL

All todos endpoints are prefixed with `/api/v1`

## Authentication

Currently, the API does not require authentication, but user_id can be passed to associate todos with specific users.

## Data Models

### TodoCreateRequest
```json
{
  "title": "string (required, 1-200 chars)",
  "description": "string (optional, max 1000 chars)",
  "completed": "boolean (default: false)",
  "priority": "string (default: 'medium')",
  "category": "string (optional, max 50 chars)",
  "due_date": "datetime (optional, ISO format)",
  "user_id": "string (optional)",
  "tags": ["array of strings (default: [])"]
}
```

### TodoUpdateRequest
```json
{
  "title": "string (optional, 1-200 chars)",
  "description": "string (optional, max 1000 chars)",
  "completed": "boolean (optional)",
  "priority": "string (optional)",
  "category": "string (optional, max 50 chars)",
  "due_date": "datetime (optional, ISO format)",
  "user_id": "string (optional)",
  "tags": ["array of strings (optional)"]
}
```

### TodoResponse
```json
{
  "id": "string (unique identifier)",
  "title": "string",
  "description": "string or null",
  "completed": "boolean",
  "priority": "string",
  "category": "string or null",
  "due_date": "datetime or null",
  "user_id": "string or null",
  "tags": ["array of strings"],
  "created_at": "string (ISO datetime)",
  "updated_at": "string (ISO datetime)"
}
```

## Priority Levels

- `low` - Low priority tasks
- `medium` - Medium priority tasks (default)
- `high` - High priority tasks
- `urgent` - Urgent tasks requiring immediate attention

## API Endpoints

### 1. List Todos

**GET** `/api/v1/todos`

Get all todos with optional filtering.

#### Query Parameters
- `user_id` (optional): Filter by user ID
- `completed` (optional): Filter by completion status (true/false)
- `category` (optional): Filter by category
- `priority` (optional): Filter by priority level
- `limit` (optional): Maximum number of results (default: 100)

#### Example Request
```bash
curl "http://localhost:8000/api/v1/todos?user_id=user123&completed=false&priority=high&limit=50"
```

#### Example Response
```json
[
  {
    "id": "abc123def456",
    "title": "Implement user authentication",
    "description": "Add JWT-based authentication system",
    "completed": false,
    "priority": "high",
    "category": "Development",
    "due_date": "2024-12-31T23:59:59",
    "user_id": "user123",
    "tags": ["backend", "security"],
    "created_at": "2024-01-15T10:30:00",
    "updated_at": "2024-01-15T10:30:00"
  }
]
```

### 2. Get Todo by ID

**GET** `/api/v1/todos/{todo_id}`

Get a specific todo by its ID.

#### Example Request
```bash
curl "http://localhost:8000/api/v1/todos/abc123def456"
```

#### Example Response
```json
{
  "id": "abc123def456",
  "title": "Implement user authentication",
  "description": "Add JWT-based authentication system",
  "completed": false,
  "priority": "high",
  "category": "Development",
  "due_date": "2024-12-31T23:59:59",
  "user_id": "user123",
  "tags": ["backend", "security"],
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00"
}
```

### 3. Create Todo

**POST** `/api/v1/todos`

Create a new todo.

#### Request Body
See TodoCreateRequest model above.

#### Example Request
```bash
curl -X POST "http://localhost:8000/api/v1/todos" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Fix critical bug",
    "description": "Resolve the memory leak in asset loading",
    "priority": "urgent",
    "category": "Bug Fix",
    "due_date": "2024-01-20T17:00:00",
    "user_id": "dev001",
    "tags": ["critical", "memory", "assets"]
  }'
```

#### Example Response
```json
{
  "id": "xyz789abc123",
  "title": "Fix critical bug",
  "description": "Resolve the memory leak in asset loading",
  "completed": false,
  "priority": "urgent",
  "category": "Bug Fix",
  "due_date": "2024-01-20T17:00:00",
  "user_id": "dev001",
  "tags": ["critical", "memory", "assets"],
  "created_at": "2024-01-15T14:22:33",
  "updated_at": "2024-01-15T14:22:33"
}
```

### 4. Update Todo

**PUT** `/api/v1/todos/{todo_id}`

Update an existing todo. Only provided fields will be updated.

#### Request Body
See TodoUpdateRequest model above.

#### Example Request
```bash
curl -X PUT "http://localhost:8000/api/v1/todos/xyz789abc123" \
  -H "Content-Type: application/json" \
  -d '{
    "completed": true,
    "description": "Memory leak fixed by optimizing asset cache"
  }'
```

#### Example Response
```json
{
  "id": "xyz789abc123",
  "title": "Fix critical bug",
  "description": "Memory leak fixed by optimizing asset cache",
  "completed": true,
  "priority": "urgent",
  "category": "Bug Fix",
  "due_date": "2024-01-20T17:00:00",
  "user_id": "dev001",
  "tags": ["critical", "memory", "assets"],
  "created_at": "2024-01-15T14:22:33",
  "updated_at": "2024-01-15T16:45:12"
}
```

### 5. Delete Todo

**DELETE** `/api/v1/todos/{todo_id}`

Delete a todo.

#### Example Request
```bash
curl -X DELETE "http://localhost:8000/api/v1/todos/xyz789abc123"
```

#### Example Response
```json
{
  "message": "Todo xyz789abc123 deleted successfully"
}
```

### 6. Toggle Todo Completion

**PATCH** `/api/v1/todos/{todo_id}/complete`

Toggle the completion status of a todo.

#### Example Request
```bash
curl -X PATCH "http://localhost:8000/api/v1/todos/abc123def456/complete"
```

#### Example Response
```json
{
  "message": "Todo marked as completed",
  "todo": {
    "id": "abc123def456",
    "title": "Implement user authentication",
    "completed": true,
    "priority": "high",
    "category": "Development",
    "created_at": "2024-01-15T10:30:00",
    "updated_at": "2024-01-15T16:50:22"
  }
}
```

### 7. Get Todo Statistics

**GET** `/api/v1/todos/stats/summary`

Get comprehensive statistics about todos.

#### Query Parameters
- `user_id` (optional): Get stats for specific user

#### Example Request
```bash
curl "http://localhost:8000/api/v1/todos/stats/summary?user_id=user123"
```

#### Example Response
```json
{
  "total_todos": 25,
  "completed": 18,
  "pending": 7,
  "high_priority": 3,
  "overdue": 1,
  "completion_rate": 72.0
}
```

### 8. Get Todo Categories

**GET** `/api/v1/todos/categories`

Get all available todo categories with usage counts.

#### Example Request
```bash
curl "http://localhost:8000/api/v1/todos/categories"
```

#### Example Response
```json
{
  "categories": ["Development", "Bug Fix", "Testing", "Documentation"],
  "count": 4,
  "details": [
    {"category": "Development", "count": 12},
    {"category": "Bug Fix", "count": 8},
    {"category": "Testing", "count": 3},
    {"category": "Documentation", "count": 2}
  ]
}
```

### 9. Get Todo Priorities

**GET** `/api/v1/todos/priorities`

Get priority distribution and available priority levels.

#### Example Request
```bash
curl "http://localhost:8000/api/v1/todos/priorities"
```

#### Example Response
```json
{
  "priorities": [
    {"priority": "high", "count": 5},
    {"priority": "low", "count": 3},
    {"priority": "medium", "count": 15},
    {"priority": "urgent", "count": 2}
  ],
  "available_priorities": ["low", "medium", "high", "urgent"]
}
```

## Error Responses

The API returns standard HTTP status codes:

- `200` - Success
- `400` - Bad Request (validation errors)
- `404` - Todo Not Found
- `500` - Internal Server Error
- `503` - Service Unavailable (database issues)

### Example Error Response
```json
{
  "detail": "Todo not found"
}
```

### Validation Error Response
```json
{
  "detail": "Invalid priority. Must be one of: low, medium, high, urgent"
}
```

## Database Integration

The Todos API uses ArangoDB for data persistence:

- **Collection**: `todos`
- **Database**: `blacksmith_atlas` (configurable via environment variables)
- **Queries**: Optimized AQL queries for filtering and statistics
- **Indexes**: Automatic indexing on commonly queried fields

### Environment Variables

- `ARANGO_HOST` - ArangoDB host (default: http://localhost:8529)
- `ARANGO_DATABASE` - Database name (default: blacksmith_atlas)
- `ARANGO_USER` - Username (default: root)
- `ARANGO_PASSWORD` - Password (default: empty)

## Integration with Assets API

The Todos API follows the same architectural patterns as the Assets API:

- FastAPI router with `/api/v1` prefix
- Pydantic models for request/response validation
- ArangoDB integration with proper error handling
- Consistent error responses and status codes
- Graceful degradation when database is unavailable

## Usage Examples

### Frontend Integration

```javascript
// Create a new todo
const createTodo = async (todoData) => {
  const response = await fetch('/api/v1/todos', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(todoData)
  });
  return response.json();
};

// Get user's todos
const getUserTodos = async (userId) => {
  const response = await fetch(`/api/v1/todos?user_id=${userId}&completed=false`);
  return response.json();
};

// Mark todo as complete
const completeTodo = async (todoId) => {
  const response = await fetch(`/api/v1/todos/${todoId}/complete`, {
    method: 'PATCH'
  });
  return response.json();
};
```

### CLI Integration

```bash
# Create a quick todo
curl -X POST http://localhost:8000/api/v1/todos \
  -H "Content-Type: application/json" \
  -d '{"title": "Review code", "priority": "high", "user_id": "dev001"}'

# Get pending todos
curl "http://localhost:8000/api/v1/todos?completed=false"

# Get project statistics
curl "http://localhost:8000/api/v1/todos/stats/summary"
```

## Testing

A test script is provided at `backend/test_todos_api.py` to validate the API structure and model definitions without requiring a running server.

```bash
cd backend
python test_todos_api.py
```

This validates:
- Model definitions and validation
- Router configuration
- Endpoint structure
- Response conversion functions

## Performance Considerations

- Database queries are optimized with proper AQL syntax
- Filtering is performed at the database level, not in application code
- Pagination is supported through the `limit` parameter  
- Statistics are calculated efficiently using ArangoDB's aggregation features
- Graceful handling of database unavailability

## Future Enhancements

Potential future features that could be added:

1. **Subtasks**: Hierarchical todo structure
2. **Attachments**: File attachments to todos
3. **Comments**: Discussion threads on todos
4. **Time Tracking**: Start/stop timers for todos
5. **Notifications**: Email/webhook notifications for due dates
6. **Templates**: Reusable todo templates
7. **Bulk Operations**: Batch create/update/delete
8. **Advanced Filtering**: Date ranges, full-text search
9. **Integration**: Link todos to specific assets or projects
10. **Reporting**: Advanced analytics and reporting