import pytest
from pathlib import Path
from app.services.sandbox_service import sandbox_service

def test_sandbox_python_execution():
    code = "import math; print(f'PI_VAL={math.pi:.4f}')"
    result = sandbox_service.execute_python(code, timeout=3.0)
    assert result["success"] is True
    assert "PI_VAL=3.1416" in result["stdout"]
    assert result["execution_time_ms"] > 0

def test_sandbox_timeout_handling():
    infinite_code = "import time; time.sleep(5)"
    result = sandbox_service.execute_python(infinite_code, timeout=1.0)
    assert result["success"] is False
    assert "timed out" in result["stderr"]

def test_dark_chart_generation():
    chart_res = sandbox_service.generate_dark_chart(
        chart_type="bar",
        data={
            "labels": ["Food", "Bills", "Transport"],
            "values": [4500, 3200, 1800]
        },
        title="ค่าใช้จ่ายประจำเดือน",
        ylabel="บาท"
    )
    assert chart_res["success"] is True
    assert Path(chart_res["file_path"]).exists()
    assert chart_res["image_url"].startswith("/api/cache/charts/")

def test_compound_interest_calculation():
    res = sandbox_service.calculate_compound_interest(
        principal=100000,
        monthly_contribution=5000,
        annual_rate_pct=7.0,
        years=5
    )
    assert res["final_balance"] > res["total_deposits"]
    assert res["total_deposits"] == 100000 + (5000 * 60)
    assert res["total_interest_earned"] > 0
    assert len(res["yearly_breakdown"]["years"]) == 6
