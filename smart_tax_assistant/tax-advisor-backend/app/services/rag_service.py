"""
RAG Service - Qdrant Version
Version: Support Qdrant Vector Database
"""

from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from typing import List
import traceback

from app.config import settings


class RAGService:
    """RAG Service สำหรับ Qdrant Vector Database"""
    
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=settings.openai_api_key
        )
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
            
            docs = self.vector_store.similarity_search(query, k=k)
            
            print(f"✅ Retrieved {len(docs)} documents from Qdrant")
            
            # แสดง snippet ของเอกสารที่ได้
            for i, doc in enumerate(docs[:2]):  # แสดง 2 docs แรก
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