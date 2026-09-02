from typing import List, Dict, Any, Optional
from pathlib import Path
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, HTTPException, UploadFile, File
# pyrefly: ignore [missing-import]
from pydantic import BaseModel
from app.config import settings
from app.services.rag_service import rag_service
from app.core.security import safe_path_resolve, validate_filename

router = APIRouter(prefix="/api/vault", tags=["vault"])

class VaultSearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 3

@router.get("/files")
async def list_files():
    """List all personal knowledge vault files in storage/vault/."""
    files = rag_service.list_vault_files()
    return {
        "vault_directory": str(settings.VAULT_DIR),
        "total_files": len(files),
        "files": files
    }

@router.post("/index")
async def index_vault():
    """Scan and index/re-index all vault documents into ChromaDB Vector Store."""
    stats = rag_service.index_vault_directory()
    return {
        "status": "completed",
        "details": stats
    }

@router.post("/search")
async def search_vault(req: VaultSearchRequest):
    """Perform semantic vector similarity search against the 150GB+ vault collection."""
    results = rag_service.search_vault(query=req.query, top_k=req.top_k or 3)
    return {
        "query": req.query,
        "results_count": len(results),
        "results": results
    }

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a new document (MD, PDF, TXT, CSV) to the personal vault and auto-index."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename required")
        
    try:
        clean_name = validate_filename(file.filename)
        save_path = safe_path_resolve(settings.VAULT_DIR, clean_name)
        
        content = await file.read()
        save_path.write_bytes(content)
        
        # Auto-index the uploaded file
        chunks = rag_service.index_file(save_path)
        
        return {
            "status": "uploaded_and_indexed",
            "filename": clean_name,
            "size_bytes": len(content),
            "chunks_indexed": chunks
        }
    except ValueError as val_err:
        raise HTTPException(status_code=403, detail=str(val_err))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")
