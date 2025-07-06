# RAG Complete - Local Development

A production-ready Retrieval-Augmented Generation (RAG) system that runs entirely on your local machine using Docker Compose.

## 🏗️ What's Included

- **Next.js Frontend** - Modern chat interface with real-time responses
- **FastAPI Backend** - High-performance API with document processing
- **PostgreSQL Database** - Document metadata and chat history
- **ChromaDB Vector Database** - Semantic search and embeddings
- **Redis Cache** - Fast caching and job queues
- **Automatic Setup** - One command to get everything running

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- OpenAI API key

### 1. Clone and Setup

```bash
git clone <your-repo-url>
cd RAG_production
```

### 2. Run Setup Script

**Linux/Mac:**
```bash
./setup-local.sh
```

**Windows:**
```bash
setup-local.bat
```

The script will:
- Create your environment file
- Ask for your OpenAI API key
- Start all services with Docker Compose
- Check that everything is running

### 3. Access Your Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 📊 What You Get

### Core Features
✅ **Document Upload** - PDF, DOCX, PPTX, TXT, MD support  
✅ **Semantic Search** - ChromaDB vector database for intelligent search  
✅ **Chat Interface** - Real-time conversations about your documents  
✅ **Document Management** - Organize with groups and tags  
✅ **Persistent Data** - Everything saved locally with Docker volumes  

### Technical Stack
- **Frontend**: Next.js 14, TypeScript, Tailwind CSS, shadcn/ui
- **Backend**: FastAPI, Python, async processing
- **Database**: PostgreSQL with proper migrations
- **Vector DB**: ChromaDB for embeddings and similarity search
- **Cache**: Redis for performance optimization
- **AI**: OpenAI GPT-4 and embeddings

## 🔧 Development Commands

```bash
# View all logs
docker-compose logs -f

# Stop all services
docker-compose down

# Restart everything
docker-compose up -d --build

# Connect to database
docker-compose exec postgres psql -U rag_user -d rag_complete

# Reset all data (⚠️ destructive)
docker-compose down -v && docker-compose up -d --build
```

## 📁 Project Structure

```
RAG_production/
├── frontend/rag_complete/    # Next.js frontend
├── backend/                  # FastAPI backend
├── supabase/migrations/      # Database schema
├── docker-compose.yml        # Local development setup
├── setup-local.sh           # Linux/Mac setup script
└── setup-local.bat          # Windows setup script
```

## 🎯 Next Steps

Ready to add advanced features? Check out our [roadmap](docs/ROADMAP.md) for:

- **User Management** - Multi-tenant teams and permissions
- **Video Transcription** - YouTube links and MP4 uploads with Whisper
- **Advanced Analytics** - Usage tracking and insights
- **External Integrations** - Slack, Google Drive, Notion

## 🆘 Troubleshooting

**Services won't start?**
```bash
docker system prune -f
docker-compose down -v
docker-compose up -d --build
```

**Can't connect to backend?**
```bash
docker-compose logs backend
curl http://localhost:8000/health
```

**Need to reset everything?**
```bash
docker-compose down -v  # Deletes all data
docker-compose up -d --build
```

## 📞 Support

- **Documentation**: Check the `docs/` folder
- **Issues**: Report bugs on GitHub
- **Logs**: Use `docker-compose logs -f` for debugging

---

**Ready to build your RAG system?** Run the setup script and start uploading documents! 🚀
