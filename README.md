# Scaling Funicular

Math API assistant powered by AI for solving mathematical problems through code generation and safe execution.

## Overview

This service provides a REST API that solves mathematical problems using Large Language Models (LLMs). When a user submits a math problem, the AI analyzes it, generates Python code to solve it, executes the code in a secure sandbox, and returns the result.

## Architecture & Approach

### How Math Problems Are Solved

1. **Question Reception**: User sends a mathematical question via HTTP GET request
2. **LLM Analysis**: OpenAI's model (via LangChain) analyzes the problem and generates appropriate Python code
3. **Code Generation**: The LLM writes a complete Python function with necessary imports and logic
4. **Security Validation**: The generated code is parsed and validated against a whitelist of allowed modules
5. **Safe Execution**: Code runs in a sandboxed environment with restricted builtins and no access to system resources
6. **Result Caching**: Successful results are cached in Redis to improve performance for repeated queries
7. **Response**: The computed answer is returned to the user

### Technology Stack & Rationale

| Technology | Purpose | Why This Choice |
|------------|---------|-----------------|
| **FastAPI** | Web framework | High performance, automatic API documentation, async support, built-in validation |
| **LangChain & LangGraph** | LLM orchestration | Provides tools/agent framework for structured LLM interactions and function calling |
| **OpenAI API** | LLM provider | State-of-the-art language models with strong mathematical reasoning capabilities |
| **Redis** | Caching layer | Fast in-memory storage for caching identical queries, reduces API costs and latency |
| **Pydantic** | Data validation | Type-safe configuration and request/response schemas with automatic validation |
| **Docker** | Containerization | Ensures consistent deployment across environments, simplifies dependency management |
| **uvicorn** | ASGI server | High-performance async server optimized for Python async applications |
| **uv** | Package manager | Fast, modern Python package manager with deterministic dependency resolution |

### Security Features

- **Sandboxed Code Execution**: Only whitelisted Python modules allowed (math, statistics, itertools, etc.)
- **Restricted Builtins**: Limited set of safe built-in functions, no file I/O or system access
- **AST Validation**: Code is parsed and validated before execution
- **No Dangerous Imports**: Blocks os, sys, subprocess, socket, requests, and other system modules

## Prerequisites

### For Docker Deployment (Recommended)

- **Docker** (version 20.10 or higher)
- **Docker Compose** (version 2.0 or higher)
- **OpenAI API Key** (required for LLM functionality)

### For Local Development

