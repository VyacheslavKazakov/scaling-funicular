#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "  Math API Microservice Launcher"
echo "=========================================="
echo ""

# Function to print colored messages
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check if Docker is installed
echo "Checking prerequisites..."
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed"
    echo ""
    echo "To install Docker on Ubuntu 22.04, run:"
    echo "  curl -fsSL https://get.docker.com -o get-docker.sh"
    echo "  sudo sh get-docker.sh"
    echo "  sudo usermod -aG docker \$USER"
    echo "  newgrp docker"
    exit 1
fi
print_success "Docker is installed ($(docker --version))"

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    print_error "Docker Compose is not installed"
    echo ""
    echo "To install Docker Compose on Ubuntu 22.04, run:"
    echo "  sudo apt-get update"
    echo "  sudo apt-get install -y docker-compose-plugin"
    exit 1
fi

# Determine which docker compose command to use
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
    print_success "Docker Compose is installed ($(docker compose version --short))"
else
    DOCKER_COMPOSE="docker-compose"
    print_success "Docker Compose is installed ($(docker-compose --version))"
fi

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    print_error "Docker daemon is not running"
    echo ""
    echo "Start Docker with:"
    echo "  sudo systemctl start docker"
    exit 1
fi
print_success "Docker daemon is running"

# Check if user has Docker permissions
if ! docker ps &> /dev/null; then
    print_error "Current user doesn't have permissions to use Docker"
    echo ""
    echo "Add yourself to the docker group:"
    echo "  sudo usermod -aG docker \$USER"
    echo "  newgrp docker"
    echo ""
    echo "Or run this script with sudo (not recommended)"
    exit 1
fi
print_success "User has Docker permissions"

# Check for required files
echo ""
echo "Checking required files..."

if [ ! -f "docker-compose.yml" ]; then
    print_error "docker-compose.yml not found"
    exit 1
fi
print_success "docker-compose.yml exists"

if [ ! -f "Dockerfile" ]; then
    print_error "Dockerfile not found"
    exit 1
fi
print_success "Dockerfile exists"

if [ ! -f "uv.lock" ]; then
    print_error "uv.lock not found - run 'uv lock' first"
    exit 1
fi
print_success "uv.lock exists"

if [ ! -f ".env" ]; then
    print_error ".env file not found"
    echo ""
    if [ -f ".env.example" ]; then
        echo "Creating .env from .env.example..."
        cp .env.example .env
        print_warning ".env file created from template"
        print_warning "IMPORTANT: Edit .env file and set your OpenAI API key!"
        echo ""
        read -p "Press Enter after you've configured .env, or Ctrl+C to exit..."
    else
        echo "Please create .env file with required variables:"
        echo "  MODEL=gpt-5-mini"
        echo "  KEY=your-openai-api-key"
        exit 1
    fi
fi
print_success ".env file exists"

# Check if OpenAI key is set
if grep -q "KEY=dummy" .env || grep -q "KEY=your-openai-api-key" .env; then
    print_warning "OpenAI API key appears to be a placeholder!"
    echo "The service will start but may not work correctly."
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Please edit .env file and set your OpenAI API key"
        exit 1
    fi
fi

echo ""
echo "=========================================="
echo "  Starting Microservice"
echo "=========================================="
echo ""

# Stop any existing containers
if $DOCKER_COMPOSE ps -q | grep -q .; then
    print_warning "Stopping existing containers..."
    $DOCKER_COMPOSE down
fi

# Build and start services
print_success "Building Docker images..."
$DOCKER_COMPOSE build

echo ""
print_success "Starting services..."
$DOCKER_COMPOSE up -d

echo ""
echo "Waiting for services to become healthy..."
for i in {1..30}; do
    if $DOCKER_COMPOSE ps | grep -q "healthy"; then
        break
    fi
    echo -n "."
    sleep 2
done
echo ""

# Check service status
echo ""
echo "=========================================="
echo "  Service Status"
echo "=========================================="
$DOCKER_COMPOSE ps

# Test if API is accessible
echo ""
echo "Testing API endpoint..."

# Retry logic: try up to 30 times with 2 second intervals (1 minute total)
MAX_ATTEMPTS=30
ATTEMPT=0
API_READY=false

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    ATTEMPT=$((ATTEMPT + 1))

    if curl -s -f http://localhost:8008/api/v1/healthcheck/ > /dev/null 2>&1; then
        API_READY=true
        break
    fi

    echo -n "."
    sleep 2
done
echo ""

if [ "$API_READY" = true ]; then
    print_success "API is accessible!"
    echo ""
    echo "=========================================="
    echo "  Service Ready!"
    echo "=========================================="
    echo ""
    echo "API Documentation: http://localhost:8008/api/v1/docs"
    echo "Health Check:      http://localhost:8008/api/v1/healthcheck/"
    echo "Answer Endpoint:   http://localhost:8008/get_answer/?question=<your-question>"
    echo ""
    echo "Example:"
    echo '  curl "http://localhost:8008/get_answer/?question=What%20is%202%20plus%202"'
    echo ""
    echo "To view logs:"
    echo "  $DOCKER_COMPOSE logs -f"
    echo ""
    echo "To stop services:"
    echo "  $DOCKER_COMPOSE down"
else
    print_error "API is not responding after $MAX_ATTEMPTS attempts"
    echo ""
    echo "Check logs with:"
    echo "  $DOCKER_COMPOSE logs"
    exit 1
fi
