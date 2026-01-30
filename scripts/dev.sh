#!/bin/bash

# TB Personal OS - Development Script
# Start all services for development

set -e

echo "🚀 Starting TB Personal OS Development Environment"
echo "=================================================="
echo ""

# Check if tmux is available
if ! command -v tmux &> /dev/null; then
    echo "⚠️  tmux not found. Starting services sequentially..."
    echo "Install tmux for better experience: sudo apt install tmux"
    echo ""
    
    # Start backend
    echo "Starting backend..."
    cd backend
    source venv/bin/activate
    python -m app.main &
    BACKEND_PID=$!
    
    cd ..
    
    # Start frontend
    echo "Starting frontend..."
    cd frontend
    npm run dev &
    FRONTEND_PID=$!
    
    cd ..
    
    echo ""
    echo "✅ Services started!"
    echo "Backend: http://localhost:8000"
    echo "Frontend: http://localhost:5173"
    echo ""
    echo "Press Ctrl+C to stop all services"
    
    # Wait for interrupt
    trap "kill $BACKEND_PID $FRONTEND_PID" EXIT
    wait
    
else
    # Use tmux for better session management
    SESSION="tb-personal-os"
    
    # Kill existing session if exists
    tmux kill-session -t $SESSION 2>/dev/null || true
    
    # Create new session
    tmux new-session -d -s $SESSION -n "backend"
    
    # Backend window
    tmux send-keys -t $SESSION:backend "cd backend && source venv/bin/activate && python -m app.main" C-m
    
    # Frontend window
    tmux new-window -t $SESSION -n "frontend"
    tmux send-keys -t $SESSION:frontend "cd frontend && npm run dev" C-m
    
    # Logs window
    tmux new-window -t $SESSION -n "logs"
    tmux send-keys -t $SESSION:logs "echo 'Logs window - Use Ctrl+B then [number] to switch windows'" C-m
    
    echo "✅ Development environment started in tmux session: $SESSION"
    echo ""
    echo "Commands:"
    echo "  Attach to session: tmux attach -t $SESSION"
    echo "  Switch windows: Ctrl+B then 0/1/2"
    echo "  Detach: Ctrl+B then d"
    echo "  Kill session: tmux kill-session -t $SESSION"
    echo ""
    echo "Services:"
    echo "  Backend: http://localhost:8000"
    echo "  Frontend: http://localhost:5173"
    echo "  API Docs: http://localhost:8000/api/docs"
    echo ""
    
    # Attach to session
    tmux attach -t $SESSION
fi
