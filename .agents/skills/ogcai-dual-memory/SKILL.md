---
name: ogcai-dual-memory
description: Manage, record, and synchronize 2-way knowledge and persistent memory across both OGCAI AI Core (SQLite profile facts, ChromaDB 150GB+ Vault, Starred memories) and Antigravity Agent (workspace rules, long-term instructions, knowledge files).
---

# OGCAI Dual-Memory & Knowledge Manager Skill (การจำข้อมูล 2 ทาง)

Use this skill whenever the user asks the assistant to **remember information**, **add knowledge**, **save preferences**, or **sync memory** across both the **OGCAI Local AI Core** and the **Antigravity Pair-Programming Agent**.

---

## 🧠 2-Way Storage Architecture (สถาปัตยกรรมการจำข้อมูล 2 ทาง)

```
                       ┌──────────────────────────────────────┐
                       │           USER INSTRUCTION           │
                       │    "จำข้อมูล X", "บันทึกเอกสาร Y"     │
                       └──────────────────┬───────────────────┘
                                          │
                   ┌──────────────────────┴──────────────────────┐
                   ▼                                             ▼
       [ Channel 1: OGCAI AI Core ]                 [ Channel 2: Antigravity Agent ]
  ┌─────────────────────────────────────┐      ┌─────────────────────────────────────┐
  │ 1. SQLite: `user_profile` table     │      │ 1. Workspace Rules:                 │
  │    (Key-Value Profile Facts)        │ ───► │    `.agents/rules/user_profile_*.md`│
  │ 2. SQLite: `starred_knowledge`      │      │ 2. Knowledge Artifacts / Notes      │
  │    (Starred permanent memories)     │      │ 3. Persistent session context       │
  │ 3. ChromaDB Vector Store:           │      │                                     │
  │    `storage/vault/` (150GB+ Embed)  │      │                                     │
  └─────────────────────────────────────┘      └─────────────────────────────────────┘
```

---

## 🚀 Quick Execution Commands

The skill provides an integrated CLI tool at `d:\OGCAI\.agents\skills\ogcai-dual-memory\scripts\add_knowledge.py`.

### 1. Add / Update a Profile Fact (บันทึกข้อมูลส่วนตัว & ความชอบ)
Adds the fact to the OGCAI database and immediately mirrors it into Antigravity workspace rules:
```powershell
backend\.venv\Scripts\python.exe .agents\skills\ogcai-dual-memory\scripts\add_knowledge.py fact --key "user_preference" --value "ชอบเขียนโค้ด Clean Architecture" --category "preference"
```

### 2. Add a Knowledge File to Vault & Vector ChromaDB (เพิ่มเอกสารคลังความรู้)
Saves the file into `storage/vault/` and automatically chunks and indexes vectors into ChromaDB:
```powershell
backend\.venv\Scripts\python.exe .agents\skills\ogcai-dual-memory\scripts\add_knowledge.py vault --filename "architecture_guidelines.md" --content "# Architecture Guidelines..."
```
Or import an existing external file:
```powershell
backend\.venv\Scripts\python.exe .agents\skills\ogcai-dual-memory\scripts\add_knowledge.py vault --filename "imported_doc.md" --from-file "d:\path\to\file.md"
```

### 3. Save Starred Permanent Memory (บันทึกข้อความดาวเด่น)
```powershell
backend\.venv\Scripts\python.exe .agents\skills\ogcai-dual-memory\scripts\add_knowledge.py starred --title "เทคนิค SQLite WAL Mode" --content "ข้อควรระวังในการตั้งค่า WAL..." --summary "คู่มือ WAL" --tags "database,sqlite"
```

### 4. Force 2-Way Synchronization (สั่ง Sync ข้อมูลทั้งหมด)
Exports all database facts into `.agents/rules/user_profile_facts.md`:
```powershell
backend\.venv\Scripts\python.exe .agents\skills\ogcai-dual-memory\scripts\add_knowledge.py sync
```

---

## 🌐 HTTP REST API Reference

If the backend server is running (`http://127.0.0.1:8000`):

| Endpoint | Method | Payload | Description |
| :--- | :--- | :--- | :--- |
| `/api/profile` | `POST` | `{"key": "...", "value": "...", "category": "..."}` | Add/update profile fact |
| `/api/profile` | `GET` | _None_ | List all stored profile facts |
| `/api/vault/upload` | `POST` | `multipart/form-data (file)` | Upload document & auto-index |
| `/api/vault/index` | `POST` | _None_ | Re-index all files in `storage/vault/` |
| `/api/vault/search` | `GET` | `?query=...&top_k=3` | Semantic Vector Search |
| `/api/starred` | `POST` | `{"title": "...", "content": "...", "tags": "..."}` | Save starred knowledge |

---

## 📋 Best Practices for 2-Way Memory

1. **Categorize Clearly**: Use categories such as `personal`, `career`, `goals`, `health`, `preferences`, `constraints`.
2. **Atomic Keys**: Use clean snake_case keys (e.g. `preferred_tech_stack`, `daily_routine_wake_time`, `financial_target`).
3. **Always Sync**: Ensure facts are synced to `.agents/rules/` so Antigravity never forgets user preferences across sessions.
