import pytest
import pytest_asyncio
from app.modules.study import study_module

@pytest.mark.asyncio
async def test_roadmap_generation():
    roadmap = await study_module.generate_skill_roadmap(
        topic="FastAPI และ Asynchronous Python",
        total_weeks=3,
        target_level="Intermediate"
    )
    assert roadmap["topic"] is not None
    assert len(roadmap["weeks"]) >= 3
    assert "core_concepts" in roadmap["weeks"][0]

@pytest.mark.asyncio
async def test_flashcard_generation():
    text = "FastAPI คือ web framework สมัยใหม่ที่รวดเร็ว พัฒนาบน Starlette และ Pydantic รองรับ async/await"
    flashcards = await study_module.generate_flashcards(content_or_topic=text, count=2)
    assert len(flashcards) > 0
    assert "front" in flashcards[0]
    assert "back" in flashcards[0]

@pytest.mark.asyncio
async def test_quiz_generation():
    quiz = await study_module.generate_quiz(topic="Python Asyncio", count=2)
    assert len(quiz) > 0
    assert "question" in quiz[0]
    assert "options" in quiz[0]
    assert len(quiz[0]["options"]) == 4
    assert "correct_index" in quiz[0]
