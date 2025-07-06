# RAG Complete - Production RAG System

A production-ready Retrieval-Augmented Generation (RAG) system built with modern technologies. Deploy locally with Docker Compose or use Platform-as-a-Service (PaaS) providers for maximum scalability.

## 🏗️ Architecture

### Frontend
- **Next.js 14** with TypeScript and Tailwind CSS
- **Shadcn/ui** for modern, accessible components
- **Real-time chat** interface with streaming responses
- **Advanced document filtering** with groups, tags, and metadata
- **Responsive design** optimized for desktop and mobile

### Backend
- **FastAPI** with Python for high-performance API
- **Advanced document processing** with multiple format support
- **Hybrid search** combining semantic and keyword search
- **Vector storage** with Pinecone for semantic search
- **Redis caching** for improved performance

### Infrastructure Options

#### 🐳 Local Development (Docker)
- **Docker Compose** for orchestrated local development
- **PostgreSQL** for relational data
- **Redis** for caching and job queues
- **Persistent volumes** for data persistence
- **Hot reload** for rapid development

#### ☁️ Hosted PaaS (Production)
- **Vercel** - Frontend hosting and deployment
- **Render** - Backend API hosting
- **Supabase** - PostgreSQL database
- **Pinecone** - Vector database for embeddings
- **Upstash** - Redis for caching and job queues

## 🚀 Quick Start

### Prerequisites
- **For Local Development**: Docker & Docker Compose
- **For Hosted Deployment**: Node.js 18+, Python 3.9+, Git
- **For Both**: OpenAI API Key, Pinecone API Key

---

## 🐳 Local Development with Docker

### 1. Clone and Setup

```bash
git clone <your-repo-url>
cd RAG_production
```

### 2. Environment Setup

```bash
# Copy the local environment template
cp env.local.example .env.local

# Edit .env.local with your API keys
nano .env.local  # or use your preferred editor
```

