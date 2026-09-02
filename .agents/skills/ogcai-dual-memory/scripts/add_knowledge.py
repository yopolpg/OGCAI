#!/usr/bin/env python3
"""
OGCAI Dual-Memory & Knowledge Manager CLI
=========================================
Synchronizes and stores knowledge in 2 directions:
1. OGCAI AI Core Layer (SQLite Database: Profile Facts, Starred Knowledge | ChromaDB Vector Vault)
2. Antigravity Agent Layer (.agents/rules/ and workspace knowledge documents)
"""

import sys
import os
import argparse
import asyncio
from pathlib import Path
from typing import Optional

# Setup root path so backend modules can be imported
ROOT_DIR = Path(__file__).resolve().parents[4] # d:\OGCAI
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# pyrefly: ignore [missing-import]
from app.config import settings
# pyrefly: ignore [missing-import]
from app.db.database import AsyncSessionLocal
# pyrefly: ignore [missing-import]
from app.db.repository import DatabaseRepository
# pyrefly: ignore [missing-import]
from app.services.rag_service import rag_service

RULES_DIR = ROOT_DIR / ".agents" / "rules"
RULES_DIR.mkdir(parents=True, exist_ok=True)
FACTS_RULE_FILE = RULES_DIR / "user_profile_facts.md"


async def add_profile_fact(key: str, value: str, category: str = "general", sync_antigravity: bool = True):
    """Add a profile fact to OGCAI SQLite and optionally sync to Antigravity rules."""
    async with AsyncSessionLocal() as session:
        fact = await DatabaseRepository.set_profile_fact(
            session=session,
            key=key,
            value=value,
            category=category,
            confidence=1.0
        )
        await session.commit()
        print(f"[OGCAI AI Core] Saved Fact to SQLite: {key} = '{value}' (category: {category})")

    if sync_antigravity:
        await sync_all_facts_to_antigravity()


async def add_vault_document(filename: str, content: str, reindex: bool = True):
    """Save document into storage/vault/ and auto-index into ChromaDB vector database."""
    settings.VAULT_DIR.mkdir(parents=True, exist_ok=True)
    file_path = settings.VAULT_DIR / filename
    file_path.write_text(content, encoding="utf-8")
    print(f"[OGCAI Vault] Saved file to {file_path}")

    if reindex:
        chunks = rag_service.index_file(file_path)
        print(f"[OGCAI ChromaDB] Indexed {chunks} semantic vector chunks from '{filename}'")


async def add_starred_knowledge(title: str, content: str, summary: str = "", tags: str = ""):
    """Add a permanent starred knowledge entry to OGCAI database."""
    async with AsyncSessionLocal() as session:
        item = await DatabaseRepository.create_starred_knowledge(
            session=session,
            title=title,
            content=content,
            summary=summary,
            tags=tags
        )
        await session.commit()
        print(f"[OGCAI Starred Knowledge] Saved item '{title}' (ID: {item.id})")


async def sync_all_facts_to_antigravity():
    """Export all profile facts from OGCAI SQLite database into Antigravity rule markdown."""
    async with AsyncSessionLocal() as session:
        facts = await DatabaseRepository.get_all_profile_facts(session)

    content_lines = [
        "# User Profile & Long-Term Preferences (OGCAI 2-Way Memory Sync)",
        "",
        "> This file is auto-synchronized between the OGCAI AI Core and the Antigravity Agent.",
        "> Always reference these enduring facts and preferences when assisting the user.",
        "",
        "## Active Profile Facts",
        ""
    ]

    if not facts:
        content_lines.append("_No profile facts recorded yet._\n")
    else:
        for f in facts:
            content_lines.append(f"- **{f.key}** (`{f.category}`): {f.value}")
        content_lines.append("")

    FACTS_RULE_FILE.write_text("\n".join(content_lines), encoding="utf-8")
    print(f"[Antigravity Rules] Synced {len(facts)} profile facts to {FACTS_RULE_FILE}")


def parse_args():
    parser = argparse.ArgumentParser(description="OGCAI 2-Way Knowledge & Memory Synchronization CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Fact command
    fact_parser = subparsers.add_parser("fact", help="Add or update user profile fact")
    fact_parser.add_argument("--key", "-k", required=True, help="Fact key identifier (e.g. user_name, career)")
    fact_parser.add_argument("--value", "-v", required=True, help="Fact detail or preference value")
    fact_parser.add_argument("--category", "-c", default="general", help="Category: personal, goal, constraint, health, preference")
    fact_parser.add_argument("--no-antigravity", action="store_true", help="Do not sync to Antigravity rules")

    # Vault command
    vault_parser = subparsers.add_parser("vault", help="Add document to Vault & ChromaDB vector store")
    vault_parser.add_argument("--filename", "-f", required=True, help="Filename (e.g. business_rules.md, knowledge.txt)")
    vault_parser.add_argument("--content", help="Text content to save into the file")
    vault_parser.add_argument("--from-file", help="Source file path to copy/import into the vault")
    vault_parser.add_argument("--no-index", action="store_true", help="Skip ChromaDB indexing")

    # Starred command
    starred_parser = subparsers.add_parser("starred", help="Add starred knowledge item")
    starred_parser.add_argument("--title", "-t", required=True, help="Knowledge title")
    starred_parser.add_argument("--content", required=True, help="Detailed content or response snippet")
    starred_parser.add_argument("--summary", "-s", default="", help="Short summary")
    starred_parser.add_argument("--tags", default="", help="Comma-separated tags")

    # Sync command
    subparsers.add_parser("sync", help="Force sync all OGCAI facts into Antigravity rules")

    return parser.parse_args()


async def main():
    args = parse_args()
    if not args.command:
        print("Usage: python add_knowledge.py [fact|vault|starred|sync] --help")
        return

    if args.command == "fact":
        await add_profile_fact(
            key=args.key,
            value=args.value,
            category=args.category,
            sync_antigravity=not args.no_antigravity
        )
    elif args.command == "vault":
        content = args.content or ""
        if args.from_file:
            src_path = Path(args.from_file)
            if src_path.exists():
                content = src_path.read_text(encoding="utf-8", errors="ignore")
            else:
                print(f"Error: Source file {src_path} not found.")
                return

        if not content:
            print("Error: Provide either --content or --from-file.")
            return

        await add_vault_document(
            filename=args.filename,
            content=content,
            reindex=not args.no_index
        )
    elif args.command == "starred":
        await add_starred_knowledge(
            title=args.title,
            content=args.content,
            summary=args.summary,
            tags=args.tags
        )
    elif args.command == "sync":
        await sync_all_facts_to_antigravity()


if __name__ == "__main__":
    asyncio.run(main())
