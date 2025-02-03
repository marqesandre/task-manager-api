# Task Manager API

A robust RESTful API built with Flask for task management with user authentication.

## Features

- User authentication with JWT tokens
- Redis session management
- MongoDB for data persistence
- Password reset via email
- CRUD operations for tasks
- Docker containerization
- Redis caching for optimized performance
- Metrics endpoint for monitoring
- Unit and integration tests

## Tech Stack

- Python 3.9+
- Flask
- MongoDB
- Redis
- Docker & Docker Compose
- JWT for authentication
- pytest for testing

## Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── models/
│   ├── routes/
│   ├── services/
│   └── utils/
├── tests/
├── docker/
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Setup

1. Clone the repository
2. Copy `.env.example` to `.env` and configure your environment variables
3. Run with Docker:
   ```bash
   docker-compose up --build
   ```

## API Documentation

### Authentication Endpoints

- POST /api/auth/register - Register new user
- POST /api/auth/login - Login user
- POST /api/auth/logout - Logout user
- POST /api/auth/reset-password - Request password reset
- POST /api/auth/reset-password/{token} - Reset password with token

### Task Endpoints

- GET /api/tasks - List all tasks
- POST /api/tasks - Create new task
- GET /api/tasks/{id} - Get task details
- PUT /api/tasks/{id} - Update task
- DELETE /api/tasks/{id} - Delete task

### Monitoring

- GET /api/metrics - Get API metrics

## Development

### Running Tests

```bash
pytest
```

### Environment Variables

Required environment variables:

- MONGODB_URI
- REDIS_URI
- JWT_SECRET_KEY
- MAIL_SERVER
- MAIL_PORT
- MAIL_USERNAME
- MAIL_PASSWORD
- MAIL_USE_TLS

## License

MIT License
