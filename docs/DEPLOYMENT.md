# Deployment Guide - PaaS Infrastructure

This guide provides step-by-step instructions for deploying RAG Complete using a fully Platform-as-a-Service (PaaS) architecture. No server management required!

## Architecture Overview

Our PaaS stack consists of:
- **Frontend**: Vercel (Next.js hosting)
- **Backend**: Render (Python FastAPI hosting)
- **Database**: Supabase (PostgreSQL)
- **Vector Database**: Pinecone (Vector embeddings)
- **Cache**: Upstash (Redis)
- **AI Services**: OpenAI (GPT and embeddings)

## Prerequisites

- GitHub account (for code hosting)
- Basic knowledge of environment variables
- API keys for AI services (OpenAI, etc.)

## Step 1: Database Setup (Supabase)

### 1.1 Create Supabase Project

1. Go to [Supabase](https://supabase.com)
2. Click "Start your project"
3. Sign in with GitHub
4. Click "New project"
5. Choose organization and fill in project details:
   - **Name**: `rag-complete-db`
   - **Database Password**: Generate a strong password
   - **Region**: Choose closest to your users
6. Click "Create new project"
7. Wait for setup to complete (2-3 minutes)

### 1.2 Configure Database

1. Once project is ready, go to **SQL Editor**
2. Click "New query"
3. Copy and paste the database schema:

```sql
-- Create documents table
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    size BIGINT NOT NULL,
    chunks_count INTEGER DEFAULT 0,
    group_id UUID,
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
    parent_id UUID,
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
    document_id UUID NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    embedding_id VARCHAR(255),
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
    session_id UUID NOT NULL,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add foreign key constraints
ALTER TABLE documents ADD CONSTRAINT fk_documents_group_id 
    FOREIGN KEY (group_id) REFERENCES document_groups(id);

ALTER TABLE document_groups ADD CONSTRAINT fk_document_groups_parent_id 
    FOREIGN KEY (parent_id) REFERENCES document_groups(id);

ALTER TABLE document_chunks ADD CONSTRAINT fk_document_chunks_document_id 
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE;

ALTER TABLE chat_messages ADD CONSTRAINT fk_chat_messages_session_id 
    FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE;

-- Add performance indexes
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_documents_group_id ON documents(group_id);
CREATE INDEX idx_documents_created_at ON documents(created_at);
CREATE INDEX idx_documents_tags ON documents USING GIN(tags);
CREATE INDEX idx_documents_metadata ON documents USING GIN(metadata);
CREATE INDEX idx_document_chunks_document_id ON document_chunks(document_id);
CREATE INDEX idx_document_chunks_embedding_id ON document_chunks(embedding_id);
CREATE INDEX idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX idx_chat_sessions_updated_at ON chat_sessions(updated_at);
CREATE INDEX idx_document_tags_name ON document_tags(name);
CREATE INDEX idx_document_tags_usage_count ON document_tags(usage_count DESC);

-- Insert default document groups
INSERT INTO document_groups (name, description, color, icon) VALUES
    ('General', 'General documents', '#3B82F6', 'folder'),
    ('Financial', 'Financial documents and reports', '#10B981', 'dollar-sign'),
    ('Legal', 'Legal documents and contracts', '#F59E0B', 'scale'),
    ('HR', 'Human resources documents', '#EF4444', 'users'),
    ('Technical', 'Technical documentation', '#8B5CF6', 'code'),
    ('Marketing', 'Marketing materials', '#F97316', 'megaphone');
```

4. Click "Run" to execute the schema
5. Go to **Settings** → **API** and note down:
   - **Project URL** (e.g., `https://your-project.supabase.co`)
   - **anon public key** (starts with `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9`)

## Step 2: Vector Database Setup (Pinecone)

### 2.1 Create Pinecone Account

1. Go to [Pinecone](https://pinecone.io)
2. Click "Sign Up Free"
3. Create account or sign in with Google/GitHub
4. Verify your email address

### 2.2 Create Vector Index

1. In Pinecone console, click "Create Index"
2. Configure the index:
   - **Index Name**: `rag-documents`
   - **Dimensions**: `1536` (for OpenAI embeddings)
   - **Metric**: `cosine`
   - **Pod Type**: `p1.x1` (starter tier)
   - **Replicas**: `1`
   - **Shards**: `1`
3. Click "Create Index"
4. Wait for index to be ready (~2 minutes)
5. Go to **API Keys** and note down:
   - **API Key**
   - **Index Name**: `rag-documents`
   - **Environment**: (e.g., `us-west1-gcp`)

## Step 3: Redis Cache Setup (Upstash)

### 3.1 Create Upstash Account

1. Go to [Upstash](https://upstash.com)
2. Click "Sign Up"
3. Sign in with GitHub or create account
4. Verify your email

### 3.2 Create Redis Database

1. In Upstash console, click "Create Database"
2. Configure database:
   - **Name**: `rag-complete-cache`
   - **Region**: Choose closest to your backend
   - **Type**: Regional (for better performance)
3. Click "Create"
4. Once created, go to database details and note down:
   - **Redis URL** (full connection string)
   - **REST URL** (for HTTP access)

## Step 4: Backend Deployment (Render)

### 4.1 Create Render Account

1. Go to [Render](https://render.com)
2. Click "Get Started"
3. Sign up with GitHub (recommended)
4. Authorize Render to access your repositories

### 4.2 Deploy Backend Service

1. In Render dashboard, click "New +"
2. Select "Web Service"
3. Connect your repository:
   - **GitHub**: Select your RAG repository
   - **Branch**: `main`
4. Configure service:
   - **Name**: `rag-complete-backend`
   - **Region**: Choose closest to your users
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Click "Advanced" and set environment variables:

```bash
# Database
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres
SUPABASE_URL=https://[PROJECT].supabase.co
SUPABASE_ANON_KEY=[YOUR_SUPABASE_ANON_KEY]

# Vector Database
PINECONE_API_KEY=[YOUR_PINECONE_API_KEY]
PINECONE_INDEX_NAME=rag-documents
PINECONE_ENVIRONMENT=[YOUR_PINECONE_ENVIRONMENT]

# Redis Cache
REDIS_URL=[YOUR_UPSTASH_REDIS_URL]

# AI Services
OPENAI_API_KEY=[YOUR_OPENAI_API_KEY]

# Application Settings
ENVIRONMENT=production
SECRET_KEY=[GENERATE_RANDOM_SECRET_KEY]
MAX_FILE_SIZE=52428800
ALLOWED_FILE_TYPES=pdf,docx,pptx,txt,md

# CORS Settings - will be updated after frontend deployment
CORS_ORIGINS=["https://your-frontend-will-be-here.vercel.app"]
```

6. Click "Create Web Service"
7. Wait for deployment to complete (~5 minutes)
8. Note down your service URL (e.g., `https://rag-complete-backend.onrender.com`)

## Step 5: Frontend Deployment (Vercel)

### 5.1 Create Vercel Account

1. Go to [Vercel](https://vercel.com)
2. Click "Sign Up"
3. Sign up with GitHub (recommended)
4. Authorize Vercel to access your repositories

### 5.2 Deploy Frontend

1. In Vercel dashboard, click "New Project"
2. Import your GitHub repository
3. Configure project:
   - **Framework Preset**: Next.js
   - **Root Directory**: `frontend/rag_complete`
   - **Build Command**: `npm run build`
   - **Output Directory**: Leave empty (default)
4. Click "Show more" and set environment variables:

```bash
# Backend API
NEXT_PUBLIC_API_URL=https://rag-complete-backend.onrender.com
NEXT_PUBLIC_API_BASE_URL=https://rag-complete-backend.onrender.com/api

# Application Settings
NEXT_PUBLIC_APP_NAME=RAG Complete
NEXT_PUBLIC_APP_VERSION=1.0.0
NEXT_PUBLIC_ENVIRONMENT=production
```

5. Click "Deploy"
6. Wait for deployment to complete (~3 minutes)
7. Note down your deployment URL (e.g., `https://rag-complete.vercel.app`)

### 5.3 Update Backend CORS Settings

1. Go back to Render dashboard
2. Open your backend service
3. Go to "Environment"
4. Update the `CORS_ORIGINS` variable:

```bash
CORS_ORIGINS=["https://your-actual-vercel-url.vercel.app"]
```

5. Save changes (this will redeploy your backend)

## Step 6: AI Services Setup

### 6.1 OpenAI API Key

1. Go to [OpenAI Platform](https://platform.openai.com)
2. Create account or sign in
3. Go to **API Keys**
4. Click "Create new secret key"
5. Name it "RAG Complete" and copy the key
6. Add to your Render environment variables as `OPENAI_API_KEY`

### 6.2 Optional: Additional AI Services

For enhanced functionality, you can add:

**Anthropic Claude:**
1. Go to [Anthropic Console](https://console.anthropic.com)
2. Create account and get API key
3. Add as `ANTHROPIC_API_KEY` in Render

**Cohere:**
1. Go to [Cohere Dashboard](https://dashboard.cohere.ai)
2. Create account and get API key
3. Add as `COHERE_API_KEY` in Render

## Step 7: Verification and Testing

### 7.1 Health Check

1. Visit your frontend URL
2. Check that the interface loads properly
3. Try uploading a small document
4. Test the chat functionality

### 7.2 Backend Health Check

Visit `https://your-backend-url.onrender.com/health` to verify the backend is running.

### 7.3 Database Connection

Check the Supabase dashboard to ensure tables are created and the connection is working.

## Step 8: Production Optimizations

### 8.1 Database Optimization

1. In Supabase, go to **Settings** → **Database**
2. Enable **Point-in-time Recovery** for backups
3. Set up **Database Webhooks** for real-time updates (optional)

### 8.2 Monitoring Setup

1. **Render**: Built-in monitoring and logs
2. **Vercel**: Built-in analytics and monitoring
3. **Supabase**: Built-in database monitoring
4. **Pinecone**: Index monitoring in dashboard

### 8.3 Domain Setup (Optional)

1. **Vercel**: Add custom domain in project settings
2. **Render**: Add custom domain in service settings
3. Update CORS origins accordingly

## Troubleshooting

### Common Issues

**Backend not starting:**
- Check Render logs for errors
- Verify all environment variables are set
- Check database connection string

**Frontend can't connect to backend:**
- Verify `NEXT_PUBLIC_API_URL` is correct
- Check CORS settings in backend
- Ensure backend is deployed and running

**Database connection errors:**
- Check Supabase project status
- Verify database URL format
- Check connection limits

**Vector search not working:**
- Verify Pinecone API key and index name
- Check index dimensions (should be 1536)
- Ensure documents are being embedded properly

**File upload issues:**
- Check file size limits (50MB default)
- Verify file types are allowed
- Check backend logs for processing errors

### Getting Help

1. Check service status pages:
   - [Render Status](https://status.render.com)
   - [Vercel Status](https://vercel-status.com)
   - [Supabase Status](https://status.supabase.com)
   - [Pinecone Status](https://status.pinecone.io)

2. Review logs:
   - Render: Service logs in dashboard
   - Vercel: Function logs in dashboard
   - Supabase: Database logs in dashboard

3. Check documentation:
   - [Render Docs](https://render.com/docs)
   - [Vercel Docs](https://vercel.com/docs)
   - [Supabase Docs](https://supabase.com/docs)
   - [Pinecone Docs](https://docs.pinecone.io)

## Cost Optimization

### Free Tier Limits

- **Render**: 750 hours/month (free tier)
- **Vercel**: 100GB bandwidth/month (hobby tier)
- **Supabase**: 500MB database + 2GB bandwidth (free tier)
- **Pinecone**: 1M vectors + 1000 queries/month (free tier)
- **Upstash**: 10,000 commands/month (free tier)

### Scaling Up

When you exceed free tiers:
- **Render**: $7/month for always-on service
- **Vercel**: $20/month for pro features
- **Supabase**: $25/month for pro features
- **Pinecone**: $70/month for production tier
- **Upstash**: $0.20 per 100,000 commands

## Security Best Practices

1. **API Keys**: Never commit API keys to version control
2. **Environment Variables**: Use platform-specific secret management
3. **CORS**: Restrict to your frontend domain only
4. **Database**: Use connection pooling and query optimization
5. **Rate Limiting**: Implement rate limiting for API endpoints
6. **File Upload**: Validate file types and sizes
7. **Monitoring**: Set up alerts for unusual activity

## Maintenance

### Regular Tasks

1. **Monitor Usage**: Check platform dashboards monthly
2. **Update Dependencies**: Keep packages updated
3. **Database Maintenance**: Monitor query performance
4. **Backup Verification**: Ensure backups are working
5. **Security Updates**: Apply security patches promptly

### Automated Deployments

Both Render and Vercel support automatic deployments from GitHub:
1. Push to main branch triggers deployment
2. Preview deployments for pull requests
3. Rollback capabilities if issues arise

This completes your fully PaaS-based RAG Complete deployment! 🚀 