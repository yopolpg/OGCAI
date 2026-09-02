import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_memory_and_vault_api_endpoints():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Create Conversation
        conv_res = await client.post("/api/conversations", json={"title": "แชททดสอบ API"})
        assert conv_res.status_code == 200
        conv_data = conv_res.json()
        conv_id = conv_data["id"]
        assert conv_id is not None

        # 2. List Conversations
        list_res = await client.get("/api/conversations")
        assert list_res.status_code == 200
        conv_list = list_res.json()
        assert any(c["id"] == conv_id for c in conv_list)

        # 3. Create & Get Profile Fact
        fact_res = await client.post("/api/profile", json={
            "key": "preferred_theme",
            "value": "dark_glassmorphism",
            "category": "preference"
        })
        assert fact_res.status_code == 200

        profile_res = await client.get("/api/profile")
        assert profile_res.status_code == 200
        facts = profile_res.json()
        assert any(f["key"] == "preferred_theme" for f in facts)

        # 4. Create & Get Starred Knowledge
        starred_res = await client.post("/api/starred", json={
            "title": "เคล็ดลับการเงิน",
            "content": "แบ่งเงิน 50/30/20",
            "tags": "finance"
        })
        assert starred_res.status_code == 200

        get_starred_res = await client.get("/api/starred")
        assert get_starred_res.status_code == 200
        starred_items = get_starred_res.json()
        assert len(starred_items) > 0

        # 5. Vault Files & Search
        files_res = await client.get("/api/vault/files")
        assert files_res.status_code == 200
        
        search_res = await client.post("/api/vault/search", json={"query": "OGCAI", "top_k": 2})
        assert search_res.status_code == 200
        assert "results" in search_res.json()
