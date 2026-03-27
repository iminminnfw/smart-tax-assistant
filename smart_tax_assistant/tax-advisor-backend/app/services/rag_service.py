"""
RAG Service - Qdrant Version
Version: Support Qdrant Vector Database + Ollama/BGE-M3/OpenAI Embeddings

Embedding options (config: embedding_provider):
  - "ollama"  : Ollama model (qwen2.5:14b, 5120 dim)
  - "bge-m3"  : BAAI/bge-m3 via sentence-transformers (1024 dim, multilingual, 8192 tokens)
  - "openai"  : OpenAI text-embedding-ada-002 (1536 dim)

BGE-M3 ให้ผลดีที่สุดสำหรับภาษาไทย + กฎหมาย เพราะรองรับ:
  1. Multilingual (ภาษาไทยเชิงลึก)
  2. 8192 token context (มาตรายาวๆ ครบในหนึ่งเวกเตอร์)
  3. Hybrid Dense+Sparse search (จับทั้ง semantic + exact keyword)
ref: BGE-M3 (arxiv), NitiBench
"""

from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from typing import List
import traceback

from app.config import settings


# ─────────────────────────────────────────────────────────────────────────────
# BGE-M3 Embedding wrapper (LangChain compatible)
# ─────────────────────────────────────────────────────────────────────────────

class BGEM3Embeddings:
    """BAAI/bge-m3 embedding via sentence-transformers (LangChain compatible)

    - 1024 dimensions, multilingual, 8192 token context
    - Dense embeddings (ใช้กับ Qdrant cosine similarity)
    """

    def __init__(self, model_name: str = "BAAI/bge-m3"):
        try:
            from sentence_transformers import SentenceTransformer
            print(f"   Loading BGE-M3: {model_name}...")
            self.model = SentenceTransformer(model_name)
            self.dimension = self.model.get_sentence_embedding_dimension()
            print(f"   BGE-M3 loaded (dim={self.dimension})")
        except ImportError:
            raise ImportError(
                "sentence-transformers is required for BGE-M3. "
                "Install with: pip install sentence-transformers"
            )

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        embedding = self.model.encode([text], normalize_embeddings=True)
        return embedding[0].tolist()


def create_embeddings():
    """สร้าง embedding instance ตาม config"""
    provider = settings.embedding_provider

    if provider == "bge-m3":
        print(f"   RAG using BGE-M3 Embeddings (multilingual, 8192 token context)")
        return BGEM3Embeddings(), 1024

    elif provider == "ollama" or settings.use_ollama:
        from langchain_ollama import OllamaEmbeddings
        print(f"   RAG using Ollama Embeddings: {settings.ollama_model}")
        emb = OllamaEmbeddings(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
        )
        return emb, 5120

    else:
        print(f"   RAG using OpenAI Embeddings")
        emb = OpenAIEmbeddings(openai_api_key=settings.openai_api_key)
        return emb, 1536


class RAGService:
    """RAG Service สำหรับ Qdrant Vector Database"""

    def __init__(self):
        self.embeddings, self._vector_size = create_embeddings()
        self.vector_store = None
        self.qdrant_client = None
        self._connect_to_qdrant()
    
    def _connect_to_qdrant(self):
        """เชื่อมต่อกับ Qdrant"""
        try:
            print(f"🔍 Connecting to Qdrant at: {settings.qdrant_url}")
            print(f"📦 Collection: {settings.qdrant_collection_name}")
            
            # สร้าง Qdrant Client
            self.qdrant_client = QdrantClient(
                url=settings.qdrant_url,
                timeout=10
            )
            
            # ตรวจสอบว่า Collection มีอยู่หรือไม่
            collections = self.qdrant_client.get_collections()
            collection_names = [c.name for c in collections.collections]
            
            print(f"📋 Available collections: {collection_names}")
            
            if settings.qdrant_collection_name not in collection_names:
                print(f"❌ Collection '{settings.qdrant_collection_name}' not found!")
                print(f"💡 Available collections: {collection_names}")
                print(f"💡 Please check your QDRANT_COLLECTION_NAME in .env")
                self.vector_store = None
                return
            
            # สร้าง Vector Store
            self.vector_store = QdrantVectorStore(
                client=self.qdrant_client,
                collection_name=settings.qdrant_collection_name,
                embedding=self.embeddings
            )
            
            print(f"✅ Qdrant Vector Store connected successfully!")
            
        except Exception as e:
            print(f"❌ Failed to connect to Qdrant: {e}")
            print(f"💡 Make sure Qdrant is running at: {settings.qdrant_url}")
            print(f"💡 Start Qdrant: docker run -p 6333:6333 qdrant/qdrant")
            traceback.print_exc()
            self.vector_store = None
            self.qdrant_client = None
    
    async def retrieve_relevant_documents(
        self, 
        query: str,
        k: int = None
    ) -> List:
        """
        ดึงเอกสารที่เกี่ยวข้องจาก Qdrant
        
        Args:
            query: คำค้นหา
            k: จำนวนเอกสารที่ต้องการ (ใช้ค่าจาก config ถ้าไม่ระบุ)
            
        Returns:
            List ของเอกสาร
        """
        if self.vector_store is None:
            print("⚠️ Qdrant Vector Store not available - returning empty list")
            return []
        
        if k is None:
            k = settings.rag_top_k
        
        try:
            print(f"🔍 Searching Qdrant for: '{query[:50]}...' (top {k})")

            try:
                docs = self.vector_store.similarity_search(query, k=k)
            except Exception:
                # fallback: exact search (bypass HNSW index)
                print("⚠️  HNSW search failed — retrying with exact search")
                from qdrant_client.models import SearchParams
                docs = self.vector_store.similarity_search(
                    query, k=k,
                    search_params=SearchParams(exact=True)
                )

            print(f"✅ Retrieved {len(docs)} documents from Qdrant")

            for i, doc in enumerate(docs[:2]):
                content_preview = doc.page_content[:100].replace('\n', ' ')
                print(f"   Doc {i+1}: {content_preview}...")

            return docs

        except Exception as e:
            print(f"❌ Qdrant retrieval error: {e}")
            traceback.print_exc()
            return []
    
    def is_available(self) -> bool:
        """ตรวจสอบว่า Qdrant Vector Store พร้อมใช้งานหรือไม่"""
        return self.vector_store is not None
    
    def get_collection_info(self) -> dict:
        """ดึงข้อมูล Collection"""
        if self.qdrant_client is None:
            return {"status": "not_connected"}
        
        try:
            collection = self.qdrant_client.get_collection(
                collection_name=settings.qdrant_collection_name
            )
            return {
                "status": "connected",
                "name": settings.qdrant_collection_name,
                "points_count": collection.points_count,
                "vectors_count": collection.vectors_count
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }