# RAG Architecture Design

## Overview

This document outlines the Retrieval-Augmented Generation (RAG) system architecture for Smart Tax Assistant.

## Status: 🚧 Planning Phase

## Goals

1. Enable semantic search across tax documents
2. Provide AI-powered document analysis
3. Generate contextual responses with source citations
4. Support Thai and English languages

## Architecture

### High-Level Flow

```
User Query
    ↓
Query Embedding
    ↓
Vector Search (Similarity)
    ↓
Context Retrieval
    ↓
LLM Generation (with Context)
    ↓
Response + Sources
```

### Components

#### 1. Embedding Service
- **Purpose:** Convert text to vector embeddings
- **Technology Options:**
  - OpenAI text-embedding-3-small (1536 dimensions)
  - Cohere multilingual embeddings
  - Local model (sentence-transformers)
- **Location:** `src/modules/rag/services/embeddings.ts`

#### 2. Vector Database
- **Purpose:** Store and search document embeddings
- **Technology Options:**
  - Pinecone (managed, scalable)
  - Supabase pgvector (PostgreSQL extension)
  - Weaviate (open-source)
  - Qdrant (open-source, fast)
- **Decision:** TBD based on scale and budget

#### 3. Retrieval Service
- **Purpose:** Find relevant documents for queries
- **Features:**
  - Semantic similarity search
  - Metadata filtering (date, category, user)
  - Ranking and re-ranking
- **Location:** `src/modules/rag/services/retrieval.ts`

#### 4. Generation Service
- **Purpose:** Generate responses using LLM
- **Technology:**
  - OpenAI GPT-4o (recommended)
  - Anthropic Claude (alternative)
  - Local LLM (for privacy)
- **Location:** `src/modules/rag/services/generation.ts`

## Data Flow

### Document Ingestion
```
Upload Document
    ↓
Extract Text (PDF, DOCX)
    ↓
Chunk Text (500-1000 tokens)
    ↓
Generate Embeddings
    ↓
Store in Vector DB (with metadata)
```

### Query Processing
```
User Query (Thai/English)
    ↓
Generate Query Embedding
    ↓
Search Vector DB (Top 5 similar chunks)
    ↓
Retrieve Full Context
    ↓
Build Prompt with Context
    ↓
LLM Generation
    ↓
Return Answer + Sources
```

## Implementation Phases

### Phase 1: Foundation (Week 1-2)
- [ ] Set up vector database
- [ ] Implement embedding service
- [ ] Create document chunking logic

### Phase 2: Retrieval (Week 3-4)
- [ ] Implement similarity search
- [ ] Add metadata filtering
- [ ] Test retrieval accuracy

### Phase 3: Generation (Week 5-6)
- [ ] Integrate LLM API
- [ ] Design prompt templates
- [ ] Implement response formatting

### Phase 4: Optimization (Week 7-8)
- [ ] Add re-ranking
- [ ] Implement caching
- [ ] Performance tuning

## Configuration

See `src/modules/rag/config/rag.config.ts` for settings.

## Security Considerations

- API keys stored in environment variables
- User data isolation
- Rate limiting on LLM calls
- Content filtering

## Performance Goals

- Query response time: < 3 seconds
- Embedding generation: < 1 second per document
- Support 1000+ documents per user

## Future Enhancements

- Multi-modal RAG (images, tables)
- Conversational memory
- Fine-tuned embeddings for Thai tax terms
- Real-time document updates

## References

- [LangChain Documentation](https://js.langchain.com/)
- [OpenAI Embeddings Guide](https://platform.openai.com/docs/guides/embeddings)
- [RAG Best Practices](https://www.pinecone.io/learn/retrieval-augmented-generation/)

---

**Last Updated:** October 2025
**Author:** Atikun