- **Python 3.13** or higher
- **uv** package manager ([installation guide](https://github.com/astral-sh/uv))
- **Redis** server (or use Docker for Redis only)
- **OpenAI API Key**

## Installation & Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd scaling-funicular
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# .env file
MODEL=gpt-5-mini
KEY=your-openai-api-key-here
ENV=dev
LOG_LEVEL=INFO
DEBUG=false
WORKERS=1

# Redis configuration (defaults work with docker-compose)
CACHE_HOST=cachedb
CACHE_PORT=6379
CACHE_DB=1
CACHE_TTL_IN_SECONDS=60
```

### 3. Running with Docker Compose (Recommended)

```bash
# Build and start all services
docker-compose up --build

# Or run in detached mode
docker-compose up -d --build
```

The API will be available at `http://localhost:8008`

### 4. Running Locally (Development)

```bash
# Install dependencies
uv sync --locked

# Start Redis (if not using Docker)
redis-server

# Update .env for local Redis
# CACHE_HOST=localhost

# Run the application
uv run python main.py
```

## API Usage

### Interactive Documentation

Once the service is running, access the auto-generated API documentation:

- **Swagger UI**: http://localhost:8008/api/v1/docs
- **OpenAPI JSON**: http://localhost:8008/api/v1/docs.json

### Endpoints

#### 1. Solve Math Problem

```http
GET /get_answer/?question=<your-math-question>
```

**Example Request:**

```bash
curl "http://localhost:8008/get_answer/?question=What%20is%20the%20derivative%20of%20x%5E2%20at%20x=3"
```

**Example Response:**

```json
{
  "answer": 6
}
```

#### 2. Health Check

```http
GET /api/v1/healthcheck/
```

**Response:**

```json
{
  "data": {
    "status": "ok"
  }
}
```

### Example Questions

```bash
# Basic arithmetic
curl "http://localhost:8008/get_answer/?question=Calculate%20the%20factorial%20of%2010"

# Geometry
curl "http://localhost:8008/get_answer/?question=Find%20the%20area%20of%20a%20circle%20with%20radius%205"

# Statistics
curl "http://localhost:8008/get_answer/?question=Calculate%20the%20mean%20and%20standard%20deviation%20of%20[1,2,3,4,5,6,7,8,9,10]"

# Linear algebra
curl "http://localhost:8008/get_answer/?question=Calculate%20the%20dot%20product%20of%20vectors%20[1,2,3]%20and%20[4,5,6]"

# Calculus
curl "http://localhost:8008/get_answer/?question=Approximate%20the%20integral%20of%20x^2%20from%200%20to%201%20using%20100%20intervals"
```

## Configuration

All configuration is managed through environment variables. See `src/core/config.py` for available options:

| Variable | Default      | Description |
|----------|--------------|-------------|
| `MODEL` | `gpt-5-mini` | OpenAI model to use |
| `KEY` | -            | OpenAI API key (required) |
| `LISTEN_ADDR` | `0.0.0.0`    | Server bind address |
| `LISTEN_PORT` | `8008`       | Server port |
| `CACHE_HOST` | `cachedb`    | Redis host |
| `CACHE_PORT` | `6379`       | Redis port |
| `CACHE_DB` | `1`          | Redis database number |
| `CACHE_TTL_IN_SECONDS` | `60`         | Cache expiration time |
| `WORKERS` | `1`          | Number of uvicorn workers |
| `DEBUG` | `false`      | Enable debug mode |
| `LOG_LEVEL` | `INFO`       | Logging level |

## Development

### Code Quality Tools

The project uses:

- **ruff**: Linting and code formatting
- **mypy**: Static type checking
- **pre-commit**: Git hooks for code quality

```bash
# Install dev dependencies
uv sync --group dev

# Run linter
uv run ruff check .

# Run type checker
uv run mypy .

# Setup pre-commit hooks
uv run pre-commit install
```

### Testing

The project includes comprehensive tests for security validation and code execution.

**Run all tests:**

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v
```

**Run tests with coverage:**

```bash
# Run with coverage report in terminal
uv run pytest --cov=src --cov-report=term-missing

# Generate HTML coverage report
uv run pytest --cov=src --cov-report=html

# Then open htmlcov/index.html in your browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux

# Coverage for specific module
uv run pytest --cov=src/api/v1/answers --cov-report=term-missing

# Detailed coverage with verbose test output
uv run pytest --cov=src --cov-report=term-missing -v
```

**Example coverage output:**

```
---------- coverage: platform darwin, python 3.13.7 -----------
Name                                   Stmts   Miss  Cover   Missing
--------------------------------------------------------------------
src/api/v1/answers/handlers.py           15      0   100%
src/api/v1/answers/routers.py            12      0   100%
src/api/v1/answers/services.py           10      0   100%
src/api/v1/answers/tools.py              25      2    92%   45-46
src/api/v1/answers/helpers.py            48      2    96%   67-68
--------------------------------------------------------------------
TOTAL                                    200     15    93%
```

**Test Structure:**

```
tests/
├── test_security_validator.py      # AST security validation tests (12 tests)
├── test_safe_execute_code.py       # Code execution sandbox tests (21 tests)
├── test_llm_handler.py              # LLM handler with mocks (7 tests)
├── test_routers.py                  # API endpoint tests (13 tests)
└── test_services.py                 # Service layer tests (10 tests)
```

### Project Structure

```
scaling-funicular/
├── main.py                          # Application entry point
├── src/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── answers/            # Math solving endpoints
│   │   │   │   ├── routers.py      # FastAPI routes
│   │   │   │   ├── services.py     # Business logic
│   │   │   │   ├── handlers.py     # LLM integration
│   │   │   │   ├── prompts.py      # LLM system prompts
│   │   │   │   └── schemas.py      # Request/response models
│   │   │   └── healthcheck/        # Health check endpoints
│   │   └── schemas.py              # Base API schemas
│   ├── core/
│   │   ├── config.py               # Configuration management
│   │   ├── logger.py               # Logging configuration
│   │   └── limiters.py             # Rate limiting
│   ├── db/
│   │   └── caches.py               # Redis cache implementation
│   └── constants.py                # Application constants
├── tests/                          # Tests
├── Dockerfile                      # Container definition
├── docker-compose.yml              # Multi-container orchestration
├── pyproject.toml                  # Project dependencies
├── pytest.ini                      # Pytest configuration
└── README.md                       # This file
```

## Allowed Python Modules in Sandbox

For security, only the following modules are available during code execution:

- **math**: Mathematical functions (sin, cos, sqrt, pi, etc.)
- **cmath**: Complex number mathematics
- **fractions**: Rational number arithmetic
- **decimal**: Decimal arithmetic
- **itertools**: Iterator tools (combinations, permutations, etc.)
- **functools**: Higher-order functions (reduce, partial, etc.)
- **operator**: Standard operators as functions
- **statistics**: Statistical functions (mean, median, stdev, etc.)
- **random**: Random number generation

Plus a restricted set of built-in functions (len, sum, min, max, range, etc.)

## Troubleshooting

### Common Issues

**Issue**: "Connection refused" errors
- **Solution**: Ensure Redis is running and `CACHE_HOST` is correctly configured

**Issue**: "Invalid API key" errors
- **Solution**: Verify your OpenAI API key is correctly set in the `.env` file

**Issue**: "Model not found" errors
- **Solution**: Check that the `MODEL` environment variable uses a valid OpenAI model name

**Issue**: Docker container fails to start
- **Solution**: Run `docker-compose logs app` to see detailed error messages

### Viewing Logs

```bash
# Docker logs
docker-compose logs -f app

# Local logs
# Logs are output to stdout/stderr
```

## License

This project is available for educational and demonstration purposes.
