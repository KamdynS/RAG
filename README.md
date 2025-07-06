# RAG Complete - Production RAG System

A production-ready Retrieval-Augmented Generation (RAG) system built with modern technologies and deployed using Platform-as-a-Service (PaaS) providers for maximum scalability and ease of deployment.

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

### Infrastructure (Fully PaaS)
- **Vercel** - Frontend hosting and deployment
- **Render** - Backend API hosting
- **Supabase** - PostgreSQL database
- **Pinecone** - Vector database for embeddings
- **Upstash** - Redis for caching and job queues

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and npm/yarn
- Python 3.9+
- Git

### 1. Clone and Setup Repositories

```bash
# Clone the main repository
git clone <your-repo-url>
cd RAG_production

# Setup frontend
cd frontend/rag_complete
npm install

# Setup backend
cd ../../backend
pip install -r requirements.txt
```

### 2. Deploy Infrastructure Services

#### A. Database Setup (Supabase)

1. Go to [Supabase](https://supabase.com) and create a new project
2. Note down your project URL and anon key
3. Run the database migrations:

```sql
-- Create documents table
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    size BIGINT NOT NULL,
    chunks_count INTEGER DEFAULT 0,
    group_id UUID REFERENCES document_groups(id),
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create document groups table
CREATE TABLE document_groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    color VARCHAR(7),
    icon VARCHAR(50),
    parent_id UUID REFERENCES document_groups(id),
    document_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create document tags table
CREATE TABLE document_tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    color VARCHAR(7),
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create document chunks table
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    embedding_id VARCHAR(255), -- Reference to Pinecone vector ID
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create chat sessions table
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create chat messages table
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL, -- 'user' or 'assistant'
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add indexes for performance
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_documents_group_id ON documents(group_id);
CREATE INDEX idx_documents_created_at ON documents(created_at);
CREATE INDEX idx_document_chunks_document_id ON document_chunks(document_id);
CREATE INDEX idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX idx_chat_sessions_updated_at ON chat_sessions(updated_at);
```

#### B. Vector Database Setup (Pinecone)

1. Go to [Pinecone](https://pinecone.io) and create an account
2. Create a new index with the following settings:
   - **Name**: `rag-documents`
   - **Dimensions**: `1536` (for OpenAI embeddings)
   - **Metric**: `cosine`
   - **Cloud Provider**: Choose your preferred region
3. Note down your API key and index name

#### C. Redis Setup (Upstash)

1. Go to [Upstash](https://upstash.com) and create an account
2. Create a new Redis database
3. Note down the Redis URL and token

#### D. Backend Deployment (Render)

1. Go to [Render](https://render.com) and create an account
2. Create a new Web Service
3. Connect your GitHub repository
4. Configure the service:
   - **Build Command**: `cd backend && pip install -r requirements.txt`
   - **Start Command**: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Environment**: Python 3.9+
5. Add environment variables (see Environment Variables section below)
6. Deploy the service and note down the service URL

#### E. Frontend Deployment (Vercel)

1. Go to [Vercel](https://vercel.com) and create an account
2. Import your GitHub repository
3. Configure the project:
   - **Framework Preset**: Next.js
   - **Root Directory**: `frontend/rag_complete`
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`
4. Add environment variables (see Environment Variables section below)
5. Deploy and note down the deployment URL

## 🔧 Environment Variables

### Backend Environment Variables (Render)

Create these environment variables in your Render service:

```bash
# Database
DATABASE_URL=postgresql://[user]:[password]@[host]:[port]/[database]
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key

# Vector Database
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_INDEX_NAME=rag-documents
PINECONE_ENVIRONMENT=your-pinecone-environment

# Redis Cache
REDIS_URL=redis://default:your-password@your-host:port

# AI Services
OPENAI_API_KEY=your-openai-api-key

# Application Settings
ENVIRONMENT=production
SECRET_KEY=your-secret-key-for-jwt
ALLOWED_ORIGINS=https://your-frontend-domain.vercel.app
MAX_FILE_SIZE=52428800  # 50MB in bytes
ALLOWED_FILE_TYPES=pdf,docx,pptx,txt,md

# CORS Settings
CORS_ORIGINS=["https://your-frontend-domain.vercel.app"]
```

### Frontend Environment Variables (Vercel)

Create these environment variables in your Vercel project:

```bash
# Backend API
NEXT_PUBLIC_API_URL=https://your-backend-service.render.com
NEXT_PUBLIC_API_BASE_URL=https://your-backend-service.render.com/api

# Application Settings
NEXT_PUBLIC_APP_NAME=RAG Complete
NEXT_PUBLIC_APP_VERSION=1.0.0
NEXT_PUBLIC_ENVIRONMENT=production

# Optional: Analytics
NEXT_PUBLIC_ANALYTICS_ID=your-analytics-id
```

## 🛠️ Local Development

### Backend Setup

1. Create a virtual environment:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create `.env` file:
```bash
cp .env.example .env
# Edit .env with your local configuration
```

4. Run the development server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

1. Install dependencies:
```bash
cd frontend/rag_complete
npm install
```

2. Create `.env.local` file:
```bash
cp .env.example .env.local
# Edit .env.local with your configuration
```

3. Run the development server:
```bash
npm run dev
```

## 📁 Project Structure

```
RAG_production/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── models/         # Pydantic models
│   │   ├── services/       # Business logic
│   │   ├── utils/          # Utility functions
│   │   └── main.py         # FastAPI application
│   ├── requirements.txt    # Python dependencies
│   └── .env.example       # Environment template
├── frontend/               # Next.js frontend
│   └── rag_complete/
│       ├── src/
│       │   ├── app/        # App router pages
│       │   ├── components/ # React components
│       │   ├── lib/        # Utility functions
│       │   └── types/      # TypeScript types
│       ├── public/         # Static assets
│       ├── package.json    # Node dependencies
│       └── .env.example   # Environment template
├── docs/                   # Documentation
│   ├── API.md             # API documentation
│   ├── DEPLOYMENT.md      # Deployment guide
│   └── DOCUMENT_FILTERING.md # Feature documentation
└── README.md              # This file
```

## 🔌 API Integration

The frontend communicates with the backend through Next.js API routes that proxy requests to the Python backend. This provides:

- **Security**: API keys and sensitive data stay on the server
- **CORS handling**: Simplified cross-origin requests
- **Error handling**: Consistent error responses
- **Caching**: Optional response caching for performance

### Available API Endpoints

#### Document Management
- `POST /api/documents/upload` - Upload documents
- `GET /api/documents` - List documents with filtering
- `POST /api/documents/filter` - Advanced document filtering
- `DELETE /api/documents/{id}` - Delete document
- `POST /api/documents/bulk` - Bulk operations

#### Document Groups
- `GET /api/document-groups` - List groups
- `POST /api/document-groups` - Create group
- `PUT /api/document-groups/{id}` - Update group
- `DELETE /api/document-groups/{id}` - Delete group

#### Document Tags
- `GET /api/document-tags` - List tags
- `POST /api/document-tags` - Create tag
- `GET /api/document-tags/popular` - Get popular tags
- `GET /api/document-tags/search` - Search tags

#### Chat & Search
- `POST /api/chat` - Send chat message
- `GET /api/chat/sessions` - List chat sessions
- `POST /api/search` - Search documents

## 🚦 Monitoring & Observability

### Health Checks
- Backend: `https://your-backend.render.com/health`
- Frontend: Built-in Vercel monitoring

### Logging
- **Backend**: Structured JSON logging with correlation IDs
- **Frontend**: Client-side error tracking with Vercel Analytics
- **Database**: Supabase built-in logging and metrics

### Performance Monitoring
- **Response Times**: Track API response times
- **Search Quality**: Monitor search accuracy and relevance
- **User Engagement**: Track feature usage and user behavior

## 🔒 Security

### Authentication & Authorization
- JWT-based authentication for API access
- Secure token storage in HTTP-only cookies
- Role-based access control for multi-tenant scenarios

### Data Protection
- HTTPS everywhere with automatic SSL certificates
- Environment-based configuration management
- Secure secret management through platform providers

### File Upload Security
- File type validation and sanitization
- Size limits and quota enforcement
- Virus scanning for uploaded content

## 🧪 Testing

### Backend Testing
```bash
cd backend
pytest tests/ -v --cov=app
```

### Frontend Testing
```bash
cd frontend/rag_complete
npm run test
npm run test:e2e
```

### Integration Testing
- API endpoint testing with realistic data
- End-to-end workflow testing
- Performance testing under load

## 📊 Performance Optimization

### Caching Strategy
- **Redis**: API response caching and session management
- **CDN**: Static asset delivery through Vercel's global CDN
- **Database**: Query optimization and connection pooling

### Search Performance
- **Vector Search**: Optimized Pinecone queries with metadata filtering
- **Hybrid Search**: Balanced semantic and keyword search
- **Result Caching**: Cache frequent search results

## 🔄 Deployment Workflow

### Automated Deployments
1. **Frontend**: Auto-deploy from main branch to Vercel
2. **Backend**: Auto-deploy from main branch to Render
3. **Database**: Managed migrations through Supabase
4. **Monitoring**: Automatic health checks and alerting

### Release Process
1. Feature development in feature branches
2. Pull request review and testing
3. Merge to main triggers automatic deployment
4. Post-deployment verification and monitoring

## 🆘 Troubleshooting

### Common Issues

#### "Cannot connect to backend"
- Check backend service status in Render dashboard
- Verify CORS configuration
- Confirm environment variables are set

#### "Database connection failed"
- Check Supabase project status
- Verify database URL and credentials
- Check connection limits and quotas

#### "Vector search not working"
- Verify Pinecone API key and index name
- Check index dimensions match embedding model
- Confirm documents are properly embedded

#### "File upload failing"
- Check file size limits
- Verify allowed file types
- Confirm storage quotas

### Getting Help

1. Check the [documentation](./docs/) for detailed guides
2. Review server logs in platform dashboards
3. Check GitHub Issues for known problems
4. Contact support through platform providers

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI for GPT and embedding models
- Pinecone for vector database infrastructure
- Supabase for database and authentication
- Vercel and Render for hosting platforms
- The open-source community for excellent tools and libraries

---

**Ready to deploy your RAG system?** Follow the setup instructions above and you'll have a production-ready system running in minutes!
