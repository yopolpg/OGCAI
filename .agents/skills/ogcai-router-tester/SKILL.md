---
name: ogcai-router-tester
description: Test, benchmark, and debug the OGCAI Auto-Model Switcher Engine and Ollama local streaming endpoints.
---

# OGCAI Router & Model Tester Skill

Use this skill to diagnose model selection, test streaming responses, and verify Ollama connectivity.

## 🎯 Model Mapping Reference
- **`qwen2.5-coder:7b`** (🟢 Default): General Chat, Thai conversation, Daily Tasks, Creative Writing.
- **`llama3.1:8b`** (🟡 Advisor): Life Advice, Health Coaching, Open-ended Philosophy, Routine Planning.
- **`deepseek-coder-v2:16b`** (🟣 Heavy Logic): Complex Math, Data Analysis, Algorithmic Coding, Complex Logic.
- **`qwen2.5:3b`** (⚪ Fast Worker): Intent Classification (~50ms), Background Memory Extraction.
- **`phi3.5:latest`** (🔵 Fallback): Fast lightweight backup model.

## 🧪 Quick Test Commands
1. **Test Router Classification via API:**
   ```powershell
   Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/route" -Method Post -ContentType "application/json" -Body '{"message": "ช่วยสอนคำนวณดอกเบี้ยทบต้นและเขียนโค้ดสูตรคณิตศาสตร์ให้หน่อย"}'
   ```
2. **Test Chat Stream Endpoint:**
   ```powershell
   Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/chat" -Method Post -ContentType "application/json" -Body '{"message": "สวัสดีครับ แนะนำตัวหน่อย"}'
   ```
3. **List Active Models:**
   ```powershell
   Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/models" -Method Get
   ```
