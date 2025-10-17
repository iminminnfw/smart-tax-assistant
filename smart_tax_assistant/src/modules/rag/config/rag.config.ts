/**
 * RAG System Configuration
 *
 * TODO: Move sensitive values to environment variables before production
 */

export const RAG_CONFIG = {
  /**
   * Embedding model configuration
   */
  embedding: {
    model: 'text-embedding-3-small', // OpenAI default
    dimensions: 1536,
    batchSize: 100,
    maxInputTokens: 8191,
  },

  /**
   * Document chunking strategy
   */
  chunking: {
    chunkSize: 1000, // tokens per chunk
    chunkOverlap: 200, // overlap between chunks
    separators: ['\n\n', '\n', '. ', ' '],
  },

  /**
   * Vector search/retrieval parameters
   */
  retrieval: {
    topK: 5, // number of similar chunks to retrieve
    minSimilarityScore: 0.7, // minimum cosine similarity
    maxContextTokens: 4000, // max tokens for LLM context
  },

  /**
   * LLM generation settings
   */
  generation: {
    model: 'gpt-4o', // OpenAI GPT-4o
    maxTokens: 1000,
    temperature: 0.7,
    topP: 1,
    frequencyPenalty: 0,
    presencePenalty: 0,
  },

  /**
   * Supported languages
   */
  languages: {
    supported: ['th', 'en'],
    default: 'th',
  },

  /**
   * Caching strategy
   */
  cache: {
    enabled: true,
    ttl: 3600, // seconds (1 hour)
    maxSize: 1000, // max cached items
  },

  /**
   * Rate limiting
   */
  rateLimit: {
    embedding: {
      requestsPerMinute: 60,
      tokensPerMinute: 150000,
    },
    generation: {
      requestsPerMinute: 20,
      tokensPerMinute: 40000,
    },
  },

  /**
   * Vector database configuration
   * TODO: Choose vector DB (Pinecone, Supabase, Qdrant, etc.)
   */
  vectorDB: {
    provider: 'pending', // 'pinecone' | 'supabase' | 'qdrant' | 'weaviate'
    indexName: 'smarttax-documents',
    namespace: 'production',
  },
} as const;

/**
 * Environment-specific overrides
 * These values should come from .env in production
 */
export const getRAGConfig = () => {
  return {
    ...RAG_CONFIG,
    apiKeys: {
      openai: process.env.OPENAI_API_KEY || '',
      pinecone: process.env.PINECONE_API_KEY || '',
    },
    vectorDB: {
      ...RAG_CONFIG.vectorDB,
      apiKey: process.env.VECTOR_DB_API_KEY || '',
      environment: process.env.VECTOR_DB_ENVIRONMENT || 'development',
    },
  };
};

/**
 * Validation helper
 */
export const validateRAGConfig = (): boolean => {
  const config = getRAGConfig();

  // Check for required API keys
  if (!config.apiKeys.openai) {
    console.warn('⚠️  OPENAI_API_KEY not set - RAG will not work');
    return false;
  }

  return true;
};
