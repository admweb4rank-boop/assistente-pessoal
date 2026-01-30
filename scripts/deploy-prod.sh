#!/bin/bash
# =============================================================================
# Igor Assistant - Production Deployment Script
# =============================================================================
# Usage: ./scripts/deploy-prod.sh [options]
# Options:
#   --build       Force rebuild images
#   --migrate     Run database migrations
#   --rollback    Rollback to previous version
#   --health      Check health after deploy
# =============================================================================

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DEPLOY_DIR="/var/www/producao/assistente_igor"
BACKUP_DIR="/var/www/backups/igor"
COMPOSE_FILE="docker-compose.prod.yml"
LOG_FILE="/var/log/igor/deploy.log"
HEALTH_URL="http://localhost:8090/health"
MAX_HEALTH_RETRIES=30
HEALTH_RETRY_INTERVAL=2

# Functions
log() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} [${level}] ${message}" | tee -a "$LOG_FILE"
}

info() { log "INFO" "${BLUE}$@${NC}"; }
success() { log "SUCCESS" "${GREEN}$@${NC}"; }
warning() { log "WARNING" "${YELLOW}$@${NC}"; }
error() { log "ERROR" "${RED}$@${NC}"; }

check_requirements() {
    info "Checking requirements..."
    
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        error "Docker Compose is not installed"
        exit 1
    fi
    
    if [ ! -f "$DEPLOY_DIR/.env" ]; then
        error ".env file not found at $DEPLOY_DIR/.env"
        exit 1
    fi
    
    success "All requirements satisfied"
}

backup_current() {
    info "Creating backup of current deployment..."
    
    local backup_name="backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR/$backup_name"
    
    # Backup docker-compose file
    cp "$DEPLOY_DIR/$COMPOSE_FILE" "$BACKUP_DIR/$backup_name/" 2>/dev/null || true
    
    # Backup .env (without secrets)
    grep -v "KEY\|TOKEN\|SECRET\|PASSWORD" "$DEPLOY_DIR/.env" > "$BACKUP_DIR/$backup_name/.env.sanitized" 2>/dev/null || true
    
    # Save current image tags
    docker images --format "{{.Repository}}:{{.Tag}}" | grep igor > "$BACKUP_DIR/$backup_name/images.txt" 2>/dev/null || true
    
    # Keep only last 5 backups
    ls -dt "$BACKUP_DIR"/backup_* 2>/dev/null | tail -n +6 | xargs rm -rf 2>/dev/null || true
    
    success "Backup created: $backup_name"
}

pull_latest() {
    info "Pulling latest code..."
    cd "$DEPLOY_DIR"
    
    git fetch origin main
    git reset --hard origin/main
    
    success "Code updated to latest main"
}

build_images() {
    info "Building Docker images..."
    cd "$DEPLOY_DIR"
    
    docker compose -f "$COMPOSE_FILE" build --no-cache
    
    success "Images built successfully"
}

run_migrations() {
    info "Running database migrations..."
    
    # Execute migrations via backend container
    docker compose -f "$COMPOSE_FILE" run --rm backend python -c "
from app.core.config import settings
from supabase import create_client
import os

# Migrations are handled by Supabase
print('Migrations are managed via Supabase Dashboard')
print('Ensure all migrations are applied before deployment')
"
    
    success "Migration check complete"
}

deploy() {
    info "Deploying services..."
    cd "$DEPLOY_DIR"
    
    # Stop old containers gracefully
    docker compose -f "$COMPOSE_FILE" down --timeout 30
    
    # Start new containers
    docker compose -f "$COMPOSE_FILE" up -d
    
    success "Services deployed"
}

health_check() {
    info "Performing health check..."
    
    local retries=0
    while [ $retries -lt $MAX_HEALTH_RETRIES ]; do
        if curl -sf "$HEALTH_URL" > /dev/null 2>&1; then
            success "Health check passed!"
            
            # Get detailed health
            curl -s "$HEALTH_URL/detailed" | python3 -m json.tool 2>/dev/null || true
            return 0
        fi
        
        retries=$((retries + 1))
        info "Waiting for services... ($retries/$MAX_HEALTH_RETRIES)"
        sleep $HEALTH_RETRY_INTERVAL
    done
    
    error "Health check failed after $MAX_HEALTH_RETRIES attempts"
    return 1
}

rollback() {
    warning "Initiating rollback..."
    
    local latest_backup=$(ls -dt "$BACKUP_DIR"/backup_* 2>/dev/null | head -1)
    
    if [ -z "$latest_backup" ]; then
        error "No backup found for rollback"
        exit 1
    fi
    
    info "Rolling back to: $latest_backup"
    
    # Stop current containers
    docker compose -f "$COMPOSE_FILE" down
    
    # Restore previous images if available
    if [ -f "$latest_backup/images.txt" ]; then
        while read image; do
            docker pull "$image" 2>/dev/null || true
        done < "$latest_backup/images.txt"
    fi
    
    # Start containers
    docker compose -f "$COMPOSE_FILE" up -d
    
    success "Rollback complete"
}

cleanup() {
    info "Cleaning up..."
    
    # Remove unused images
    docker image prune -f
    
    # Remove unused volumes (be careful!)
    # docker volume prune -f
    
    # Clean up old logs
    find /var/log/igor -name "*.log" -mtime +30 -delete 2>/dev/null || true
    
    success "Cleanup complete"
}

print_summary() {
    echo ""
    echo "=========================================="
    echo "         DEPLOYMENT SUMMARY"
    echo "=========================================="
    echo ""
    docker compose -f "$COMPOSE_FILE" ps
    echo ""
    echo "Frontend: http://localhost:3000"
    echo "Backend:  http://localhost:8090"
    echo "API Docs: http://localhost:8090/docs"
    echo "Health:   http://localhost:8090/health"
    echo ""
    echo "=========================================="
}

# Main execution
main() {
    echo ""
    echo "=========================================="
    echo "    Igor Assistant - Production Deploy"
    echo "=========================================="
    echo ""
    
    local do_build=false
    local do_migrate=false
    local do_rollback=false
    local do_health=true
    
    # Parse arguments
    for arg in "$@"; do
        case $arg in
            --build)
                do_build=true
                ;;
            --migrate)
                do_migrate=true
                ;;
            --rollback)
                do_rollback=true
                ;;
            --no-health)
                do_health=false
                ;;
            *)
                warning "Unknown option: $arg"
                ;;
        esac
    done
    
    # Create log directory
    mkdir -p "$(dirname "$LOG_FILE")"
    mkdir -p "$BACKUP_DIR"
    
    if $do_rollback; then
        rollback
        if $do_health; then
            health_check || exit 1
        fi
        exit 0
    fi
    
    check_requirements
    backup_current
    pull_latest
    
    if $do_build; then
        build_images
    fi
    
    if $do_migrate; then
        run_migrations
    fi
    
    deploy
    
    if $do_health; then
        sleep 5
        if ! health_check; then
            error "Deployment failed health check"
            warning "Consider running: $0 --rollback"
            exit 1
        fi
    fi
    
    cleanup
    print_summary
    
    success "Deployment completed successfully! 🚀"
}

# Run main function
main "$@"
