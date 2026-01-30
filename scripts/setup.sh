#!/bin/bash

# TB Personal OS - Setup Script
# Run this script to set up the development environment

set -e

echo "🚀 TB Personal OS - Setup Script"
echo "================================="
echo ""

# Check if running from project root
if [ ! -f "README.md" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# 1. Backend Setup
echo "📦 Setting up Python backend..."
cd backend

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Copy env file if not exists
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit backend/.env with your credentials"
fi

cd ..

# 2. Frontend Setup
echo ""
echo "📦 Setting up React frontend..."
cd frontend

# Install dependencies
if command -v npm &> /dev/null; then
    echo "Installing Node dependencies..."
    npm install
elif command -v yarn &> /dev/null; then
    echo "Installing Node dependencies with yarn..."
    yarn install
else
    echo "❌ Error: npm or yarn not found. Please install Node.js"
    exit 1
fi

# Copy env file if not exists
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit frontend/.env with your credentials"
fi

cd ..

# 3. Database Setup
echo ""
echo "🗄️  Database setup..."
echo "Please run the following SQL files in your Supabase SQL Editor:"
echo "  1. docs/database/schema.sql"
echo "  2. docs/database/seed.sql (optional)"
echo ""

# 4. Final instructions
echo "✅ Setup completed!"
echo ""
echo "Next steps:"
echo "  1. Edit backend/.env with your API keys"
echo "  2. Edit frontend/.env with your Supabase credentials"
echo "  3. Run database migrations in Supabase"
echo "  4. Start backend: cd backend && source venv/bin/activate && python -m app.main"
echo "  5. Start frontend: cd frontend && npm run dev"
echo ""
echo "📚 Documentation: docs/README.md"
echo "🐛 Issues: Check IMPLEMENTATION.md"
echo ""
