# OGCAI - Technical Stack & Architecture

เอกสารนี้ระบุรายละเอียดสถาปัตยกรรม เทคโนโลยี และการจัดสรรโมเดล AI ในเครื่องสำหรับระบบ **OGCAI (Personal Local AI Assistant)**

---

## 1. ภาพรวมสถาปัตยกรรมระบบ (System Architecture)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Frontend (Modern Minimalist UI)                      │
│  - Clean Chat Workspace (หน้าต่างสนทนาคลีนตา ใช้งานง่าย ไม่รก)          │
│  - Categorized Tool Drawer (แถบเครื่องมือจัดหมวดหมู่: เงิน, สุขภาพ, เรียน)│
│  - Active Model Badge (แสดงโมเดลที่ระบบเลือกให้อัตโนมัติ + ปรับเองได้)    │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ HTTP / WebSocket (SSE Streaming)
┌────────────────────────────────────▼────────────────────────────────────┐
│                    Backend Core (Python FastAPI)                        │
├─────────────────────────────────────────────────────────────────────────┤
│ 1. 🔄 Seamless Auto-Model Switcher (วิเคราะห์ Intent & เลือกโมเดลอัตโนมัติ) │
│ 2. 🧠 Multi-tier Memory Manager (Short-term, Long-term Profile, Starred)│
│ 3. 🛠️ Local Tool Engine (Python Math/Plotting, Document Parser)         │
│ 4. 📁 Categorized Modules (Finance, Health/Routine, Study, General)      │
└────────────────────┬──────────────────────────────┬─────────────────────┘
                     │                              │
┌────────────────────▼────────┐┌────────────────────▼─────────────────────┐
│    Model Server (Ollama)    ││    Local High-Capacity Storage (150GB+)  │
│  - qwen2.5:3b (Fast Router) ││  - storage/db/ (SQLite WAL + Auto-Backup)│
│  - qwen2.5-coder:7b (Daily) ││  - storage/vectors/ (ChromaDB High-Res)  │
│  - llama3.1:8b (Advisor)    ││  - storage/vault/ (Personal Docs/PDF/CSV)│
│  - deepseek-coder-v2:16b    ││  - storage/cache/ (Prompt & Graph Cache) │
│  - phi3.5:latest            ││                                          │
└─────────────────────────────┘└──────────────────────────────────────────┘
```

---

## 2. ระบบสลับโมเดลอัตโนมัติ (Seamless Auto-Model Switching Engine)

ระบบจะวิเคราะห์ประเภทคำถามและความซับซ้อนของงานในเสี้ยววินาที แล้วเลือกโมเดลที่ทำงานนั้นได้ดีที่สุดให้อัตโนมัติ:

```
                       [คำถามจากผู้ใช้]
                               │
                ┌──────────────▼──────────────┐
                │  Fast Classifier & Router   │ (ใช้ qwen2.5:3b / Pattern Match)
                │      (~50-100 ms latency)   │
                └──────────────┬──────────────┘
                               │
       ┌───────────────────────┼───────────────────────┐
       │                       │                       │
[สนทนาทั่วไป / ภาษาไทย]  [ให้คำปรึกษา / วางแผนชีวิต]  [คำนวณซับซ้อน / Deep Logic]
       │                       │                       │
       ▼                       ▼                       ▼
 🟢 qwen2.5-coder:7b      🟡 llama3.1:8b          🟣 deepseek-coder-v2:16b
 (ตอบไว ภาษาไทยสละสลวย) (มองภาพกว้าง ลึกซึ้ง)   (ตรรกะแม่นยำสูง แก้งานยาก)
