"""
สคริปต์สำหรับยัดข้อมูลเข้า Qdrant Vector Database
"""

import sys
import os
from pathlib import Path

# เพิ่ม path เพื่อ import modules
sys.path.append(str(Path(__file__).parent.parent))

from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from app.config import settings
import glob

class DataIngestor:
    """
    จัดการการยัดข้อมูลเข้า Vector Database
    """

    def __init__(self):
        self.qdrant_client = QdrantClient(url=settings.qdrant_url)

        # เลือก Embeddings ตาม config
        if settings.use_ollama:
            from langchain_ollama import OllamaEmbeddings
            print(f"🦙 Ingest using Ollama Embeddings: {settings.ollama_model}")
            self.embeddings = OllamaEmbeddings(
                model=settings.ollama_model,
                base_url=settings.ollama_base_url,
            )
            # Ollama embedding dimensions ขึ้นอยู่กับ model
            # qwen2.5:14b = 5120, qwen2.5:7b = 3584, nomic-embed-text = 768
            self.vector_size = 5120
        else:
            print(f"🤖 Ingest using OpenAI Embeddings")
            self.embeddings = OpenAIEmbeddings(
                openai_api_key=settings.openai_api_key
            )
            self.vector_size = 1536  # text-embedding-ada-002

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.rag_chunk_size,
            chunk_overlap=settings.rag_chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
    
    def load_documents_from_directory(self, directory: str) -> list[Document]:
        """
        โหลดเอกสารจาก directory
        """
        documents = []
        
        # หาไฟล์ .txt ทั้งหมด
        txt_files = glob.glob(f"{directory}/*.txt")
        
        print(f"Found {len(txt_files)} text files")
        
        for file_path in txt_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # สร้าง Document object
                doc = Document(
                    page_content=content,
                    metadata={
                        "source": os.path.basename(file_path),
                        "file_path": file_path
                    }
                )
                documents.append(doc)
                print(f"[OK] Loaded: {os.path.basename(file_path)}")

            except Exception as e:
                print(f"[ERROR] Error loading {file_path}: {e}")
        
        return documents
    
    def split_documents(self, documents: list[Document]) -> list[Document]:
        """
        แบ่งเอกสารเป็น chunks เล็กๆ
        """
        print(f"\nSplitting {len(documents)} documents into chunks...")
        chunks = self.text_splitter.split_documents(documents)
        print(f"[OK] Created {len(chunks)} chunks")
        return chunks
    
    def create_collection(self):
        """
        สร้าง Collection ใน Qdrant
        """
        try:
            # ลบ collection เดิม (ถ้ามี)
            try:
                self.qdrant_client.delete_collection(
                    collection_name=settings.qdrant_collection_name
                )
                print(f"Deleted existing collection: {settings.qdrant_collection_name}")
            except:
                pass
            
            # สร้าง collection ใหม่ (vector size ตาม embedding model)
            print(f"   Vector size: {self.vector_size}")
            self.qdrant_client.create_collection(
                collection_name=settings.qdrant_collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=Distance.COSINE
                )
            )
            print(f"[OK] Created collection: {settings.qdrant_collection_name}")
            
        except Exception as e:
            print(f"Error creating collection: {e}")
            raise
    
    def ingest_to_qdrant(self, chunks: list[Document]):
        """
        ยัดข้อมูลเข้า Qdrant
        """
        print(f"\nIngesting {len(chunks)} chunks to Qdrant...")
        
        try:
            QdrantVectorStore.from_documents(
                chunks,
                self.embeddings,
                url=settings.qdrant_url,
                collection_name=settings.qdrant_collection_name,
            )
            print(f"[OK] Successfully ingested all chunks!")
            
        except Exception as e:
            print(f"Error ingesting data: {e}")
            raise
    
    def verify_ingestion(self):
        """
        ตรวจสอบว่าข้อมูลถูกยัดเข้าไปแล้ว
        """
        try:
            collection_info = self.qdrant_client.get_collection(
                collection_name=settings.qdrant_collection_name
            )
            print(f"\n[OK] Collection Info:")
            print(f"  - Vectors count: {collection_info.vectors_count}")
            print(f"  - Points count: {collection_info.points_count}")
            
        except Exception as e:
            print(f"Error verifying ingestion: {e}")

def main():
    """
    Main function
    """
    print("=" * 60)
    print("AI Tax Advisor - Data Ingestion")
    print("=" * 60)
    
    # Path ไปยัง data directory
    data_dir = Path(__file__).parent.parent / "data" / "tax_knowledge"
    
    if not data_dir.exists():
        print(f"\nError: Directory not found: {data_dir}")
        print("Please create the directory and add .txt files")
        return
    
    print(f"\nData directory: {data_dir}")
    
    # Initialize Ingestor
    ingestor = DataIngestor()
    
    # Step 1: Load documents
    print("\n" + "=" * 60)
    print("STEP 1: Loading documents")
    print("=" * 60)
    documents = ingestor.load_documents_from_directory(str(data_dir))
    
    if not documents:
        print("\nNo documents found! Please add .txt files to:")
        print(f"  {data_dir}")
        return
    
    # Step 2: Split into chunks
    print("\n" + "=" * 60)
    print("STEP 2: Splitting documents")
    print("=" * 60)
    chunks = ingestor.split_documents(documents)
    
    # Step 3: Create collection
    print("\n" + "=" * 60)
    print("STEP 3: Creating Qdrant collection")
    print("=" * 60)
    ingestor.create_collection()
    
    # Step 4: Ingest data
    print("\n" + "=" * 60)
    print("STEP 4: Ingesting data to Qdrant")
    print("=" * 60)
    ingestor.ingest_to_qdrant(chunks)
    
    # Step 5: Verify
    print("\n" + "=" * 60)
    print("STEP 5: Verification")
    print("=" * 60)
    ingestor.verify_ingestion()
    
    print("\n" + "=" * 60)
    print("[SUCCESS] Data ingestion completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    main()