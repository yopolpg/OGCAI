import os
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from pypdf import PdfReader

from app.config import settings

logger = logging.getLogger("ogcai.rag_service")

class RAGService:
    def __init__(self):
        # Ensure vector and vault directories exist
        settings.VECTORS_DIR.mkdir(parents=True, exist_ok=True)
        settings.VAULT_DIR.mkdir(parents=True, exist_ok=True)
        
        self.client = chromadb.PersistentClient(
            path=str(settings.VECTORS_DIR),
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.vault_collection = self.client.get_or_create_collection(
            name="personal_vault",
            metadata={"description": "OGCAI Personal Knowledge Vault 150GB+ Embeddings"}
        )

    def _chunk_text(self, text: str, chunk_size: int = 800, overlap: int = 150) -> List[str]:
        """Split document text into overlapping semantic chunks."""
        text = text.strip()
        if not text:
            return []
        
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            start += (chunk_size - overlap)
        return chunks

    def _extract_text_from_file(self, file_path: Path) -> str:
        """Parse text content from various file formats (.md, .txt, .csv, .pdf)."""
        suffix = file_path.suffix.lower()
        try:
            if suffix in [".md", ".txt", ".csv", ".json", ".py", ".html"]:
                return file_path.read_text(encoding="utf-8", errors="ignore")
            elif suffix == ".pdf":
                reader = PdfReader(str(file_path))
                pages_text = []
                for idx, page in enumerate(reader.pages):
                    page_content = page.extract_text()
                    if page_content:
                        pages_text.append(f"[Page {idx+1}]\n{page_content}")
                return "\n\n".join(pages_text)
            else:
                # Fallback to plain text read
                return file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {e}")
            return ""

    def index_file(self, file_path: Path) -> int:
        """Parse, chunk, and index a single document file into ChromaDB."""
        if not file_path.exists():
            return 0
            
        content = self._extract_text_from_file(file_path)
        if not content:
            return 0

        chunks = self._chunk_text(content)
        if not chunks:
            return 0

        file_id = hashlib.md5(str(file_path.relative_to(settings.STORAGE_DIR)).encode()).hexdigest()
        
        # Delete existing chunks for this file if any (re-indexing support)
        try:
            self.vault_collection.delete(where={"file_id": file_id})
        except Exception:
            pass

        ids = [f"{file_id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "file_id": file_id,
                "filename": file_path.name,
                "relative_path": str(file_path.relative_to(settings.VAULT_DIR)) if file_path.is_relative_to(settings.VAULT_DIR) else file_path.name,
                "chunk_index": i,
                "total_chunks": len(chunks)
            }
            for i in range(len(chunks))
        ]

        self.vault_collection.add(
            documents=chunks,
            metadatas=metadatas,
            ids=ids
        )
        logger.info(f"Indexed {len(chunks)} chunks from {file_path.name}")
        return len(chunks)

    def index_vault_directory(self) -> Dict[str, Any]:
        """Scan and index all supported files in storage/vault/."""
        indexed_count = 0
        total_chunks = 0
        supported_exts = {".md", ".txt", ".csv", ".pdf", ".json", ".py"}

        for file_path in settings.VAULT_DIR.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in supported_exts:
                chunks = self.index_file(file_path)
                if chunks > 0:
                    indexed_count += 1
                    total_chunks += chunks

        return {
            "files_indexed": indexed_count,
            "total_chunks": total_chunks,
            "total_vectors_in_db": self.vault_collection.count()
        }

    def search_vault(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Search the vault collection for semantically relevant chunks."""
        if not query.strip() or self.vault_collection.count() == 0:
            return []

        try:
            results = self.vault_collection.query(
                query_texts=[query],
                n_results=min(top_k, self.vault_collection.count())
            )
            
            output = []
            docs = results.get("documents", [[]])[0]
            metas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0] if "distances" in results else [0.0] * len(docs)
            
            for doc, meta, dist in zip(docs, metas, distances):
                output.append({
                    "content": doc,
                    "filename": meta.get("filename", ""),
                    "path": meta.get("relative_path", ""),
                    "chunk_index": meta.get("chunk_index", 0),
                    "distance": dist
                })
            return output
        except Exception as e:
            logger.error(f"Search error in vault collection: {e}")
            return []

    def build_rag_context(self, query: str, top_k: int = 3) -> str:
        """Format retrieved vault chunks into a prompt-ready context block."""
        results = self.search_vault(query, top_k=top_k)
        if not results:
            return ""

        context_blocks = ["[ข้อมูลอ้างอิงจากคลังเอกสารส่วนตัว (Personal Vault)]"]
        for idx, item in enumerate(results, 1):
            context_blocks.append(
                f"--- เอกสารที่ {idx}: {item['filename']} (ส่วนที่ {item['chunk_index']+1}) ---\n{item['content']}"
            )
        return "\n\n".join(context_blocks)

    def list_vault_files(self) -> List[Dict[str, Any]]:
        """List all files in the vault folder with size and status."""
        files = []
        for file_path in settings.VAULT_DIR.rglob("*"):
            if file_path.is_file():
                stat = file_path.stat()
                files.append({
                    "name": file_path.name,
                    "relative_path": str(file_path.relative_to(settings.VAULT_DIR)),
                    "size_bytes": stat.st_size,
                    "size_kb": round(stat.st_size / 1024, 2),
                    "modified_at": stat.st_mtime
                })
        return files

rag_service = RAGService()
