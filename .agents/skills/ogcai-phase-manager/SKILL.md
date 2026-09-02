---
name: ogcai-phase-manager
description: Manage OGCAI project phases, check progress across all phase documents, update split-plans, and run test suites with minimal tokens.
---

# OGCAI Phase Manager Skill

Use this skill to quickly check, advance, or verify development phases in the **OGCAI** workspace.

## 📌 Phase Document Map
- **Master Plan:** [plan.md](file:///d:/OGCAI/plan.md)
- **Phase 1 (Core Engine & Auto-Routing):** [docs/phases/phase1_core_engine.md](file:///d:/OGCAI/docs/phases/phase1_core_engine.md)
- **Phase 2 (Memory & Vault):** [docs/phases/phase2_memory_vault.md](file:///d:/OGCAI/docs/phases/phase2_memory_vault.md)
- **Phase 3 (Modules & Tools):** [docs/phases/phase3_modules_tools.md](file:///d:/OGCAI/docs/phases/phase3_modules_tools.md)
- **Phase 4 (Frontend UI):** [docs/phases/phase4_frontend_ui.md](file:///d:/OGCAI/docs/phases/phase4_frontend_ui.md)
- **Phase 5 (Packaging & Tuning):** [docs/phases/phase5_optimization_packaging.md](file:///d:/OGCAI/docs/phases/phase5_optimization_packaging.md)

## 🚀 Quick Commands
1. **Run Backend Test Suite:**
   ```powershell
   cd d:\OGCAI\backend; .venv\Scripts\python.exe -m pytest tests/
   ```
2. **Start Backend Server:**
   ```powershell
   cd d:\OGCAI\backend; .venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
   ```
3. **Check Ollama Status:**
   ```powershell
   Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -Method Get
   ```

## 📋 Rule for Updating Status
Whenever a phase task is worked on or completed:
1. Update the checkboxes `[x]` and status labels `[🔄 กำลังพัฒนา]` / `[✅ เสร็จสมบูรณ์]` in the corresponding `docs/phases/phaseX_*.md` file.
2. Update the progress table in [plan.md](file:///d:/OGCAI/plan.md).
