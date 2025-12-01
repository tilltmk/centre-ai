-- Centre AI MCP Server - PostgreSQL Database Initialization
-- Version 2.0.0

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ========================================
-- ADMINISTRATORS
-- ========================================
CREATE TABLE IF NOT EXISTS admins (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(200),
    email VARCHAR(255),
    bio TEXT,
    avatar_url TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- MEMORIES (Knowledge Storage)
-- ========================================
CREATE TABLE IF NOT EXISTS memories (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    memory_type VARCHAR(50) DEFAULT 'general',
    importance INTEGER DEFAULT 5 CHECK (importance >= 1 AND importance <= 10),
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    embedding_id VARCHAR(100),
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- CODEBASES
-- ========================================
CREATE TABLE IF NOT EXISTS codebases (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL UNIQUE,
    description TEXT,
    repo_url TEXT,
    local_path TEXT,
    language VARCHAR(50),
    indexed_at TIMESTAMP,
    file_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- CODE FILES
-- ========================================
CREATE TABLE IF NOT EXISTS code_files (
    id SERIAL PRIMARY KEY,
    codebase_id INTEGER REFERENCES codebases(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    content TEXT,
    language VARCHAR(50),
    embedding_id VARCHAR(100),
    metadata JSONB DEFAULT '{}',
    indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- INSTRUCTIONS (AI-managed directives)
-- ========================================
CREATE TABLE IF NOT EXISTS instructions (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(100),
    priority INTEGER DEFAULT 5 CHECK (priority >= 1 AND priority <= 10),
    scope VARCHAR(50) DEFAULT 'global',  -- global, project, session
    is_active BOOLEAN DEFAULT true,
    created_by VARCHAR(100),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- ARTIFACTS (AI-generated content storage)
-- ========================================
CREATE TABLE IF NOT EXISTS artifacts (
    id SERIAL PRIMARY KEY,
    title VARCHAR(300) NOT NULL,
    content TEXT NOT NULL,
    artifact_type VARCHAR(50) NOT NULL,  -- code, document, diagram, config, data, image
    language VARCHAR(50),  -- programming language if code
    mime_type VARCHAR(100),
    file_extension VARCHAR(20),
    version INTEGER DEFAULT 1,
    parent_id INTEGER REFERENCES artifacts(id),  -- for versioning
    project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL,
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- PROJECTS
-- ========================================
CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'active',
    priority INTEGER DEFAULT 5 CHECK (priority >= 1 AND priority <= 10),
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- CONVERSATIONS
-- ========================================
CREATE TABLE IF NOT EXISTS conversations (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) UNIQUE NOT NULL,
    title VARCHAR(200),
    summary TEXT,
    participants TEXT[] DEFAULT '{}',
    message_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- MESSAGES
-- ========================================
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- KNOWLEDGE GRAPH - NODES
-- ========================================
CREATE TABLE IF NOT EXISTS knowledge_nodes (
    id SERIAL PRIMARY KEY,
    node_type VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT,
    parent_id INTEGER REFERENCES knowledge_nodes(id),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- KNOWLEDGE GRAPH - EDGES
-- ========================================
CREATE TABLE IF NOT EXISTS knowledge_edges (
    id SERIAL PRIMARY KEY,
    source_id INTEGER REFERENCES knowledge_nodes(id) ON DELETE CASCADE,
    target_id INTEGER REFERENCES knowledge_nodes(id) ON DELETE CASCADE,
    relationship VARCHAR(100) NOT NULL,
    weight FLOAT DEFAULT 1.0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- INDEXES
-- ========================================
CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(memory_type);
CREATE INDEX IF NOT EXISTS idx_memories_tags ON memories USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_memories_importance ON memories(importance DESC);
CREATE INDEX IF NOT EXISTS idx_code_files_codebase ON code_files(codebase_id);
CREATE INDEX IF NOT EXISTS idx_code_files_language ON code_files(language);
CREATE INDEX IF NOT EXISTS idx_instructions_category ON instructions(category);
CREATE INDEX IF NOT EXISTS idx_instructions_active ON instructions(is_active);
CREATE INDEX IF NOT EXISTS idx_instructions_scope ON instructions(scope);
CREATE INDEX IF NOT EXISTS idx_artifacts_type ON artifacts(artifact_type);
CREATE INDEX IF NOT EXISTS idx_artifacts_project ON artifacts(project_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_tags ON artifacts USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_artifacts_parent ON artifacts(parent_id);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_conversations_session ON conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_edges_source ON knowledge_edges(source_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_edges_target ON knowledge_edges(target_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_nodes_type ON knowledge_nodes(node_type);

-- ========================================
-- UPDATE TRIGGER
-- ========================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers
DO $$
DECLARE
    t text;
BEGIN
    FOR t IN SELECT unnest(ARRAY['admins', 'memories', 'codebases', 'instructions', 'artifacts', 'projects', 'conversations'])
    LOOP
        EXECUTE format('DROP TRIGGER IF EXISTS update_%s_updated_at ON %s', t, t);
        EXECUTE format('CREATE TRIGGER update_%s_updated_at BEFORE UPDATE ON %s FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()', t, t);
    END LOOP;
END;
$$ language 'plpgsql';

-- ========================================
-- COMPLETED
-- ========================================
SELECT 'Centre AI database initialized successfully' as status;
