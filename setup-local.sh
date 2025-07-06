#!/bin/bash

# RAG Complete - Local Development Setup Script
# This script helps you set up the local development environment

set -e

echo "🚀 Setting up RAG Complete for local development..."
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    echo "Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"

# Check if .env.local exists
if [ ! -f .env.local ]; then
    echo "📝 Creating .env.local file..."
    cp env.local.example .env.local
    echo "⚠️  IMPORTANT: Please edit .env.local and add your API key:"
    echo "   - OPENAI_API_KEY"
    echo ""
    echo "   ChromaDB vector database is included by default."
    echo "   No additional API keys needed for local development!"
    echo ""
    echo "   Opening .env.local for editing..."
    if command -v code &> /dev/null; then
        code .env.local
    elif command -v nano &> /dev/null; then
        nano .env.local
    else
        echo "   Please edit .env.local manually"
    fi
    echo ""
    read -p "Press Enter after you've updated the .env.local file..."
fi

echo "✅ Environment file configured"

# Build and start services
echo "🏗️  Building and starting services..."
docker-compose up -d --build

echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if services are running
echo "🔍 Checking service health..."

# Check PostgreSQL
if docker-compose exec postgres pg_isready -U rag_user -d rag_complete > /dev/null 2>&1; then
    echo "✅ PostgreSQL is ready"
else
    echo "❌ PostgreSQL is not ready"
fi

# Check Redis
if docker-compose exec redis redis-cli ping | grep -q PONG; then
    echo "✅ Redis is ready"
else
    echo "❌ Redis is not ready"
fi

# Check Backend
if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend API is ready"
else
    echo "⚠️  Backend API is starting up..."
fi

# Check Frontend
if curl -s -f http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend is ready"
else
    echo "⚠️  Frontend is starting up..."
fi

echo ""
echo "🎉 Setup complete! Your RAG Complete application is running:"
echo ""
echo "🌐 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000"
echo "📊 API Documentation: http://localhost:8000/docs"
echo "🗃️  Database: localhost:5432"
echo "🔴 Redis: localhost:6379"
echo "🎯 ChromaDB: http://localhost:8001"
echo ""
echo "📋 Useful commands:"
echo "  docker-compose logs -f          # View all logs"
echo "  docker-compose logs -f backend  # View backend logs"
echo "  docker-compose logs -f frontend # View frontend logs"
echo "  docker-compose down             # Stop all services"
echo "  docker-compose up -d            # Start all services"
echo ""
echo "🔧 To run with Pinecone instead of ChromaDB:"
echo "  docker-compose --profile pinecone up -d"
echo ""
echo "Happy coding! 🚀" 