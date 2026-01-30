#!/bin/bash

# Deploy Script - TB Personal OS
# Usage: ./scripts/deploy.sh [environment]

set -e  # Exit on error

ENVIRONMENT=${1:-production}
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/www/producao/assistente_igor/backups"

echo "🚀 Starting deployment to $ENVIRONMENT..."
echo "📅 Timestamp: $TIMESTAMP"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if running as correct user
if [ "$USER" != "root" ] && [ "$USER" != "www-data" ]; then
    print_warning "Consider running as www-data or root"
fi

# 1. Backup current deployment
print_status "Creating backup..."
mkdir -p "$BACKUP_DIR"
tar -czf "$BACKUP_DIR/backup_$TIMESTAMP.tar.gz" \
    --exclude='node_modules' \
    --exclude='venv' \
    --exclude='.git' \
    --exclude='logs' \
    -C /var/www/producao assistente_igor

# 2. Pull latest code (if using git)
if [ -d ".git" ]; then
    print_status "Pulling latest code..."
    git pull origin main
fi

# 3. Backend deployment
print_status "Deploying backend..."
cd backend

# Install/update dependencies
if [ -d "venv" ]; then
    source venv/bin/activate
else
    python3 -m venv venv
    source venv/bin/activate
fi

pip install --upgrade pip
pip install -r requirements.txt

# Run database migrations (if using Alembic)
if [ -f "alembic.ini" ]; then
    print_status "Running database migrations..."
    alembic upgrade head
fi

# 4. Frontend deployment
print_status "Deploying frontend..."
cd ../frontend

# Install dependencies
npm ci --production=false

# Build
npm run build

# 5. ML Service deployment
print_status "Deploying ML service..."
cd ../ml-service

if [ -d "venv" ]; then
    source venv/bin/activate
else
    python3 -m venv venv
    source venv/bin/activate
fi

pip install --upgrade pip
pip install -r requirements.txt

# 6. Restart services
print_status "Restarting services..."

# Using systemd
if command -v systemctl &> /dev/null; then
    sudo systemctl restart assistant-backend
    sudo systemctl restart assistant-ml-service
    sudo systemctl restart assistant-frontend  # if serving with systemd
    print_status "Services restarted via systemd"
    
# Using Docker Compose
elif [ -f "../docker-compose.yml" ]; then
    cd ..
    docker-compose down
    docker-compose up -d --build
    print_status "Services restarted via Docker Compose"
    
# Using PM2
elif command -v pm2 &> /dev/null; then
    pm2 restart all
    print_status "Services restarted via PM2"
else
    print_warning "Could not detect service manager. Please restart services manually."
fi

# 7. Health checks
print_status "Running health checks..."
sleep 5  # Wait for services to start

# Check backend
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    print_status "Backend is healthy"
else
    print_error "Backend health check failed!"
    exit 1
fi

# Check frontend (if applicable)
if curl -f http://localhost:3000 > /dev/null 2>&1; then
    print_status "Frontend is healthy"
else
    print_warning "Frontend health check failed (might be served differently)"
fi

# 8. Cleanup old backups (keep last 10)
print_status "Cleaning old backups..."
cd "$BACKUP_DIR"
ls -t | tail -n +11 | xargs -r rm

# 9. Send deployment notification (Telegram)
if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$TELEGRAM_CHAT_ID" ]; then
    MESSAGE="🚀 Deployment completed successfully!%0AEnvironment: $ENVIRONMENT%0ATimestamp: $TIMESTAMP"
    curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" \
        -d "chat_id=$TELEGRAM_CHAT_ID" \
        -d "text=$MESSAGE" \
        > /dev/null
fi

echo ""
print_status "Deployment completed successfully! 🎉"
echo ""
echo "Services:"
echo "  - Backend: http://localhost:8000"
echo "  - Frontend: http://localhost:3000"
echo "  - ML Service: http://localhost:8001"
echo ""
echo "Backup saved to: $BACKUP_DIR/backup_$TIMESTAMP.tar.gz"
echo ""
