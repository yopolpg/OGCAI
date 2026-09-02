import pytest
from pathlib import Path
from app.config import settings
from app.services.rag_service import rag_service

def test_rag_vault_indexing_and_search():
    # 1. Create sample document in vault
    sample_doc = settings.VAULT_DIR / "ogcai_guide.md"
    sample_doc.write_text(
        "# คู่มือการใช้งาน OGCAI\n\n"
        "OGCAI คือผู้ช่วย AI ส่วนตัวที่ทำงานแบบ Local 100% บนเครื่องคอมพิวเตอร์ของคุณ\n"
        "มีความสามารถในการสลับโมเดลอัตโนมัติ และจัดเก็บข้อมูลความจำส่วนตัวขนาดใหญ่กว่า 150GB+\n",
        encoding="utf-8"
    )

    # 2. Index the file
    chunks = rag_service.index_file(sample_doc)
    assert chunks > 0

    # 3. Test Search
    results = rag_service.search_vault("จุดเด่นของ OGCAI และพื้นที่จัดเก็บ", top_k=2)
    assert len(results) > 0
    assert any("OGCAI" in r["content"] for r in results)

    # 4. Test RAG context builder
    context = rag_service.build_rag_context("ความจุพื้นที่จัดเก็บ 150GB", top_k=1)
    assert "ข้อมูลอ้างอิงจากคลังเอกสารส่วนตัว" in context
    assert "ogcai_guide.md" in context
