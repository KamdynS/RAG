-- Create document groups table first (needed for documents FK)
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

-- Add Row Level Security (RLS) policies for security
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_groups ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;

-- Create policies for public access (adjust as needed for your auth requirements)
CREATE POLICY "Enable read access for all users" ON documents FOR SELECT USING (true);
CREATE POLICY "Enable insert access for all users" ON documents FOR INSERT WITH CHECK (true);
CREATE POLICY "Enable update access for all users" ON documents FOR UPDATE USING (true);
CREATE POLICY "Enable delete access for all users" ON documents FOR DELETE USING (true);

CREATE POLICY "Enable read access for all users" ON document_groups FOR SELECT USING (true);
CREATE POLICY "Enable insert access for all users" ON document_groups FOR INSERT WITH CHECK (true);
CREATE POLICY "Enable update access for all users" ON document_groups FOR UPDATE USING (true);
CREATE POLICY "Enable delete access for all users" ON document_groups FOR DELETE USING (true);

CREATE POLICY "Enable read access for all users" ON document_tags FOR SELECT USING (true);
CREATE POLICY "Enable insert access for all users" ON document_tags FOR INSERT WITH CHECK (true);
CREATE POLICY "Enable update access for all users" ON document_tags FOR UPDATE USING (true);
CREATE POLICY "Enable delete access for all users" ON document_tags FOR DELETE USING (true);

CREATE POLICY "Enable read access for all users" ON document_chunks FOR SELECT USING (true);
CREATE POLICY "Enable insert access for all users" ON document_chunks FOR INSERT WITH CHECK (true);
CREATE POLICY "Enable update access for all users" ON document_chunks FOR UPDATE USING (true);
CREATE POLICY "Enable delete access for all users" ON document_chunks FOR DELETE USING (true);

CREATE POLICY "Enable read access for all users" ON chat_sessions FOR SELECT USING (true);
CREATE POLICY "Enable insert access for all users" ON chat_sessions FOR INSERT WITH CHECK (true);
CREATE POLICY "Enable update access for all users" ON chat_sessions FOR UPDATE USING (true);
CREATE POLICY "Enable delete access for all users" ON chat_sessions FOR DELETE USING (true);

CREATE POLICY "Enable read access for all users" ON chat_messages FOR SELECT USING (true);
CREATE POLICY "Enable insert access for all users" ON chat_messages FOR INSERT WITH CHECK (true);
CREATE POLICY "Enable update access for all users" ON chat_messages FOR UPDATE USING (true);
CREATE POLICY "Enable delete access for all users" ON chat_messages FOR DELETE USING (true); 