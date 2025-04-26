CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    chunk_id INTEGER NOT NULL,
    tag TEXT NOT NULL,
    video_id TEXT,
    uri TEXT,
    session_id TEXT NOT NULL,
    embedding vector(384)
);