```

### เกณฑ์การสลับโมเดลอัตโนมัติ:
1. **งานทั่วไป / ภาษาไทย / ช่วยคิดงานประจำวัน ➔ `qwen2.5-coder:7b`**
   - เป็น Default Model สำหรับคำถามทั่วไป มีความเร็วสูง เข้าใจไวยากรณ์ภาษาไทยได้แม่นยำ
2. **งานให้คำปรึกษา / วางแผนชีวิต / สุขภาพ / ปรัชญา ➔ `llama3.1:8b`**
   - สลับอัตโนมัติเมื่อตรวจพบคำถามเชิงอารมณ์ คำปรึกษาเป้าหมายชีวิต หรือการสนทนาปลายเปิด
3. **งานคำนวณยาก / วิเคราะห์ข้อมูล / โค้ดเชิงลึก ➔ `deepseek-coder-v2:16b`**
   - สลับอัตโนมัติเมื่อพบสูตรคณิตศาสตร์หลายชั้น หรือโจทย์ตรรกะซับซ้อน
4. **งานเบื้องหลัง (Background Worker) ➔ `qwen2.5:3b`**
   - ทำงานเงียบๆ ในพื้นหลัง: สรุปความจำ, สกัดข้อเท็จจริงสำคัญลง Profile โดยไม่รบกวนโมเดลหลัก
5. **Manual Override Option:**
   - ผู้ใช้สามารถคลิกสลับโมเดลเองได้ตลอดเวลาผ่านปุ่ม Model Badge ที่มุมขวาบนของแชท

---

## 3. สถาปัตยกรรมการจัดเก็บข้อมูลขนาดใหญ่ (High-Capacity Storage Architecture 150GB+)

เนื่องจากมีพื้นที่จัดเก็บกว่า 150GB+ ระบบสามารถทำงานได้อย่างเต็มประสิทธิภาพโดยไม่ต้องบีบอัดหรือตัดทอนข้อมูล:

| โฟลเดอร์จัดเก็บ | เทคโนโลยีที่ใช้ | ความจุ & หน้าที่การทำงาน |
| :--- | :--- | :--- |
| **`storage/vectors/`** | **ChromaDB** (Persistent Local) | จัดเก็บ Vector Embeddings ความละเอียดสูงของเอกสาร ตำราเรียน บันทึก และคลังความรู้ รองรับการค้นหาแบบ Semantic RAG ได้อย่างแม่นยำ |
| **`storage/db/`** | **SQLite (WAL Mode)** | จัดเก็บประวัติแชทฉบับเต็มทุกเซสชัน, ข้อมูลการเงิน, บันทึกสุขภาพ, User Profile และระบบ Auto-Snapshot สำรองข้อมูลอัตโนมัติ |
| **`storage/vault/`** | **Personal Knowledge Vault** | คลังเอกสารส่วนตัว (PDFs, Markdown Notes, Excel/CSVs, Books) ให้ AI เข้าถึงและประมวลผลได้โดยตรง |
| **`storage/cache/`** | **Local Cache Engine** | แคชสำหรับผลลัพธ์การคำนวณ, กราฟสถิติที่สร้างขึ้น, และ Context Cache ของโมเดลเพื่อความเร็วสูงสุด |

---

## 4. การออกแบบ Frontend: ใช้งานง่ายที่สุด เครื่องมือครบ ไม่รกตา (Clean & Intuitive UI)

### 4.1 ปรัชญาการออกแบบ (Design Principles)
- **Zero-Clutter Workspace:** หน้าจอหลักมีเฉพาะประวัติการคุยและกล่องข้อความที่สะอาดตา (Minimalist Dark Glass UI)
- **Categorized Drawer / Floating Palette:** เครื่องมือเฉพาะด้านถูกจัดเป็นหมวดหมู่อย่างเป็นระเบียบ ซ่อนอยู่ในแถบด้านข้างหรือเรียกด้วยปุ่มลัด ไม่เกะกะสายตา

### 4.2 การจัดหมวดหมู่เครื่องมือ (Categorized Tool Modules)

| หมวดหมู่ | ไอคอน | เครื่องมือที่มีให้ในหมวด (One-Click Actions) |
| :--- | :---: | :--- |
| **💬 แชทหลัก (General Chat)** | ⚡ | ถาม-ตอบทั่วไป, Auto-Model Badge, แนบไฟล์ในเครื่อง, ปุ่ม Star บันทึกคำตอบ |
| **💰 การเงิน (Finance)** | 📊 | บันทึกรายรับ-รายจ่ายด่วน, จำลองดอกเบี้ยทบต้น, วางแผนงบประมาณประจำเดือน, กราฟสรุปการเงิน |
| **🩺 สุขภาพ & กิจวัตร (Health & Habits)** | 🥗 | Habit Tracker (เช็คพฤติกรรม), แนะนำตารางออกกำลังกาย, วางแผนตารางเวลาชีวิต (Routine Planner) |
| **📚 การเรียน & พัฒนาตนเอง (Study)** | 🎓 | สรุปบทเรียนจากไฟล์/ข้อความ, วาง Roadmap การเรียน, ทำแบบทดสอบ Flashcard ทบทวน |
| **🧠 ความจำส่วนตัว (Memory & Profile)** | ⭐ | ดูและแก้ไขข้อมูลที่ AI จำเกี่ยวกับเรา, ดูคลังคำตอบที่เคยกด Favorite/Star ไว้ |
| **📁 คลังเอกสาร (Personal Vault)** | 📂 | ลากไฟล์ PDF/CSV/MD มาวางใน Vault เพื่อให้ AI ทำ Indexing และนำไปใช้อ้างอิง |

---

## 5. รายละเอียดเทคโนโลยีแต่ละส่วน (Component Breakdown)

### 5.1 Backend & Orchestration
- **Framework:** **Python 3.11+ / FastAPI**
- **Ollama Engine:** `httpx` Async Streaming API เชื่อมต่อ Local Ollama (`http://127.0.0.1:11434`)
- **Routing Engine:** Regex Pattern Matcher ผสมกับ `qwen2.5:3b` Zero-shot Intent Classifier
- **Sandbox Execution:** Local Python Subprocess สำหรับคำนวณและวาดกราฟแบบปลอดภัย

### 5.2 Frontend UI
- **Tech Stack:** **React (Vite) + TailwindCSS / Glassmorphism**
- **Component Styling:** Modern Dark Theme, Smooth Transitions, Minimal Clean Layout
- **Rendering Libraries:**
  - `react-markdown` + `highlight.js` (แสดงผลโค้ด)
  - `KaTeX` (แสดงผลสูตรคำนวณและคณิตศาสตร์)
  - `Chart.js` / `Recharts` (แสดงผลกราฟสถิติและการเงิน)
