"""
สคริปต์สำหรับยัดข้อมูลเข้า Qdrant Vector Database

รองรับ 2 โหมด chunking:
  1. Hierarchy-Aware Chunking (default) — แบ่งตามโครงสร้างเอกสาร (## / ### / ---)
     เก็บ metadata ว่า chunk อยู่ภายใต้ section/subsection ไหน
     ref: NitiBench (arxiv.org/abs/2502.10868)

  2. Fixed-size Chunking (legacy) — RecursiveCharacterTextSplitter ตาม chunk_size
"""

import re
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

try:
    from langchain_community.document_loaders import PyPDFLoader
    HAS_PDF_LOADER = True
except ImportError:
    HAS_PDF_LOADER = False
    print("⚠️  PyPDFLoader not available. Install: pip install langchain-community pypdf")


# ─────────────────────────────────────────────────────────────────────────────
# PDF Text Cleanup for Thai Documents
# ─────────────────────────────────────────────────────────────────────────────

def clean_thai_pdf_text(text: str) -> str:
    """แก้ปัญหา PyPDF แยก Thai text เป็นตัวอักษรเดี่ยวทีละบรรทัด

    เช่น:
        ระดับ
        สูง

        และ
        ต้อง
    → "ระดับสูง และต้อง"
    """
    # 1. แทนที่ newlines ระหว่างตัวอักษรไทย/อังกฤษ ด้วยช่องว่าง
    #    แต่เก็บ double-newline (paragraph break) ไว้
    text = re.sub(r'\n{3,}', '\n\n', text)  # normalize 3+ newlines → 2

    lines = text.split('\n')
    merged = []
    buffer = ""

    for line in lines:
        stripped = line.strip()

        # บรรทัดว่าง = paragraph break
        if not stripped:
            if buffer:
                merged.append(buffer)
                buffer = ""
            merged.append("")  # keep paragraph break
            continue

        # ถ้า line เป็น markdown header → flush buffer แล้วเริ่ม line ใหม่
        if stripped.startswith('#'):
            if buffer:
                merged.append(buffer)
                buffer = ""
            merged.append(stripped)
            continue

        # ถ้า line สั้น (< 40 chars) และไม่จบด้วย punctuation → น่าจะเป็น fragment
        if len(stripped) < 40 and not re.search(r'[.!?\)）。、，：；]$', stripped):
            # ต่อเข้า buffer โดยไม่เว้นวรรคถ้าเป็นภาษาไทยต่อไทย
            if buffer:
                last_char = buffer[-1] if buffer else ''
                first_char = stripped[0] if stripped else ''
                # Thai-Thai หรือ Thai-space-Thai → ต่อโดยตรง
                if _is_thai(last_char) and _is_thai(first_char):
                    buffer += stripped
                else:
                    buffer += " " + stripped
            else:
                buffer = stripped
        else:
            # line ยาวพอ → เป็นประโยคเต็ม
            if buffer:
                last_char = buffer[-1] if buffer else ''
                first_char = stripped[0] if stripped else ''
                if _is_thai(last_char) and _is_thai(first_char):
                    buffer += stripped
                else:
                    buffer += " " + stripped
                merged.append(buffer)
                buffer = ""
            else:
                merged.append(stripped)

    if buffer:
        merged.append(buffer)

    # ลบบรรทัดว่างซ้ำ
    result = '\n'.join(merged)
    result = re.sub(r'\n{3,}', '\n\n', result)
    return result.strip()


def _is_thai(char: str) -> bool:
    """ตรวจว่าตัวอักษรเป็นภาษาไทยหรือไม่"""
    if not char:
        return False
    return '\u0E00' <= char <= '\u0E7F'


# ─────────────────────────────────────────────────────────────────────────────
# Hierarchy-Aware Text Splitter for Thai Legal Documents
# ─────────────────────────────────────────────────────────────────────────────