**Required API Keys in `.env.local`:**
- `OPENAI_API_KEY` - Get from [OpenAI](https://platform.openai.com/api-keys)

**Vector Database Options (choose one):**
- **Pinecone (hosted)**: `PINECONE_API_KEY`, `PINECONE_INDEX_NAME`, `PINECONE_ENVIRONMENT`
- **ChromaDB (local)**: Uncomment the ChromaDB variables in `.env.local`

### 3. Run the Application

```bash
# Option 1: Use the setup script (recommended)
# Linux/Mac:
./setup-local.sh

# Windows:
setup-local.bat

# Option 2: Manual setup
docker-compose up -d --build

# Option 3: Run with local vector database (ChromaDB)
docker-compose --profile local-vector up -d --build

# Option 4: Run with Supabase local development
docker-compose --profile supabase up -d --build
```

### 4. Access Your Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Database**: localhost:5432
- **Redis**: localhost:6379
- **ChromaDB** (if using local vector): http://localhost:8001
- **Logs**: Available in Docker containers and `logs/` directory

### 5. Development Commands

```bash
# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up -d --build

# Run with Supabase local development
docker-compose --profile supabase up -d
```

### 6. Database Management

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U rag_user -d rag_complete

# View database logs
docker-compose logs postgres

# Reset database (⚠️ This will delete all data)
docker-compose down -v
docker-compose up -d --build
```

---

## ☁️ Hosted PaaS Deployment

### 1. Clone and Setup Repositories

```bash
git clone <your-repo-url>
cd RAG_production

# Setup frontend
cd frontend/rag_complete
npm install

# Setup backend
cd ../../backend
pip install -r requirements.txt
```

### 2. Database Setup (Supabase)

#### Create Supabase Project
1. Go to [Supabase](https://supabase.com) and create a new project
2. Note down your project URL and anon key

#### Run Database Migration
```bash
# Option 1: Using Supabase CLI (recommended)
supabase init
supabase db push

# Option 2: Manual SQL execution
# Copy and run the SQL from: supabase/migrations/20240101000000_initial_schema.sql
```

### 3. Vector Database Setup (Pinecone)

1. Go to [Pinecone](https://pinecone.io) and create an account
2. Create a new index:
   - **Name**: `rag-documents`
   - **Dimensions**: `1536` (for OpenAI embeddings)
   - **Metric**: `cosine`
3. Note down your API key and environment

### 4. Redis Setup (Upstash)

1. Go to [Upstash](https://upstash.com) and create a Redis database
2. Note down the Redis URL

### 5. Backend Deployment (Render)

1. Go to [Render](https://render.com) and create a Web Service
2. Connect your GitHub repository
3. Configure the service:
   - **Build Command**: `cd backend && pip install -r requirements.txt`
   - **Start Command**: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Environment**: Python 3.9+

4. Add environment variables from `env.hosted.example`:
   ```bash
   DATABASE_URL=postgresql://[user]:[password]@[host]:[port]/[database]
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_ANON_KEY=your-supabase-anon-key
   PINECONE_API_KEY=your-pinecone-api-key
   PINECONE_INDEX_NAME=rag-documents
   PINECONE_ENVIRONMENT=your-pinecone-environment
   REDIS_URL=redis://default:your-password@your-host:port
   OPENAI_API_KEY=your-openai-api-key
   ENVIRONMENT=production
   SECRET_KEY=your-secret-key-for-jwt
   CORS_ORIGINS=["https://your-frontend-domain.vercel.app"]
   ```

### 6. Frontend Deployment (Vercel)

1. Go to [Vercel](https://vercel.com) and import your repository
2. Configure the project:
   - **Framework**: Next.js
   - **Root Directory**: `frontend/rag_complete`
   - **Build Command**: `npm run build`

3. Add environment variables:
   ```bash
   NEXT_PUBLIC_API_URL=https://your-backend-service.render.com
   NEXT_PUBLIC_API_BASE_URL=https://your-backend-service.render.com/api
   NEXT_PUBLIC_APP_NAME=RAG Complete
   NEXT_PUBLIC_APP_VERSION=1.0.0
   NEXT_PUBLIC_ENVIRONMENT=production
   ```

---

## 📁 Project Structure

```
RAG_production/
├── supabase/                   # Database migrations and config
│   ├── config.toml            # Supabase CLI configuration
│   ├── migrations/            # Database migration files
│   └── .gitignore            # Supabase-specific ignores
├── backend/                   # FastAPI backend
│   ├── app/
│   │   ├── api/              # API routes
│   │   ├── models/           # Pydantic models
│   │   ├── services/         # Business logic
│   │   ├── utils/            # Utility functions
│   │   └── main.py           # FastAPI application
│   ├── Dockerfile            # Backend container config
│   ├── requirements.txt      # Python dependencies
│   └── config_template.env   # Backend env template
├── frontend/                  # Next.js frontend
│   └── rag_complete/
│       ├── src/
│       │   ├── app/          # App router pages
│       │   ├── components/   # React components
│       │   ├── lib/          # Utility functions
│       │   └── types/        # TypeScript types
│       ├── Dockerfile        # Frontend container config
│       ├── package.json      # Node dependencies
│       └── next.config.js    # Next.js configuration
├── docs/                      # Documentation
├── docker-compose.yml         # Local development orchestration
├── docker-compose.override.yml # Development overrides
├── env.local.example         # Local development env template
├── env.hosted.example        # Hosted deployment env template
├── setup-local.sh           # Local setup script
└── README.md                # This file
```

## 🔌 API Integration

### Development API Endpoints

When running locally, the backend is available at `http://localhost:8000`:

#### Document Management
- `POST /api/documents/upload` - Upload documents
- `GET /api/documents` - List documents with filtering
- `POST /api/documents/filter` - Advanced document filtering
- `DELETE /api/documents/{id}` - Delete document

#### Chat & Search
- `POST /api/chat` - Send chat message
- `GET /api/chat/sessions` - List chat sessions
- `POST /api/search` - Search documents

### Production API Integration

The frontend communicates with the backend through Next.js API routes that proxy requests to the Python backend for security and CORS handling.

## 🧪 Testing

### Local Testing
```bash
# Backend tests
docker-compose exec backend pytest tests/ -v

# Frontend tests
docker-compose exec frontend npm test

# Integration tests
docker-compose exec backend pytest tests/integration/ -v
```

### Hosted Testing
```bash
# Backend tests
cd backend
pytest tests/ -v --cov=app

# Frontend tests
cd frontend/rag_complete
npm run test
npm run test:e2e
```

## 🚦 Monitoring & Observability

### Local Development
- **Logs**: `docker-compose logs -f`
- **Health Checks**: Built into Docker containers
- **Database**: Direct PostgreSQL access on localhost:5432

### Production (Hosted)
- **Backend**: Render built-in logging and metrics
- **Frontend**: Vercel Analytics and monitoring
- **Database**: Supabase built-in logging and metrics
- **Health Checks**: `/health` endpoint on backend

## 🔒 Security

### Local Development
- Default credentials for local services
- No HTTPS required for local development
- Open access for testing

### Production (Hosted)
- **HTTPS**: Automatic SSL certificates
- **Environment Variables**: Secure secret management
- **CORS**: Configured for production domains
- **Authentication**: JWT-based API authentication

## 📊 Performance Optimization

### Local Development
- **Hot Reload**: Automatic code reloading
- **Volume Mounts**: Direct file system access
- **Development Mode**: Optimized for fast iteration

### Production (Hosted)
- **CDN**: Vercel global edge network
- **Caching**: Redis and application-level caching
- **Connection Pooling**: Optimized database connections
- **Vector Search**: Pinecone optimized queries

## 🔄 Deployment Workflow

### Local Development Workflow
1. Make code changes
2. Services automatically reload
3. Test in browser
4. Commit changes

### Production Deployment Workflow
1. **Frontend**: Auto-deploy from main branch to Vercel
2. **Backend**: Auto-deploy from main branch to Render
3. **Database**: Managed migrations through Supabase
4. **Monitoring**: Automatic health checks and alerting

## 🆘 Troubleshooting

### Local Development Issues

#### "Cannot connect to backend"
```bash
# Check backend logs
docker-compose logs backend

# Restart backend service
docker-compose restart backend

# Check if backend is healthy
curl http://localhost:8000/health
```

#### "Database connection failed"
```bash
# Check PostgreSQL logs
docker-compose logs postgres

# Check if PostgreSQL is ready
docker-compose exec postgres pg_isready -U rag_user -d rag_complete

# Reset database
docker-compose down -v
docker-compose up -d --build
```

#### "Services won't start"
```bash
# Check Docker system
docker system df
docker system prune  # Clean up space

# Check Docker Compose
docker-compose config  # Validate configuration
docker-compose down && docker-compose up -d --build
```

### Production Issues

#### "Backend deployment failed"
- Check Render build logs
- Verify environment variables
- Check Python version compatibility

#### "Frontend deployment failed"
- Check Vercel build logs
- Verify Next.js configuration
- Check environment variables

#### "Database migration failed"
- Check Supabase dashboard
- Verify database connection
- Run migrations manually

### Getting Help

1. **Local Issues**: Check Docker logs and service health
2. **Production Issues**: Check platform dashboards
3. **Documentation**: Review [docs/](./docs/) folder
4. **GitHub Issues**: Report bugs and feature requests

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. **Local Development**: Test with Docker Compose
4. **Production Testing**: Deploy to staging environment
5. Commit changes: `git commit -m 'Add amazing feature'`
6. Push to branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Local Development**: Docker and Docker Compose communities
- **Production Infrastructure**: Vercel, Render, Supabase, Pinecone, Upstash
- **AI Services**: OpenAI for GPT and embedding models
- **Open Source**: The amazing open-source community

---

## 🎯 Next Steps

### For Local Development
1. Run `./setup-local.sh` to get started
2. Edit `.env.local` with your API keys
3. Access your app at http://localhost:3000

### For Production Deployment
1. Follow the PaaS deployment guide above
2. Set up monitoring and alerting
3. Configure your custom domain

**Ready to build your RAG system?** Choose your deployment method and start building! 🚀
