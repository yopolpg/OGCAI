---
name: ogcai-phase-reporter
description: Generate comprehensive post-execution progress reports for OGCAI phases covering pass/fail status, bottlenecks, unsupported commands/limitations, and test results.
---

# OGCAI Phase & Task Post-Execution Reporter Skill

Use this skill whenever a development phase, task, or major milestone is finished to generate a standardized, high-transparency post-run report.

## 📋 Standard Report Structure (โครงสร้างรายงานมาตรฐาน)

When reporting back to the user after finishing work, format the report using the following markdown template:

```markdown
# 📊 รายงานสรุปผลการทำงาน (Phase Execution Report)

### 1. สถานะภาพรวม (Overall Status)
- **Phase/Task:** [ชื่อ Phase และ Task ที่ทำ]
- **ผลลัพธ์:** `[✅ ผ่าน / PASSED]` หรือ `[❌ ไม่ผ่าน / FAILED]`
- **ความคืบหน้ารวมของโครงการ:** XX%

### 2. สิ่งที่สร้างและพัฒนาสำเร็จ (Completed Deliverables)
- รายการไฟล์ที่สร้าง/แก้ไข พร้อม clickable links
- ความสามารถใหม่ที่เพิ่มเข้ามาในระบบ

### 3. 🚧 จุดที่ติดปัญหาและวิธีแก้ไข (Bottlenecks & Resolutions)
- ระบุปัญหาหรือ Error ที่พบระหว่างการพัฒนา (เช่น ปัญหา Event Loop, Concurrency, Package Conflict)
- แนวทางและวิธีแก้ปัญหาที่ใช้

### 4. ⚠️ คำสั่ง/เครื่องมือที่ใช้ไม่ได้หรือมีข้อจำกัด (Command & Tool Limitations)
- ระบุคำสั่ง Terminal/Shell ที่ใช้ไม่ได้บนระบบ Windows (เช่น `python` แทนที่จะเป็น `uv`, ข้อจำกัดของ hardlink, pip shim)
- คำแนะนำวิธีรันคำสั่งที่ถูกต้องสำหรับเครื่องนี้

### 5. 🧪 ผลการทดสอบ (Verification & Test Matrix)
- ตารางสรุปผลการรัน Test Suite (Total Passed / Failed, Execution Time)
- รายละเอียดแต่ละ Test Case ที่ตรวจสอบ

### 6. ⏭️ แผนงานและขั้นตอนถัดไป (Next Steps)
- สรุปงานที่จะต้องทำต่อใน Phase ถัดไป
```

## 💡 Quick Rules
1. Always list exact filenames with clickable links `[filename](file:///d:/OGCAI/...)`.
2. Explicitly mention any Windows-specific command nuances (e.g. using `uv pip` instead of `python -m pip`).
3. Keep the report clear, transparent, and actionable.