class ThaiLegalTextSplitter:
    """แบ่งเอกสารกฎหมายไทยตามโครงสร้างลำดับชั้น (Hierarchy-Aware Chunking)

    แทนที่จะตัดตามจำนวนตัวอักษรตายตัว (fixed-size) จะตัดตามโครงสร้างเอกสาร:
    - ระดับ 1: `---` (major section divider)
    - ระดับ 2: `## ` (section header)
    - ระดับ 3: `### ` (sub-section header)

    แต่ละ chunk จะเก็บ metadata ว่าอยู่ภายใต้ section/subsection ไหน
    เพื่อให้ retrieval ได้บริบทครบถ้วน

    ถ้า chunk ยาวเกิน max_chunk_size จะ fallback ใช้ RecursiveCharacterTextSplitter
    """

    def __init__(self, max_chunk_size: int = 2000):
        self.max_chunk_size = max_chunk_size
        self.fallback_splitter = RecursiveCharacterTextSplitter(
            chunk_size=max_chunk_size,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

    def split_documents(self, documents: list) -> list:
        """แบ่ง list ของ Document ด้วย hierarchy-aware chunking"""
        all_chunks = []
        for doc in documents:
            chunks = self._split_text_hierarchical(
                doc.page_content,
                base_metadata=doc.metadata,
            )
            all_chunks.extend(chunks)
        return all_chunks

    def _split_text_hierarchical(self, text: str, base_metadata: dict) -> list:
        """แบ่งข้อความตามโครงสร้าง markdown headers"""
        chunks = []
        current_section = ""
        current_subsection = ""

        # แบ่งด้วย --- (major divider) ก่อน แล้วแบ่ง ## / ### ภายใน
        major_sections = re.split(r"\n---\n", text)

        for section_text in major_sections:
            section_text = section_text.strip()
            if not section_text:
                continue

            # แบ่ง ## headers ภายใน major section
            h2_parts = re.split(r"\n(?=## )", section_text)

            for h2_part in h2_parts:
                h2_part = h2_part.strip()
                if not h2_part:
                    continue

                # จับ section header
                h2_match = re.match(r"^## (.+?)$", h2_part, re.MULTILINE)
                if h2_match:
                    current_section = h2_match.group(1).strip()
                    current_subsection = ""

                # แบ่ง ### headers ภายใน ## section
                h3_parts = re.split(r"\n(?=### )", h2_part)

                for h3_part in h3_parts:
                    h3_part = h3_part.strip()
                    if not h3_part:
                        continue

                    # จับ subsection header
                    h3_match = re.match(r"^### (.+?)$", h3_part, re.MULTILINE)
                    if h3_match:
                        current_subsection = h3_match.group(1).strip()

                    # สร้าง chunk พร้อม metadata
                    metadata = {
                        **base_metadata,
                        "section": current_section,
                        "subsection": current_subsection,
                        "hierarchy": f"{current_section} > {current_subsection}" if current_subsection else current_section,
                    }

                    # ถ้า chunk ยาวเกิน max_chunk_size — fallback split
                    if len(h3_part) > self.max_chunk_size:
                        sub_docs = self.fallback_splitter.create_documents(
                            [h3_part],
                            metadatas=[metadata],
                        )
                        chunks.extend(sub_docs)
                    else:
                        chunks.append(Document(
                            page_content=h3_part,
                            metadata=metadata,
                        ))

        return chunks

class DataIngestor:
    """
    จัดการการยัดข้อมูลเข้า Vector Database
    """

    def __init__(self):
        self.qdrant_client = QdrantClient(url=settings.qdrant_url)

        # เลือก Embeddings ตาม config (ใช้ factory เดียวกับ rag_service)
        from app.services.rag_service import create_embeddings
        self.embeddings, self.vector_size = create_embeddings()

        # Hierarchy-Aware Chunking (default) — แบ่งตามโครงสร้างเอกสาร
        self.hierarchy_splitter = ThaiLegalTextSplitter(
            max_chunk_size=settings.rag_chunk_size * 2,  # อนุญาตให้ section ยาวกว่า fixed-size
        )

        # Fixed-size Chunking (legacy fallback)
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
        
        # --- เพิ่มส่วนนี้: โหลดไฟล์ .pdf ---
        pdf_files = glob.glob(f"{directory}/*.pdf")
        print(f"Found {len(pdf_files)} PDF files")

        if pdf_files and not HAS_PDF_LOADER:
            print("[SKIP] Cannot load PDFs — missing langchain-community or pypdf")
        elif pdf_files:
            for file_path in pdf_files:
                try:
                    loader = PyPDFLoader(file_path)
                    pdf_docs = loader.load()
                    for doc in pdf_docs:
                        doc.metadata["source"] = os.path.basename(file_path)
                        doc.metadata["file_path"] = file_path
                        # Clean up broken Thai text from PDF extraction
                        original_len = len(doc.page_content)
                        doc.page_content = clean_thai_pdf_text(doc.page_content)
                        cleaned_len = len(doc.page_content)
                        if original_len != cleaned_len:
                            print(f"     [CLEAN] Page {doc.metadata.get('page', '?')}: {original_len} → {cleaned_len} chars")
                    documents.extend(pdf_docs)
                    print(f"[OK] Loaded: {os.path.basename(file_path)} ({len(pdf_docs)} pages)")
                except Exception as e:
                    print(f"[ERROR] Error loading {file_path}: {e}")
        # --- จบส่วนเพิ่ม ---

        return documents
    
    def split_documents(self, documents: list[Document], use_hierarchy: bool = True) -> list[Document]:
        """
        แบ่งเอกสารเป็น chunks

        Args:
            use_hierarchy: True = Hierarchy-Aware (ตามโครงสร้าง ## / ### / ---)
                          False = Fixed-size (RecursiveCharacterTextSplitter)
        """
        if use_hierarchy:
            print(f"\nSplitting {len(documents)} documents (Hierarchy-Aware mode)...")
            chunks = self.hierarchy_splitter.split_documents(documents)
            # แสดง hierarchy metadata
            sections = set()
            for c in chunks:
                h = c.metadata.get("hierarchy", "")
                if h:
                    sections.add(h)
            print(f"[OK] Created {len(chunks)} chunks across {len(sections)} sections")
            for s in sorted(sections)[:10]:
                print(f"     - {s}")
            if len(sections) > 10:
                print(f"     ... and {len(sections) - 10} more")
        else:
            print(f"\nSplitting {len(documents)} documents (Fixed-size mode)...")
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
        ยัดข้อมูลเข้า Qdrant ทีละ chunk พร้อม progress
        """
        import time
        from qdrant_client.models import PointStruct
        import uuid

        total = len(chunks)
        print(f"\nIngesting {total} chunks to Qdrant (one by one with progress)...")

        points = []
        for i, chunk in enumerate(chunks, 1):
            start = time.time()
            try:
                # สร้าง embedding ทีละ chunk
                vector = self.embeddings.embed_query(chunk.page_content)
                elapsed = time.time() - start
                print(f"  [{i:2d}/{total}] embedding OK ({elapsed:.1f}s) | {chunk.page_content[:60].strip()!r}")

                points.append(PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector,
                    payload={
                        "page_content": chunk.page_content,
                        **chunk.metadata,
                    }
                ))
            except Exception as e:
                print(f"  [{i:2d}/{total}] ERROR: {e}")
                raise

        # อัปโหลดทุก point เข้า Qdrant ในครั้งเดียว
        print(f"\nUploading {len(points)} points to Qdrant...")
        self.qdrant_client.upsert(
            collection_name=settings.qdrant_collection_name,
            points=points,
        )
        print(f"[OK] Successfully ingested all {total} chunks!")
    
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