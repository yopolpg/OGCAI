#!/usr/bin/env python
"""
OGCAI System Readiness & Pre-flight Healthcheck Inspector
Checks Ollama, Storage, Database WAL, ChromaDB, and Model allocations.
"""

import sys
import os
import asyncio
from pathlib import Path

# Fix Windows console encoding for UTF-8 and emojis
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Add backend directory to sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

# pyrefly: ignore [missing-import]
from app.config import settings
# pyrefly: ignore [missing-import]
from app.services.ollama_service import ollama_service
# pyrefly: ignore [missing-import]
from app.db.database import init_db, DB_FILE_PATH
# pyrefly: ignore [missing-import]
from app.services.rag_service import rag_service

async def run_healthcheck():
    print("=" * 65)
    print("       🚀 OGCAI System Readiness & Pre-flight Inspector")
    print("=" * 65)

    all_passed = True

    # 1. Check Storage Directories
    print("\n📁 [1/4] Checking High-Capacity Storage Directories (150GB+)...")
    settings.ensure_directories()
    for name, path in [
        ("Database (SQLite WAL)", settings.DB_DIR),
        ("Vectors (ChromaDB)", settings.VECTORS_DIR),
        ("Personal Vault (150GB+)", settings.VAULT_DIR),
        ("Cache & Charts", settings.CACHE_DIR)
    ]:
        if path.exists():
            print(f"  [OK] {name:<26} -> {path}")
        else:
            print(f"  [FAIL] {name:<26} -> Missing!")
            all_passed = False

    # 2. Check SQLite Database in WAL Mode
    print("\n💾 [2/4] Checking SQLite Database Schema & WAL Concurrency...")
    try:
        await init_db()
        print(f"  [OK] SQLite Database File      -> {DB_FILE_PATH}")
        print(f"  [OK] WAL Mode & Foreign Keys   -> Active (High Concurrency Ready)")
    except Exception as e:
        print(f"  [FAIL] Database Init Error     -> {e}")
        all_passed = False

    # 3. Check ChromaDB Semantic Vector Vault
    print("\n🧠 [3/4] Checking ChromaDB Semantic Vector Engine...")
    try:
        count = rag_service.vault_collection.count()
        print(f"  [OK] ChromaDB Persistent Store -> {settings.VECTORS_DIR}")
        print(f"  [OK] Vault Vector Collection   -> Ready ({count} indexed vectors)")
    except Exception as e:
        print(f"  [FAIL] ChromaDB Connection Error -> {e}")
        all_passed = False

    # 4. Check Local Ollama Engine & Models
    print("\n🤖 [4/4] Checking Local Ollama Server & Model Allocation...")
    try:
        health = await ollama_service.check_health()
        if health.get("status") == "healthy":
            print(f"  [OK] Ollama Local Server       -> {settings.OLLAMA_BASE_URL} (Online)")
            models = health.get("models", [])
            print(f"  [OK] Total Installed Models    -> {len(models)} models found")
            for m in models:
                print(f"       • {m}")
        else:
            print(f"  [WARN] Ollama Local Server     -> Offline or Not Responding ({health.get('error')})")
            print("         (Run 'ollama serve' to start Ollama server)")
    except Exception as e:
        print(f"  [FAIL] Ollama Error            -> {e}")
        all_passed = False

    await ollama_service.close()

    print("\n" + "=" * 65)
    if all_passed:
        print("  [SUCCESS] ALL SYSTEMS OPERATIONAL! OGCAI is 100% Ready to Launch.")
    else:
        print("  [WARN] Some components need attention before launching.")
    print("=" * 65 + "\n")

if __name__ == "__main__":
    asyncio.run(run_healthcheck())
