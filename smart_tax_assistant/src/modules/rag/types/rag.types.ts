// RAG Type Definitions

/**
 * Configuration for embedding model
 */
export interface EmbeddingConfig {
  model: string;
  dimensions: number;
  provider: 'openai' | 'cohere' | 'local';
  batchSize?: number;
}

/**
 * Result from vector similarity search
 */
export interface VectorSearchResult {
  documentId: string;
  content: string;
  score: number;
  metadata: {
    userId: string;
    fileName: string;
    fileType: string;
    uploadDate: string;
    category?: string;
    [key: string]: any;
  };
}

/**
 * Context provided to LLM for generation
 */
export interface RAGContext {
  query: string;
  documents: VectorSearchResult[];
  maxTokens: number;
  language?: 'th' | 'en';
}

/**
 * Response from RAG system
 */
export interface RAGResponse {
  answer: string;
  sources: Array<{
    documentId: string;
    fileName: string;
    excerpt: string;
    relevanceScore: number;
    pageNumber?: number;
  }>;
  confidence: number;
  language: 'th' | 'en';
}

/**
 * Document chunk for embedding
 */
export interface DocumentChunk {
  id: string;
  documentId: string;
  content: string;
  chunkIndex: number;
  metadata: {
    startPage?: number;
    endPage?: number;
    section?: string;
  };
}

/**
 * Embedding vector
 */
export interface Embedding {
  id: string;
  chunkId: string;
  vector: number[];
  model: string;
  createdAt: Date;
}

/**
 * Search query parameters
 */
export interface SearchParams {
  query: string;
  topK?: number;
  minScore?: number;
  filters?: {
    userId?: string;
    category?: string;
    dateRange?: {
      start: Date;
      end: Date;
    };
  };
}

/**
 * Generation parameters for LLM
 */
export interface GenerationParams {
  model: string;
  temperature: number;
  maxTokens: number;
  systemPrompt?: string;
}

// TODO: Add more types as RAG implementation progresses
