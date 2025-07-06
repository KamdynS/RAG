@echo off
setlocal enabledelayedexpansion

echo 🚀 Setting up RAG Complete for local development...
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not installed. Please install Docker first.
    echo Visit: https://docs.docker.com/get-docker/
    pause
    exit /b 1
)

REM Check if Docker Compose is installed
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Compose is not installed. Please install Docker Compose first.
    echo Visit: https://docs.docker.com/compose/install/
    pause
    exit /b 1
)

echo ✅ Docker and Docker Compose are installed

REM Check if .env.local exists
if not exist .env.local (
    echo 📝 Creating .env.local file...
    copy env.local.example .env.local >nul
    echo ⚠️  IMPORTANT: Please edit .env.local and add your API keys:
    echo    - OPENAI_API_KEY
    echo    - PINECONE_API_KEY
    echo    - PINECONE_INDEX_NAME
    echo    - PINECONE_ENVIRONMENT
    echo.
    echo Opening .env.local for editing...
    
    REM Try to open with different editors
    where code >nul 2>&1
    if %errorlevel% equ 0 (
        code .env.local
    ) else (
        where notepad >nul 2>&1
        if %errorlevel% equ 0 (
            notepad .env.local
        ) else (
            echo Please edit .env.local manually
        )
    )
    
    echo.
    pause
)

echo ✅ Environment file configured

REM Build and start services
echo 🏗️  Building and starting services...
docker-compose up -d --build

echo ⏳ Waiting for services to be ready...
timeout /t 10 /nobreak >nul

REM Check if services are running
echo 🔍 Checking service health...

REM Check PostgreSQL
docker-compose exec -T postgres pg_isready -U rag_user -d rag_complete >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ PostgreSQL is ready
) else (
    echo ❌ PostgreSQL is not ready
)

REM Check Redis
docker-compose exec -T redis redis-cli ping | findstr "PONG" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Redis is ready
) else (
    echo ❌ Redis is not ready
)

REM Check Backend
curl -s -f http://localhost:8000/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Backend API is ready
) else (
    echo ⚠️  Backend API is starting up...
)

REM Check Frontend
curl -s -f http://localhost:3000 >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Frontend is ready
) else (
    echo ⚠️  Frontend is starting up...
)

echo.
echo 🎉 Setup complete! Your RAG Complete application is running:
echo.
echo 🌐 Frontend: http://localhost:3000
echo 🔧 Backend API: http://localhost:8000
echo 📊 API Documentation: http://localhost:8000/docs
echo 🗃️  Database: localhost:5432
echo 🔴 Redis: localhost:6379
echo 📝 Logs: ./logs folder
echo.
echo 📋 Useful commands:
echo   docker-compose logs -f          # View all logs
echo   docker-compose logs -f backend  # View backend logs
echo   docker-compose logs -f frontend # View frontend logs
echo   docker-compose down             # Stop all services
echo   docker-compose up -d            # Start all services
echo.
echo 🔧 To run with Supabase local development:
echo   docker-compose --profile supabase up -d
echo.
echo Happy coding! 🚀
pause 