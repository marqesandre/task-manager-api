# Task Manager API

A RESTful API for task management built with Flask, MongoDB, and Redis.

## Features

- JWT Authentication with Redis
- Task CRUD operations
- MongoDB for data persistence
- Prometheus metrics
- Docker support

## Setup

1. Clone the repository
2. Copy `.env.example` to `.env` and configure variables
3. Run with Docker:

```bash
docker-compose up --build
```

## API Endpoints

### Authentication
- POST /auth/login - Login with email and password
- POST /auth/logout - Logout (invalidates token)

### Tasks
- GET /tasks - List all tasks
- POST /tasks - Create new task
- GET /tasks/{id} - Get task details
- PUT /tasks/{id} - Update task
- DELETE /tasks/{id} - Delete task

### Monitoring
- GET /metrics - Prometheus metrics

## Testing

Run tests with:

```bash
pytest
```

## Security

- Passwords are hashed using bcrypt
- JWT tokens expire after 5 minutes
- Environment variables for sensitive data
